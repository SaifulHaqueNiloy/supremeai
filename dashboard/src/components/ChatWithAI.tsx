// ChatWithAI.tsx - Clean AI Chat Interface
import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Space, message, Tag, Tooltip } from 'antd';
import {
    SendOutlined,
    RobotOutlined,
    CopyOutlined,
    ThunderboltOutlined,
    DatabaseOutlined,
    BulbOutlined,
    FileTextOutlined
} from '@ant-design/icons';
import { authUtils } from '../lib/authUtils';
import AISuggestionInformer from './AISuggestionInformer';

interface ChatMessage {
    id: string;
    sender: 'user' | 'ai';
    agent: string;
    content: string;
    timestamp: string;
    confidence?: number;
    intent?: string;
    status?: 'pending' | 'completed' | 'error';
}

interface ChatWithAIProps {
    chatFont?: string;
}

const ChatWithAI: React.FC<ChatWithAIProps> = ({ chatFont = 'font-mono' }) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectedAgent, setSelectedAgent] = useState('all');
    const [agents, setAgents] = useState<any[]>([]);
    const [knowledge, setKnowledge] = useState<{rules: any[], plans: any[], actions: any[]}>({ rules: [], plans: [], actions: [] });
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchAgents();
        fetchChatHistory();
        fetchKnowledge();
        const interval = setInterval(() => {
            fetchChatHistory();
            fetchKnowledge();
        }, 15000);
        return () => clearInterval(interval);
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchAgents = async () => {
        try {
            const isAuthenticated = authUtils.isAuthenticated();
            if (!isAuthenticated) {
                const demoAgents = [
                    { id: 'gpt-4o', name: 'GPT-4o', status: 'online', type: 'llm' },
                    { id: 'claude-3', name: 'Claude 3.5', status: 'online', type: 'llm' },
                    { id: 'phi-3', name: 'Phi-3 Mini', status: 'offline', type: 'llm' }
                ];
                setAgents(demoAgents);
                return;
            }

            const response = await authUtils.fetchWithAuth('/api/ai/agents');
            if (response.ok) {
                const data = await response.json();
                setAgents(data);
            } else {
                console.warn('Failed to fetch agents from API, using fallback data');
            }
        } catch (error) {
            console.error('Failed to fetch agents');
        }
    };

    const fetchKnowledge = async () => {
        try {
            const isAuthenticated = authUtils.isAuthenticated();
            if (!isAuthenticated) {
                const demoRules = [
                    { id: 1, content: 'Code quality must be maintained', confidence: 0.9 },
                    { id: 2, content: 'Security scans are required', confidence: 0.95 }
                ];
                const demoPlans = [
                    { id: 1, content: 'Q2 Roadmap: Enhance model orchestration', title: 'Q2 Roadmap' },
                    { id: 2, content: 'Security audit: Third-party penetration testing', title: 'Security Audit' }
                ];
                setKnowledge({ rules: demoRules, plans: demoPlans, actions: [] });
                return;
            }

            const [rulesRes, plansRes, actionsRes] = await Promise.all([
                authUtils.fetchWithAuth('/api/admin/rules').catch(() => null),
                authUtils.fetchWithAuth('/api/admin/plans').catch(() => null),
                authUtils.fetchWithAuth('/api/admin/chat/actions/pending').catch(() => null)
            ]);
            const rules = rulesRes?.ok ? await rulesRes.json() : [];
            const plans = plansRes?.ok ? await plansRes.json() : [];
            const actions = actionsRes?.ok ? await actionsRes.json() : [];
            setKnowledge({ 
                rules: rules.slice(0, 5), 
                plans: plans.slice(0, 5),
                actions: actions.slice(0, 5)
            });
        } catch (error) {
            console.error('Failed to fetch knowledge context');
        }
    };

    const fetchChatHistory = async () => {
        try {
            const user = authUtils.getCurrentUser();
            const userId = user?.uid || 'anonymous';
            const isAuthenticated = authUtils.isAuthenticated();

            if (isAuthenticated) {
                const response = await authUtils.fetchWithAuth(`/api/chat/history?user_id=${userId}&limit=50`);
                if (response.ok) {
                    const data = await response.json();
                    const historyMessages: ChatMessage[] = data.map((item: any) => ({
                        id: item.id,
                        sender: (item.is_admin ? 'ai' : 'user') as 'ai' | 'user',
                        agent: item.is_admin ? 'SupremeAI' : 'Operator',
                        content: item.message,
                        timestamp: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        status: 'completed' as const,
                        intent: item.intent || 'NORMAL'
                    }));
                    setMessages(historyMessages);
                }
            }
        } catch (error) {
            console.error('Failed to fetch chat history');
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            sender: 'user',
            agent: 'You',
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            status: 'completed'
        };

        setMessages(prev => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setLoading(true);

        try {
            let detectedIntent = 'NORMAL';
            if (currentInput.toLowerCase().includes('rule') || currentInput.toLowerCase().includes('must') || currentInput.toLowerCase().includes('always')) {
                detectedIntent = 'RULE';
            } else if (currentInput.toLowerCase().includes('plan') || currentInput.toLowerCase().includes('roadmap') || currentInput.toLowerCase().includes('step')) {
                detectedIntent = 'PROJECT_PLAN';
            } else if (currentInput.toLowerCase().includes('run') || currentInput.toLowerCase().includes('execute') || currentInput.toLowerCase().includes('cmd')) {
                detectedIntent = 'COMMAND';
            }

            const response = await authUtils.fetchWithAuth('/api/chat/send', {
                method: 'POST',
                body: JSON.stringify({
                    message: currentInput,
                    agent: selectedAgent === 'all' ? null : selectedAgent,
                    detected_intent: detectedIntent
                }),
            });

            if (response.ok) {
                const data = await response.json();
                const aiMessage: ChatMessage = {
                    id: (Date.now() + 1).toString(),
                    sender: 'ai',
                    agent: data.agent_name || 'Neural Core',
                    content: data.message || 'Processing optimized.',
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    confidence: data.confidence ? Math.round(data.confidence * 100) : 98,
                    intent: data.intent || detectedIntent,
                    status: 'completed',
                };
                setMessages((prev) => [...prev, aiMessage]);

                if (aiMessage.intent === 'RULE' || aiMessage.intent === 'PROJECT_PLAN') {
                    message.success(`Knowledge updated`);
                    fetchKnowledge();
                }
            }
        } catch (error: any) {
            message.error('Request failed');
        } finally {
            setLoading(false);
        }
    };

    const getIntentColor = (intent?: string) => {
        switch (intent) {
            case 'RULE': return '#f5222d';
            case 'COMMAND': return '#52c41a';
            case 'PROJECT_PLAN': return '#1890ff';
            case 'DEBUG': return '#faad14';
            case 'INFO_COLLECTION': return '#722ed1';
            case 'ADMIN_ACTION': return '#eb2f96';
            default: return 'rgba(255,255,255,0.2)';
        }
    };

    const handleConfirmAction = async (itemId: string, confirmed: boolean) => {
        try {
            const response = await authUtils.fetchWithAuth('/api/chat/confirm', {
                method: 'POST',
                body: JSON.stringify({ item_id: itemId, confirmed, item_type: 'admin_action' })
            });
            if (response.ok) {
                message.success(confirmed ? 'Action confirmed' : 'Action declined');
                fetchKnowledge();
            }
        } catch (error) {
            message.error('Confirmation failed');
        }
    };

    return (
        <div className="flex h-[600px] bg-[#0a0a0a] text-white overflow-hidden border border-white/10 rounded-lg shadow-lg">
            {/* Left Column: Chat Interface */}
            <div className="flex-1 flex flex-col border-r border-white/5 relative">
                {/* Clean Header */}
                <div className="px-4 py-3 bg-white/[0.02] border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <RobotOutlined className="text-emerald-500 text-[16px]" />
                        <span className="text-[14px] font-bold text-white">AI Assistant</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={selectedAgent}
                            onChange={(e) => setSelectedAgent(e.target.value)}
                            className="bg-black/40 border border-white/10 text-[11px] px-3 py-1 rounded text-white/80 outline-none hover:border-emerald-500/30 transition-colors"
                        >
                            <option value="all">All Agents</option>
                            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                        </select>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-white/30">
                            <RobotOutlined className="text-4xl mb-4 text-emerald-500/50" />
                            <span className="text-sm font-medium">Start a conversation...</span>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] ${msg.sender === 'user' ? 'order-2' : 'order-1'}`}>
                                    {/* Sender indicator */}
                                    <div className="flex items-center gap-2 mb-1 px-1">
                                        {msg.sender === 'ai' && <RobotOutlined className="text-xs text-emerald-500" />}
                                        <span className="text-xs font-medium text-white/60">{msg.sender === 'ai' ? 'AI' : 'You'}</span>
                                        {msg.intent && msg.intent !== 'NORMAL' && (
                                            <Tag color={getIntentColor(msg.intent)} className="text-[10px] leading-none py-0 px-1 border-none bg-white/10">
                                                {msg.intent}
                                            </Tag>
                                        )}
                                    </div>

                                    {/* Message bubble */}
                                    <div className={`px-4 py-3 rounded-lg text-sm leading-relaxed ${
                                        msg.sender === 'user'
                                        ? 'bg-emerald-600/20 border border-emerald-500/30 text-white rounded-br-none'
                                        : 'bg-white/[0.05] border border-white/10 text-white/90 rounded-bl-none'
                                    }`}>
                                        {msg.content}
                                    </div>

                                    {/* Action buttons for AI messages */}
                                    {msg.sender === 'ai' && (
                                        <div className="flex gap-2 mt-2 px-1">
                                            <button
                                                onClick={() => { navigator.clipboard.writeText(msg.content); message.success('Copied!'); }}
                                                className="text-xs text-white/40 hover:text-white/80 transition-colors"
                                            >
                                                <CopyOutlined /> Copy
                                            </button>
                                            
                                            {msg.intent === 'ADMIN_ACTION' && msg.status !== 'completed' && (
                                                <div className="flex gap-2">
                                                    <Button 
                                                        size="small" 
                                                        type="primary" 
                                                        ghost 
                                                        className="text-[10px] h-6"
                                                        onClick={() => handleConfirmAction(msg.id, true)}
                                                    >
                                                        Confirm Action
                                                    </Button>
                                                    <Button 
                                                        size="small" 
                                                        danger 
                                                        ghost 
                                                        className="text-[10px] h-6"
                                                        onClick={() => handleConfirmAction(msg.id, false)}
                                                    >
                                                        Decline
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white/[0.02] border-t border-white/5">
                    <form onSubmit={handleSendMessage} className="flex gap-3">
                        <Input
                            placeholder="Type your message..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                            className="flex-1 bg-black/40 border-white/20 text-white placeholder:text-white/40 rounded-lg focus:border-emerald-500/60 transition-all"
                            suffix={<AISuggestionInformer 
                                context="admin_chat" 
                                onSelect={(val) => setInput(val)} 
                                style={{ marginRight: -10 }}
                            />}
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {loading ? <ThunderboltOutlined spin /> : <SendOutlined />}
                            {loading ? 'Sending' : 'Send'}
                        </button>
                    </form>
                </div>
            </div>

            {/* Right Column: Context Panel */}
            <div className="w-80 bg-white/[0.02] border-l border-white/10 flex flex-col">
        {/* Rules Section */}
        {Array.isArray(knowledge.rules) && knowledge.rules.length > 0 && (
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <BulbOutlined className="text-orange-500" />
            <span className="text-sm font-semibold text-white">Active Rules</span>
            <span className="text-xs bg-orange-500/20 text-orange-300 px-2 py-1 rounded">
              {knowledge.rules.length}
            </span>
          </div>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {knowledge.rules.slice(0, 3).map((rule, idx) => (
              <div key={idx} className="text-xs text-white/70 bg-white/5 p-2 rounded border border-white/10">
                {rule.content || rule.message}
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Plans Section */}
        {Array.isArray(knowledge.plans) && knowledge.plans.length > 0 && (
        <div className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileTextOutlined className="text-blue-500" />
            <span className="text-sm font-semibold text-white">Project Plans</span>
            <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
              {knowledge.plans.length}
            </span>
          </div>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {knowledge.plans.slice(0, 3).map((plan, idx) => (
              <div key={idx} className="text-xs text-white/70 bg-white/5 p-2 rounded border border-white/10">
                {plan.content || plan.title}
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Empty state */}
        {(Array.isArray(knowledge.rules) ? knowledge.rules.length : 0) === 0 && 
         (Array.isArray(knowledge.plans) ? knowledge.plans.length : 0) === 0 && (
        <div className="flex-1 flex items-center justify-center text-white/30">
          <div className="text-center">
            <DatabaseOutlined className="text-2xl mb-2" />
            <div className="text-sm">No context available</div>
          </div>
        </div>
        )}
            </div>
        </div>
    );
};

export default ChatWithAI;