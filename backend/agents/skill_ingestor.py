# backend/agents/skill_ingestor.py
import ast
import hashlib
import urllib.request
import zipfile
import io
from pathlib import Path
from typing import Tuple, Dict, Any
from schemas.skill_manifest import SkillManifest, SkillStatus
from schemas.skill_index import SkillIndexManager
from sandbox.docker_sandbox import DockerSandbox

class SkillIngestor:
    def __init__(self, base_skills_dir: str = "backend/skills"):
        self.base_dir = Path(base_skills_dir)
        self.staging_dir = self.base_dir / "staging"
        self.quarantine_dir = self.base_dir / "quarantine"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        self.index_manager = SkillIndexManager()
        self.sandbox = DockerSandbox()

    def static_ast_safety_check(self, code: str) -> Tuple[bool, str]:
        """
        স্যান্ডবক্সে পাঠানোর আগে পাইথনের AST মডিউল দিয়ে কোডের সাইলেন্ট ব্ল্যাকলিস্ট স্ক্যান।
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # ১. বিপজ্জনক ইমপোর্ট চেক
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ["os", "subprocess", "sys", "requests", "urllib", "socket"]:
                            return False, f"Forbidden import found: {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ["os", "subprocess", "sys", "requests", "urllib", "socket"]:
                        return False, f"Forbidden from-import found: {node.module}"

                # ২. ইভল/এক্সিকিউট মেথড ব্লকিং
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                        return False, "Dangerous code pattern found: Use of exec/eval is highly restricted."
            return True, "AST static integrity verified."
        except SyntaxError:
            return False, "Invalid Python syntax detected."

    def ingest_mcp_skill(self, manifest: SkillManifest, zip_url: str, entry_file: str, test_payload: str) -> Dict[str, Any]:
        """
        উৎস থেকে স্কিল ডাউনলোড করে কোয়ারেন্টাইন পাইপলাইন রান করায়।
        """
        # সেফ সোর্স ওরিজিন এনফোর্সমেন্ট
        if not self.index_manager.is_source_allowed(str(manifest.source_url)):
            manifest.status = SkillStatus.REJECTED
            self.index_manager.update_skill(manifest)
            return {"success": False, "detail": "Security violation: Source domain is not in verified allowlist."}

        try:
            # ১. HTTP Stream জিপ ডাউনলোড (জিরো-ব্লোট মেমরি বাফার)
            with urllib.request.urlopen(zip_url) as response:
                zip_data = response.read()

            # ২. চেকসাম ইন্টিগ্রিটি ভেরিফিকেশন (SHA-256)
            download_hash = hashlib.sha256(zip_data).hexdigest()
            if download_hash != manifest.checksum:
                manifest.status = SkillStatus.REJECTED
                self.index_manager.update_skill(manifest)
                return {"success": False, "detail": "Integrity check failed: Verification checksum mismatch."}

            # ৩. স্ট্রিম আনজিপ করে নির্দিষ্ট ফাইল এক্সট্র্যাক্ট করা
            skill_target_dir = self.staging_dir / manifest.skill_id
            skill_target_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
                archive.extractall(path=skill_target_dir)

            # ৪. ফাইল রিড ও এএসটি স্ট্যাটিক সেফটি চেক এনফোর্স
            entry_path = skill_target_dir / entry_file
            if not entry_path.exists():
                return {"success": False, "detail": f"Manifest entry point {entry_file} missing in archive."}

            code_content = entry_path.read_text(encoding="utf-8")
            is_safe, static_msg = self.static_ast_safety_check(code_content)

            if not is_safe:
                manifest.status = SkillStatus.REJECTED
                self.index_manager.update_skill(manifest)
                return {"success": False, "detail": f"Static Security Drop: {static_msg}"}

            # ৫. কোড স্টেজিংয়ে মুভ ও ডাইনামিক স্যান্ডবক্স টেস্ট
            manifest.status = SkillStatus.QUARANTINE
            self.index_manager.update_skill(manifest)

            sandbox_res = self.sandbox.run_quarantine_test(skill_target_dir, entry_file, test_payload)

            if sandbox_res["exit_code"] == 0:
                # ডাইনামিক স্মোক টেস্ট সফল!
                return {
                    "success": True,
                    "status": "QUARANTINE_PASSED",
                    "detail": "Skill successfully ingested, statically verified, and sandbox smoke-tested. Awaiting Librarian Approval.",
                    "sandbox_output": sandbox_res["stdout"]
                }
            else:
                # স্যান্ডবক্সে কোড ক্র্যাশ করেছে বা নেটওয়ার্ক এস্কেপ করার চেষ্টা করেছে
                manifest.status = SkillStatus.REJECTED
                self.index_manager.update_skill(manifest)
                return {
                    "success": False,
                    "status": "REJECTED",
                    "detail": f"Dynamic Quarantine Failure: Code aborted with exit code {sandbox_res['exit_code']}.",
                    "sandbox_error": sandbox_res["stderr"]
                }

        except Exception as e:
            manifest.status = SkillStatus.REJECTED
            self.index_manager.update_skill(manifest)
            return {"success": False, "detail": f"Ingestion infrastructure breakdown: {str(e)}"}
