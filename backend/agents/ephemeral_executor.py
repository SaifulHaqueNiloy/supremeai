# backend/agents/ephemeral_executor.py
import re
import shutil
from pathlib import Path
from typing import Any

# বাংলা মন্তব্য: রেন্ডার ডকার লেআউটের সাথে সামঞ্জস্যপূর্ণ রাখতে backend. ইম্পোর্ট রুট সরিয়ে দেওয়া হয়েছে
from sandbox.docker_sandbox import DockerSandbox


class EphemeralExecutor:
    # বাংলা মন্তব্য: ডকার এনভায়রনমেন্ট অনুযায়ী ডিফল্ট পাথ "backend/skills" থেকে "skills" করা হলো
    def __init__(self, base_skills_dir: str = "skills"):
        self.base_dir = Path(base_skills_dir)
        self.ephemeral_dir = self.base_dir / "ephemeral"
        self.ephemeral_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox = DockerSandbox()

    def execute_use_and_throw(self, skill_id: str, raw_code: str, test_payload: str) -> dict[str, Any]:
        # 🛡️ কঠোর Path Traversal ইনজেকশন ফিল্টারিং
        if not re.match(r"^[a-zA-Z0-9_]+$", skill_id):
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
