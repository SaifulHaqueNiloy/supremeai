import React, { useState } from "react";
import { DashboardLayout } from "./DashboardLayout";

interface DashboardShellProps {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  isServerOnline: boolean;
  workspace: React.ReactNode;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
}

export const DashboardShell: React.FC<DashboardShellProps> = ({
  isServerOnline,
  workspace
}) => {
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: '1', sender: 'user', text: 'How can I optimize this function?' },
  ]);
  const [chatInput, setChatInput] = useState('');

  const handleSendMessage = () => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;

    // Add user message
    setChatMessages(prev => [...prev, { id: crypto.randomUUID(), sender: 'user', text: trimmed }]);
    setChatInput('');

    // Simulate AI response
    setTimeout(() => {
      setChatMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        sender: 'ai',
        text: 'I can help optimize that. Could you share the full function and the performance concern you are facing?'
      }]);
    }, 600);
  };

  return (
    <DashboardLayout title="Dashboard">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Workspace */}
        <div className="lg:col-span-2">
          {workspace}

          {/* Code Editor Panel */}
          <div className="mt-6 bg-gray-900 text-white rounded-xl shadow-sm border border-gray-800 overflow-hidden">
            <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center">
              <span className="text-sm font-medium">index.tsx</span>
            </div>
            <div className="p-4 font-mono text-sm">
              <pre className="text-gray-300">
                <code>
                  {`import React from 'react';\n\nexport const App = () => {\n  return <div>Hello World!</div>;\n};`}
                </code>
              </pre>
            </div>
          </div>
        </div>

        {/* Right Column - Server Status */}
        <div className="space-y-6">
          {/* Server Status */}
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 p-4">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-2 ${isServerOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                Server Status: {isServerOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 p-4">
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Active Projects</h3>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">24</p>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 p-4">
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tasks Completed</h3>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">142</p>
            </div>
          </div>

          {/* AI Assistant */}
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 flex flex-col h-[400px]">
            <div className="p-4 border-b border-gray-200 dark:border-slate-800">
              <h3 className="font-semibold text-gray-900 dark:text-white">AI Assistant</h3>
            </div>
            <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`text-sm max-w-[85%] p-3 rounded-lg ${msg.sender === 'user'
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100 self-end'
                      : 'bg-gray-100 dark:bg-slate-800 text-gray-800 dark:text-gray-200 self-start'
                    }`}
                >
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="p-4 border-t border-gray-200 dark:border-slate-800">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Ask AI anything..."
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-700 rounded-lg text-sm bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSendMessage}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
