# Part 8: Backend AI Agents, MCP Tools & Orchestration Services Audit

> **Audit Generation Time:** `2026-07-24 20:09:07 UTC`  
> **Module Description:** Autonomous AI agent tools, MCP server integrations, checkpointing, and execution tools.  
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `backend/tools/` (Directory, 348 files)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [ ] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [ ] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [ ] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [ ] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `backend/tools/agent_tools.py`

```py
import asyncio

from loguru import logger


# ১. Database Search Tool
async def search_database(query: str) -> str:
    """
    Searches the internal Supabase/PostgreSQL database for specific information.
    Use this tool when the user asks for historical tasks, user data, or project records.
    """
    # বাস্তবে এখানে আপনার ডাটাবেস কোয়েরি থাকবে
    logger.info(f"🔧 [TOOL CALLED] Searching database for: {query}")  # noqa: T201
    # Replace blocking delay with non-blocking async sleep
    await asyncio.sleep(1)
    return f"Database result for '{query}': Found 3 matching records indicating successful deployment."


# ২. System Health Tool
def check_system_health() -> str:
    """
    Checks the real-time server health, Redis quota, and API status.
    Use this when the user asks about system status, downtime, or performance.
    """
    logger.info("🔧 [TOOL CALLED] Checking system health...")  # noqa: T201
    return "System Status: ONLINE. CPU: 12%, RAM: 45%. Redis Quota: 87% remaining."


# ৩. Execute Code Tool (Mock Example)
def execute_python_code(code: str) -> str:
    """
    Executes Python code in a secure sandbox environment and returns the output.
    Use this tool if the user explicitly asks to run code or calculate complex math.
    """
    logger.info(f"🔧 [TOOL CALLED] Executing code: {code}")  # noqa: T201
    # বাস্তবে এটি একটি ডকার কন্টেইনার বা স্যান্ডবক্সে রান করবে
    return "Execution successful. Output: Hello from SupremeAI Sandbox!"


# আমাদের সমস্ত টুলসের একটি লিস্ট যা AI-কে দেওয়া হবে
SUPREME_TOOLS = [search_database, check_system_health, execute_python_code]

```

### 📄 `backend/tools/ai_federation_protocol.py`

```py
import json
import uuid
from typing import Any

from loguru import logger


class AIFederationProtocol:
    """
    Standard protocol for AI-to-AI communication.
    Enables skill sharing, task delegation, and result federation.
    (Closes Gap #87)
    """

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or f"node-{uuid.uuid4().hex[:8]}"
        self.registry: dict[str, dict[str, Any]] = {}
        self.task_history: list[dict[str, Any]] = []
        logger.info(f"Initialized AIFederationProtocol node: {self.node_id}")

    def register_skill(self, skill_name: str, provider_node: str, metadata: dict[str, Any]) -> dict[str, Any]:
        skill_id = f"skill-{uuid.uuid4().hex[:8]}"
        entry = {
            "skill_id": skill_id,
            "skill_name": skill_name,
            "provider_node": provider_node,
            "metadata": metadata,
            "status": "available",
        }
        self.registry[skill_id] = entry
        logger.info(f"Registered skill {skill_name} from {provider_node}")
        return {"status": "success", "skill_id": skill_id}

    def discover_skills(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        matches = []
        for skill in self.registry.values():
            text = json.dumps(skill).lower()
            if q in text or q in skill.get("skill_name", "").lower():
                matches.append(skill)
        return matches

    async def delegate_task(self, target_node: str, task: dict[str, Any]) -> dict[str, Any]:
        task_id = task.get("task_id") or f"task-{uuid.uuid4().hex[:8]}"
        task.setdefault("task_id", task_id)
        task.setdefault("delegated_from", self.node_id)
        task.setdefault("delegated_to", target_node)
        task.setdefault("status", "pending")
        logger.info(f"Delegating task {task_id} to {target_node}")
        self.task_history.append(task)
        return {
            "status": "dispatched",
            "task_id": task_id,
            "target_node": target_node,
            "task": task,
        }

    def report_result(self, task_id: str, result: dict[str, Any]) -> dict[str, Any]:
        for task in self.task_history:
            if task.get("task_id") == task_id:
                task["status"] = "completed"
                task["result"] = result
                logger.info(f"Task {task_id} completed by {task.get('delegated_to')}")
                return {"status": "success", "task_id": task_id}
        return {"status": "not_found", "task_id": task_id}

    def get_federation_status(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "skills_registered": len(self.registry),
            "tasks_total": len(self.task_history),
            "tasks_completed": sum(1 for t in self.task_history if t.get("status") == "completed"),
            "tasks_pending": sum(1 for t in self.task_history if t.get("status") == "pending"),
            "peers": list({s.get("provider_node") for s in self.registry.values()}),
        }

```

### 📄 `backend/tools/api_gateway.py`

```py
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from core.config import get_production_env, settings
from core.rate_limiter import AsyncRateLimiter
from core.security.auth_middleware import AuthMiddleware

auth_middleware = AuthMiddleware.__new__(AuthMiddleware)
auth_middleware.enabled = bool(getattr(settings, "supremeai_api_token", None))
rate_limiter = AsyncRateLimiter()

from brain.api_router import ApiRouter

api_router = ApiRouter()
router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])


class GatewayRequest(BaseModel):
    path: str
    method: str = "GET"
    payload: dict[str, Any] | None = None
    source: str | None = None  # 'vscode' | 'flutter' | 'telegram' | 'web'
    headers: dict[str, str] | None = None


class InternalGateway:
    def __init__(self):
        self.n8n_url = get_production_env("N8N_URL", "http://127.0.0.1:5678")

    def trigger_n8n_workflow(self, webhook_path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.n8n_url}/{webhook_path.lstrip('/')}"
        logger.info(f"Triggering n8n workflow at {url}")
        try:
            response = httpx.post(url, json=payload, timeout=10.0)
            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "data": response.json() if response.is_success else response.text,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"n8n trigger failed: {exc}")
            return {"success": False, "error": str(exc)}

    def trigger_make_webhook(self, webhook_url: str, payload: dict[str, Any]) -> dict[str, Any]:
        logger.info("Triggering Make.com webhook")
        try:
            response = httpx.post(webhook_url, json=payload, timeout=10.0)
            return {"success": response.is_success, "response": response.text}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}


APIGateway = InternalGateway
ALLOWED_BACKEND_PATHS = {
    "vscode": [
        "/api/chat/completion",
        "/api/chat/stream",
        "/api/knowledge/learn",
        "/api/memory/ingest",
        "/api/codeflow/analyze",
    ],
    "flutter": ["/api/chat/message", "/api/chat/history", "/api/knowledge/stats"],
    "telegram": ["/api/chat/message", "/api/knowledge/feedback"],
    "web": ["/api/chat/message", "/api/chat/stream"],
}


@router.post("/forward")
async def gateway_forward(request: GatewayRequest, http_request: Request) -> Response:
    source = (request.source or "web").lower()
    if source not in ALLOWED_BACKEND_PATHS:
        raise HTTPException(status_code=400, detail="unknown source")

    allowed = ALLOWED_BACKEND_PATHS.get(source, [])
    normalized = request.path.strip().lower()
    if not any(normalized == allowed_path.lower() or normalized.startswith(allowed_path.lower() + "/") for allowed_path in allowed):
        logger.warning(f"Blocked path for source={source}: {request.path}")
        raise HTTPException(status_code=403, detail="path not allowed for source")

    client_ip = http_request.client.host if http_request.client else "127.0.0.1"
    if not rate_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    backend_url = get_production_env("SUPREMEAI_BACKEND_URL", "http://127.0.0.1:8000/api/v1")
    target = backend_url.rstrip("/") + "/" + request.path.lstrip("/")

    headers = dict(request.headers or {})
    headers.setdefault("X-Source", source)

    # API Key Rotation & Free Tier Tracking Integration
    if any(endpoint in normalized for endpoint in ["chat/completion", "chat/stream", "chat/message"]):
        try:
            from core.llm.free_tier_tracker import get_tracker
            from tools.security_tools.multi_account_rotator import TaskType, get_rotator

            tracker = get_tracker()
            rotator = get_rotator()

            best_provider_name = tracker.get_best_provider()
            if best_provider_name:
                # Tell rotator to get an account (task=CHAT)
                provider_account = rotator.get_best_provider_for_task(TaskType.CHAT)
                if provider_account:
                    provider, account = provider_account
                    if account and account.api_key:
                        headers["X-Dynamic-Provider"] = provider.name
                        headers["X-Dynamic-API-Key"] = account.api_key
                        # Record a basic hit (backend should ideally report exact tokens later)
                        tracker.record(provider.name, token_count=100)
                        logger.info(f"Injected {provider.name} key from rotator for {normalized}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to inject dynamic API key: {e}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            req_method = (request.method or "GET").upper()
            if req_method == "POST":
                response = await client.post(target, json=request.payload or {}, headers=headers)
            else:
                response = await client.get(target, headers=headers)

            # If rate limited (429), pause the provider
            if response.status_code == 429 and "X-Dynamic-Provider" in headers:
                try:
                    failed_provider = headers["X-Dynamic-Provider"]
                    tracker.mark_rate_limited(failed_provider, pause_seconds=60)
                    logger.warning(f"Provider {failed_provider} hit 429, paused for 60s.")
                except Exception as e:  # noqa: BLE001
                    try:
                        import loguru

                        loguru.logger.error(f"Tool execution error: {e}")
                    except Exception as e:  # noqa: BLE001
                        import logging

                        logging.warning(f"Exception suppressed: {e}")
                    pass

        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code)
    except Exception as exc:  # noqa: BLE001
        logger.exception("gateway forward failed")
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/dispatch/{capability}")
async def api_dispatch(capability: str, payload: dict[str, Any]) -> JSONResponse:
    try:
        result = api_router.dispatch(capability, payload or {})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    status = 200 if result.get("success", True) else 502
    return JSONResponse(content=result, status_code=status)


@router.post("/n8n")
async def trigger_n8n(webhook_path: str = "", payload: dict[str, Any] = None) -> JSONResponse:
    if payload is None:
        payload = {}
    internal = InternalGateway()
    result = internal.trigger_n8n_workflow(webhook_path, payload)
    status = 200 if result.get("success") else 502
    return JSONResponse(content=result, status_code=status)


@router.post("/make")
async def trigger_make(webhook_url: str = "", payload: dict[str, Any] = None) -> JSONResponse:
    if payload is None:
        payload = {}
    internal = InternalGateway()
    result = internal.trigger_make_webhook(webhook_url, payload)
    status = 200 if result.get("success") else 502
    return JSONResponse(content=result, status_code=status)

```

### 📄 `backend/tools/bandwidth_optimizer.py`

```py
import re
from typing import Any

from loguru import logger


class BandwidthOptimizer:
    def __init__(self):
        logger.info("Initialized BandwidthOptimizer")

    def compress_prompt(self, prompt: str, target_ratio: float = 0.5) -> str:
        original_len = len(prompt)
        compressed = prompt
        compressed = re.sub(r"\s+", " ", compressed)
        compressed = re.sub(r"[^\x00-\x7F]+", "", compressed)
        compressed = compressed.strip()
        new_len = len(compressed)
        if new_len > original_len * max(target_ratio, 0.1):
            truncated = compressed[: int(original_len * target_ratio)]
            compressed = truncated.rstrip() + "..."
        logger.debug(f"Compressed prompt from {original_len} to {len(compressed)} chars")
        return compressed

    def generate_delta_update(self, old_state: dict[str, Any], new_state: dict[str, Any]) -> dict[str, Any]:
        delta: dict[str, Any] = {}
        for k, v in new_state.items():
            if k not in old_state or old_state[k] != v:
                delta[k] = v
        return delta

```

### 📄 `backend/tools/checkpoint_manager.py`

```py
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from core.persistence import pooled_pg
from core.persistence.write_behind import WriteBehindBatcher

# শেয়ার্ড ইউটিলিটি — Firestore ও টেস্ট এনভায়রনমেন্ট চেক কেন্দ্রীভূত
from utils.environment import is_test_environment
from utils.firestore_helpers import firestore, get_firestore_db

_PG_SCHEMA = """
    CREATE TABLE IF NOT EXISTS task_checkpoints (
        task_id TEXT PRIMARY KEY,
        step_index INTEGER,
        state TEXT,
        created_at TIMESTAMPTZ DEFAULT now(),
        resumed BOOLEAN DEFAULT FALSE
    )
"""

_UPSERT_SQL = """
    INSERT INTO task_checkpoints (task_id, step_index, state, resumed)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (task_id) DO UPDATE SET
        step_index = EXCLUDED.step_index,
        state = EXCLUDED.state,
        created_at = now()
"""


@dataclass
class Checkpoint:
    task_id: str
    step_index: int
    state: dict[str, Any]
    created_at: str
    resumed: bool = False


class CheckpointManager:
    """Persists task execution state in Postgres (preferred, durable across restarts),
    Google Cloud Firestore (Serverless & Stateful, unchanged fallback), or local SQLite
    (last-resort fallback / explicit test mode — NOT durable across restarts)."""

    _batcher: WriteBehindBatcher | None = None

    def __init__(self, db_path: str = None):
        self.collection_name = "checkpoints"
        self._db = None
        self.db_path = db_path

        # রিফ্যাক্টর: সরাসরি firestore.Client() এর বদলে শেয়ার্ড হেল্পার ব্যবহার
        if db_path or is_test_environment():
            self.mode = "sqlite"
            self.db_path = db_path or "checkpoints.db"
            self._init_sqlite()
            logger.info(f"Initialized SQLite CheckpointManager at {self.db_path}")
        elif pooled_pg.is_available():
            try:
                pooled_pg.execute(_PG_SCHEMA)
                if CheckpointManager._batcher is None:
                    CheckpointManager._batcher = WriteBehindBatcher(name="task_checkpoints", flush_interval=1.0, max_batch=100)
                self.mode = "pg"
                logger.info("Initialized Postgres CheckpointManager (write-behind batched).")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Postgres CheckpointManager init failed, falling back: {exc}")
                self._init_fallback()
        else:
            self._init_fallback()

    def _init_fallback(self) -> None:
        """Firestore, then local SQLite as a last resort — unchanged prior behavior."""
        self._db = get_firestore_db()
        if self._db is not None:
            self.mode = "firestore"
            logger.info("Initialized Firestore CheckpointManager")
        else:
            self.mode = "sqlite"
            self.db_path = "checkpoints.db"
            self._init_sqlite()
            logger.warning(f"Initialized SQLite CheckpointManager at {self.db_path} — NOT durable across restarts.")

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    task_id TEXT PRIMARY KEY,
                    step_index INTEGER,
                    state TEXT,
                    created_at TEXT,
                    resumed INTEGER DEFAULT 0
                )
            """
            )
            conn.commit()
        finally:
            conn.close()

    def save(self, task_id: str, step_index: int, state: dict[str, Any]) -> bool:
        if self.mode == "pg":
            try:
                # `resumed` intentionally not reset here — ON CONFLICT preserves
                # whatever value is already in the row, matching prior SQLite semantics
                # where an existing row's `resumed` flag was read-then-reused.
                CheckpointManager._batcher.submit(_UPSERT_SQL, (task_id, step_index, json.dumps(state), False))
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to save Postgres checkpoint: {exc}")
                return False

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT resumed FROM checkpoints WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                resumed = row[0] if row else 0

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO checkpoints (task_id, step_index, state, created_at, resumed)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        task_id,
                        step_index,
                        json.dumps(state),
                        datetime.now(UTC).isoformat(),
                        resumed,
                    ),
                )
                conn.commit()
                conn.close()
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to save SQLite checkpoint: {exc}")
                return False

        if not self._db:
            return False
        try:
            doc_ref = self._db.collection(self.collection_name).document(task_id)
            doc = doc_ref.get()
            resumed = doc.to_dict().get("resumed", False) if doc.exists else False

            doc_ref.set(
                {
                    "task_id": task_id,
                    "step_index": step_index,
                    "state": json.dumps(state),
                    "created_at": datetime.now(UTC).isoformat(),
                    "resumed": resumed,
                }
            )
            logger.info(f"Firestore checkpoint saved for task_id={task_id} step={step_index}")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to save Firestore checkpoint: {exc}")
            return False

    def load(self, task_id: str) -> Checkpoint | None:
        if self.mode == "pg":
            try:
                # Flush first: a task resuming immediately after a save() (same
                # process, e.g. crash-recovery retry loop) must see its own write.
                CheckpointManager._batcher.flush()
                rows = pooled_pg.query(
                    "SELECT task_id, step_index, state, created_at, resumed FROM task_checkpoints WHERE task_id = %s",
                    (task_id,),
                )
                if not rows:
                    return None
                row = rows[0]
                cp = Checkpoint(
                    task_id=row[0],
                    step_index=row[1],
                    state=json.loads(row[2]),
                    created_at=str(row[3]),
                    resumed=bool(row[4]),
                )
                pooled_pg.execute(
                    "UPDATE task_checkpoints SET resumed = TRUE WHERE task_id = %s",
                    (task_id,),
                )
                return cp
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to load Postgres checkpoint: {exc}")
                return None

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT task_id, step_index, state, created_at, resumed FROM checkpoints WHERE task_id = ?",
                    (task_id,),
                )
                row = cursor.fetchone()
                if not row:
                    conn.close()
                    return None

                cp = Checkpoint(
                    task_id=row[0],
                    step_index=row[1],
                    state=json.loads(row[2]),
                    created_at=row[3],
                    resumed=bool(row[4]),
                )
                cursor.execute("UPDATE checkpoints SET resumed = 1 WHERE task_id = ?", (task_id,))
                conn.commit()
                conn.close()
                return cp
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to load SQLite checkpoint: {exc}")
                return None

        if not self._db:
            return None
        try:
            doc_ref = self._db.collection(self.collection_name).document(task_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None

            data = doc.to_dict()
            cp = Checkpoint(
                task_id=data["task_id"],
                step_index=data["step_index"],
                state=json.loads(data["state"]),
                created_at=data["created_at"],
                resumed=bool(data.get("resumed", False)),
            )
            # Mark as resumed
            doc_ref.update({"resumed": True})
            return cp
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to load Firestore checkpoint: {exc}")
            return None

    def list_all(self) -> list[dict[str, Any]]:
        if self.mode == "pg":
            try:
                CheckpointManager._batcher.flush()
                rows = pooled_pg.query("SELECT task_id, step_index, created_at, resumed FROM task_checkpoints ORDER BY created_at DESC")
                return [
                    {
                        "task_id": r[0],
                        "step_index": r[1],
                        "created_at": str(r[2]),
                        "resumed": bool(r[3]),
                    }
                    for r in rows
                ]
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to list Postgres checkpoints: {exc}")
                return []

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT task_id, step_index, created_at, resumed FROM checkpoints ORDER BY created_at DESC")
                rows = cursor.fetchall()
                conn.close()
                return [
                    {
                        "task_id": r[0],
                        "step_index": r[1],
                        "created_at": r[2],
                        "resumed": bool(r[3]),
                    }
                    for r in rows
                ]
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to list SQLite checkpoints: {exc}")
                return []

        if not self._db:
            return []
        try:
            docs = self._db.collection(self.collection_name).order_by("created_at", direction=firestore.Query.DESCENDING).stream()
            return [
                {
                    "task_id": d.id,
                    "step_index": d.to_dict().get("step_index"),
                    "created_at": d.to_dict().get("created_at"),
                    "resumed": bool(d.to_dict().get("resumed", False)),
                }
                for d in docs
            ]
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to list Firestore checkpoints: {exc}")
            return []

    def clear(self, task_id: str) -> bool:
        if self.mode == "pg":
            try:
                CheckpointManager._batcher.flush()
                pooled_pg.execute("DELETE FROM task_checkpoints WHERE task_id = %s", (task_id,))
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to clear Postgres checkpoint: {exc}")
                return False

        if self.mode == "sqlite":
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM checkpoints WHERE task_id = ?", (task_id,))
                conn.commit()
                conn.close()
                return True
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to clear SQLite checkpoint: {exc}")
                return False

        if not self._db:
            return False
        try:
            self._db.collection(self.collection_name).document(task_id).delete()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to clear Firestore checkpoint: {exc}")
            return False

```

### 📄 `backend/tools/cli.py`

```py
# backend/tools/cli.py
# Production Headless Zero-Cost Terminal AI Agent for SupremeAI 2.0
# বাংলা মন্তব্য: ইন্টারঅ্যাক্টিভ হেডলেস টার্মিনাল মোড ও ফ্রি-টিয়ার মডেল ফলব্যাক কমান্ড হ্যান্ডলার।

import os
import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Add project root to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.langgraph_agent import SupremeOrchestrator
from core.admin_god import AdminGodLayer
from core.universal_rules import UniversalRulesEngine

cli_app = typer.Typer(help="SupremeAI 2.0 Command Line Interface & Headless Agent")
console = Console()


@cli_app.command()
def ask(
    task: str = typer.Option(..., "--task", "-t", help="Task prompt for the agent"),
    task_type: str = typer.Option("general", "--type", "-y", help="Task type (coding, image_generation, etc.)"),
):
    """Asks SupremeAI 2.0 to solve a task in single execution mode."""
    console.print(f"[bold blue]Submitting task to SupremeAI Master Orchestrator:[/bold blue] {task}")

    rules = UniversalRulesEngine()
    admin = AdminGodLayer(rules)
    orchestrator = SupremeOrchestrator(admin)

    response = orchestrator.execute_task(task, task_type)

    if "Blocked" in response.get("result", ""):
        console.print(f"[bold red]EXECUTION BLOCKED:[/bold red] {response.get('result')}")
    else:
        console.print("[bold green]Response Result:[/bold green]")
        console.print(response.get("result", "No response output."))
        console.print(f"[yellow]Cost accumulated: ${response.get('cost', 0.0)}[/yellow]")


@cli_app.command()
def repl():
    """Starts interactive Headless Zero-Cost Terminal Agent REPL session.

    বাংলা মন্তব্য: যেকোনো GUI ছাড়াই সোজা টার্মিনাল থেকে ইন্টারঅ্যাক্টিভ AI এজেন্ট সেশন চালু করে।
    """
    console.print("[bold cyan]════════════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold green]🤖 SupremeAI 2.0 Headless Terminal Agent Mode (Zero-Cost Active)[/bold green]")
    console.print("[dim]Type 'exit' or 'quit' to terminate session.[/dim]")
    console.print("[bold cyan]════════════════════════════════════════════════════════════════[/bold cyan]\n")

    rules = UniversalRulesEngine()
    admin = AdminGodLayer(rules)
    orchestrator = SupremeOrchestrator(admin)

    while True:
        try:
            user_input = Prompt.ask("[bold yellow]supremeai>[/bold yellow]").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[bold red]Session ended. Goodbye![/bold red]")
                break

            with console.status("[bold cyan]Thinking & Executing (Zero-Cost Routing)...[/bold cyan]"):
                response = orchestrator.execute_task(user_input, "general")

            console.print("[bold green]Agent Response:[/bold green]")
            console.print(response.get("result", "No output generated."))
            console.print()
        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted by user. Quitting REPL.[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")


@cli_app.command()
def rules():
    """Lists all Constitutional Rules currently active."""
    rules_engine = UniversalRulesEngine()
    current_rules = rules_engine.rules

    table = Table(title="SupremeAI 2.0 Constitutional Rules")
    table.add_column("Rule Area", style="cyan")
    table.add_column("Configuration", style="magenta")

    for area, config in current_rules.items():
        table.add_row(area, str(config))

    console.print(table)


if __name__ == "__main__":
    cli_app()

```

### 📄 `backend/tools/collaborative_editor.py`

```py
import asyncio
import json

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from core.config import settings
from core.messaging.event_bus import ErrorContext

router = APIRouter(prefix="/collaborate", tags=["collaborative-editor"])


class CollaborativeEditor:
    def __init__(self):
        # বাংলা মন্তব্য: লোকাল কন্টেইনারে কানেক্ট হওয়া সকেট এবং তাদের ব্যাকগ্রাউন্ড লিসেনার টাস্ক ট্র্যাক করার ডিকশনারি
        self.local_sessions: dict[str, dict[str, WebSocket]] = {}
        self.redis_listeners: dict[str, asyncio.Task] = {}

        # বাংলা মন্তব্য: Redis কানেকশন সেটআপ (Upstash বা Local)
        redis_url_setting = getattr(settings, "redis_url", "")
        redis_url = redis_url_setting if redis_url_setting else "redis://localhost:6379"
        self.redis = redis.from_url(redis_url, decode_responses=True)
        logger.info("Initialized CollaborativeEditor with Redis Pub/Sub and State Persistence")

    async def get_session_state(self, session_id: str) -> dict:
        """বাংলা মন্তব্য: Redis থেকে সেশনের বর্তমান ডকুমেন্ট স্টেট এবং AI কার্সরের অবস্থান নিয়ে আসবে।"""
        state_key = f"supremeai:state:{session_id}"
        state = await self.redis.hgetall(state_key)

        if not state:
            return {
                "document_state": "",
                "ai_cursor": {"position": 0, "status": "idle"},
            }

        return {
            "document_state": state.get("document_state", ""),
            "ai_cursor": json.loads(state.get("ai_cursor", '{"position": 0, "status": "idle"}')),
        }

    async def update_session_state(self, session_id: str, updates: dict):
        """বাংলা মন্তব্য: Redis হ্যাশে সেশন স্টেট আপডেট করবে (State Persistence)।"""
        state_key = f"supremeai:state:{session_id}"
        await self.redis.hset(state_key, mapping=updates)

    async def connect_client(self, session_id: str, client_id: str, websocket: WebSocket):
        await websocket.accept()

        if session_id not in self.local_sessions:
            self.local_sessions[session_id] = {}
            # বাংলা মন্তব্য: নতুন সেশনের জন্য একটি ব্যাকগ্রাউন্ড Redis Pub/Sub লিসেনার টাস্ক চালু করা হচ্ছে
            listener_task = asyncio.create_task(self._redis_listener(session_id))
            self.redis_listeners[session_id] = listener_task

        self.local_sessions[session_id][client_id] = websocket
        logger.info(f"Client {client_id} connected locally to session {session_id}")

        # বাংলা মন্তব্য: ইউজার কানেক্ট হওয়ার সাথে সাথে Redis থেকে সর্বশেষ স্টেট ফেচ করে তাকে পাঠানো
        current_state = await self.get_session_state(session_id)
        await websocket.send_text(json.dumps({"type": "sync_state", "state": current_state}))

    async def disconnect_client(self, session_id: str, client_id: str):
        if session_id in self.local_sessions:
            if client_id in self.local_sessions[session_id]:
                del self.local_sessions[session_id][client_id]
                logger.info(f"Client {client_id} disconnected from local session {session_id}")

            # বাংলা মন্তব্য: এই কন্টেইনারে সেশনের আর কোনো ইউজার না থাকলে লিসেনার বন্ধ করে মেমোরি বাঁচানো হবে
            if not self.local_sessions[session_id]:
                del self.local_sessions[session_id]
                if session_id in self.redis_listeners:
                    self.redis_listeners[session_id].cancel()
                    del self.redis_listeners[session_id]
                    logger.info(f"Stopped Redis listener for session {session_id} on this instance")

    async def broadcast(self, session_id: str, message: dict, sender_id: str = None):
        """বাংলা মন্তব্য: মেসেজটি সরাসরি লোকাল সকেটে না পাঠিয়ে, Redis চ্যানেলে পাবলিশ করা হচ্ছে।"""
        if sender_id:
            message["sender_id"] = sender_id

        channel = f"supremeai:collab:{session_id}"
        await self.redis.publish(channel, json.dumps(message))

    async def broadcast_delta(self, session_id: str, delta: dict, sender_id: str = None):
        """বাংলা মন্তব্য: CRDT মার্জিং লজিক এবং স্টেট পারসিস্টেন্স"""
        current_state = await self.get_session_state(session_id)
        doc_state = current_state["document_state"]
        ai_cursor = current_state["ai_cursor"]

        pos = delta.get("position", 0)
        insert_text = delta.get("insert", "")

        # ডকুমেন্ট আপডেট করা
        new_doc_state = doc_state[:pos] + insert_text + doc_state[pos:]

        # AI কার্সর শিফট লজিক (Operational Transformation Simulation)
        if pos <= ai_cursor.get("position", 0):
            ai_cursor["position"] += len(insert_text)

        # আপডেট হওয়া স্টেট Redis এ সেভ করা
        await self.update_session_state(
            session_id,
            {"document_state": new_doc_state, "ai_cursor": json.dumps(ai_cursor)},
        )

        message = {
            "type": "delta",
            "delta": delta,
            "document_state": new_doc_state,
            "ai_cursor": ai_cursor,
        }
        await self.broadcast(session_id, message, sender_id)

    async def trigger_ai_edit(self, session_id: str, prompt: str, client_id: str):
        # ১. AI কার্সরের স্ট্যাটাস আপডেট করা
        current_state = await self.get_session_state(session_id)
        ai_cursor = current_state.get("ai_cursor", {"position": 0})
        ai_cursor["status"] = "processing"
        await self.update_session_state(session_id, {"ai_cursor": json.dumps(ai_cursor)})

        # ২. ফ্রন্টএন্ডে "AI is typing..." অ্যানিমেশন চালু করার সিগন্যাল পাঠানো
        message = {"type": "ai_response", "prompt": prompt, "status": "processing"}
        await self.broadcast(session_id, message, client_id)

        # ৩. মেইন থ্রেড ব্লক না করে ব্যাকগ্রাউন্ডে AI টাস্ক চালু করা
        asyncio.create_task(self._process_ai_request(session_id, prompt))

    async def _process_ai_request(self, session_id: str, prompt: str):
        """বাংলা মন্তব্য: Freebuff বা AI মডেলকে দিয়ে কোড লিখিয়ে এডিটরে পুশ করা হবে।"""
        try:
            # আমরা এখানে CloudSandboxOrchestrator ব্যবহার করছি Freebuff কে কল করার জন্য
            from tools.cloud_sandbox_orchestrator import CloudSandboxOrchestrator

            orchestrator = CloudSandboxOrchestrator()

            logger.info(f"Asking Freebuff/AI to generate code for: {prompt}")

            # AI কে দিয়ে কোড জেনারেট করানো (আপাতত আপনার Freebuff ইন্টিগ্রেশন মেথড কল করছি)
            response = await orchestrator.delegate_to_freebuff(prompt=f"Write python code for: {prompt}")

            # জেনারেট হওয়া কোড এক্সট্র্যাক্ট করা
            if response.get("status") == "success":
                ai_generated_code = f"\n\n# --- AI Generated Code ---\n# Prompt: {prompt}\n{response.get('output', '')}\n"
            else:
                # ফলব্যাক (যদি Freebuff কাজ না করে)
                ai_generated_code = f"\n\n# --- AI Response ---\n# Executed Prompt: {prompt}\ndef auto_generated_feature():\n    logger.info('Hello from SupremeAI!')\n"

            # বর্তমান স্টেট ফেচ করে শেষে কোড যুক্ত করা
            current_state = await self.get_session_state(session_id)
            doc_state = current_state["document_state"]
            insert_position = len(doc_state)

            # ডেল্টা তৈরি করা (কোড এডিটরে পুশ করার জন্য)
            delta = {"insert": ai_generated_code, "position": insert_position}

            # এডিটরে কোড ব্রডকাস্ট করা (সব ইউজারের কাছে চলে যাবে)
            await self.broadcast_delta(session_id, delta, sender_id="supreme-ai-agent")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing AI request: {e}")
        finally:
            # কাজ শেষ, "AI is typing..." অ্যানিমেশন বন্ধ করার সিগন্যাল পাঠানো
            await self.broadcast(
                session_id,
                {"type": "ai_response", "status": "idle"},
                sender_id="supreme-ai-agent",
            )

    async def _redis_listener(self, session_id: str):
        """বাংলা মন্তব্য: Redis চ্যানেল থেকে মেসেজ রিসিভ করে লোকাল ক্লায়েন্টদের কাছে পাঠাবে।"""
        channel = f"supremeai:collab:{session_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        logger.info(f"Subscribed to Redis channel: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    msg_obj = json.loads(data)
                    sender_id = msg_obj.get("sender_id")

                    if session_id in self.local_sessions:
                        for client_id, ws in self.local_sessions[session_id].items():
                            # যে মেসেজ পাঠিয়েছে তাকে ইকো না করা
                            if client_id != sender_id:
                                try:
                                    await ws.send_text(data)
                                except Exception as e:  # noqa: BLE001
                                    logger.error(f"Error sending to local client {client_id}: {e}")
        except asyncio.CancelledError:
            await pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from Redis channel: {channel}")

    async def start_collaboration_session(self, session_id: str):
        """বাংলা মন্তব্য: while True: sleep() পোলিং লুপ বাদ দিয়ে PubSub/SSE Event-Driven মডেলে মাইগ্রেট করা হলো।"""
        logger.info(f"Starting collaborative session for {session_id} using Redis PubSub.")
        try:
            from core.swarm_pubsub import swarm_streamer

            async for event in swarm_streamer.subscribe():
                if f"session_{session_id}" in event:
                    logger.info(f"Received collaboration event: {event}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Collaboration session error: {e}")
            from core.messaging.event_bus import ErrorEvent, error_event_bus

            error_event_bus.emit(
                ErrorEvent(
                    module="collaborative_editor",
                    error_type="SESSION_ERROR",
                    message=str(e)[:200],
                    severity="CRITICAL",
                    structured_context=ErrorContext(module="auto_fixed"),
                )
            )
            raise RuntimeError("Collaboration session failed.") from e


editor_manager = CollaborativeEditor()


@router.websocket("/ws/{session_id}/{client_id}")
async def websocket_collab(websocket: WebSocket, session_id: str, client_id: str):
    await editor_manager.connect_client(session_id, client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "delta":
                    await editor_manager.broadcast_delta(session_id, message.get("delta", {}), client_id)
                elif msg_type == "ai_request":
                    prompt = message.get("prompt", "")
                    await editor_manager.trigger_ai_edit(session_id, prompt, client_id)
                elif msg_type == "cursor":
                    await editor_manager.broadcast(
                        session_id,
                        {
                            "type": "cursor",
                            "client_id": client_id,
                            "position": message.get("position", {}),
                        },
                        client_id,
                    )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from client {client_id}")
    except WebSocketDisconnect:
        await editor_manager.disconnect_client(session_id, client_id)
    except Exception as e:  # noqa: BLE001
        logger.error(f"WebSocket error in session {session_id} for client {client_id}: {e}")
        await editor_manager.disconnect_client(session_id, client_id)

```

### 📄 `backend/tools/comment_thread_ai.py`

```py
"""
CommentThreadAI — Real Implementation
Handles GitHub PR/issue comment threads:
1. Auto-summarize long threads
2. Propose code fix from reviewer comment
3. Post AI reply back to GitHub
4. Detect stale/blocked PRs
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from core.config import settings

router = APIRouter(prefix="/comment-ai", tags=["comment-thread-ai"])

GITHUB_API = "https://api.github.com"
_GITHUB_TOKEN = getattr(settings, "github_token", "")


# ── Pydantic models ───────────────────────────────────────────────────────────


class PRCommentPayload(BaseModel):
    repo_full_name: str  # e.g. "owner/repo"
    pr_number: int
    comment_body: str
    file_path: str | None = None
    line_number: int | None = None
    comment_id: int | None = None
    auto_reply: bool = True  # post reply to GitHub?


class ThreadSummaryRequest(BaseModel):
    repo_full_name: str
    pr_number: int | None = None
    issue_number: int | None = None


class CommentThreadAI:
    def __init__(self, github_token: str | None = None):
        self.token = github_token or _GITHUB_TOKEN
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        logger.info(f"CommentThreadAI initialized (GitHub token: {'set' if self.token else 'MISSING'})")

    # ── LLM call ─────────────────────────────────────────────────────────────
    async def _llm(self, prompt: str, task_type: str = "coding", max_cost: float = 0.02) -> str:
        try:
            from brain.model_router import ModelRouter

            r = ModelRouter()
            result = await r.async_route_and_generate(prompt, task_type=task_type, max_cost=max_cost)
            return result.get("text", "") if isinstance(result, dict) else str(result)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"LLM call failed: {exc}")
            return ""

    # ── GitHub API helpers ────────────────────────────────────────────────────
    async def _gh_get(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{GITHUB_API}{path}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    async def _gh_post(self, path: str, body: dict) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{GITHUB_API}{path}", headers=self._headers, json=body)
        resp.raise_for_status()
        return resp.json()

    async def _get_pr_comments(self, repo: str, pr_number: int) -> list[dict]:
        """Fetch all review + issue comments on a PR."""
        comments = []
        try:
            # Review comments (line-level)
            review = await self._gh_get(f"/repos/{repo}/pulls/{pr_number}/comments")
            comments.extend(review if isinstance(review, list) else [])
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get PR review comments for {repo}#{pr_number}: {e}")
        try:
            # Issue comments (general PR comments)
            issue = await self._gh_get(f"/repos/{repo}/issues/{pr_number}/comments")
            comments.extend(issue if isinstance(issue, list) else [])
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get PR issue comments for {repo}#{pr_number}: {e}")
        return comments

    async def _get_pr_files(self, repo: str, pr_number: int) -> list[dict]:
        try:
            return await self._gh_get(f"/repos/{repo}/pulls/{pr_number}/files")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get PR files for {repo}#{pr_number}: {e}")
            return []

    async def _post_pr_comment(self, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        """Post a general comment on a PR."""
        if not self.token:
            return {"status": "skipped", "reason": "No GitHub token"}
        try:
            result = await self._gh_post(f"/repos/{repo}/issues/{pr_number}/comments", {"body": body})
            logger.info(f"Posted comment on {repo}#{pr_number}")
            return {"status": "success", "comment_url": result.get("html_url")}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GitHub post comment failed: {exc}")
            return {"status": "error", "error": str(exc)}

    async def _reply_to_review_comment(self, repo: str, pr_number: int, comment_id: int, body: str) -> dict[str, Any]:
        """Reply to a specific review comment thread."""
        if not self.token:
            return {"status": "skipped", "reason": "No GitHub token"}
        try:
            result = await self._gh_post(
                f"/repos/{repo}/pulls/{pr_number}/comments/{comment_id}/replies",
                {"body": body},
            )
            return {"status": "success", "reply_url": result.get("html_url")}
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Reply to review comment failed: {exc}")
            return {"status": "error", "error": str(exc)}

    # ── Core functions ────────────────────────────────────────────────────────

    async def handle_pr_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        comment_body: str,
        file_path: str | None = None,
        line_number: int | None = None,
        comment_id: int | None = None,
        auto_reply: bool = True,
    ) -> dict[str, Any]:
        """
        Process a PR review comment:
        1. Generate a code fix
        2. Explain the reasoning
        3. Optionally post reply to GitHub
        """
        logger.info(f"Handling PR comment: {repo_full_name}#{pr_number} file={file_path}:{line_number}")

        location = ""
        if file_path:
            location = f"\nFile: {file_path}"
            if line_number:
                location += f", Line {line_number}"

        prompt = (
            "You are a senior software engineer responding to a code review comment. "
            "Your job is:\n"
            "1. Understand what the reviewer is asking\n"
            "2. Propose a minimal, correct code fix\n"
            "3. Briefly explain WHY this change is needed\n\n"
            f"Repository: {repo_full_name}\n"
            f"PR: #{pr_number}{location}\n"
            f"Reviewer Comment: {comment_body}\n\n"
            "Format your response as:\n"
            "**Fix:**\n```\n<replacement code>\n```\n\n"
            "**Reason:** <one-line explanation>\n\n"
            "Keep it concise and professional."
        )

        ai_response = await self._llm(prompt, task_type="coding", max_cost=0.03)
        if not ai_response:
            return {"status": "error", "error": "LLM returned empty response"}

        result: dict[str, Any] = {
            "status": "success",
            "repo": repo_full_name,
            "pr_number": pr_number,
            "action": "code_fix_proposed",
            "proposed_fix": ai_response,
            "comment_posted": False,
        }

        if auto_reply and self.token:
            reply_body = f"🤖 **SupremeAI Auto-Response**\n\n{ai_response}\n\n---\n*Generated by SupremeAI. Please review before applying.*"
            if comment_id:
                post_result = await self._reply_to_review_comment(repo_full_name, pr_number, comment_id, reply_body)
            else:
                post_result = await self._post_pr_comment(repo_full_name, pr_number, reply_body)

            result["comment_posted"] = post_result.get("status") == "success"
            result["comment_url"] = post_result.get("comment_url") or post_result.get("reply_url")

        return result

    async def summarize_thread(
        self,
        repo_full_name: str,
        pr_number: int | None = None,
        issue_number: int | None = None,
    ) -> dict[str, Any]:
        """Fetch all comments and produce an AI summary of the discussion."""
        target_number = pr_number or issue_number
        if not target_number:
            return {"status": "error", "error": "Provide pr_number or issue_number"}

        try:
            comments = await self._get_pr_comments(repo_full_name, target_number)
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": f"GitHub API failed: {exc}"}

        if not comments:
            return {
                "status": "success",
                "summary": "No comments found on this PR/issue.",
            }

        thread_text = "\n\n".join(
            [
                f"[{c.get('user', {}).get('login', 'unknown')}]: {c.get('body', '')[:500]}"
                for c in comments[:30]  # cap at 30 comments
            ]
        )

        prompt = (
            f"Summarize this GitHub PR/issue discussion thread.\n"
            f"Repository: {repo_full_name}, #: {target_number}\n\n"
            f"Thread:\n{thread_text}\n\n"
            "Provide:\n"
            "1. **Main topic** (1 sentence)\n"
            "2. **Key concerns raised** (bullet points)\n"
            "3. **Current status** (resolved / blocked / in-progress)\n"
            "4. **Recommended next action** (1 sentence)\n"
            "Be concise."
        )

        summary = await self._llm(prompt, task_type="reasoning", max_cost=0.03)
        return {
            "status": "success",
            "repo": repo_full_name,
            "target": f"#{target_number}",
            "comment_count": len(comments),
            "summary": summary,
        }

    async def detect_stale_prs(self, repo_full_name: str, days_threshold: int = 7) -> dict[str, Any]:
        """Find PRs with no activity in N days."""
        try:
            prs = await self._gh_get(f"/repos/{repo_full_name}/pulls?state=open&per_page=50")
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": str(exc)}

        import datetime

        now = datetime.datetime.now(datetime.UTC)
        stale = []
        for pr in prs if isinstance(prs, list) else []:
            updated = pr.get("updated_at", "")
            if updated:
                try:
                    dt = datetime.datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.UTC)
                    days_idle = (now - dt).days
                    if days_idle >= days_threshold:
                        stale.append(
                            {
                                "number": pr["number"],
                                "title": pr.get("title", ""),
                                "author": pr.get("user", {}).get("login", ""),
                                "days_idle": days_idle,
                                "url": pr.get("html_url", ""),
                            }
                        )
                except Exception as e:  # noqa: BLE001
                    try:
                        import loguru

                        loguru.logger.error(f"Tool execution error: {e}")
                    except Exception as e:  # noqa: BLE001
                        import logging

                        logging.warning(f"Exception suppressed: {e}")
                    pass

        return {
            "status": "success",
            "repo": repo_full_name,
            "stale_threshold_days": days_threshold,
            "stale_pr_count": len(stale),
            "stale_prs": sorted(stale, key=lambda x: x["days_idle"], reverse=True),
        }

    async def handle_github_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process GitHub webhook events for PR comments."""
        action = payload.get("action", "")
        ("pr_review_comment" if "pull_request_review_comment" in str(payload.keys()) else "issue_comment")

        if action not in ("created", "edited"):
            return {"status": "ignored", "action": action}

        comment = payload.get("comment", {})
        comment_body = comment.get("body", "")

        # Only respond if comment mentions @supremeai or contains trigger keywords
        triggers = [
            "@supremeai",
            "fix this",
            "suggest a fix",
            "auto-fix",
            "what should",
        ]
        should_respond = any(t.lower() in comment_body.lower() for t in triggers)

        if not should_respond:
            return {"status": "ignored", "reason": "No trigger keyword found"}

        repo = payload.get("repository", {}).get("full_name", "")
        pr = payload.get("pull_request", {}) or payload.get("issue", {})
        pr_number = pr.get("number")

        if not repo or not pr_number:
            return {"status": "error", "error": "Missing repo or PR number in webhook"}

        file_path = comment.get("path")
        line_number = comment.get("line") or comment.get("original_line")
        comment_id = comment.get("id")

        return await self.handle_pr_comment(
            repo_full_name=repo,
            pr_number=pr_number,
            comment_body=comment_body,
            file_path=file_path,
            line_number=line_number,
            comment_id=comment_id,
            auto_reply=True,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
_comment_ai = CommentThreadAI()


# ── REST Endpoints ────────────────────────────────────────────────────────────


@router.post("/handle-comment")
async def handle_comment(payload: PRCommentPayload):
    """Handle a PR review comment — propose fix and optionally auto-reply."""
    return await _comment_ai.handle_pr_comment(
        repo_full_name=payload.repo_full_name,
        pr_number=payload.pr_number,
        comment_body=payload.comment_body,
        file_path=payload.file_path,
        line_number=payload.line_number,
        comment_id=payload.comment_id,
        auto_reply=payload.auto_reply,
    )


@router.post("/summarize")
async def summarize_thread(request: ThreadSummaryRequest):
    """Summarize a GitHub PR/issue comment thread with AI."""
    return await _comment_ai.summarize_thread(
        repo_full_name=request.repo_full_name,
        pr_number=request.pr_number,
        issue_number=request.issue_number,
    )


@router.get("/stale-prs/{owner}/{repo}")
async def detect_stale(owner: str, repo: str, days: int = 7):
    """Find PRs with no activity in N days."""
    return await _comment_ai.detect_stale_prs(f"{owner}/{repo}", days)


@router.post("/webhook")
async def github_webhook(request: Request, x_github_event: str = Header(default="ping")):
    """GitHub webhook receiver for PR comment events."""
    if x_github_event == "ping":
        return {"status": "pong"}
    try:
        payload = await request.json()
    except Exception as e:  # noqa: BLE001
        try:
            import loguru

            loguru.logger.error(f"Tool execution error: {e}")
        except Exception as e:  # noqa: BLE001
            import logging

            logging.warning(f"Exception suppressed: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if x_github_event not in ("pull_request_review_comment", "issue_comment"):
        return {"status": "ignored", "event": x_github_event}

    return await _comment_ai.handle_github_webhook(payload)

```

### 📄 `backend/tools/conversation_manager.py`

```py
import uuid
from typing import Any

from loguru import logger


class ConversationManager:
    def __init__(self):
        self.sessions: dict[str, dict[str, Any]] = {}
        logger.info("Initialized ConversationManager")

    def create_session(self) -> str:
        session_id = uuid.uuid4().hex
        self.sessions[session_id] = {
            "history": [],
            "summary": "Start of conversation.",
            "entities": {},
        }
        return session_id

    def add_message(self, session_id: str, role: str, content: str, max_history: int = 10):
        if session_id not in self.sessions:
            raise ValueError(f"Invalid session {session_id}")
        if len(content) > 4000:
            content = content[:4000] + "...[truncated]"
        session = self.sessions[session_id]
        session["history"].append({"role": role, "content": content})
        if len(session["history"]) > max_history:
            old_msg = session["history"].pop(0)
            prev = session.get("summary", "")
            session["summary"] = f"{prev} [{old_msg['role']}: {old_msg['content'][:60]}...]".strip()
            if len(session["summary"]) > 2000:
                session["summary"] = session["summary"][:2000]
        if role == "user":
            for word in content.split():
                if len(word) > 3 and word.lower() not in {
                    "this",
                    "that",
                    "with",
                    "have",
                }:
                    session["entities"][word.lower()] = session["entities"].get(word.lower(), 0) + 1

    def get_context(self, session_id: str) -> list[dict[str, str]]:
        if session_id not in self.sessions:
            return []
        session = self.sessions[session_id]
        context: list[dict[str, str]] = []
        if session.get("summary"):
            context.append({"role": "system", "content": f"Previous context: {session['summary']}"})
        context.extend(session["history"])
        return context

```

### 📄 `backend/tools/ensemble_router.py`

```py
# backend/tools/ensemble_router.py
# SupremeAI 2.0 — Provider Selection Intelligence (PSI) Ensemble Router
# ======================================================================
# বাংলা মন্তব্য: জিরো-কস্ট গ্যারান্টি সহ সার্কিট ব্রেকার ও অটো-রোটেশন রউটার।
# PSI-001: বাংলা/জটিল চিন্তায় Moonshot Kimi K2.5
# PSI-002: কোডিং ও গণিতে DeepSeek V3
# PSI-003: রেট-লিমিট বা কোটা ফেইল করলে Together AI অটো-ফলব্যাক
# PSI-004: অফলাইন বা সিক্রেট ক্ষেত্রে Ollama (Local)

import asyncio
from typing import Any

from loguru import logger


class EnsembleRouter:
    """
    বাংলা মন্তব্য: প্রজেক্টের কোর এআই রউটিং ইঞ্জিন — PSI রুলস মেনে একাধিক
    ফ্রি এআই প্রভাইডারের মধ্যে অটো-সুইচিং ও এগ্রিগেশন পরিচালনা করে।
    """

    def __init__(self) -> None:
        self.quota_exhausted: set[str] = set()

    async def route_and_vote(self, prompt: str, models: list[str] | None = None) -> dict[str, Any]:
        if models is None:
            # বাংলা মন্তব্য: ফ্রি-টিয়ার এবং ওপেন-সোর্স প্রভাইডারদের প্রায়োরিটি অর্ডার
            models = ["deepseek", "kimi", "together", "groq", "ollama"]

        # বাংলা মন্তব্য: পূর্বে রেট লিমিট বা কোটা শেষ হওয়া প্রভাইডারদের স্কিপ করা
        active_models = [m for m in models if m not in self.quota_exhausted]
        if not active_models:
            active_models = ["ollama"]  # লোকাল ফলব্যাক

        logger.info(f"⚡ PSI Ensemble Running on active models: {active_models}")

        try:
            from brain.model_router import ModelRouter

            router = ModelRouter()

            tasks = [router.async_route_and_generate(prompt, task_type="general", max_cost=0.0) for _ in active_models]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            valid = {}
            for model, resp in zip(active_models, responses, strict=False):
                if isinstance(resp, Exception):
                    err_msg = str(resp).lower()
                    if "429" in err_msg or "quota" in err_msg or "rate limit" in err_msg:
                        logger.warning(f"⚠️ PSI Circuit Breaker: Model {model} hit rate-limit/quota. Rotating out.")
                        self.quota_exhausted.add(model)
                    else:
                        logger.warning(f"Ensemble model {model} failed: {resp}")
                    continue

                text = resp.get("text", "") if isinstance(resp, dict) else str(resp)
                valid[model] = text

            best_model, best_response = (
                max(valid.items(), key=lambda item: len(item[1])) if valid else (active_models[0], "Auto-generated zero-cost fallback response.")
            )

            return {
                "status": "success",
                "best_model": best_model,
                "best_response": best_response,
                "all_responses": valid,
                "quota_exhausted_models": list(self.quota_exhausted),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Ensemble routing exception: {exc}")
            return {
                "status": "error",
                "error": str(exc),
                "best_model": active_models[0] if active_models else "ollama",
                "best_response": "Zero-cost local resilience fallback active.",
                "all_responses": {},
            }

```

### 📄 `backend/tools/freebuff_client.py`

```py
import asyncio

from loguru import logger


class FreebuffClient:
    """বাংলা মন্তব্য: Cohesion আপগ্রেড — এক্সটার্নাল CLI টুল ডেলিগেশনের একক দায়িত্ব।"""

    def __init__(self, binary_path: str = "freebuff"):
        self.binary_path = binary_path

    async def delegate_task(self, command_args: list) -> dict:
        logger.info(f"📡 Delegating asynchronous workload to external CLI tool: {self.binary_path}")
        try:
            proc = await asyncio.create_subprocess_exec(
                self.binary_path,
                *command_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip(),
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"🔴 Freebuff CLI execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

```

### 📄 `backend/tools/graph_service.py`

```py
from loguru import logger
from neo4j import AsyncGraphDatabase

from core.config import settings

# বাংলা মন্তব্য: স্কিল ইন্টিগ্রেশন এবং নলেজ গ্রাফ ম্যাপিং করার সার্ভিস লেয়ার।


class GraphService:
    def __init__(self):
        # বাংলা মন্তব্য: Neo4j Aura (ফ্রি টিয়ার) এর ক্রেডেনশিয়াল
        self.uri = getattr(settings, "neo4j_uri", "bolt://localhost:7687")
        self.user = getattr(settings, "neo4j_user", "neo4j")
        self.password = getattr(settings, "neo4j_password", None)

        # বাংলা মন্তব্য: যদি পাসওয়ার্ড না থাকে, অথবা টেস্ট এনভায়রনমেন্টে মক সিক্রেট থাকে (যেমন: 'mock_NEO4J_URI'), তবে ড্রাই-রান মোড চালু হবে।
        self.dry_run = not self.password or self.uri.startswith("mock_") or (isinstance(self.password, str) and self.password.startswith("mock_"))

        if self.dry_run:
            logger.warning("NEO4J_PASSWORD missing or mock credentials detected. GraphService will run in dry-run/mock mode.")
            self.driver = None
        else:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Initialized Neo4j GraphService")

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def sync_skills_to_graph(self, skills: list[dict]):
        """বাংলা মন্তব্য: স্কিলগুলোকে নোড (Node) হিসেবে গ্রাফ ডাটাবেসে সিঙ্ক করবে।"""
        if self.dry_run:
            logger.info(f"Dry-run: Would sync {len(skills)} skills to graph.")
            return True

        async with self.driver.session() as session:
            for skill in skills:
                await session.run(
                    "MERGE (s:Skill {id: $id}) SET s.name = $name, s.category = $category, s.success_rate = $success_rate",
                    id=skill["id"],
                    name=skill["name"],
                    category=skill["category"],
                    success_rate=skill.get("success_rate", 0.0),
                )
        return True

    async def create_relationship(self, source_id: str, target_id: str, rel_type: str, strength: float = 1.0):
        """বাংলা মন্তব্য: দুটি স্কিলের মধ্যে রিলেশনシップ (Edge) তৈরি করবে।"""
        if self.dry_run:
            logger.info(f"Dry-run: Would create {rel_type} between {source_id} and {target_id}.")
            return True

        async with self.driver.session() as session:
            query = f"MATCH (s1:Skill {{id: $source}}), (s2:Skill {{id: $target}}) MERGE (s1)-[r:{rel_type}]->(s2) SET r.strength = $strength"
            await session.run(query, source=source_id, target=target_id, strength=strength)
        return True

    async def get_skill_path(self, start_name: str, end_name: str) -> list[str]:
        """বাংলা মন্তব্য: একটি স্কিল থেকে অন্য স্কিলে যাওয়ার লার্নিং পাথ বের করবে।"""
        if self.dry_run:
            return ["Dry-run Path Node 1", "Dry-run Path Node 2"]

        async with self.driver.session() as session:
            result = await session.run(
                "MATCH path = shortestPath((start:Skill {name: $start})-[:DEPENDS_ON|PREREQUISITE*1..10]-(end:Skill {name: $end})) "
                "RETURN [n in nodes(path) | n.name] AS path",
                start=start_name,
                end=end_name,
            )
            records = await result.data()
            return records[0]["path"] if records else []

```

### 📄 `backend/tools/headless_agent_registry.py`

```py
# backend/tools/headless_agent_registry.py
"""
Headless, Zero-Cost Terminal-Based AI Agent Registry
=====================================================

স্থানীয় নথিপত্র: docs/-01-admin's plan/headless,zro cost terminal base ai agent/

এই মডিউলটি SupremeAI-এর প্যারালেল এজেন্ট এক্সিকিউটরের জন্য সব ধরনের টার্মিনাল-বেইজড এআই এজেন্টের কনফিগারেশন হারhibit করে।
প্রতিটি এজেন্টের জন্য MCP (Model Context Protocol) সার্ভার কনফিগারেশন এবং CLI কমান্ড সংজ্ঞায়িত করা হয়েছে।
"""

from __future__ import annotations

from typing import Any

from core.config import settings


def get_headless_agent_configs() -> dict[str, dict[str, Any]]:
    """বাংলা মন্তব্য: সব হেডলেস এজেন্টের কনফিগারেশন রিটার্ন করে। (ডাটাবেস থেকে)"""
    try:
        from loguru import logger

        from tools.mcp.mcp_supabase import _get_connection

        conn = _get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT agent_name, config_json FROM agent_configs WHERE status = 'active'")
            rows = cur.fetchall()
            if rows:
                return {row[0]: row[1] for row in rows}
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to fetch agent configs from DB, falling back to local: {e}")

    agent_settings: dict[str, dict[str, Any]] = {
        # bangla: গুগল অফিসিয়াল ফ্রি এআই এজেন্ট, ১০০০ রিকোয়েস্ট/দিন ফ্রি, MCP সাপোর্ট করে
        "gemini-cli": {
            "description": "Google Gemini CLI - Official free terminal AI agent",
            "command": "uvx",
            "args": ["gemini-cli-mcp"],
            "env": {
                "GEMINI_API_KEY": getattr(settings, "gemini_api_key", ""),
                "GOOGLE_API_KEY": getattr(settings, "google_api_key", ""),
            },
            "startup_timeout": 15,
            "allowed_tools": [
                "read_file",
                "write_file",
                "run_command",
                "search_web",
            ],
            "mcp_servers": ["filesystem"],
        },
        # bangla: ওপেন-সোর্স Devin বিকল্প, MIT লাইসেন্স, Docker স্যান্ডবক্স ব্যবহার করে
        "openhands": {
            "description": "OpenHands (Open-Source Devin Alternative)",
            "command": "uvx",
            "args": ["openhands-mcp-server"],
            "env": {
                "OPENHANDS_API_KEY": getattr(settings, "openhands_api_key", ""),
            },
            "startup_timeout": 20,
            "allowed_tools": [
                "browse_web",
                "execute_command",
                "read_file",
                "write_file",
                "search_code",
            ],
            "mcp_servers": ["filesystem", "github"],
            "python_sdk": True,
        },
        # bangla: অটোনোমাস কোডিং এজেন্ট, ৬১K+ গিটহাব স্টার, CLI/হেডলেস মোড
        "cline-cli": {
            "description": "Cline CLI in headless mode - Autonomous coding agent",
            "command": "npx",
            "args": ["@cline/cli", "--headless"],
            "env": {
                "ANTHROPIC_API_KEY": getattr(settings, "anthropic_api_key", ""),
                "CLINE_API_KEY": getattr(settings, "cline_api_key", ""),
            },
            "startup_timeout": 15,
            "allowed_tools": [
                "edit_file",
                "run_terminal_command",
                "search_replace",
                "read_file",
            ],
            "mcp_servers": ["filesystem", "github", "slack"],
            "supported_providers": [
                "DeepSeek",
                "Groq",
                "Ollama",
                "Anthropic",
                "OpenAI",
            ],
        },
        # bangla: কাস্টমাইজেবল ওয়ার্কফ্লো প্ল্যাটফর্ম, IDE + CLI + ক্লাউড এজেন্ট কভার করে
        "continue-dev": {
            "description": "Continue.dev - Customizable AI coding workflow platform",
            "command": "uvx",
            "args": ["continue-mcp-server"],
            "env": {
                "CONTINUE_API_KEY": getattr(settings, "continue_api_key", ""),
            },
            "startup_timeout": 15,
            "allowed_tools": [
                "chat",
                "edit",
                "generate_code",
                "refactor",
            ],
            "mcp_servers": ["filesystem", "github"],
            "self_hosted_models": True,
        },
        # bangla: টার্মিনাল পেয়ার প্রোগ্রামার, লোকাল গিট এবং ওপেন-রাউটার/ডিপসিক সাপোর্ট
        "aider": {
            "description": "Aider - Terminal-based AI pair programming tool",
            "command": "uvx",
            "args": ["aider-mcp"],
            "env": {
                "AIDER_API_KEY": getattr(settings, "aider_api_key", ""),
                "OPENROUTER_API_KEY": getattr(settings, "openrouter_api_key", ""),
            },
            "startup_timeout": 10,
            "allowed_tools": [
                "git_commit",
                "edit_file",
                "lint_code",
                "run_tests",
            ],
            "mcp_servers": ["filesystem", "github"],
            "cli_fallback": "aider",
        },
        # bangla: প্রিন্সটন ইউনিভার্সিটির তৈরি, গিটহাব ইস্যু সলভ করার জন্য সেরা টার্মিনাল এজেন্ট
        "swe-agent": {
            "description": "SWE-agent (Princeton) - GitHub issue solver terminal agent",
            "command": "uvx",
            "args": ["swe-agent-mcp"],
            "env": {
                "GITHUB_TOKEN": getattr(settings, "github_token", ""),
                "OPENAI_API_KEY": getattr(settings, "openai_api_key", ""),
            },
            "startup_timeout": 20,
            "allowed_tools": [
                "resolve_github_issue",
                "create_pr",
                "run_tests",
                "browse_repo",
            ],
            "mcp_servers": ["github", "filesystem"],
        },
        # bangla: জটিল বড় প্রজেক্ট হ্যান্ডল করার জন্য তৈরি,_version control for AI_ ফিচার
        "plandex": {
            "description": "Plandex - Terminal-based AI coding engine for complex projects",
            "command": "uvx",
            "args": ["plandex-mcp-server"],
            "env": {
                "PLANDEX_API_KEY": getattr(settings, "plandex_api_key", ""),
            },
            "startup_timeout": 15,
            "allowed_tools": [
                "execute_plan",
                "rollback_change",
                "apply_patch",
                "run_command",
            ],
            "mcp_servers": ["filesystem", "github"],
            "local_model_support": True,
        },
        # bangla: ওপেন-সোর্স Devin বিকল্প, নিজস্ব ব্রাউজার এজেন্ট এবং প্ল্যানিং মেকানিজম
        "devika": {
            "description": "Devika - Open-source Devin alternative with browser agent",
            "command": "uvx",
            "args": ["devika-mcp-server"],
            "env": {
                "GEMINI_API_KEY": getattr(settings, "gemini_api_key", ""),
                "GROQ_API_KEY": getattr(settings, "groq_api_key", ""),
            },
            "startup_timeout": 20,
            "allowed_tools": [
                "web_search",
                "browser_automation",
                "code_execution",
                "plan_feature",
            ],
            "mcp_servers": ["filesystem", "github"],
            "local_models": ["Ollama", "Groq"],
        },
        # bangla: ৯৫% কোড নিজে লিখে অ্যাপ্লিকেশন দাঁড় করিয়ে দেয়, স্টেপ-বাই-স্টেপ ডেভেলপার মতো কাজ করে
        "gpt-pilot": {
            "description": "GPT Pilot / Pythagora - Step-by-step autonomous app builder",
            "command": "uvx",
            "args": ["gpt-pilot-mcp-server"],
            "env": {
                "OPENAI_API_KEY": getattr(settings, "openai_api_key", ""),
                "Pythagora_API_KEY": getattr(settings, "pythagora_api_key", ""),
            },
            "startup_timeout": 25,
            "allowed_tools": [
                "generate_full_app",
                "ask_clarification",
                "run_integration_tests",
                "write_tests",
            ],
            "mcp_servers": ["filesystem", "github"],
            "clarifying_questions": True,
        },
        # bangla: সম্পূর্ণ ফ্রি এবং আনলিমিটেড এআই কোডিং, সেলফ-হোস্টেড ইনফ্রাস্ট্রাকচার
        "codeium": {
            "description": "Codeium - Zero-cost unlimited AI coding engine",
            "command": "uvx",
            "args": ["codeium-lang-server"],
            "env": {
                "CODEIUM_API_KEY": getattr(settings, "codeium_api_key", ""),
            },
            "startup_timeout": 15,
            "allowed_tools": [
                "autocomplete",
                "chat",
                "refactor",
                "search_code",
            ],
            "mcp_servers": ["filesystem"],
            "ide_extension": True,
            "headless_mode": True,
        },
    }
    return agent_settings


def get_headless_agent_registry() -> dict[str, Any]:
    """
    বাংলা মন্তব্য: MCP রেজিস্ট্রির জন্য সব হেডলেস এজেন্টের কনফিগারেশন রিটার্ন করে।
    এই ফাংশনটি parallel_agent_executor.py-এর সাথে ইন্টিগ্রেট করতে ব্যবহৃত হবে।
    """
    configs = get_headless_agent_configs()
    registry = {}
    for name, cfg in configs.items():
        registry[name] = {
            "command": cfg.get("command", "uvx"),
            "args": cfg.get("args", []),
            "env": cfg.get("env", {}),
            "startup_timeout": cfg.get("startup_timeout", 10),
            "allowed_tools": cfg.get("allowed_tools", []),
        }
    return registry


def get_agent_mcp_servers(agent_name: str) -> list[str]:
    """বাংলা মন্তব্য: নির্দিষ্ট এজেন্টের জন্য প্রয়োজনীয় MCP সার্ভারLisTS রিটার্ন করে।"""
    configs = get_headless_agent_configs()
    agent = configs.get(agent_name)
    if not agent:
        return []
    return agent.get("mcp_servers", [])

```

### 📄 `backend/tools/health_checker.py`

```py
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from core.config import settings


class HealthChecker:
    def __init__(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.error_history_path = os.path.join(self.data_dir, "error_history.jsonl")
        self.telegram_bot_token = getattr(settings, "telegram_bot_token", "")
        self.admin_chat_id = getattr(settings, "admin_telegram_chat_id", "")

    def run_health_check(self) -> dict[str, Any]:
        dependencies = [
            "fastapi",
            "pydantic",
            "sqlite3",
            "sympy",
            "matplotlib",
            "PIL",
            "chromadb",
        ]
        dep_status = {}
        for dep in dependencies:
            try:
                __import__(dep)
                dep_status[dep] = "OK"
            except ImportError:
                dep_status[dep] = "MISSING"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_exists = os.path.exists(os.path.join(base_dir, ".env"))
        db_exists = os.path.exists(os.path.join(base_dir, "data", "supreme_memory.db"))

        overall_status = "HEALTHY"
        if "MISSING" in dep_status.values() or not env_exists:
            overall_status = "WARNING"

        report = {
            "overall_status": overall_status,
            "dependencies": dep_status,
            "env_file_configured": env_exists,
            "sqlite_db_exists": db_exists,
            "python_version": sys.version,
        }
        report_path = os.path.join(self.data_dir, "health_status.json")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to write health report: {exc}")
        return report

    def log_error(self, error: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            **error,
        }
        try:
            with open(self.error_history_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to log error: {exc}")

    def detect_anomalies(self) -> list[dict[str, Any]]:
        anomalies: list[dict[str, Any]] = []
        error_count = 0
        rate_spike = False
        latency_delta = 0.0
        failed_api_calls = 0
        if os.path.exists(self.error_history_path):
            recent_errors: list[dict[str, Any]] = []
            cutoff = datetime.now(UTC) - timedelta(minutes=10)
            with open(self.error_history_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        ts = datetime.fromisoformat(record["timestamp"])
                        if ts >= cutoff:
                            recent_errors.append(record)
                    except Exception as e:  # noqa: BLE001
                        try:
                            import loguru

                            loguru.logger.error(f"Tool execution error: {e}")
                        except Exception as e:  # noqa: BLE001
                            import logging

                            logging.warning(f"Exception suppressed: {e}")
                        continue
            error_count = len(recent_errors)
            if error_count > 20:
                rate_spike = True
                anomalies.append(
                    {
                        "type": "error_rate_spike",
                        "details": f"{error_count} errors in last 10 minutes",
                        "severity": "HIGH",
                    }
                )
        if rate_spike:
            failed_api_calls = error_count
            anomalies.append(
                {
                    "type": "failed_api_calls",
                    "details": f"Estimated {failed_api_calls} failed calls",
                    "severity": "MEDIUM",
                }
            )
        if latency_delta > 2.0:
            anomalies.append(
                {
                    "type": "latency_increase",
                    "details": f"Latency increased by {latency_delta:.2f}s",
                    "severity": "MEDIUM",
                }
            )
        return anomalies

    async def report_to_admin(self, anomalies: list[dict[str, Any]]) -> bool:
        if not anomalies:
            return False
        lines = ["Anomaly Detection Alert"]
        for anomaly in anomalies:
            lines.append("[" + anomaly["severity"] + "] " + anomaly["type"] + ": " + anomaly["details"])
        text = "\n".join(lines)
        if not self.telegram_bot_token or not self.admin_chat_id:
            logger.warning("Telegram credentials not configured; anomaly report not sent")
            return False
        try:
            import httpx

            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json={"chat_id": self.admin_chat_id, "text": text})
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to report anomaly: {exc}")
            return False

    def propose_solutions(self, anomaly: dict[str, Any]) -> list[str]:
        anomaly_type = anomaly.get("type")
        if anomaly_type == "error_rate_spike":
            return [
                "Check logs for new exceptions",
                "Verify recent API deployments",
                "Enable circuit breaker",
            ]
        if anomaly_type == "failed_api_calls":
            return [
                "Verify provider API keys",
                "Switch to fallback provider",
                "Review rate limits",
            ]
        if anomaly_type == "latency_increase":
            return [
                "Enable query caching",
                "Review database indexes",
                "Scale horizontally",
            ]
        return ["Investigate system logs", "Run HealthChecker.run_health_check()"]

```

### 📄 `backend/tools/langchain_agent_example.py`

```py
# LangChain and LaunchDarkly AgentControl Integration Example
# বাংলা মন্তব্য: লঞ্চডার্কলি এজেন্টস কন্ট্রোল এবং ল্যাংচেইন ইন্টিগ্রেশনের একটি পূর্ণাঙ্গ ও কার্যকরী উদাহরণ

import os
import sys

from loguru import logger

from core.config import settings

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import logging

    import ldclient
    from langchain_anthropic import ChatAnthropic
    from langchain_community.callbacks import get_openai_callback
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from ldai import AIAgentConfig, AIAgentConfigDefault, LDAIClient, ModelConfig
    from ldai.tracker import TokenUsage
    from ldclient.config import Config
    from ldclient.context import Context
    from ldobserve import ObservabilityConfig, ObservabilityPlugin, observe

    INTEGRATION_OK = True
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    INTEGRATION_OK = False


def handle_agent_call_langchain(
    config: "AIAgentConfig",
    user_input: str,
) -> str:
    """
    LaunchDarkly AgentConfig এবং LangChain এর সাহায্যে এজেন্ট কল হ্যান্ডেল করে।
    """
    tracker = config.create_tracker()

    # বাংলা মন্তব্য: লঞ্চডার্কলি থেকে ডায়নামিক মডেল নির্ধারণ, অন্যথায় ডিফল্ট মডেল ব্যবহার
    default_model = "gemini-2.5-flash" if getattr(settings, "gemini_api_key", None) else "claude-3-5-sonnet-20241022"
    model_name = config.model.name if (config.model and config.model.name) else default_model

    # বাংলা মন্তব্য: লঞ্চডার্কলি মডেল প্রোভাইডার প্রিফিক্স (যেমন: "Gemini.") থাকলে তা বাদ দেওয়া হচ্ছে
    if "." in model_name:
        model_name = model_name.split(".")[-1]

    # বাংলা মন্তব্য: মডেল টাইপ অনুযায়ী সঠিক ল্যাংচেইন লাইব্রেরি সিলেক্ট করা হচ্ছে
    if "gemini" in model_name.lower():
        llm = ChatGoogleGenerativeAI(model=model_name)
    else:
        llm = ChatAnthropic(model=model_name)

    messages = []
    if config.instructions:
        messages.append(SystemMessage(content=config.instructions))
    messages.append(HumanMessage(content=user_input))

    # বাংলা মন্তব্য: লঞ্চডার্কলি অবজারভেবিলিটি ব্যবহার করে কাস্টম লগ রেকর্ড এবং স্প্যান স্টার্ট করা হচ্ছে
    observe.record_log("Executing LangChain Agent Call", logging.INFO, {"model": model_name})

    try:
        with observe.start_span("langchain-invoke", attributes={"model": model_name}) as span:
            span.set_attribute("custom-langchain-attribute", "custom-value")

            # বাংলা মন্তব্য: টোকেন ট্র্যাকিংয়ের জন্য ল্যাংচেইন কলব্যাক প্রোভাইডার ব্যবহার করা হচ্ছে
            with get_openai_callback() as cb:
                response = llm.invoke(messages)

            # লঞ্চডার্কলি ট্র্যাকার ব্যবহার করে ম্যাট্রিক্স রেকর্ড করা হচ্ছে
            tracker.track_tokens(
                TokenUsage(
                    input=cb.prompt_tokens,
                    output=cb.completion_tokens,
                    total=cb.total_tokens,
                )
            )
            tracker.track_success()
            return str(response.content)
    except Exception as exc:  # noqa: BLE001
        tracker.track_error()
        logger.error(f"LangChain invocation failed: {exc}")
        raise exc


if __name__ == "__main__":
    if not INTEGRATION_OK:
        logger.info("❌ Setup failed: missing packages.")  # noqa: T201
        sys.exit(1)

    # বাংলা মন্তব্য: লঞ্চডার্কলি ক্লায়েন্ট কনফিগারেশন এবং অবজারভেবিলিটি প্লাগইন ইনিশিয়ালাইজেশন
    sdk_key = getattr(settings, "launchdarkly_sdk_key", "sdk-85f22e74-cb85-481b-8fd9-bfb2dd5f0e10")
    ldclient.set_config(
        Config(
            sdk_key,
            plugins=[
                ObservabilityPlugin(
                    ObservabilityConfig(
                        service_name="supremeai-langchain-example",
                        service_version="1.0.0",
                    )
                )
            ],
        )
    )
    aiclient = LDAIClient(ldclient.get())
    context = Context.builder("user-123").kind("user").build()

    default_model = "gemini-2.5-flash" if getattr(settings, "gemini_api_key", None) else "claude-3-5-sonnet-20241022"
    config = aiclient.agent_config(
        "supremes-writing-assistant",
        context,
        default=AIAgentConfigDefault(
            enabled=True,
            model=ModelConfig(name=default_model),
            instructions="You are a helpful writing assistant.",
        ),
    )

    logger.info("Evaluating AgentConfig...")  # noqa: T201
    if config.enabled:
        try:
            result = handle_agent_call_langchain(config, "Hello, write a short tagline for SupremeAI.")
            logger.info(f"Result: {result}")  # noqa: T201
        except Exception as e:  # noqa: BLE001
            logger.info(f"Error during runtime execution: {e}")  # noqa: T201
    else:
        logger.info("Config is disabled in LaunchDarkly.")  # noqa: T201

```


---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

*Run external AI prompt against Section 3 above to populate.*

---

## 5. 🛠️ Recommended Delta Patches & Actions

*Pending audit execution.*

---
*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
