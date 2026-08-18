"""
Live Brain Visualizer Bridge & WebSocket Stream
================================================
Exposes real-time graph events and WebSocket stream for the 3D Brain Visualizer in Frontend.
"""

from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from memory.context_graph_service import context_graph_service

router = APIRouter(prefix="/brain-visualizer", tags=["Brain Visualizer"])


class VisualizerConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[BrainVisualizer] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[BrainVisualizer] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast_pulse(self, event_type: str, node_data: dict[str, Any]):
        message = {"event": event_type, "data": node_data}
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)


manager = VisualizerConnectionManager()


@router.get("/snapshot")
async def get_graph_snapshot(tenant_id: str = "ALL", limit: int = 200):
    """
    Returns full graph snapshot formatted for 3D visualizer canvas.
    """
    return context_graph_service.export_for_visualizer(tenant_id=tenant_id, limit=limit)


@router.websocket("/ws")
async def websocket_brain_stream(websocket: WebSocket):
    """
    Real-time WebSocket stream for brain synapse pulses and graph mutations.
    """
    await manager.connect(websocket)
    try:
        # Send initial snapshot
        initial_data = context_graph_service.export_for_visualizer(limit=100)
        await websocket.send_json({"event": "INIT_SNAPSHOT", "data": initial_data})

        while True:
            # Keep-alive heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"[BrainVisualizer WS] Error: {e}")
        manager.disconnect(websocket)
