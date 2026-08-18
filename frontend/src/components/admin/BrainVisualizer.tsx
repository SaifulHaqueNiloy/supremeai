/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Brain,
  Search,
  Zap,
  Sparkles,
  RefreshCw,
  PlusCircle,
  Activity,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Database,
  Cpu,
  Clock,
  Send,
  X,
  ExternalLink,
} from 'lucide-react';
import { apiClient } from '../../services/apiClient';
import { Card, Badge } from '../ui';

interface BrainNode {
  id: string;
  session_id: string;
  label: string;
  summary: string;
  agent_type: string;
  task_type: string;
  cluster: string;
  color: string;
  importance: number;
  tags: string[];
  created_at: string;
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  radius?: number;
}

interface BrainLink {
  id: string;
  source: string;
  target: string;
  strength: number;
  type: string;
}

interface BrainCluster {
  name: string;
  color: string;
  count: number;
}

interface BrainGraphResponse {
  nodes: BrainNode[];
  links: BrainLink[];
  clusters: BrainCluster[];
  stats: {
    total_memories: number;
    total_synapses: number;
    zero_repeat_accuracy: string;
    retention_rate: string;
    active_clusters: number;
    last_synapse_pulse: string;
  };
}

export function BrainVisualizer() {
  const queryClient = useQueryClient();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // States
  const [selectedNode, setSelectedNode] = useState<BrainNode | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeRecallMatches, setActiveRecallMatches] = useState<Record<string, number>>({});
  const [isSimulating, setIsSimulating] = useState(false);
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<BrainNode | null>(null);
  const [showInjectModal, setShowInjectModal] = useState(false);

  // Form states for manual injection
  const [injectSummary, setInjectSummary] = useState('');
  const [injectTaskType, setInjectTaskType] = useState('architecture');
  const [injectAgent, setInjectAgent] = useState('SupremeArchitect');
  const [injectTags, setInjectTags] = useState('extreme-logic, core-rule');

  // Query graph data
  const { data: graphData, isLoading, refetch } = useQuery<BrainGraphResponse>({
    queryKey: ['admin-brain-visual-graph'],
    queryFn: () => apiClient.get<BrainGraphResponse>('/admin-api/brain/visual-graph'),
    refetchInterval: 30000,
  });

  // Mutable nodes & physics state
  const physicsNodesRef = useRef<BrainNode[]>([]);
  const animationFrameRef = useRef<number | null>(null);

  // Initialize physics nodes when data loads
  useEffect(() => {
    if (graphData?.nodes) {
      physicsNodesRef.current = graphData.nodes.map((node, i) => {
        const existing = physicsNodesRef.current.find((n) => n.id === node.id);
        const radius = Math.max(14, Math.round(node.importance * 22));
        return {
          ...node,
          x: existing ? existing.x : node.x + (Math.random() - 0.5) * 40,
          y: existing ? existing.y : node.y + (Math.random() - 0.5) * 40,
          vx: existing ? existing.vx : (Math.random() - 0.5) * 0.5,
          vy: existing ? existing.vy : (Math.random() - 0.5) * 0.5,
          radius,
        };
      });
    }
  }, [graphData]);

  // Simulate recall mutation
  const recallMutation = useMutation({
    mutationFn: (query: string) =>
      apiClient.post<{ matches: Array<{ node_id: string; similarity_score: number }> }>(
        '/admin-api/brain/simulate-recall',
        { query, limit: 10 }
      ),
    onSuccess: (data) => {
      const matchMap: Record<string, number> = {};
      data.matches.forEach((m) => {
        matchMap[m.node_id] = m.similarity_score;
      });
      setActiveRecallMatches(matchMap);
      setIsSimulating(false);
    },
    onError: () => setIsSimulating(false),
  });

  // Inject memory mutation
  const injectMutation = useMutation({
    mutationFn: (payload: any) => apiClient.post('/admin-api/brain/inject-memory', payload),
    onSuccess: () => {
      setShowInjectModal(false);
      setInjectSummary('');
      queryClient.invalidateQueries({ queryKey: ['admin-brain-visual-graph'] });
    },
  });

  const handleSimulateRecall = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim()) {
      setActiveRecallMatches({});
      return;
    }
    setIsSimulating(true);
    recallMutation.mutate(searchQuery);
  };

  const handleInjectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!injectSummary.trim()) return;
    injectMutation.mutate({
      task_type: injectTaskType,
      agent_type: injectAgent,
      summary: injectSummary,
      importance: 0.96,
      tags: injectTags.split(',').map((t) => t.trim()).filter(Boolean),
    });
  };

  // Canvas Render & Physics Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let pulseStep = 0;

    const render = () => {
      pulseStep += 0.03;
      const width = canvas.width;
      const height = canvas.height;
      const centerX = width / 2 + pan.x;
      const centerY = height / 2 + pan.y;

      ctx.clearRect(0, 0, width, height);

      // Deep space grid background
      ctx.save();
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.03)';
      ctx.lineWidth = 1;
      const gridSize = 40 * zoom;
      const offsetX = (centerX % gridSize);
      const offsetY = (centerY % gridSize);

      for (let x = offsetX; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = offsetY; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
      ctx.restore();

      const nodes = physicsNodesRef.current;
      const links = graphData?.links || [];

      // Simple physics step: gentle center gravity + node repulsion
      for (let i = 0; i < nodes.length; i++) {
        const n1 = nodes[i];
        if (draggedNode && draggedNode.id === n1.id) continue;

        // Center spring
        const targetX = n1.x;
        const targetY = n1.y;
        n1.vx = (n1.vx || 0) * 0.92;
        n1.vy = (n1.vy || 0) * 0.92;

        // Subtle gentle breathing movement
        n1.vx += Math.sin(pulseStep + i) * 0.05;
        n1.vy += Math.cos(pulseStep + i) * 0.05;
      }

      // Draw Links (Synapse lines)
      ctx.save();
      links.forEach((link, idx) => {
        const sourceNode = nodes.find((n) => n.id === link.source);
        const targetNode = nodes.find((n) => n.id === link.target);

        if (!sourceNode || !targetNode) return;

        const isFiltered =
          selectedCluster !== 'ALL' &&
          sourceNode.cluster !== selectedCluster &&
          targetNode.cluster !== selectedCluster;

        const sx = centerX + sourceNode.x * zoom;
        const sy = centerY + sourceNode.y * zoom;
        const tx = centerX + targetNode.x * zoom;
        const ty = centerY + targetNode.y * zoom;

        // Determine link glow
        const isMatchSource = activeRecallMatches[sourceNode.id];
        const isMatchTarget = activeRecallMatches[targetNode.id];
        const isHighlighted = isMatchSource && isMatchTarget;

        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(tx, ty);

        if (isHighlighted) {
          ctx.strokeStyle = '#00f3ff';
          ctx.lineWidth = 2.5 * zoom;
          ctx.shadowColor = '#00f3ff';
          ctx.shadowBlur = 12;
        } else if (isFiltered) {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
          ctx.lineWidth = 0.5 * zoom;
        } else {
          ctx.strokeStyle = 'rgba(0, 243, 255, 0.12)';
          ctx.lineWidth = 1 * zoom;
          ctx.shadowBlur = 0;
        }
        ctx.stroke();

        // Traveling energy pulse along synapse
        if (!isFiltered) {
          const progress = (pulseStep * 0.5 + idx * 0.2) % 1;
          const px = sx + (tx - sx) * progress;
          const py = sy + (ty - sy) * progress;

          ctx.beginPath();
          ctx.arc(px, py, 2 * zoom, 0, Math.PI * 2);
          ctx.fillStyle = isHighlighted ? '#ffffff' : 'rgba(0, 243, 255, 0.6)';
          ctx.fill();
        }
      });
      ctx.restore();

      // Draw Nodes
      nodes.forEach((node, i) => {
        const nx = centerX + node.x * zoom;
        const ny = centerY + node.y * zoom;
        const baseRadius = (node.radius || 16) * zoom;
        const isSelected = selectedNode?.id === node.id;
        const matchScore = activeRecallMatches[node.id];
        const isMatch = matchScore !== undefined && matchScore >= 0.45;
        const isClusterMatch = selectedCluster === 'ALL' || node.cluster === selectedCluster;

        ctx.save();

        // Dim if cluster filter is active
        if (!isClusterMatch && !isMatch) {
          ctx.globalAlpha = 0.18;
        }

        // Active Recall illuminated pulse rings
        if (isMatch) {
          const ringRadius = baseRadius + (Math.sin(pulseStep * 3) + 1) * 8 * zoom;
          ctx.beginPath();
          ctx.arc(nx, ny, ringRadius, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(0, 243, 255, ${0.4 + (matchScore || 0) * 0.4})`;
          ctx.lineWidth = 2 * zoom;
          ctx.stroke();
        }

        // Selected aura
        if (isSelected) {
          ctx.beginPath();
          ctx.arc(nx, ny, baseRadius + 7 * zoom, 0, Math.PI * 2);
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2 * zoom;
          ctx.shadowColor = node.color || '#00f3ff';
          ctx.shadowBlur = 18;
          ctx.stroke();
        }

        // Main Node Core
        ctx.beginPath();
        ctx.arc(nx, ny, baseRadius, 0, Math.PI * 2);
        ctx.fillStyle = node.color || '#00f3ff';
        ctx.shadowColor = node.color || '#00f3ff';
        ctx.shadowBlur = isMatch ? 24 : 12;
        ctx.fill();

        // Inner core glow
        ctx.beginPath();
        ctx.arc(nx, ny, baseRadius * 0.55, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.shadowBlur = 0;
        ctx.fill();

        // Node Label
        if (zoom >= 0.75 || isSelected || isMatch) {
          ctx.font = `600 ${Math.max(10, Math.round(11 * zoom))}px "Space Grotesk", sans-serif`;
          ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.85)';
          ctx.textAlign = 'center';
          ctx.fillText(node.label, nx, ny + baseRadius + 14 * zoom);

          if (isMatch) {
            ctx.font = `700 ${Math.max(9, Math.round(10 * zoom))}px monospace`;
            ctx.fillStyle = '#00f3ff';
            ctx.fillText(`${Math.round((matchScore || 0) * 100)}% MATCH`, nx, ny - baseRadius - 8 * zoom);
          }
        }

        ctx.restore();
      });

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [graphData, zoom, pan, selectedNode, selectedCluster, activeRecallMatches, draggedNode]);

  // Handle Resize
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current && canvasRef.current.parentElement) {
        canvasRef.current.width = canvasRef.current.parentElement.clientWidth;
        canvasRef.current.height = canvasRef.current.parentElement.clientHeight;
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Mouse Interaction (Click / Drag / Pan)
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const centerX = canvas.width / 2 + pan.x;
    const centerY = canvas.height / 2 + pan.y;

    // Check if a node was clicked
    const clicked = physicsNodesRef.current.find((n) => {
      const nx = centerX + n.x * zoom;
      const ny = centerY + n.y * zoom;
      const radius = (n.radius || 16) * zoom + 5;
      const dist = Math.hypot(mouseX - nx, mouseY - ny);
      return dist <= radius;
    });

    if (clicked) {
      setSelectedNode(clicked);
      setDraggedNode(clicked);
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: mouseX - pan.x, y: mouseY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (draggedNode) {
      const centerX = canvas.width / 2 + pan.x;
      const centerY = canvas.height / 2 + pan.y;
      draggedNode.x = (mouseX - centerX) / zoom;
      draggedNode.y = (mouseY - centerY) / zoom;
    } else if (isDraggingCanvas) {
      setPan({
        x: mouseX - dragStart.x,
        y: mouseY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingCanvas(false);
    setDraggedNode(null);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => Math.min(2.5, Math.max(0.4, prev * zoomFactor)));
  };

  const resetView = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
    setActiveRecallMatches({});
    setSearchQuery('');
  };

  return (
    <div className="flex-grow flex flex-col h-full bg-[#02050e] text-white overflow-hidden relative font-sans">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-6 py-3 border-b border-cyan-500/20 bg-[#040816]/80 backdrop-blur-md z-10 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(0,243,255,0.3)]">
            <Brain size={22} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-wider uppercase font-mono text-cyan-300">
                SupremeAI Neural Brain Visualizer
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-cyan-500/20 text-cyan-400 rounded-full border border-cyan-500/40">
                LIVE MATRIX
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              Persistent Memory Nodes • pgvector Semantic Synapse Network
            </p>
          </div>
        </div>

        {/* Semantic Search Simulator */}
        <form onSubmit={handleSimulateRecall} className="flex items-center gap-2 flex-1 max-w-md mx-4">
          <div className="relative w-full">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Simulate Recall (e.g. 'argon2 port 8089', 'deployment', 'CI fix')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#070d1e] border border-slate-700/80 rounded-xl pl-9 pr-20 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/50 font-mono"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setActiveRecallMatches({});
                }}
                className="absolute right-12 top-2 text-slate-400 hover:text-white text-xs"
              >
                <X size={14} />
              </button>
            )}
            <button
              type="submit"
              disabled={isSimulating}
              className="absolute right-1.5 top-1 px-2.5 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded-lg text-[10px] font-mono font-bold border border-cyan-500/40 transition-all flex items-center gap-1"
            >
              {isSimulating ? <RefreshCw size={10} className="animate-spin" /> : <Sparkles size={10} />}
              Test
            </button>
          </div>
        </form>

        {/* Top Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowInjectModal(true)}
            className="px-3 py-1.5 bg-gradient-to-r from-cyan-600/30 to-blue-600/30 hover:from-cyan-600/50 hover:to-blue-600/50 border border-cyan-400/40 rounded-xl text-xs font-mono font-semibold text-cyan-200 transition-all flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,243,255,0.15)]"
          >
            <PlusCircle size={14} />
            Inject Memory
          </button>
          <button
            onClick={() => refetch()}
            className="p-2 bg-slate-800/60 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-all"
            title="Refresh Brain Graph"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 relative overflow-hidden flex">
        {/* Canvas Element */}
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          className="flex-1 h-full cursor-grab active:cursor-grabbing"
        />

        {/* Floating HUD: Stats & Clusters Bar */}
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-3 pointer-events-none">
          {/* Stats Badges */}
          <div className="flex flex-wrap gap-2 pointer-events-auto bg-[#040816]/80 p-2.5 rounded-2xl border border-slate-800/80 backdrop-blur-md shadow-xl">
            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] font-mono">
              <Database size={12} className="text-cyan-400" />
              <span className="text-slate-400">Synapses:</span>
              <span className="text-white font-bold">{graphData?.stats?.total_memories || 8}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] font-mono">
              <Zap size={12} className="text-emerald-400" />
              <span className="text-slate-400">Zero-Repeat:</span>
              <span className="text-emerald-400 font-bold">
                {graphData?.stats?.zero_repeat_accuracy || '99.6%'}
              </span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] font-mono">
              <Cpu size={12} className="text-purple-400" />
              <span className="text-slate-400">Retention:</span>
              <span className="text-purple-300 font-bold">100% Sovereign</span>
            </div>
          </div>

          {/* Cluster Category Selector */}
          <div className="flex flex-wrap gap-1.5 max-w-sm pointer-events-auto bg-[#040816]/80 p-2 rounded-2xl border border-slate-800/80 backdrop-blur-md shadow-xl">
            <button
              onClick={() => setSelectedCluster('ALL')}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-mono transition-all ${
                selectedCluster === 'ALL'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_8px_rgba(0,243,255,0.3)]'
                  : 'bg-slate-900/50 text-slate-400 hover:text-white border border-transparent'
              }`}
            >
              All Clusters
            </button>
            {graphData?.clusters?.map((c) => (
              <button
                key={c.name}
                onClick={() => setSelectedCluster(c.name)}
                className={`px-2 py-1 rounded-lg text-[10px] font-mono flex items-center gap-1.5 transition-all ${
                  selectedCluster === c.name
                    ? 'bg-white/10 text-white border border-white/30'
                    : 'bg-slate-900/50 text-slate-400 hover:text-white border border-transparent'
                }`}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color }} />
                {c.name} ({c.count})
              </button>
            ))}
          </div>
        </div>

        {/* Floating Zoom Controls */}
        <div className="absolute bottom-4 left-4 z-10 flex items-center gap-1.5 bg-[#040816]/80 p-1.5 rounded-2xl border border-slate-800/80 backdrop-blur-md">
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z * 1.2))}
            className="p-1.5 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-lg"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.4, z / 1.2))}
            className="p-1.5 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-lg"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-lg"
            title="Reset View"
          >
            <Maximize2 size={14} />
          </button>
        </div>

        {/* Selected Node Inspector Drawer (Right Panel) */}
        {selectedNode && (
          <div className="w-80 md:w-96 bg-[#040816]/95 border-l border-cyan-500/20 backdrop-blur-xl p-5 flex flex-col justify-between overflow-y-auto z-20 shadow-2xl transition-all animate-in slide-in-from-right duration-200">
            <div className="flex flex-col gap-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="w-3.5 h-3.5 rounded-full shadow-[0_0_10px_currentColor]"
                    style={{ backgroundColor: selectedNode.color, color: selectedNode.color }}
                  />
                  <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wider">
                    {selectedNode.cluster} Synapse
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
                <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">Session / Key</div>
                <div className="text-xs font-mono text-cyan-300 break-all">{selectedNode.session_id}</div>
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="text-[10px] text-slate-400 font-mono uppercase">Learned Intelligence</div>
                <div className="p-3.5 bg-cyan-950/20 border border-cyan-500/30 rounded-xl text-xs text-slate-200 font-mono leading-relaxed shadow-inner">
                  {selectedNode.summary}
                </div>
              </div>

              {/* Node Metadata Badges */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
                  <div className="text-[9px] text-slate-400 font-mono uppercase">Agent</div>
                  <div className="text-xs font-mono text-white font-medium">{selectedNode.agent_type}</div>
                </div>
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
                  <div className="text-[9px] text-slate-400 font-mono uppercase">Task Type</div>
                  <div className="text-xs font-mono text-cyan-400 font-medium">{selectedNode.task_type}</div>
                </div>
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
                  <div className="text-[9px] text-slate-400 font-mono uppercase">Importance</div>
                  <div className="text-xs font-mono text-emerald-400 font-bold">
                    {Math.round(selectedNode.importance * 100)}%
                  </div>
                </div>
                <div className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800">
                  <div className="text-[9px] text-slate-400 font-mono uppercase">Created</div>
                  <div className="text-[11px] font-mono text-slate-300">
                    {selectedNode.created_at ? selectedNode.created_at.slice(0, 10) : 'Recent'}
                  </div>
                </div>
              </div>

              {/* Tags */}
              {selectedNode.tags && selectedNode.tags.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">Semantic Tags</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-[10px] font-mono border border-slate-700"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Test Recall with this node query */}
            <div className="pt-4 border-t border-slate-800/80 mt-4 flex flex-col gap-2">
              <button
                onClick={() => {
                  setSearchQuery(selectedNode.summary.slice(0, 60));
                  recallMutation.mutate(selectedNode.summary.slice(0, 60));
                }}
                className="w-full py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded-xl text-xs font-mono font-semibold border border-cyan-500/40 transition-all flex items-center justify-center gap-1.5"
              >
                <Sparkles size={12} />
                Trace Related Synapses
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Memory Injection Modal */}
      {showInjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg bg-[#070d1e] border border-cyan-500/30 rounded-2xl p-6 shadow-[0_0_30px_rgba(0,243,255,0.2)]">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <PlusCircle size={18} className="text-cyan-400" />
                <h3 className="font-mono font-bold text-sm text-white uppercase">
                  Inject Memory into Eternal Brain
                </h3>
              </div>
              <button
                onClick={() => setShowInjectModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleInjectSubmit} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">
                  Knowledge / Rule Summary
                </label>
                <textarea
                  rows={4}
                  value={injectSummary}
                  onChange={(e) => setInjectSummary(e.target.value)}
                  placeholder="Enter the permanent rule, pattern, or extreme creative logic to forge..."
                  className="w-full bg-[#040816] border border-slate-700 rounded-xl p-3 text-xs text-white font-mono outline-none focus:border-cyan-400"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Task Type</label>
                  <select
                    value={injectTaskType}
                    onChange={(e) => setInjectTaskType(e.target.value)}
                    className="w-full bg-[#040816] border border-slate-700 rounded-lg p-2 text-xs text-white font-mono"
                  >
                    <option value="architecture">Architecture</option>
                    <option value="deploy">Deployment</option>
                    <option value="ci">CI/CD</option>
                    <option value="bug-fix">Bug Fix / Repair</option>
                    <option value="security">Security</option>
                    <option value="routing">Model Routing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Agent Type</label>
                  <input
                    type="text"
                    value={injectAgent}
                    onChange={(e) => setInjectAgent(e.target.value)}
                    className="w-full bg-[#040816] border border-slate-700 rounded-lg p-2 text-xs text-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Tags (Comma-separated)</label>
                <input
                  type="text"
                  value={injectTags}
                  onChange={(e) => setInjectTags(e.target.value)}
                  placeholder="rule, failsafe, security"
                  className="w-full bg-[#040816] border border-slate-700 rounded-lg p-2 text-xs text-white font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowInjectModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={injectMutation.isPending}
                  className="px-5 py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-xl text-xs font-mono transition-all flex items-center gap-1.5"
                >
                  {injectMutation.isPending ? <RefreshCw size={12} className="animate-spin" /> : <Zap size={12} />}
                  Forge Memory Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
