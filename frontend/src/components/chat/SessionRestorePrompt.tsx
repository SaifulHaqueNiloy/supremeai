import React, { useState, useEffect } from 'react';
import { RefreshCcw, X, Clock, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { apiClient } from '../../services/apiClient';

interface SessionDNA {
  session_id: string;
  last_active: string;
  summary: string;
  topics: string[];
  memories_count: number;
}

interface Props {
  onRestore: (dna: SessionDNA) => void;
  onDismiss: () => void;
}

export const SessionRestorePrompt: React.FC<Props> = ({ onRestore, onDismiss }) => {
  const [dna, setDna] = useState<SessionDNA | null>(null);
  const [loading, setLoading] = useState(true);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const fetchSessionDna = async () => {
      try {
        const response = await apiClient.get<{ success: boolean; dna: SessionDNA | null }>('/api/chat/session-dna');
        if (response.success && response.dna) {
          setDna(response.dna);
        } else {
          setIsVisible(false);
        }
      } catch (error) {
        console.error('Failed to fetch session DNA:', error);
        setIsVisible(false);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSessionDna();
  }, []);

  if (loading || !isVisible || !dna) {
    return null;
  }

  const handleRestore = () => {
    onRestore(dna);
    setIsVisible(false);
  };

  const handleDismiss = () => {
    onDismiss();
    setIsVisible(false);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="absolute top-4 right-4 z-50 w-96 bg-slate-900/90 backdrop-blur-md border border-indigo-500/30 rounded-2xl p-5 shadow-[0_0_30px_rgba(79,70,229,0.15)] text-slate-200"
      >
        <button 
          onClick={handleDismiss}
          className="absolute top-3 right-3 text-slate-400 hover:text-white transition-colors"
        >
          <X size={16} />
        </button>
        
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-500/30">
            <Brain size={20} className="text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Continue Previous Thread?</h3>
            <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
              <Clock size={10} />
              <span>Last active: {dna.last_active}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-slate-800/50 rounded-xl p-3 mb-4 text-xs leading-relaxed text-slate-300 border border-slate-700/50">
          <span className="text-indigo-300 font-semibold mb-1 block">Context DNA:</span>
          {dna.summary}
          
          {dna.topics && dna.topics.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {dna.topics.map((topic, i) => (
                <span key={i} className="px-1.5 py-0.5 bg-slate-700 rounded text-[9px] font-mono text-indigo-200 border border-slate-600">
                  {topic}
                </span>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={handleRestore}
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-bold text-white shadow-lg shadow-indigo-900/20 transition-all active:scale-95"
          >
            <RefreshCcw size={14} />
            RESTORE CONTEXT
          </button>
          <button 
            onClick={handleDismiss}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold text-slate-300 transition-colors border border-slate-700"
          >
            New Session
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
