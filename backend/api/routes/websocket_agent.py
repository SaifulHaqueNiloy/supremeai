import asyncio
import json
import os

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect, status
from loguru import logger

from core.llm.llm_gateway import llm_gateway
from core.queue.task_queue import task_queue
from core.security import verify_token
from database.supabase_client import SupabaseDB

router = APIRouter(prefix="/ws", tags=["Neural Engine Stream"])

# FIX (perf): _pref_locks was an unbounded dict that leaked memory per user.
# Switched to LRU cache with maxsize to bound memory usage on free-tier.
try:
    from cachetools import LRUCache

    _pref_locks: LRUCache = LRUCache(maxsize=1000)
except ImportError:
    # Fallback: plain dict if cachetools is not installed (still leaks but works)
    _pref_locks = {}  # type: ignore[assignment]
_pref_locks_lock = asyncio.Lock()


# বাংলা মন্তব্য: ইউজারের রিকোয়ারমেন্ট এনালাইসিস করে তা ডাটাবেজে সেভ রাখার জন্য ব্যাকগ্রাউন্ড অ্যাসিনক্রোনাস টাস্ক
async def analyze_and_save_preferences(user_id: str, user_message: str):
    async with _pref_locks_lock:
        if user_id not in _pref_locks:
            _pref_locks[user_id] = asyncio.Lock()
        lock = _pref_locks[user_id]

    async with lock:
        db = SupabaseDB()
        existing = await asyncio.to_thread(db.get_user_preferences, user_id)
        existing = existing or {}
        existing_prefs = existing.get("preferences") or {}

        safe_message = user_message.replace('"', "'")

        analysis_prompt = f"""Analyze the user's message to extract their work profile, technical stack, and preferred answer style.
User Message: '{safe_message}'
Existing Profile: {json.dumps(existing_prefs)}

Return ONLY a valid JSON object matching this structure (merge with existing if relevant):
{{
  "preferred_stack": "e.g., Python/FastAPI, TypeScript/React, none",
  "answering_style": "e.g., direct code, step-by-step tutorial, concise",
  "work_type": "e.g., debugging, new feature design, general"
}}
JSON:"""

        try:
            response = await llm_gateway.acompletion(
                prompt=analysis_prompt, task_type="analysis", stream=False
            )
            text = response.get("text", "{}") if isinstance(response, dict) else str(response)

            if "```" in text:
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:]
            new_prefs = json.loads(text.strip())
            if new_prefs:
                merged_prefs = {**existing_prefs, **new_prefs}
                await asyncio.to_thread(
                    db.upsert_user_preferences,
                    {"user_id": user_id, "preferences": merged_prefs},
                )
                logger.info(f"🤖 [WS] Updated user preferences for {user_id}")
        except Exception as e:
            logger.warning(f"⚠️ [WS] Failed to analyze user preferences: {type(e).__name__}: {e}")


async def handle_analyze_preferences(task_data: dict):
    user_id = task_data.get("user_id")
    content = task_data.get("payload", {}).get("content", "")
    if user_id and content:
        await analyze_and_save_preferences(user_id, content)
    return True


task_queue.register_handler("analyze_preferences", handle_analyze_preferences)


# ==========================================
# 🔌 WEBSOCKET CONNECTION MANAGER
# ==========================================
class DistributedConnectionManager:
    # DoS Protection Config
    MAX_TOTAL_CONNECTIONS = int(os.getenv("WS_MAX_CONNECTIONS", "50"))
    MAX_PER_USER = int(os.getenv("WS_MAX_PER_USER", "3"))
    MAX_PER_IP = int(os.getenv("WS_MAX_PER_IP", "10"))
    AUTH_ATTEMPT_WINDOW = int(os.getenv("WS_AUTH_WINDOW_SECONDS", "60"))
    MAX_AUTH_ATTEMPTS_PER_IP = int(os.getenv("WS_MAX_AUTH_ATTEMPTS", "5"))
    STALE_CONNECTION_TIMEOUT = int(os.getenv("WS_STALE_TIMEOUT_SECONDS", "300"))
    CLEANUP_INTERVAL = int(os.getenv("WS_CLEANUP_INTERVAL_SECONDS", "60"))
    MAX_MEMORY_MB = int(os.getenv("WS_MAX_MEMORY_MB", "100"))

    def __init__(self):
        from collections import defaultdict

        # Legacy tracking for pubsub and pref tasks
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._pref_tasks: dict[str, set[asyncio.Task]] = {}
        self.redis = None
        self.pubsub = None

        # New DoS tracking
        self._ip_connections: dict[str, int] = defaultdict(int)
        self._auth_attempts: dict[str, list[float]] = defaultdict(list)
        self._last_activity: dict[int, float] = {}  # id(ws) -> float

        # Cleanup
        self._cleanup_task = None

    async def start_background_tasks(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_stale_connections())
            logger.info("🛡️ [WS] DoS protection enabled - background cleanup started")

    def _get_memory_usage_mb(self) -> float:
        try:
            import resource

            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except ImportError:
            # Fallback
            return self._total_connections() * 0.01

    def _is_memory_pressure(self) -> bool:
        return self._get_memory_usage_mb() > self.MAX_MEMORY_MB

    def _check_ip_rate_limit(self, ip_address: str) -> bool:
        import time

        now = time.time()
        self._auth_attempts[ip_address] = [
            t for t in self._auth_attempts[ip_address] if now - t < self.AUTH_ATTEMPT_WINDOW
        ]
        if len(self._auth_attempts[ip_address]) >= self.MAX_AUTH_ATTEMPTS_PER_IP:
            logger.warning(f"⚠️ [WS] IP {ip_address} rate limited.")
            return False
        return True

    def _record_auth_attempt(self, ip_address: str):
        import time

        self._auth_attempts[ip_address].append(time.time())

    def _total_connections(self) -> int:
        return sum(len(conns) for conns in self.active_connections.values())

    async def _cleanup_stale_connections(self):
        import time

        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL)
                now = time.time()
                for user_id, conns in list(self.active_connections.items()):
                    active = []
                    for ws in conns:
                        last_act = self._last_activity.get(id(ws), now)
                        if now - last_act > self.STALE_CONNECTION_TIMEOUT:
                            try:
                                await ws.close(code=1001)
                            except Exception:
                                pass
                            if id(ws) in self._last_activity:
                                del self._last_activity[id(ws)]
                        else:
                            active.append(ws)
                    if active:
                        self.active_connections[user_id] = active
                    else:
                        self.active_connections.pop(user_id, None)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WS] Cleanup error: {e}")

    async def _get_redis(self):
        if not self.redis:
            import redis.asyncio as aioredis

            try:
                from core.config import settings

                redis_url = getattr(settings, "redis_url", getattr(settings, "REDIS_URL", None))
            except ImportError:
                redis_url = "redis://<your-redis-url>"
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("ws_broadcast")
            asyncio.create_task(self._listen_to_redis())
        return self.redis

    async def _listen_to_redis(self):
        while True:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    user_id = data.get("user_id")
                    content = data.get("content")
                    if user_id in self.active_connections:
                        for ws in self.active_connections[user_id]:
                            try:
                                await ws.send_text(content)
                            except Exception as e:
                                import logging

                                logging.getLogger(__name__).exception(f"Silenced error: {e}")
            except Exception as e:
                logger.error(f"Redis pubsub error: {e}")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket, user_id: str, ip_address: str = "127.0.0.1"):
        import time

        if self._is_memory_pressure():
            logger.warning(f"⚠️ [WS] Rejecting {user_id}: memory pressure")
            await websocket.close(code=1013, reason="Server overloaded")
            return False

        if self._total_connections() >= self.MAX_TOTAL_CONNECTIONS:
            logger.warning(f"⚠️ [WS] Rejecting {user_id}: total limit reached")
            await websocket.close(code=1013, reason="Too many connections")
            return False

        per_user = len(self.active_connections.get(user_id, []))
        if per_user >= self.MAX_PER_USER:
            logger.warning(f"⚠️ [WS] Rejecting {user_id}: per-user limit")
            await websocket.close(code=1013, reason="Too many connections for user")
            return False

        ip_count = self._ip_connections.get(ip_address, 0)
        if ip_count >= self.MAX_PER_IP:
            logger.warning(f"⚠️ [WS] Rejecting {user_id}: IP limit")
            await websocket.close(code=1013, reason="IP limit exceeded")
            return False

        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

        self._ip_connections[ip_address] += 1
        self._last_activity[id(websocket)] = time.time()

        await self._get_redis()
        await self.start_background_tasks()

        logger.info(f"🟢 [WS] Connected: {user_id} from {ip_address}")
        return True

    def disconnect(self, websocket: WebSocket, user_id: str, ip_address: str = "127.0.0.1"):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        self._ip_connections[ip_address] -= 1
        if id(websocket) in self._last_activity:
            del self._last_activity[id(websocket)]

        logger.info(f"🔴 [WS] Client Disconnected: {user_id}")

    async def record_activity(self, websocket: WebSocket):
        import time

        self._last_activity[id(websocket)] = time.time()

    async def broadcast_to_user(self, user_id: str, content: str):
        redis = await self._get_redis()
        await redis.publish("ws_broadcast", json.dumps({"user_id": user_id, "content": content}))

    async def _authenticate(
        self, websocket: WebSocket, client_ip: str = "127.0.0.1"
    ) -> dict | None:
        if not self._check_ip_rate_limit(client_ip):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Rate limited")
            return None

        try:
            auth_msg = await websocket.receive_json()
            token = auth_msg.get("token")
            if auth_msg.get("type") != "auth" or not token:
                self._record_auth_attempt(client_ip)
                logger.warning("[WS] Rejected unauthenticated WS connection")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return None
            return verify_token(token)
        except Exception as e:
            self._record_auth_attempt(client_ip)
            logger.warning(f"[WS] Invalid token: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

    def track_pref_task(self, user_id: str, task: asyncio.Task) -> None:
        self._pref_tasks.setdefault(user_id, set()).add(task)

    def cancel_pref_tasks(self, user_id: str) -> None:
        tasks = self._pref_tasks.get(user_id, set())
        for task in tasks:
            task.cancel()
        self._pref_tasks.pop(user_id, None)


manager = DistributedConnectionManager()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    request: Request,
):
    """
    Real-time bidirectional WebSocket for Token-by-Token streaming and Agentic Tool execution.
    Supports both plain text (Flutter) and JSON payloads with base64 images (Web Chat).
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    auth_payload = await manager._authenticate(websocket, client_ip)
    if not auth_payload:
        return

    user_id = auth_payload.get("sub", "unknown")
    connected = await manager.connect(websocket, user_id, client_ip)
    if not connected:
        return

    # সেশন হিস্ট্রি মেইনটেইন করার জন্য চ্যাট অবজেক্ট তৈরি করা
    chat_history = []

    # বাংলা মন্তব্য: কানেক্টেড ইউজারের পূর্ববর্তী প্রেফারেন্স ডাটাবেজ থেকে রিড করা হচ্ছে
    db = SupabaseDB()
    user_pref_record = await asyncio.to_thread(db.get_user_preferences, user_id)
    user_pref_record = user_pref_record or {}
    user_prefs = user_pref_record.get("preferences") or {}

    try:
        while True:
            # ১. ফ্রন্টএন্ড থেকে ইউজার প্রম্পট রিসিভ করা
            user_message = await websocket.receive_text()
            await manager.record_activity(websocket)

            # ==========================================
            # 👁️ MULTI-MODAL PAYLOAD PARSING
            # ==========================================
            try:
                payload = json.loads(user_message)
                text_prompt = payload.get("text", "")
                image_base64 = payload.get("image_base64", None)

                content_to_send = text_prompt
                if image_base64:
                    logger.info("📸 [WS] Image payload received and decoded.")

            except json.JSONDecodeError:
                content_to_send = user_message

            try:
                chat_history.append({"role": "user", "content": content_to_send})

                system_instructions = (
                    "You are SupremeAI, a personalized autonomous coding assistant."
                )
                if user_prefs:
                    system_instructions += (
                        f" The user prefers: Answering Style: {user_prefs.get('answering_style', 'default')}, "
                        f"Preferred Stack: {user_prefs.get('preferred_stack', 'default')}, "
                        f"Work Type: {user_prefs.get('work_type', 'default')}."
                    )

                messages_payload = [
                    {"role": "system", "content": system_instructions},
                    *chat_history,
                ]

                response_stream = await llm_gateway.acompletion(
                    prompt=messages_payload, task_type="chat", stream=True
                )

                response_content = ""
                async for chunk in response_stream:
                    if chunk:
                        await websocket.send_text(chunk)
                        response_content += chunk
                        await asyncio.sleep(0.01)

                chat_history.append({"role": "assistant", "content": response_content})

                await websocket.send_text("[DONE]")
                logger.info("✅ [AI]: Stream completed.")

                await task_queue.enqueue(
                    task_type="analyze_preferences",
                    payload={"content": content_to_send},
                    user_id=user_id,
                )

            except Exception as e:
                # বাংলা মন্তব্য: P1 Fix — সকল exception সম্পূর্ণ log করা হচ্ছে।
                # আগে শুধু logger.info("❌ [GENERATION ERROR]") ছিল — production debugging অসম্ভব ছিল।
                logger.error(
                    f"[WS] Neural pipeline error for user={user_id}: {type(e).__name__}: {e}",
                    exc_info=True,
                )
                await websocket.send_text(f"\n[Error: {type(e).__name__}]\n[DONE]")

    except Exception as e:
        import logging

        logging.getLogger(__name__).exception(f"Silenced error: {e}")
    finally:
        # বাংলা মন্তব্য: P1 Fix — finally block নিশ্চিত করে যে যেকোনো কারণে exit হলেও
        # (WebSocketDisconnect, Exception, বা CancelledError) zombie task cancel হবে এবং disconnect হবে।
        manager.disconnect(websocket, user_id)
        if user_id:
            manager.cancel_pref_tasks(user_id)
