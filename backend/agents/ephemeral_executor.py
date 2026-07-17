# backend/agents/ephemeral_executor.py
import re
import shutil
from pathlib import Path
from typing import Dict, Any
from backend.sandbox.docker_sandbox import DockerSandbox

class EphemeralExecutor:
    def __init__(self, base_skills_dir: str = "backend/skills"):
        self.base_dir = Path(base_skills_dir)
        self.ephemeral_dir = self.base_dir / "ephemeral"
        self.ephemeral_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox = DockerSandbox()

    def execute_use_and_throw(self, skill_id: str, raw_code: str, test_payload: str) -> Dict[str, Any]:
        # 🛡️ কঠোর Path Traversal ইনজেকশন ফিল্টারিং
        if not re.match(r'^[a-zA-Z0-9_]+$', skill_id):
            return {"exit_code": -1, "stdout": "", "stderr": "Blocked: Malicious Path Traversal Character in Skill ID"}

        runtime_dir = self.ephemeral_dir / skill_id
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
        runtime_dir.mkdir(parents=True, exist_ok=True)

        entry_file = "main.py"
        try:
            (runtime_dir / entry_file).write_text(raw_code, encoding="utf-8")
            return self.sandbox.run_quarantine_test(runtime_dir, entry_file, test_payload)
        finally:
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
