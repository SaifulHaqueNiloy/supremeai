# backend/agents/skill_librarian.py
import shutil
from pathlib import Path
from typing import List, Dict, Any
from schemas.skill_manifest import SkillManifest, SkillStatus
from schemas.skill_index import SkillIndexManager

class SkillLibrarian:
    def __init__(self, base_skills_dir: str = "backend/skills"):
        self.base_dir = Path(base_skills_dir)
        self.quarantine_dir = self.base_dir / "quarantine"
        self.approved_dir = self.base_dir / "approved"
        self.ephemeral_dir = self.base_dir / "ephemeral"

        self.approved_dir.mkdir(parents=True, exist_ok=True)
        self.index_manager = SkillIndexManager()

    def list_quarantine_queue(self) -> List[Dict[str, Any]]:
        """কোয়ারেন্টাইনে থাকা পেন্ডিং স্কিলগুলোর মেটাডেটা তালিকা রিটার্ন করে।"""
        index = self.index_manager.load_index()
        return [
            meta for meta in index.values()
            if meta.get("status") == SkillStatus.QUARANTINE
        ]

    def process_approval(self, skill_id: str, action: str, ai_patch_code: str = None) -> Dict[str, Any]:
        """Admin এর নির্দেশ অনুযায়ী স্কিল স্থানান্তর ও অনুমোদন গেটওয়ে এনফোর্স করে।"""
        index = self.index_manager.load_index()
        if skill_id not in index:
            return {"success": False, "detail": "Skill not found in global registry."}

        manifest_data = index[skill_id]
        manifest = SkillManifest(**manifest_data)
        source_path = self.quarantine_dir / skill_id

        if action == "APPROVE":
            target_path = self.approved_dir / skill_id
            manifest.status = SkillStatus.APPROVED
            # যদি এআই মডিফাইড কোড থাকে, তবে সোর্স ফাইলটি প্যাচ করা হবে
            if ai_patch_code:
                self._apply_morphic_patch(source_path, ai_patch_code)

            shutil.move(str(source_path), str(target_path))

        elif action == "APPROVE_AS_EPHEMERAL":
            target_path = self.ephemeral_dir / skill_id
            manifest.status = SkillStatus.EPHEMERAL
            shutil.move(str(source_path), str(target_path))

        elif action == "REJECT":
            manifest.status = SkillStatus.REJECTED
            if source_path.exists():
                shutil.rmtree(source_path)
        else:
            return {"success": False, "detail": "Invalid approval action identifier."}

        # গ্লোবাল ইনডেক্স ফাইল আপডেট
        self.index_manager.update_skill(manifest)
        self._trigger_admin_notification(skill_id, action)

        return {"success": True, "detail": f"Skill {skill_id} state successfully updated to {manifest.status}."}

    def _apply_morphic_patch(self, skill_dir: Path, patch_code: str):
        """Morphic Adaptation: র কোডকে SwarmAgentBase ফর্মে রূপান্তর করে।"""
        main_file = skill_dir / "main.py"
        main_file.write_text(patch_code, encoding="utf-8")

    def _trigger_admin_notification(self, skill_id: str, action: str):
        """সিস্টেম অ্যাডমিন বা ডিসকর্ড ওয়েবহুকে স্টেট পরিবর্তনের নোটিফিকেশন পাঠায়।"""
        print(f"📢 [NOTIFICATION SYSTEM] Skill '{skill_id}' processed with action: {action}")
