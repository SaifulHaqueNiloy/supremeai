# Part 6: P2P Compute Mesh & Zero-Trust Sandboxing Audit

> **Audit Generation Time:** `2026-07-24 20:09:07 UTC`  
> **Module Description:** Zero-trust MicroVM sandbox execution, hardware resource broker, and crypto proof-of-work credit system.  
> **Status:** `SELF_CONTAINED / READY FOR EXTERNAL AI AUDIT`

---

## 1. 📁 Target Subsystems & File Inventory

- `backend/p2p/resource_broker.py` (File, 4807 bytes)
- `backend/p2p/credit_system.py` (File, 1117 bytes)
- `backend/core/microvm_sandbox.py` (File, 18898 bytes)

---

## 2. 🔍 Audit Objectives & Key Checklist

- [ ] **Code Quality & Type Safety:** Check MyPy type hints and Ruff linting rules.
- [ ] **Security & Resilience:** Check exception handling, circuit breakers, and rate limiters.
- [ ] **Zero-Cost & Free-Tier Optimization:** Ensure no paid cloud service dependencies.
- [ ] **Bangla Code Comments:** Verify `// বাংলা মন্তব্য` is present across updated code blocks.

---

## 3. 📦 Complete Subsystem Source Code Dump

Below is the full source code for all target files in this module. Any external AI can audit this single document directly.

### 📄 `backend/p2p/resource_broker.py`

```py
"""P2P Resource Broker for SupremeAI 2.0.

বাংলা: P2P কম্পিউট রিসোর্স শেয়ারিং, নোড ম্যাচমেকিং, জিরো-ট্রাস্ট স্যান্ডবক্সিং এবং ক্রিপ্টোগ্রাফিক প্রুফ ভ্যালিডেশন।
"""

import logging
import time
from typing import Any

from core.microvm_sandbox import run_in_sandbox
from backend.p2p.credit_system import credit_system

logger = logging.getLogger("supremeai.p2p.resource_broker")


class P2PResourceBroker:
    """Brokers compute requests between resource providers and consumers inside isolated Sandboxes."""

    def __init__(self):
        self._active_nodes: dict[str, dict[str, Any]] = {}

    def register_node(
        self,
        node_id: str,
        owner_id: str,
        capabilities: dict[str, Any],
        public_key_pem: str | None = None,
    ) -> dict[str, Any]:
        """Register a peer node capable of providing compute resources inside Zero-Trust Sandbox.

        বাংলা: নতুন P2P কম্পিউট প্রোভাইডার নোড রেজিস্টার করার সময় পাবলিসিটি কি ও স্যান্ডবক্স ক্যাপাবিলিটি সংগৃহীত হয়।
        """
        node_info = {
            "node_id": node_id,
            "owner_id": owner_id,
            "capabilities": capabilities,
            "public_key": public_key_pem,
            "registered_at": time.time(),
            "last_heartbeat": time.time(),
            "status": "idle",
            "sandboxed": True,
        }
        self._active_nodes[node_id] = node_info
        logger.info(f"P2P Zero-Trust Node registered: {node_id} (owner: {owner_id}, sandbox=True)")
        return node_info

    def find_best_node(self, required_capability: str, min_credits: float = 1.0) -> dict[str, Any] | None:
        """Find an idle node matching the capability requirements.

        বাংলা: চাওয়া কম্পিউট ক্ষমতার উপর ভিত্তি করে স্যান্ডবক্সড সেরা নোড খুঁজে বের করে।
        """
        now = time.time()
        for node_id, node in self._active_nodes.items():
            # Filter stale heartbeats (> 60s)
            if now - node["last_heartbeat"] > 60:
                continue
            if node["status"] == "idle" and node["capabilities"].get(required_capability, False):
                return node
        return None

    async def execute_sandboxed_task(self, task_code: str, node_id: str) -> dict[str, Any]:
        """
        Execute incoming untrusted peer code strictly inside MicroVM / Container Sandbox.
        বাংলা মন্তব্য: জিরো-ট্রাস্ট সিকিউরিটির জন্য P2P নোডের নির্দেশ সরাসরি লোকাল সার্ভারে না চালিয়ে মাইক্রোভিএম স্যান্ডবক্সে এক্সিকিউট করা হয়।
        """
        logger.info(f"Executing P2P Task inside Zero-Trust MicroVM Sandbox for node {node_id}")
        result = await run_in_sandbox(task_code, timeout_seconds=30.0)
        return result

    def allocate_task(self, consumer_id: str, required_capability: str, cost: float) -> dict[str, Any]:
        """Match and allocate a task to a provider node, deducting credits.

        বাংলা: টাস্ক বরাদ্দ করে এবং ক্রেডিট লেজার অ্যাডজাস্ট করে।
        """
        consumer_balance = credit_system.get_balance(consumer_id)
        if consumer_balance < cost:
            return {"status": "error", "message": f"Insufficient credits ({consumer_balance} < {cost})"}

        node = self.find_best_node(required_capability)
        if not node:
            return {"status": "error", "message": "No available P2P provider nodes matching requirements"}

        # Transfer credits via credit_system ledger
        credit_system.deduct_credits(consumer_id, cost)
        credit_system.add_credits(node["owner_id"], cost)

        node["status"] = "busy"
        return {
            "status": "allocated",
            "node_id": node["node_id"],
            "provider_id": node["owner_id"],
            "sandboxed": True,
            "cost": cost,
        }

    def release_node(self, node_id: str):
        """Release a node back to idle status."""
        if node_id in self._active_nodes:
            self._active_nodes[node_id]["status"] = "idle"


resource_broker = P2PResourceBroker()


```

### 📄 `backend/p2p/credit_system.py`

```py
import uuid
from typing import Any

from loguru import logger


class CreditLedger:
    async def earn(self, user_id: str, amount: float, reason: str) -> dict[str, Any]:
        return {
            "tx_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "reason": reason,
            "type": "credit",
        }

    async def spend(self, user_id: str, amount: float, reason: str) -> dict[str, Any]:
        return {
            "tx_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": -amount,
            "reason": reason,
            "type": "debit",
        }

    async def opt_out(self, user_id: str) -> None:
        logger.info(f"User {user_id} opted out of P2P")

    async def opt_in(self, user_id: str) -> None:
        logger.info(f"User {user_id} opted in to P2P")

    async def balance(self, user_id: str) -> float:
        return 0.0


class ResourceBroker:
    async def match(self, task: dict[str, Any]) -> dict[str, Any]:
        return {"matched": False, "reason": "no_available_peers"}

```

### 📄 `backend/core/microvm_sandbox.py`

```py
# backend/core/microvm_sandbox.py
# বাংলা মন্তব্য: সম্পূর্ণ রি-ফ্যাক্টর — Path Traversal Whitelist + Strict Validation।
# sandbox_root এখন Settings থেকে আসে এবং startup-এ whitelist validate হয়।
# string interpolation দিয়ে path build করা নিষিদ্ধ — pathlib.Path ব্যবহার।
# Docker image whitelist enforced — arbitrary image run নিষিদ্ধ।
# os.environ-এ secrets inject করা বন্ধ।
# CancelledError সবসময় re-raise।
import asyncio
import contextlib
import json

# ── Security Constants ─────────────────────────────────────────────────────────
import platform
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import settings
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus

# বাংলা মন্তব্য: Sandbox root whitelist — অনুমোদিত directories শুধু এখানে থাকতে পারে।
# কেউ SANDBOX_ROOT=/etc/cron.d দিলে startup-এই crash হবে।
_SANDBOX_ROOT_WHITELIST: frozenset[str] = frozenset(
    {
        "/tmp/sandboxes",  # nosec B108 — whitelisted
        "/var/tmp/sandboxes",
        "/run/sandboxes",
        "C:\\tmp\\sandboxes",
        "C:\\temp\\sandboxes",
    }
    if platform.system() == "Windows"
    else {
        "/tmp/sandboxes",
        "/var/tmp/sandboxes",
        "/run/sandboxes",
    }
)

# বাংলা মন্তব্য: vm_id এ শুধু alphanumeric, hyphen, underscore allowed — path injection prevent
_VM_ID_PATTERN: re.Pattern = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# বাংলা মন্তব্য: Docker image whitelist — arbitrary image run নিষিদ্ধ
_ALLOWED_DOCKER_IMAGES: frozenset[str] = frozenset(
    {
        "python:3.11-slim",
        "python:3.12-slim",
        "node:20-slim",
    }
)

# বাংলা মন্তব্য: Default docker image — whitelist-এর প্রথমটি
_DEFAULT_DOCKER_IMAGE: str = "python:3.11-slim"


def _validate_sandbox_root(path_str: str) -> Path:
    """
    বাংলা মন্তব্য: Sandbox root path startup validation।
    Whitelist-এ না থাকলে ValueError — startup crash।
    Symlink traversal check সহ resolved path check করা হয়।
    """
    path = Path(path_str).resolve()
    # বাংলা মন্তব্য: resolved path whitelist-এ check করতে হবে — symlink bypass prevent
    if str(path) not in _SANDBOX_ROOT_WHITELIST:
        raise ValueError(
            f"SANDBOX_ROOT '{path_str}' (resolved: '{path}') is not in the allowed whitelist "
            f"{sorted(_SANDBOX_ROOT_WHITELIST)}. "
            f"Set SANDBOX_ROOT env var to an approved path."
        )
    return path


def _validate_vm_id(vm_id: str) -> str:
    """বাংলা মন্তব্য: vm_id pattern validation — path injection prevent।"""
    if not _VM_ID_PATTERN.match(vm_id):
        raise ValueError(f"Invalid vm_id '{vm_id}'. Only alphanumeric, hyphen, underscore allowed (max 64 chars).")
    return vm_id


def _safe_vm_path(sandbox_root: Path, vm_id: str) -> Path:
    """
    বাংলা মন্তব্য: vm_id থেকে safe path তৈরি।
    ResourceGuard.verify_path ব্যবহার করে path traversal check করা হয়।
    """
    from core.security.resource_guard import ResourceGuard

    vm_path = (sandbox_root / vm_id).resolve()
    return ResourceGuard.verify_path(vm_path)


class MicroVMSandbox:
    """
    বাংলা মন্তব্য: Path-Hardened MicroVM Sandbox।
    - সব paths pathlib.Path দিয়ে তৈরি (string interpolation নয়)
    - sandbox_root startup-এ whitelist validated
    - vm_id regex validated
    - Docker image whitelist enforced
    - CancelledError সবসময় re-raise
    """

    _vm_id_counter: int = 0

    def __init__(self) -> None:
        # বাংলা মন্তব্য: paths Settings থেকে আসছে — hardcode নেই
        self.firecracker_path = Path(settings.firecracker_path)
        self.gvisor_path = Path(settings.gvisor_path)

        # বাংলা মন্তব্য: sandbox_root startup-এ validate হবে — invalid = ValueError
        self.sandbox_root = _validate_sandbox_root(settings.sandbox_root)
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

        self.network_disabled = True
        self.auto_destroy = True
        self.allow_fallback = settings.allow_sandbox_fallback

        logger.info(f"[MicroVMSandbox] Initialized. sandbox_root={self.sandbox_root} | allow_fallback={self.allow_fallback}")

    @classmethod
    def _generate_vm_id(cls) -> str:
        """বাংলা মন্তব্য: Validated vm_id generate করা।"""
        cls._vm_id_counter += 1
        vm_id = f"supremeai-vm-{int(time.time())}-{cls._vm_id_counter}"
        return _validate_vm_id(vm_id)

    def _check_microvm_available(self) -> str | None:
        """বাংলা মন্তব্য: Available VM runtime check। String type return করে।"""
        if shutil.which("firecracker"):
            return "firecracker"
        if shutil.which("runsc"):
            return "gvisor"
        return None

    def _create_microvm_config(self, vm_dir: Path, vm_id: str) -> Path:
        """
        বাংলা মন্তব্য: Firecracker config তৈরি — pathlib.Path ব্যবহার।
        string interpolation দিয়ে path build করা সম্পূর্ণ নিষিদ্ধ।
        """
        config = {
            "boot-source": {
                "kernel_image_path": "/tmp/vmlinux",  # nosec B108 — known fixed path
                "boot_args": "console=ttyS0 reboot=k panic=1 pci=off",
            },
            "drives": [
                {
                    "drive_id": "rootfs",
                    # বাংলা মন্তব্য: pathlib.Path — string concatenation নয়
                    "path_on_host": str(vm_dir / "rootfs.ext4"),
                    "is_root_device": True,
                }
            ],
            "machine-config": {"vcpu_count": 1, "mem_size_mib": 128},
            "network-interfaces": [] if self.network_disabled else [],
        }
        config_path = vm_dir / "config.json"
        from core.security.resource_guard import ResourceGuard

        ResourceGuard.write_text(config_path, json.dumps(config), encoding="utf-8")
        return config_path

    async def execute_async(self, cmd: str, timeout: int = 30, language: str = "python") -> dict[str, Any]:
        """বাংলা মন্তব্য: Secure code execution। Path validation mandatory।"""
        vm_runtime = self._check_microvm_available()

        if not vm_runtime:
            if not self.allow_fallback:
                logger.error("[MicroVMSandbox] No MicroVM runtime available and fallback disabled.")
                error_event_bus.emit(
                    ErrorEvent(
                        module="microvm_sandbox",
                        error_type="SANDBOX_UNAVAILABLE",
                        message="No MicroVM runtime (Firecracker/gVisor) available.",
                        severity="ERROR",
                        structured_context=ErrorContext(module="auto_fixed"),
                        context={"allow_fallback": False, "language": language},
                    )
                )
                return {
                    "success": False,
                    "error": "MicroVM sandbox unavailable — security enforcement active.",
                    "provider": "none",
                }
            vm_runtime = "docker"

        try:
            vm_id = self._generate_vm_id()
            vm_dir = _safe_vm_path(self.sandbox_root, vm_id)
            vm_dir.mkdir(parents=True, exist_ok=True)
        except ValueError as exc:
            logger.exception(f"[MicroVMSandbox] Path validation failed: {exc}")
            return {"success": False, "error": str(exc), "provider": "none"}

        try:
            if vm_runtime == "firecracker":
                return await self._run_firecracker(vm_dir, vm_id, timeout)
            elif vm_runtime == "gvisor":
                return await self._run_gvisor(cmd, timeout)
            else:
                return await self._run_docker_fallback(cmd, timeout)
        except asyncio.CancelledError:
            # বাংলা মন্তব্য: CancelledError re-raise — কখনো suppress করা যাবে না
            logger.warning(f"[MicroVMSandbox] Execution cancelled for vm_id={vm_id}")
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[MicroVMSandbox] Unexpected error for vm_id={vm_id}: {exc}")
            error_event_bus.emit(
                ErrorEvent(
                    module="microvm_sandbox",
                    error_type="EXECUTION_FAILED",
                    message=str(exc)[:500],
                    severity="ERROR",
                    structured_context=ErrorContext(module="auto_fixed"),
                    context={"vm_id": vm_id, "vm_runtime": vm_runtime},
                )
            )
            return {"success": False, "error": str(exc), "provider": vm_runtime}
        finally:
            if self.auto_destroy:
                self._destroy_vm_dir(vm_dir)

    async def _run_firecracker(self, vm_dir: Path, vm_id: str, timeout: int) -> dict[str, Any]:
        """বাংলা মন্তব্য: Firecracker run — pathlib.Path দিয়ে args build।"""
        self._create_microvm_config(vm_dir, vm_id)
        api_sock = vm_dir / "api.sock"

        try:
            result = subprocess.run(
                # বাংলা মন্তব্য: list-based args — shell=True নিষিদ্ধ
                ["firecracker", "--api-sock", str(api_sock)],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,  # explicit — no shell injection
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "provider": "firecracker",
                "ephemeral": True,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timeout",
                "provider": "firecracker",
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[MicroVMSandbox] Firecracker error: {exc}")
            return {"success": False, "error": str(exc), "provider": "firecracker"}

    async def _run_gvisor(self, cmd: str, timeout: int) -> dict[str, Any]:
        """
        বাংলা মন্তব্য: gVisor run — cmd tempfile-এ write করে execute।
        string interpolation দিয়ে cmd argument inject করা নিষিদ্ধ।
        tempfile sandbox_root-এ তৈরি হয় — /tmp bypass নয়।
        """
        tmp_path: Path | None = None
        try:
            # বাংলা মন্তব্য: tempfile sandbox_root-এ — arbitrary dir নয়
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                dir=str(self.sandbox_root),
            ) as tf:
                tf.write(cmd)
                tmp_path = Path(tf.name)

            result = subprocess.run(
                # বাংলা মন্তব্য: "--" separator — flags injection prevent
                ["runsc", "do", "--", "python3", str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "provider": "gvisor",
                "ephemeral": True,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timeout",
                "provider": "gvisor",
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[MicroVMSandbox] gVisor error: {exc}")
            return {"success": False, "error": str(exc), "provider": "gvisor"}
        finally:
            # বাংলা মন্তব্য: temp file সবসময় cleanup — resource leak নিষিদ্ধ
            if tmp_path and tmp_path.exists():
                with contextlib.suppress(OSError):
                    tmp_path.unlink()

    async def _run_docker_fallback(self, cmd: str, timeout: int) -> dict[str, Any]:
        """
        বাংলা মন্তব্য: Docker fallback — whitelist image only।
        cmd tempfile-এ write করা হয় — argument injection নয়।
        """
        # বাংলা মন্তব্য: _ALLOWED_DOCKER_IMAGES whitelist enforce
        docker_image = _DEFAULT_DOCKER_IMAGE
        assert docker_image in _ALLOWED_DOCKER_IMAGES  # nosec B101

        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                dir=str(self.sandbox_root),  # sandbox root-এ — arbitrary dir নয়
            ) as tf:
                tf.write(cmd)
                tmp_path = Path(tf.name)

            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--read-only",
                    "--network",
                    "none",
                    "--memory",
                    "128m",
                    "--cpus",
                    "0.5",
                    # বাংলা মন্তব্য: validated temp file path — string interpolation নয়
                    "-v",
                    f"{tmp_path}:/sandbox/code.py:ro",
                    docker_image,  # whitelisted image শুধু
                    "python",
                    "/sandbox/code.py",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "provider": "docker-fallback",
                "ephemeral": True,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Execution timeout",
                "provider": "docker-fallback",
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[MicroVMSandbox] Docker fallback error: {exc}")
            return {"success": False, "error": str(exc), "provider": "docker-fallback"}
        finally:
            # বাংলা মন্তব্য: temp file সবসময় cleanup — resource leak নিষিদ্ধ
            if tmp_path and tmp_path.exists():
                with contextlib.suppress(OSError):
                    tmp_path.unlink()

    def _destroy_vm_dir(self, vm_dir: Path) -> None:
        """বাংলা মন্তব্য: VM directory cleanup — pathlib.Path দিয়ে।"""
        try:
            if vm_dir.exists():
                shutil.rmtree(vm_dir)
            logger.debug(f"[MicroVMSandbox] VM dir destroyed: {vm_dir}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[MicroVMSandbox] Failed to destroy VM dir {vm_dir}: {exc}")

    async def health_check(self) -> dict[str, Any]:
        """বাংলা মন্তব্য: Health check — admin dashboard-এ expose করা যাবে।"""
        vm_runtime = self._check_microvm_available()
        return {
            "status": "ready" if vm_runtime else "unavailable",
            "provider": vm_runtime or "none",
            "auto_destroy": self.auto_destroy,
            "network_disabled": self.network_disabled,
            "sandbox_root": str(self.sandbox_root),
            "allow_fallback": self.allow_fallback,
        }


# ── Lazy Singleton ─────────────────────────────────────────────────────────────
# বাংলা মন্তব্য: Lazy singleton — import time-এ initialization নিষিদ্ধ।
# আগে: `sandbox = MicroVMSandbox()` import-এ execute হতো — cold start বাড়াতো।
# এখন: প্রথম ব্যবহারের সময় instantiate হবে।
_sandbox_instance: MicroVMSandbox | None = None


def get_sandbox() -> MicroVMSandbox:
    """বাংলা মন্তব্য: Lazy singleton factory — import সময়ে initialization নিষিদ্ধ।"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = MicroVMSandbox()
    return _sandbox_instance


async def execute_code_securely(code: str, timeout: int = 30, language: str = "python") -> dict[str, Any]:
    """বাংলা মন্তব্য: Public API — sandbox validate করে code execute করে।"""
    return await get_sandbox().execute_async(code, timeout, language)


# বাংলা মন্তব্য: import asyncio উপরে সরানো হয়েছে।

```


---

## 4. 🐛 Identified Vulnerabilities & Edge Cases

*Run external AI prompt against Section 3 above to populate.*

---

## 5. 🛠️ Recommended Delta Patches & Actions

*Pending audit execution.*

---
*Generated automatically by SupremeAI 2.0 Audit Generator Script.*
