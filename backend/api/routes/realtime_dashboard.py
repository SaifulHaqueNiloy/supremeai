"""
Real-time Dashboard WebSocket Endpoint
======================================

Bridges the existing SwarmPubSub infrastructure to WebSocket clients
for real-time dashboard updates, metrics streaming, and live log feeds.

Channels:
    - metrics.update     — System metrics (CPU, memory, active agents)
    - logs.stream        — Live application logs
    - jobs.status        — CI/CD job status updates
    - alerts.emergency   — Critical system alerts
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from loguru import logger

from core.error_bus import with_error_bus
from core.security import verify_token
from core.swarm_pubsub import get_swarm_streamer

router = APIRouter(prefix="/ws", tags=["Real-time Dashboard"])


class DashboardWebSocketManager:
    """
    Manages WebSocket connections for dashboard real-time updates.
    Bridges SwarmPubSub events to connected WebSocket clients.
    """

    def __init__(self):
        self.active_connections: dict[WebSocket, dict] = {}
        self.swarm_streamer = get_swarm_streamer()
        self.subscription_task = None
        self._last_metrics_state: dict = {}

    async def connect(self, websocket: WebSocket, user_auth: dict):
        """Accept WebSocket connection and register user."""
        await websocket.accept()
        self.active_connections[websocket] = {
            "auth": user_auth,
            "channels": set(),  # Which channels the client wants to receive
            "connected_at": asyncio.get_event_loop().time(),
            "initial_snapshot_sent": False,
        }
        logger.info(f"📈 Dashboard WebSocket connected for user {user_auth.get('sub', 'unknown')}")

        # Start subscription task if not already running
        if self.subscription_task is None or self.subscription_task.done():
            self.subscription_task = asyncio.create_task(self.broadcast_to_clients())

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            del self.active_connections[websocket]
            logger.info("📉 Dashboard WebSocket disconnected")

            # Cancel subscription task if no more connections
            if not self.active_connections and self.subscription_task:
                self.subscription_task.cancel()
                self.subscription_task = None

    def add_channel_subscription(self, websocket: WebSocket, channel: str):
        """Add a channel subscription for a specific WebSocket."""
        if websocket in self.active_connections:
            self.active_connections[websocket]["channels"].add(channel)

    def remove_channel_subscription(self, websocket: WebSocket, channel: str):
        """Remove a channel subscription for a specific WebSocket."""
        if websocket in self.active_connections:
            self.active_connections[websocket]["channels"].discard(channel)

    async def send_personal_message(self, websocket: WebSocket, message: str):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    def compute_metric_delta(self, new_data: dict) -> dict:
        """Compute delta between new metrics payload and last known state."""
        delta = {k: v for k, v in new_data.items() if self._last_metrics_state.get(k) != v}
        self._last_metrics_state = new_data.copy()
        return delta

    @with_error_bus("broadcast_to_clients")
    async def broadcast_to_clients(self):
        """Listen to SwarmPubSub and broadcast to interested WebSocket clients with delta optimization."""
        try:
            async for raw_message in self.swarm_streamer.subscribe():
                try:
                    # Parse the message from SwarmPubSub
                    message_data = json.loads(raw_message)
                    event_type = message_data.get("type", "unknown")

                    # Map event types to channels
                    event_channel = self._get_event_channel(event_type)

                    # Optimize metrics updates by computing delta
                    payload_to_send = raw_message
                    if event_channel == "metrics.update" and isinstance(message_data.get("data"), dict):
                        delta = self.compute_metric_delta(message_data["data"])
                        delta_payload = json.dumps({
                            "type": "metrics.delta",
                            "delta": delta,
                            "timestamp": message_data.get("timestamp", asyncio.get_event_loop().time())
                        })

                    # Filter and forward to interested clients
                    for websocket, conn_info in list(self.active_connections.items()):
                        interested_channels = conn_info["channels"]

                        if event_channel in interested_channels or "all" in interested_channels:
                            try:
                                if event_channel == "metrics.update" and conn_info.get("initial_snapshot_sent"):
                                    # Send lightweight delta update
                                    await self.send_personal_message(websocket, delta_payload)
                                else:
                                    # Send full snapshot and flag initial snapshot sent
                                    await self.send_personal_message(websocket, payload_to_send)
                                    conn_info["initial_snapshot_sent"] = True
                            except Exception:
                                self.disconnect(websocket)

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from SwarmPubSub: {raw_message}")
                except Exception as e:
                    logger.error(f"Error processing SwarmPubSub message: {e}")

        except asyncio.CancelledError:
            logger.info("SwarmPubSub subscription task cancelled")
        except Exception as e:
            logger.error(f"Error in broadcast_to_clients: {e}")

    def _get_event_channel(self, event_type: str) -> str:
        """Map event types to channels for filtering."""
        # Metrics events
        if event_type.startswith("metrics.") or event_type in [
            "cpu_usage",
            "memory_usage",
            "active_agents",
            "system_load",
        ]:
            return "metrics.update"

        # Log events
        elif event_type.startswith("log.") or event_type in ["log_entry", "error_log", "info_log", "debug_log"]:
            return "logs.stream"

        # Job events
        elif event_type.startswith("job.") or event_type in [
            "job_started",
            "job_completed",
            "job_failed",
            "job_status",
        ]:
            return "jobs.status"

        # Alert events
        elif event_type.startswith("alert.") or event_type in ["critical_alert", "security_alert", "emergency_alert"]:
            return "alerts.emergency"

        # Default to misc for other events
        else:
            return "misc.events"


# Create a global instance
dashboard_manager = DashboardWebSocketManager()


@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates.

    Expected query params:
    - token: Authentication token
    - channels: Comma-separated list of channels to subscribe to
               (e.g., "metrics.update,logs.stream,jobs.status")
    """
    # Authenticate the connection
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("Dashboard WebSocket connection rejected - no token provided")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        auth_payload = verify_token(token)
        if not auth_payload:
            logger.warning("Dashboard WebSocket connection rejected - invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.warning(f"Dashboard WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get desired channels from query params
    channels_param = websocket.query_params.get("channels", "")
    desired_channels = set(channels_param.split(",")) if channels_param else {"all"}

    await dashboard_manager.connect(websocket, auth_payload)

    # Subscribe to requested channels
    for channel in desired_channels:
        if channel.strip():  # Skip empty strings
            dashboard_manager.add_channel_subscription(websocket, channel.strip())

    try:
        # Keep the connection alive and listen for messages from client
        # (for any client-initiated actions in the future)
        while True:
            # Currently just listening, but could handle client commands
            data = await websocket.receive_text()

            # Parse client commands (for future extensibility)
            try:
                client_message = json.loads(data)
                command = client_message.get("command")

                if command == "subscribe":
                    channel = client_message.get("channel")
                    if channel:
                        dashboard_manager.add_channel_subscription(websocket, channel)
                        await dashboard_manager.send_personal_message(
                            websocket, json.dumps({"type": "subscription_ack", "channel": channel})
                        )

                elif command == "unsubscribe":
                    channel = client_message.get("channel")
                    if channel:
                        dashboard_manager.remove_channel_subscription(websocket, channel)
                        await dashboard_manager.send_personal_message(
                            websocket, json.dumps({"type": "unsubscription_ack", "channel": channel})
                        )

                elif command == "ping":
                    # Respond to ping with pong
                    await dashboard_manager.send_personal_message(
                        websocket, json.dumps({"type": "pong", "timestamp": asyncio.get_event_loop().time()})
                    )

            except json.JSONDecodeError:
                # Not a JSON command, might be regular text
                logger.debug(f"Non-JSON message from dashboard client: {data}")

    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Unexpected error in dashboard WebSocket: {e}")
        dashboard_manager.disconnect(websocket)
