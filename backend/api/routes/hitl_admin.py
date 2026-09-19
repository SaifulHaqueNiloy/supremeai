"""Admin HITL queue — Firestore-backed pending approvals (M17 P-A/P-C).

বাংলা (route-ownership): এই রুট `hitl_admin` মাউন্ট-অগ্রাধিকারে
`/api/v1/hitl/{pending,approve,reject}`-এর মালিক — ফ্রন্টএন্ড ApprovalQueue
এই চুক্তিতেই খাওয়া (data/hooks.ts)। executor-যুক্ত pending-task পৃষ্ঠ
(`approval_manager`) আলাদা স্টোরে থাকে; ৭→১ স্টোর-একত্রীকরণ M17 P-D-তে।

M17 P-C সৎ-সেমান্টিকস ফিক্স: আগে `get_tenant_db`-এর TenantAwareFirestore
পাঠানো হতো, কিন্তু HITLEngine-এর স্টোর-চুক্তি হলো কাঁচা ক্লায়েন্ট
(`.client`) — ফলে প্রতিটি অপারেশন নীরবে ব্যর্থ/খালি [] ফেরত দিত (fake-empty
কিউ)। এখন গ্লোবাল firestore ক্লায়েন্ট সরাসরি সমাধান করা হয়; সমাধান
না হলে লাউড 503 — নীরব খালি-কিউ ভান নেই।
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_current_admin
from services.hitl.engine import HITLEngine

router = APIRouter()


class RejectionRequest(BaseModel):
    reason: str


def _hitl_engine() -> HITLEngine:
    """Resolve the global Firestore client and build a contract-valid HITLEngine.

    বাংলা: admin approvals টেন্যান্ট-স্কোপড নয় (গ্লোবাল কিউ) — তাই
    TenantAwareFirestore নয়, কাঁচা ক্লায়েন্টের shim। ক্লায়েন্ট অনুপস্থিতে
    fail-closed 503 (কোনো অবস্থায় নীরব [] নয়)।
    """

    class _ClientShim:
        # HITLEngine-এর স্টোর-চুক্তি: `.client` + `.collection()`।
        def __init__(self, client):
            self.client = client

        def collection(self, name: str):
            return self.client.collection(name)

    try:
        from core.gcp_firestore import get_firestore_client

        client = get_firestore_client()
    except Exception as e:  # বাংলা: সমাধান-ব্যর্থতা লাউড — নীরব [] নয়
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"HITL store unavailable: {type(e).__name__}",
        ) from e
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HITL store unavailable (Firestore client not configured).",
        )
    return HITLEngine(db=_ClientShim(client))


@router.get("/pending", dependencies=[Depends(get_current_admin)])
async def get_pending_approvals():
    """
    Get all pending actions requiring human approval.
    """
    engine = _hitl_engine()
    return engine.get_pending_approvals()


@router.post("/approve/{record_id}", dependencies=[Depends(get_current_admin)])
async def approve_pending_action(
    record_id: str,
    current_admin: dict = Depends(get_current_admin),
):
    """
    Approve a pending action.
    """
    engine = _hitl_engine()
    try:
        record = engine.approve(
            admin_user_id=current_admin.get("user_id", "admin"), record_id=record_id
        )

        return {"status": "success", "message": f"Record {record_id} approved.", "record": record}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reject/{record_id}", dependencies=[Depends(get_current_admin)])
async def reject_pending_action(
    record_id: str,
    payload: RejectionRequest,
    current_admin: dict = Depends(get_current_admin),
):
    """
    Reject a pending action.
    """
    engine = _hitl_engine()
    try:
        record = engine.reject(
            admin_user_id=current_admin.get("user_id", "admin"),
            record_id=record_id,
            reason=payload.reason,
        )
        return {"status": "success", "message": f"Record {record_id} rejected.", "record": record}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
