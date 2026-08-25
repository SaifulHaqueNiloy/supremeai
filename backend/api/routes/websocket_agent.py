import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from loguru import logger

from core.llm.llm_gateway import llm_gateway
from core.queue.task_queue import task_queue
from core.security import verify_token
from database.supabase_client import SupabaseDB

router = APIRouter(prefix="/ws", tags=["Neural Engine Stream"])

_pref_locks: dict[str, asyncio.Lock] = {}
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
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._pref_tasks: dict[str, set[asyncio.Task]] = {}
        self.redis = None
        self.pubsub = None

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
                            except Exception:
                                pass
            except Exception as e:
                logger.error(f"Redis pubsub error: {e}")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        await self._get_redis()
        logger.info(f"🟢 [WS] New Client Connected to Neural Engine: {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"🔴 [WS] Client Disconnected: {user_id}")

    async def broadcast_to_user(self, user_id: str, content: str):
        redis = await self._get_redis()
        await redis.publish("ws_broadcast", json.dumps({"user_id": user_id, "content": content}))

    async def _authenticate(self, websocket: WebSocket) -> dict | None:
        # বাংলা মন্তব্য: P0 Fix — Anonymous WebSocket access সম্পূর্ণ নিষিদ্ধ।
        # Token না থাকলে বা invalid হলে WS_1008 (Policy Violation) দিয়ে তাৎক্ষণিক reject।
        try:
            auth_msg = await websocket.receive_json()
            token = auth_msg.get("token")
            if auth_msg.get("type") != "auth" or not token:
                logger.warning(
                    "[WS] Rejected unauthenticated WebSocket connection — auth message missing or invalid."
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return None
            return verify_token(token)
        except Exception as e:
            logger.warning(f"[WS] Invalid token — closing WebSocket connection: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

    def track_pref_task(self, user_id: str, task: asyncio.Task) -> None:
        self._pref_tasks.setdefault(user_id, set()).add(task)

    def cancel_pref_tasks(self, user_id: str) -> None:
        # বাংলা মন্তব্য: disconnect হলে সব background pref task cancel করা হচ্ছে — zombie task প্রতিরোধ
        tasks = self._pref_tasks.get(user_id, set())
        for task in tasks:
            task.cancel()
        self._pref_tasks.pop(user_id, None)


manager = DistributedConnectionManager()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
):
    """
    Real-time bidirectional WebSocket for Token-by-Token streaming and Agentic Tool execution.
    Supports both plain text (Flutter) and JSON payloads with base64 images (Web Chat).
    """
    # বাংলা মন্তব্য: _authenticate ব্যর্থ হলে সরাসরি return — double-close এড়াতে
    auth_payload = await manager._authenticate(websocket)
    if not auth_payload:
        return

    user_id = auth_payload.get("sub", "unknown")
    await manager.connect(websocket, user_id)

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

    except WebSocketDisconnect:
        pass
    finally:
        # বাংলা মন্তব্য: P1 Fix — finally block নিশ্চিত করে যে যেকোনো কারণে exit হলেও
        # (WebSocketDisconnect, Exception, বা CancelledError) zombie task cancel হবে এবং disconnect হবে।
        manager.disconnect(websocket, user_id)
        if user_id:
            manager.cancel_pref_tasks(user_id)
