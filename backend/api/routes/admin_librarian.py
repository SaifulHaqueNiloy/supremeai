# backend/api/routes/admin_librarian.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.agents.skill_librarian import SkillLibrarian

# 🔄 প্রিফিক্স ডুপ্লিকেশন ফিক্স (/api/api/admin... থেকে /api/admin...)
router = APIRouter(prefix="/admin/librarian", tags=["Librarian Gateway"])
librarian = SkillLibrarian()

class ApprovalRequest(BaseModel):
    skill_id: str
    action: str  # APPROVE, APPROVE_AS_EPHEMERAL, REJECT
    ai_patch_code: Optional[str] = None

@router.get("/queue", response_model=List[dict])
async def get_quarantine_queue():
    """কোয়ারেন্টাইনে থাকা পেন্ডিং স্কিলগুলোর লিস্ট ড্যাশবোর্ডে পাঠায়"""
    try:
        return librarian.list_quarantine_queue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch queue: {str(e)}")

@router.post("/process")
async def process_skill_action(payload: ApprovalRequest):
    """Admin এর ক্লিক করা অ্যাকশন (Approve/Reject) প্রসেস করে"""
    result = librarian.process_approval(
        skill_id=payload.skill_id,
        action=payload.action,
        ai_patch_code=payload.ai_patch_code
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["detail"])
    return result
