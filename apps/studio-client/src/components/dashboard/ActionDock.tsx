import React, { useState } from 'react';
import { useDroppable, useDraggable, DndContext } from '@dnd-kit/core';
import { GitBranch, MessageSquare, UploadCloud, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface IntegrationState {
  state: 'idle' | 'processing' | 'success' | 'error';
  message: string;
}

export function ActionDock({ sessionId }: { sessionId: string }) {
  const [integration, setIntegration] = useState<IntegrationState>({ state: 'idle', message: 'Drag a file to an integration below' });

  const handleDragEnd = async (event: any) => {
    const { over, active } = event;
    if (over) {
      const toolId = over.id; // 'github' or 'slack'
      setIntegration({ state: 'processing', message: `Connecting to ${toolId}...` });

      try {
        const res = await fetch(`/api/session/${sessionId}/integrations/${toolId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            triggered_from: 'action_dock',
            active_file: active.id || 'dragged_file.ts',
            content: '// Uploaded from UI'
          })
        });

        const data = await res.json();
        if (res.ok) {
          setIntegration({ state: 'success', message: data.message || 'Success!' });
        } else {
          setIntegration({ state: 'error', message: data.detail || 'Error occurred' });
        }
      } catch (err: any) {
        setIntegration({ state: 'error', message: err.message });
      }
    }
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[var(--supremeai-color-bg-elevated-dark)] border border-[var(--supremeai-color-border-accent-dark)] shadow-2xl shadow-indigo-500/20 rounded-2xl p-4 w-[600px] flex flex-col items-center gap-4">

      {/* Neon Pulse Magic Window */}
      <div className={`w-full py-2 px-4 rounded-xl text-center text-sm font-medium transition-all duration-300 ${
        integration.state === 'processing' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50 animate-pulse' :
        integration.state === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/50' :
        integration.state === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/50' :
        'bg-white/5 text-gray-400 border border-white/10'
      }`}>
        <div className="flex items-center justify-center gap-2">
          {integration.state === 'processing' && <Loader2 className="w-4 h-4 animate-spin" />}
          {integration.state === 'success' && <CheckCircle className="w-4 h-4" />}
          {integration.state === 'error' && <XCircle className="w-4 h-4" />}
          {integration.state === 'idle' && <UploadCloud className="w-4 h-4" />}
          <span>{integration.message}</span>
        </div>
      </div>

      <DndContext onDragEnd={handleDragEnd}>
        <div className="flex items-center justify-center gap-6 w-full">
           <DraggableFile id="example.ts" />
           <div className="h-8 w-[1px] bg-white/10 mx-2" />
           <DroppableIntegration id="github" icon={<GitBranch className="w-6 h-6" />} label="GitHub" />
           <DroppableIntegration id="slack" icon={<MessageSquare className="w-6 h-6" />} label="Slack" />
        </div>
      </DndContext>
    </div>
  );
}

function DraggableFile({ id }: { id: string }) {
  const {attributes, listeners, setNodeRef, transform} = useDraggable({ id });
  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;

  return (
    <div
      ref={setNodeRef} style={style} {...listeners} {...attributes}
      className="cursor-grab active:cursor-grabbing px-4 py-2 bg-white/10 hover:bg-white/15 border border-white/20 rounded-lg text-sm text-gray-200 transition-colors shadow-lg z-50"
    >
      📄 {id}
    </div>
  );
}

function DroppableIntegration({ id, icon, label }: { id: string, icon: React.ReactNode, label: string }) {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border-2 transition-all duration-300 w-24 h-24 ${
        isOver
          ? 'border-indigo-500 bg-indigo-500/20 text-indigo-400 scale-105'
          : 'border-white/10 bg-white/5 text-gray-400 hover:border-white/20 hover:text-gray-200'
      }`}
    >
      {icon}
      <span className="text-xs font-semibold">{label}</span>
    </div>
  );
}
