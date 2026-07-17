# backend/agents/ephemeral_executor.py
import shutil
import os
from pathlib import Path
from typing import Dict, Any
from sandbox.docker_sandbox import DockerSandbox

class EphemeralExecutor:
    def __init__(self, base_skills_dir: str = "backend/skills"):
        self.base_dir = Path(base_skills_dir)
        self.ephemeral_dir = self.base_dir / "ephemeral"
        self.ephemeral_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox = DockerSandbox()

    def is_rare_request(self, user_prompt: str) -> bool:
        """
        Classifier: ইউজারের প্রম্পটটি বিরল বা ক্ষণস্থায়ী কাজের কিনা তা নির্ণয় করে।
        (প্রোডাকশনে এখানে একটি লাইটওয়েট রুল-বেসড বা ক্লাসিফায়ার মডেল বসানো যাবে)
        """
        rare_keywords = ["calculate astronomical", "eclipse 2040", "one-time graph", "parse obsolete format"]
        return any(keyword in user_prompt.lower() for keyword in rare_keywords)

    def execute_use_and_throw(self, skill_id: str, raw_code: str, test_payload: str) -> Dict[str, Any]:
        """
        কোড মেমরিতে নিয়ে স্যান্ডবক্সে রান করায় এবং এক্সিকিউশন শেষে চিরতরে মুছে ফেলে।
        """
        runtime_dir = self.ephemeral_dir / skill_id
        runtime_dir.mkdir(parents=True, exist_ok=True)

        entry_file = "main.py"
        code_path = runtime_dir / entry_file

        try:
            # ১. ক্ষণস্থায়ী ফাইল রাইট
            code_path.write_text(raw_code, encoding="utf-8")

            # ২. ডকার স্যান্ডবক্স আইসোলেটেড রান এনফোর্সমেন্ট (Default-deny Network)[cite: 1]
            sandbox_res = self.sandbox.run_quarantine_test(runtime_dir, entry_file, test_payload)
            return sandbox_res

        finally:
            # 🧹 ৩. ওয়াটারটাইট ক্লিনআপ লুপ (গার্বেজ কালেকশন এনফোর্সমেন্ট)[cite: 1]
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
                print(f"✨ [EPHEMERAL CLEANUP] Strict runtime cache purged for skill: {skill_id}")
