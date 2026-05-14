// ChatWithAI.tsx - Enhanced with Multi-Chat Sessions
import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Space, message, Tag, Tooltip, Modal, Badge } from 'antd';
import {
    SendOutlined,
    RobotOutlined,
    CopyOutlined,
    ThunderboltOutlined,
    DatabaseOutlined,
    PlusOutlined,
    DeleteOutlined,
    EditOutlined,
    MessageOutlined
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

interface ChatSession {
    id: string;
    name: string;
    messages: ChatMessage[];
    createdAt: string;
}

interface ChatWithAIProps {
    chatFont?: string;
}

const ChatWithAI: React.FC<ChatWithAIProps> = ({ chatFont = 'font-mono' }) => {
    // Session State
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [isRenameModalVisible, setIsRenameModalVisible] = useState(false);
    const [sessionToRename, setSessionToRename] = useState<ChatSession | null>(null);
    const [newName, setNewName] = useState('');

    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectedAgent, setSelectedAgent] = useState('all');
    const [agents, setAgents] = useState<any[]>([]);
    const [knowledge, setKnowledge] = useState<{rules: any[], plans: any[], actions: any[]}>({ rules: [], plans: [], actions: [] });
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Load sessions from localStorage on mount
    useEffect(() => {
        const savedSessions = localStorage.getItem('supremeai_chat_sessions');
        if (savedSessions) {
            try {
                const parsed = JSON.parse(savedSessions);
                setSessions(parsed);
                if (parsed.length > 0) {
                    setActiveSessionId(parsed[0].id);
                } else {
                    createNewSession();
                }
            } catch (e) {
                console.error('Failed to parse saved sessions');
                createNewSession();
            }
        } else {
            createNewSession();
        }
        
        fetchAgents();
        fetchKnowledge();
    }, []);

    // Save sessions to localStorage whenever they change
    useEffect(() => {
        if (sessions.length >= 0) {
            localStorage.setItem('supremeai_chat_sessions', JSON.stringify(sessions));
        }
    }, [sessions]);

    const activeSession = sessions.find(s => s.id === activeSessionId);
    const messages = activeSession?.messages || [];

    const createNewSession = () => {
        const newSession: ChatSession = {
            id: Date.now().toString(),
            name: 'New Chat',
            messages: [],
            createdAt: new Date().toISOString()
        };
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
    };

    const deleteSession = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        const filtered = sessions.filter(s => s.id !== id);
        setSessions(filtered);
        if (activeSessionId === id) {
            setActiveSessionId(filtered.length > 0 ? filtered[0].id : null);
            if (filtered.length === 0) {
                // We'll create one in the useEffect if needed, but let's do it here for UX
                setTimeout(() => {
                    if (filtered.length === 0) createNewSession();
                }, 0);
            }
        }
        message.success('Chat deleted');
    };

    const handleRename = (session: ChatSession, e: React.MouseEvent) => {
        e.stopPropagation();
        setSessionToRename(session);
        setNewName(session.name);
        setIsRenameModalVisible(true);
    };

    const saveNewName = () => {
        if (sessionToRename && newName.trim()) {
            setSessions(prev => prev.map(s => 
                s.id === sessionToRename.id ? { ...s, name: newName.trim() } : s
            ));
            setIsRenameModalVisible(false);
            message.success('Chat renamed');
        }
    };

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
            }
        } catch (error) {
            console.error('Failed to fetch agents');
        }
    };

    const fetchKnowledge = async () => {
        try {
            const isAuthenticated = authUtils.isAuthenticated();
            if (!isAuthenticated) {
                setKnowledge({ rules: [], plans: [], actions: [] });
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
                rules: Array.isArray(rules) ? rules.slice(0, 5) : [], 
                plans: Array.isArray(plans) ? plans.slice(0, 5) : [],
                actions: Array.isArray(actions) ? actions.slice(0, 5) : []
            });
        } catch (error) {
            console.error('Failed to fetch knowledge context');
        }
    };

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading || !activeSessionId) return;

        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            sender: 'user',
            agent: 'You',
            content: input,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            status: 'completed'
        };

        // Update session messages
        let currentSessions = [...sessions];
        const sessionIndex = currentSessions.findIndex(s => s.id === activeSessionId);
        if (sessionIndex !== -1) {
            currentSessions[sessionIndex].messages.push(userMessage);
            
            // Smart Name: If first message or default name, generate name
            if (currentSessions[sessionIndex].messages.length === 1 || currentSessions[sessionIndex].name === 'New Chat') {
                const words = input.split(' ');
                currentSessions[sessionIndex].name = words.slice(0, 4).join(' ') + (words.length > 4 ? '...' : '');
            }
            
            setSessions(currentSessions);
        }

        const currentInput = input;
        setInput('');
        setLoading(true);

        try {
            const response = await authUtils.fetchWithAuth('/api/chat/send', {
                method: 'POST',
                body: JSON.stringify({
                    message: currentInput,
                    agent: selectedAgent === 'all' ? null : selectedAgent,
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
                    intent: data.intent || 'NORMAL',
                    status: 'completed',
                };
                
                setSessions(prev => prev.map(s => 
                    s.id === activeSessionId ? { ...s, messages: [...s.messages, aiMessage] } : s
                ));
            }
        } catch (error: any) {
            message.error('Request failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-[700px] bg-[#050505] text-white overflow-hidden border border-white/10 rounded-xl shadow-2xl backdrop-blur-md">
            {/* Left Sidebar: Sessions */}
            <div className="w-64 bg-white/[0.03] border-r border-white/10 flex flex-col">
                <div className="p-4 border-b border-white/10">
                    <Button 
                        type="primary" 
                        icon={<PlusOutlined />} 
                        block 
                        onClick={createNewSession}
                        className="bg-emerald-600 hover:bg-emerald-500 border-none h-10 font-bold flex items-center justify-center gap-2"
                    >
                        New Chat
                    </Button>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                    {sessions.map(s => (
                        <div 
                            key={s.id}
                            onClick={() => setActiveSessionId(s.id)}
                            className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                                activeSessionId === s.id 
                                ? 'bg-white/10 border border-white/20' 
                                : 'hover:bg-white/5 border border-transparent'
                            }`}
                        >
                            <div className="flex items-center gap-3 overflow-hidden">
                                <MessageOutlined className={activeSessionId === s.id ? 'text-emerald-500' : 'text-white/40'} />
                                <span className="text-sm truncate font-medium">{s.name}</span>
                            </div>
                            <div className={`flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity`}>
                                <EditOutlined 
                                    className="text-xs text-white/40 hover:text-white" 
                                    onClick={(e) => handleRename(s, e)}
                                />
                                <DeleteOutlined 
                                    className="text-xs text-white/40 hover:text-red-500" 
                                    onClick={(e) => deleteSession(s.id, e)}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Column: Chat Interface */}
            <div className="flex-1 flex flex-col relative">
                {/* Header */}
                <div className="px-6 py-4 bg-white/[0.01] border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                            <RobotOutlined className="text-emerald-500 text-lg" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white mb-0">{activeSession?.name || 'Neural Chat'}</h3>
                            <span className="text-[10px] text-emerald-500/80 uppercase tracking-widest font-bold">SupremeAI Neural Core</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <select
                            value={selectedAgent}
                            onChange={(e) => setSelectedAgent(e.target.value)}
                            className="bg-black/60 border border-white/10 text-[11px] px-4 py-2 rounded-lg text-white/80 outline-none hover:border-emerald-500/50 transition-all focus:ring-1 focus:ring-emerald-500/30"
                        >
                            <option value="all">Dynamic Routing (All)</option>
                            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                        </select>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-[#050505]">
                    {messages.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-white/20">
                            <div className="w-16 h-16 bg-white/[0.03] rounded-full flex items-center justify-center mb-4 border border-white/5 shadow-inner">
                                <MessageOutlined className="text-3xl text-emerald-500/30" />
                            </div>
                            <span className="text-xs font-medium tracking-[0.3em] uppercase opacity-50">Initiating Neural Connection...</span>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[85%] ${msg.sender === 'user' ? 'order-2' : 'order-1'}`}>
                                    <div className={`flex items-center gap-2 mb-2 px-1 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <span className="text-[10px] font-bold text-white/40 uppercase tracking-tight">
                                            {msg.sender === 'ai' ? msg.agent : 'You'} • {msg.timestamp}
                                        </span>
                                    </div>
                                    <div className={`px-5 py-4 rounded-2xl text-[14px] leading-relaxed shadow-xl ${
                                        msg.sender === 'user'
                                        ? 'bg-gradient-to-br from-emerald-600/30 to-emerald-800/10 border border-emerald-500/30 text-white rounded-tr-none'
                                        : 'bg-white/[0.05] border border-white/10 text-white/90 rounded-tl-none backdrop-blur-md'
                                    }`}>
                                        {msg.content}
                                    </div>
                                    {msg.sender === 'ai' && (
                                        <div className="flex gap-4 mt-2 px-1">
                                            <button
                                                onClick={() => { navigator.clipboard.writeText(msg.content); message.success('Copied to Clipboard'); }}
                                                className="text-[10px] text-white/30 hover:text-emerald-400 transition-all flex items-center gap-1 uppercase font-black"
                                            >
                                                <CopyOutlined /> Copy
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-6 bg-gradient-to-t from-black to-transparent border-t border-white/5">
                    <form onSubmit={handleSendMessage} className="relative group">
                        <Input
                            placeholder="Type a command or question..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={loading}
                            className="h-14 bg-white/[0.03] border-white/10 text-white placeholder:text-white/20 rounded-xl px-6 pr-40 focus:bg-white/[0.06] focus:border-emerald-500/50 transition-all shadow-inner"
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                             <AISuggestionInformer 
                                context="admin_chat" 
                                onSelect={(val) => setInput(val)} 
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                className="h-10 px-6 bg-emerald-600 hover:bg-emerald-500 disabled:bg-white/10 text-white rounded-lg font-bold transition-all disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-emerald-900/40"
                            >
                                {loading ? <ThunderboltOutlined spin /> : <SendOutlined />}
                                {loading ? 'PROCESSING' : 'SEND'}
                            </button>
                        </div>
                    </form>
                    <p className="text-[9px] text-center mt-3 text-white/20 font-bold tracking-[0.2em] uppercase">
                        AI-Driven Autonomy System • Core v4.2 Stable
                    </p>
                </div>
            </div>

            {/* Right Column: Knowledge Context (Optimized) */}
            <div className="w-80 bg-white/[0.01] border-l border-white/10 hidden xl:flex flex-col">
                <div className="p-6">
                    <div className="flex items-center gap-3 mb-8">
                        <DatabaseOutlined className="text-emerald-500" />
                        <h4 className="text-xs font-black text-white uppercase tracking-[0.2em] mb-0">System Context</h4>
                    </div>
                    
                    {knowledge.rules && knowledge.rules.length > 0 ? (
                        <div className="mb-8">
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Active Rules</span>
                                <Badge count={knowledge.rules.length} style={{ backgroundColor: '#10b981', fontSize: '9px', fontWeight: 'bold' }} />
                            </div>
                            <div className="space-y-3">
                                {knowledge.rules.map((r, i) => (
                                    <div key={i} className="p-4 bg-white/[0.02] border border-white/5 rounded-xl text-[11px] text-white/60 leading-relaxed hover:bg-white/[0.04] transition-colors shadow-sm">
                                        {r.content || r.message}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-12 opacity-20">
                            <DatabaseOutlined className="text-3xl mb-3" />
                            <span className="text-[10px] uppercase font-bold tracking-widest">No Active Rules</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Rename Modal */}
            <Modal
                title={<span className="text-white font-bold uppercase tracking-wider">Rename Chat Session</span>}
                open={isRenameModalVisible}
                onOk={saveNewName}
                onCancel={() => setIsRenameModalVisible(false)}
                okText="Save Changes"
                cancelText="Cancel"
                centered
                className="dark-modal"
                styles={{ body: { backgroundColor: '#0a0a0a', borderBottomLeftRadius: '12px', borderBottomRightRadius: '12px' } }}
            >
                <div className="py-4">
                    <label className="block text-[10px] font-black text-white/30 uppercase tracking-[0.2em] mb-3">New Session Name</label>
                    <Input 
                        value={newName} 
                        onChange={(e) => setNewName(e.target.value)}
                        className="bg-white/[0.05] border-white/10 text-white h-12 rounded-xl focus:border-emerald-500/50"
                        placeholder="Enter a descriptive name..."
                        onPressEnter={saveNewName}
                        autoFocus
                    />
                </div>
            </Modal>

            <style>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: rgba(16, 185, 129, 0.2);
                }
                .dark-modal .ant-modal-content {
                    background-color: #0a0a0a;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    overflow: hidden;
                }
                .dark-modal .ant-modal-header {
                    background-color: #0a0a0a;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                .dark-modal .ant-modal-title {
                    color: white;
                }
                .dark-modal .ant-modal-close-x {
                    color: rgba(255, 255, 255, 0.4);
                }
                .dark-modal .ant-btn-primary {
                    background-color: #059669;
                    border: none;
                }
                .dark-modal .ant-btn-default {
                    background-color: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    color: white;
                }
            `}</style>
        </div>
    );
};

export default ChatWithAI;