import json

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi import status
from loguru import logger

from core.messaging.event_bus import ErrorEvent
from core.messaging.event_bus import error_event_bus
import jwt
from core.config import settings


router = APIRouter(prefix="/ws/hitl", tags=["hitl"])


class HITLConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New HITL WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"HITL WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to HITL WebSocket: {e}")
                self.disconnect(connection)


manager = HITLConnectionManager()


async def hitl_event_listener(event: ErrorEvent):
    """Listens to the event bus and broadcasts HITL review requests to active WebSockets."""
    if event.error_type == "HITL_REVIEW_REQUIRED":
        payload = {
            "type": "HITL_REVIEW_REQUIRED",
            "message": event.message,
            "context": event.context,
            "severity": event.severity,
            "module": event.module,
        }
        await manager.broadcast(json.dumps(payload))


# Register listener so we can push fixes to UI in real-time
error_event_bus.register_listener(hitl_event_listener)


async def verify_hitl_token(websocket: WebSocket) -> bool:
    """
    Verify the JWT token scopes to ensure only ADMIN or SUPERVISOR can access HITL WS.
    Extracts token from Authorization header, query param 'token', or Sec-WebSocket-Protocol.
    """
    token = websocket.headers.get("Authorization") or websocket.headers.get("X-API-KEY")

    # Fallback to query parameters (common for browsers)
    if not token:
        token = websocket.query_params.get("token")

    # Fallback to Sec-WebSocket-Protocol (often used to pass tokens in JS WebSockets)
    if not token:
        protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
        for p in protocols:
            p = p.strip()
            if p and p != "hitl":
                token = p
                break

    if not token:
        logger.warning("HITL WebSocket connection rejected: Missing token")
        return False

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        role = payload.get("role", "").lower()
        if role not in ["admin", "supervisor"]:
            logger.warning(f"HITL WebSocket connection rejected: Insufficient role '{role}'")
            return False
        return True
    except jwt.ExpiredSignatureError:
        logger.warning("HITL WebSocket connection rejected: Token expired")
        return False
    except jwt.PyJWTError as e:
        logger.warning(f"HITL WebSocket connection rejected: Invalid token - {e}")
        return False


@router.websocket("/")
async def websocket_hitl_endpoint(websocket: WebSocket):
    # Enforce Auth
    is_authorized = await verify_hitl_token(websocket)
    if not is_authorized:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Ping/Pong Heartbeat to keep connection alive and detect drops
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:  # noqa: BLE001
        logger.error(f"HITL WebSocket error: {e}")
        manager.disconnect(websocket)
