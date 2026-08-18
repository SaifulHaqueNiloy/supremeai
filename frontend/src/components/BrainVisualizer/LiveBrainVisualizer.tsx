import React, { useEffect, useRef, useState } from "react";

interface Node {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface Edge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export const LiveBrainVisualizer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [activeNode, setActiveNode] = useState<Node | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Initial fetch snapshot
    fetch("/api/brain-visualizer/snapshot")
      .then((res) => res.json())
      .then((data) => {
        if (data.nodes) {
          const initializedNodes = data.nodes.map((n: Node, idx: number) => ({
            ...n,
            x: 200 + Math.cos(idx) * 150 + (Math.random() - 0.5) * 50,
            y: 200 + Math.sin(idx) * 150 + (Math.random() - 0.5) * 50,
            vx: 0,
            vy: 0,
          }));
          setGraphData({ nodes: initializedNodes, edges: data.edges || [] });
        }
      })
      .catch(() => {
        // Fallback demo graph
        setGraphData({
          nodes: [
            { id: "agent_orchestrator", label: "Orchestrator", type: "Agent", x: 250, y: 150 },
            { id: "skill_mcp_mesh", label: "MCP Mesh", type: "Skill", x: 150, y: 250 },
            { id: "memory_pgvector", label: "Eternal Brain", type: "Memory", x: 350, y: 250 },
          ],
          edges: [
            { source: "agent_orchestrator", target: "skill_mcp_mesh", type: "USES_SKILL", weight: 1.0 },
            { source: "agent_orchestrator", target: "memory_pgvector", type: "RECALLS", weight: 1.0 },
          ],
        });
      });

    // WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/api/brain-visualizer/ws`);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "NODE_PULSE") {
          setActiveNode(payload.data);
        }
      } catch {
        // ignore malformed ws messages
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  // 2D Canvas Force Simulation & Neon Cyberpunk Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw Edges
      graphData.edges.forEach((edge) => {
        const src = graphData.nodes.find((n) => n.id === edge.source);
        const tgt = graphData.nodes.find((n) => n.id === edge.target);
        if (src && tgt && src.x && src.y && tgt.x && tgt.y) {
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(tgt.x, tgt.y);
          ctx.strokeStyle = "rgba(59, 130, 246, 0.4)";
          ctx.lineWidth = 1.5;
          ctx.stroke();
        }
      });

      // Draw Nodes
      graphData.nodes.forEach((node) => {
        if (!node.x || !node.y) return;

        const isHighlighted = activeNode?.id === node.id;
        const radius = isHighlighted ? 12 : 8;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);

        // Neon Glow Colors by Type
        if (node.type === "Agent") {
          ctx.fillStyle = "#10B981"; // Emerald
          ctx.shadowColor = "#10B981";
        } else if (node.type === "Skill") {
          ctx.fillStyle = "#8B5CF6"; // Purple
          ctx.shadowColor = "#8B5CF6";
        } else {
          ctx.fillStyle = "#3B82F6"; // Blue
          ctx.shadowColor = "#3B82F6";
        }

        ctx.shadowBlur = isHighlighted ? 15 : 6;
        ctx.fill();
        ctx.shadowBlur = 0; // reset

        // Label
        ctx.fillStyle = "#E2E8F0";
        ctx.font = "10px Inter, sans-serif";
        ctx.fillText(node.label || node.id, node.x + 12, node.y + 3);
      });

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [graphData, activeNode]);

  return (
    <div className="relative w-full h-[400px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-2xl p-4">
      <div className="absolute top-3 left-4 z-10 flex items-center gap-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
          SupremeAI Neural Matrix
        </span>
        <span
          className={`h-2 w-2 rounded-full ${
            wsConnected ? "bg-emerald-500 animate-ping" : "bg-slate-600"
          }`}
        />
      </div>
      <canvas
        ref={canvasRef}
        width={600}
        height={400}
        className="w-full h-full cursor-crosshair"
      />
    </div>
  );
};
