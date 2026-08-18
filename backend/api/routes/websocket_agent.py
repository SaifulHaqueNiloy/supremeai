import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from loguru import logger

from core.llm.llm_gateway import llm_gateway
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
            response = await llm_gateway.acompletion(prompt=analysis_prompt, task_type="analysis", stream=False)
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


# ==========================================
# 🔌 WEBSOCKET CONNECTION MANAGER
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._pref_tasks: dict[str, set[asyncio.Task]] = {}

    async def connect(self, websocket: WebSocket):
        # AUDIT FIX: accept made idempotent.
        # first-message auth flow accepts before connect; double-accept raises.
        # Only accept when still in CONNECTING state.
        from starlette.websockets import WebSocketState
        if websocket.application_state == WebSocketState.CONNECTING:
            await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("[WS] New Client Connected to Neural Engine.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("🔴 [WS] Client Disconnected.")

    async def _authenticate(self, websocket: WebSocket) -> dict | None:
        # বাংলা মন্তব্য: P0 Fix — Anonymous WebSocket access সম্পূর্ণ নিষিদ্ধ।
        # Token query param-এ থাকলে verify করা হয়; না থাকলে None (endpoint-এ প্রথম
        # মেসেজ auth-flow চেষ্টা করা হয়)। URL-এ token না পাঠিয়ে auth-message-এ
        # পাঠানোই preferred (mobile main.dart সেভাবেই পাঠায়)।
        token = websocket.query_params.get("token")
        if not token:
            return None
        try:
            return verify_token(token)
        except Exception as e:
            logger.warning(f"[WS] Invalid token — closing WebSocket connection: {e}")
            return None

    def track_pref_task(self, user_id: str, task: asyncio.Task) -> None:
        self._pref_tasks.setdefault(user_id, set()).add(task)

    def cancel_pref_tasks(self, user_id: str) -> None:
        # বাংলা মন্তব্য: disconnect হলে সব background pref task cancel করা হচ্ছে — zombie task প্রতিরোধ
        tasks = self._pref_tasks.get(user_id, set())
        for task in tasks:
            task.cancel()
        self._pref_tasks.pop(user_id, None)


manager = ConnectionManager()


@router.websocket("/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    """
    Real-time bidirectional WebSocket for Token-by-Token streaming and Agentic Tool execution.
    Supports both plain text (Flutter) and JSON payloads with base64 images (Web Chat).

    AUDIT FIX: Authentication now works two ways:
      1. URL query ?token= (legacy/backward-compatible)
      2. First JSON message after connect: {"type":"auth","token":...} (mobile flow)
    Token is never required in URL — first-message auth is preferred to avoid
    log / referrer leakage.
    """
    # Step 1: query-param token (legacy)
    auth_payload = await manager._authenticate(websocket)
    # `first_message` is read-and-consumed when used for auth; None otherwise.
    first_message: str | None = None

    if not auth_payload:
        # Step 2: No query token — accept then require an auth JSON message (mobile flow)
        await websocket.accept()
        try:
            first_message = await asyncio.wait_for(websocket.receive_text(), timeout=15)
        except (asyncio.TimeoutError, WebSocketDisconnect):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            parsed_first = json.loads(first_message) if first_message else None
        except json.JSONDecodeError:
            parsed_first = None

        if isinstance(parsed_first, dict) and parsed_first.get("type") == "auth":
            candidate = parsed_first.get("token")
            if candidate:
                try:
                    auth_payload = verify_token(candidate)
                except Exception as e:
                    logger.warning(f"[WS] Invalid token in auth message: {e}")
                    auth_payload = None
            if not auth_payload:
                logger.warning("[WS] Rejected unauthenticated WebSocket connection — invalid auth message token.")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            # Auth message consumed — subsequent messages are chat prompts.
        else:
            logger.warning("[WS] Rejected unauthenticated WebSocket connection — no auth token provided.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Connection is now authenticated (accept happened via connect() or earlier).
    await manager.connect(websocket)
    # Session history
    chat_history = []

    user_id = auth_payload.get("sub", "unknown")
    db = SupabaseDB()
    user_pref_record = await asyncio.to_thread(db.get_user_preferences, user_id)
    user_pref_record = user_pref_record or {}
    user_prefs = user_pref_record.get("preferences") or {}

    try:
        while True:
            # 1. Receive user prompt
            user_message = await websocket.receive_text()

            # MULTI-MODAL PAYLOAD PARSING
            try:
                payload = json.loads(user_message)
                content_to_send = payload.get("text", "")
                image_base64 = payload.get("image_base64", None)
                if image_base64:
                    logger.info("[WS] Image payload received and decoded.")
            except (json.JSONDecodeError, ValueError):
                content_to_send = user_message

            # AUDIT FIX: skip empty payloads to avoid wasted LLM calls / crashes.
            if not isinstance(content_to_send, str) or not content_to_send.strip():
                logger.warning("[WS] Empty message received — skipping LLM call.")
                await websocket.send_text("\n[DONE]")
                continue

            try:
                chat_history.append({"role": "user", "content": content_to_send})

                system_instructions = "You are SupremeAI, a personalized autonomous coding assistant."
                if user_prefs:
                    system_instructions += (
                        f" The user prefers: Answering Style: {user_prefs.get('answering_style', 'default')}, "
                        f"Preferred Stack: {user_prefs.get('preferred_stack', 'default')}, "
                        f"Work Type: {user_prefs.get('work_type', 'default')}."
                    )

                messages_payload = [{"role": "system", "content": system_instructions}, *chat_history]

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
                logger.info("[AI]: Stream completed.")

                pref_task = asyncio.create_task(analyze_and_save_preferences(user_id, content_to_send))
                manager.track_pref_task(user_id, pref_task)

            except Exception as e:
                # P1 Fix: log full exception for production debugging.
                logger.error(
                    f"[WS] Neural pipeline error for user={user_id}: {type(e).__name__}: {e}",
                    exc_info=True,
                )
                await websocket.send_text(f"\n[Error: {type(e).__name__}]\n[DONE]")

    except WebSocketDisconnect:
        pass
    finally:
        # P1 Fix: ensure zombie tasks are cancelled and connection cleaned up on any exit path.
        manager.disconnect(websocket)
        if user_id:
            manager.cancel_pref_tasks(user_id)
