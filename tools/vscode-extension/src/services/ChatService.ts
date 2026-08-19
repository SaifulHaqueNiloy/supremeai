/**
 * ChatService — handles all chat messaging, streaming (WebSocket + REST SSE),
 * and local fallback response generation.
 * Thin Client নীতি: সমস্ত LLM orchestration SupremeAI backend-এর মাধ্যমে।
 */

import * as vscode from 'vscode';
import WebSocket from 'ws';
import { AxiosInstance } from 'axios';
import { AuthService } from './AuthService';
import {
  ChatMessage,
  ChatRequest,
  ChatResponse,
  SupremeAIConfig,
} from '../types';

export class ChatService {
  constructor(
    private client: AxiosInstance,
    private config: SupremeAIConfig,
    private sessionId: string,
  ) {}

  /**
   * Send a chat message (non-streaming)
   * POST /api/chat/message
   */
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await this.client.post<ChatResponse>('/api/chat/message', {
        ...request,
        sessionId: this.sessionId,
      });
      return response.data;
    } catch (error: any) {
      console.error(`[SupremeAI] Chat error: ${error.message}`);
      // Fallback to backend via REST stream when primary chat endpoint is unreachable
      const fallbackReply = await this.streamChatCompletion(
        { ...request, message: this.buildContextAwareMessage(request) },
      );
      return {
        success: true,
        message: 'Success (Fallback)',
        response: fallbackReply,
        sessionId: this.sessionId,
        timestamp: new Date().toISOString(),
      };
    }
  }

  buildContextAwareMessage(request: ChatRequest): string {
    let fullMessage = request.message || '';
    const contextParts: string[] = [];
    const filePath = request.context?.filePath || (request as any).filePath;
    const language = request.context?.language || (request as any).language;
    if (filePath) contextParts.push(`File: ${filePath}`);
    if (language) contextParts.push(`Language: ${language}`);
    const code = (request as any).codeContext || (request as any).code;
    if (code) {
      contextParts.push(`Code:\n\`\`\`\n${code}\n\`\`\``);
    }
    if (contextParts.length > 0) {
      fullMessage += '\n\n--- Context ---\n' + contextParts.join('\n');
    }
    return fullMessage;
  }

  /**
   * Stream chat response — prefers /ws/chat WebSocket, falls back to REST SSE.
   */
  async streamChatResponse(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    const authService = AuthService.getInstance();
    if (authService && authService.isAuthenticated()) {
      try {
        return await this.streamChatOverWs(request, onToken);
      } catch (err: any) {
        console.warn(`[SupremeAI] /ws/chat failed, falling back to REST: ${err?.message}`);
      }
    }
    return this.streamChatCompletion(request, onToken);
  }

  /**
   * Stream chat over /ws/chat WebSocket with auth-first-message handshake.
   * বাংলা: টোকেন URL-এ নয়, সংযোগের পর প্রথম মেসেজে {"type":"auth","token":...} পাঠানো হয়।
   */
  async streamChatOverWs(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    const token = AuthService.getInstance()?.getToken();
    if (!token) {
      throw new Error('No auth token available for /ws/chat');
    }

    const wsUrl = `${this.getWsBaseUrl()}/ws/chat`;
    const socket = new WebSocket(wsUrl);

    return new Promise<string>((resolve, reject) => {
      let fullText = '';
      let settled = false;
      const finish = (action: 'resolve' | 'reject', value?: any) => {
        if (settled) return;
        settled = true;
        if (action === 'resolve') {
          resolve(value);
        } else {
          reject(value instanceof Error ? value : new Error(String(value)));
        }
      };

      const timer = setTimeout(() => {
        finish('reject', new Error('WebSocket chat timed out'));
        socket.close();
      }, 60000);

      socket.on('open', () => {
        socket.send(JSON.stringify({ type: 'auth', token }));
        socket.send(JSON.stringify({ ...request, sessionId: this.sessionId }));
      });

      socket.on('message', (data: Buffer | string) => {
        const text = data.toString();
        if (text.includes('[DONE]')) {
          clearTimeout(timer);
          finish('resolve', fullText);
          socket.close();
          return;
        }
        if (text.includes('[Error:')) {
          clearTimeout(timer);
          finish('reject', new Error(text));
          socket.close();
          return;
        }
        if (text.trim()) {
          fullText += text;
          onToken?.(text);
        }
      });

      socket.on('error', (err: any) => {
        clearTimeout(timer);
        finish('reject', err);
      });

      socket.on('close', () => {
        clearTimeout(timer);
        finish('resolve', fullText);
      });
    });
  }

  async streamChatCompletion(request: ChatRequest, onToken?: (token: string) => void): Promise<string> {
    try {
      const base = this.config.backendUrl.replace(/\/$/, '');
      const url = `${base}/api/chat/stream`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(AuthService.getInstance()?.getToken()
            ? { Authorization: `Bearer ${AuthService.getInstance()!.getToken()!}` }
            : {}),
        },
        body: JSON.stringify({ ...request, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`Stream failed with status ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No readable stream in response');
      }

      const decoder = new TextDecoder();
      let fullText = '';

      // বাংলা মন্তব্য: 'no-constant-condition' এড়াতে 'for (;;)' ব্যবহার করা হলো
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const parts = chunk.split('\n');
        for (const part of parts) {
          const trimmed = part.trim();
          if (!trimmed.startsWith('data:')) continue;
          const payload = trimmed.slice(5).trim();
          if (payload === '[DONE]') break;
          try {
            const parsed = JSON.parse(payload);
            const token = parsed.token ?? parsed.content ?? parsed.text ?? '';
            if (typeof token === 'string' && token) {
              fullText += token;
              onToken?.(token);
            }
          } catch {
            if (payload) {
              fullText += payload;
              onToken?.(payload);
            }
          }
        }
      }

      return fullText;
    } catch (error: any) {
      console.error(`[SupremeAI] Completion stream error: ${error.message}`);
      throw new Error(`Backend stream error: ${error.message}`);
    }
  }

  async getChatHistory(sessionId?: string): Promise<ChatMessage[]> {
    try {
      const response = await this.client.get('/api/chat/history', {
        params: { sessionId: sessionId || this.sessionId },
      });
      return response.data.messages || [];
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to get chat history: ${error.message}`);
      return [];
    }
  }

  async clearChatHistory(sessionId?: string): Promise<boolean> {
    try {
      await this.client.delete('/api/chat/history', {
        data: { sessionId: sessionId || this.sessionId },
      });
      return true;
    } catch (error: any) {
      console.error(`[SupremeAI] Failed to clear chat history: ${error.message}`);
      return false;
    }
  }

  /** Generate a fully offline fallback response when backend is unreachable. */
  generateFallbackResponse(message: string): string {
    const lowerMsg = message.toLowerCase();
    if (lowerMsg.includes('bangla') || lowerMsg.includes('বাংলা')) {
      return 'হ্যাঁ, আমি বাংলায় কথা বলতে পারি! আমি আপনার সুপ্রিমএআই (SupremeAI) অ্যাসিস্ট্যান্ট। আমি আপনাকে কোডিং, বাগ ফিক্সিং এবং কোড রিফ্যাক্টরিংয়ে সাহায্য করতে পারি।';
    }
    if (lowerMsg.includes('hello') || lowerMsg.includes('hi') || lowerMsg.includes('hey')) {
      return "Hello! I'm your SupremeAI assistant. How can I help you with your code today?";
    }
    if (lowerMsg.includes('bug') || lowerMsg.includes('error') || lowerMsg.includes('fix')) {
      return "I can help you debug! Please share the error message or the problematic code, and I'll analyze it for you.";
    }
    if (lowerMsg.includes('refactor') || lowerMsg.includes('improve') || lowerMsg.includes('optimize')) {
      return "I can help refactor your code! Please share the code you'd like to improve, and I'll suggest optimizations.";
    }
    return (
      "I'm here to help with your coding needs! You can ask me to:\n" +
      '• Explain code\n• Fix bugs\n• Refactor code\n• Review code\n• Answer programming questions\n\nPlease share your code or question!'
    );
  }

  private getWsBaseUrl(): string {
    const base = (this.config.backendUrl || '').replace(/\/$/, '');
    if (base.startsWith('https://')) return 'wss://' + base.slice('https://'.length);
    if (base.startsWith('http://')) return 'ws://' + base.slice('http://'.length);
    return base;
  }
}
