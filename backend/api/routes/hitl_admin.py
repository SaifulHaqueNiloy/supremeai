from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from skills.installer import SkillInstaller

from api.dependencies import get_current_admin
from core.tenant_db import TenantAwareFirestore, get_tenant_db
from services.hitl.engine import HITLEngine

router = APIRouter()


class RejectionRequest(BaseModel):
    reason: str


@router.get("/pending", dependencies=[Depends(get_current_admin)])
async def get_pending_approvals(db: TenantAwareFirestore = Depends(get_tenant_db)):
    """
    Get all pending actions requiring human approval.
    """
    engine = HITLEngine(db=db)
    return engine.get_pending_approvals()


@router.post("/approve/{record_id}", dependencies=[Depends(get_current_admin)])
async def approve_pending_action(
    record_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: TenantAwareFirestore = Depends(get_tenant_db),
):
    """
    Approve a pending action.
    """
    engine = HITLEngine(db=db)
    try:
        record = engine.approve(
            admin_user_id=current_admin.get("user_id", "admin"), record_id=record_id
        )

        # If the approved action is a skill deployment, we finalize the installation here
        if record.get("target_resource", "").startswith("skills/"):
            payload = record.get("payload", {})
            installer = SkillInstaller()
            ok = installer.install_skill_from_source(
                name=payload.get("skill_name"),
                code=payload.get("code"),
                version=payload.get("version"),
                description=payload.get("description"),
                dependencies=payload.get("dependencies", []),
                uss=payload.get("uss", {}),
            )
            if not ok:
                raise RuntimeError("Failed to register and install approved skill.")

            # Update Firestore skills collection to active
            from datetime import UTC, datetime

            skill_meta = {
                "skill_name": payload.get("skill_name"),
                "demand_justification": payload.get("demand_justification"),
                "generated_code": payload.get("code"),
                "status": "ACTIVE",
                "deployed_at": datetime.now(UTC),
                "uss": payload.get("uss", {}),
                "proposal_id": payload.get("proposal_id"),
            }
            db.client.collection("skills").document(payload.get("skill_name")).set(skill_meta)

        return {"status": "success", "message": f"Record {record_id} approved.", "record": record}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reject/{record_id}", dependencies=[Depends(get_current_admin)])
async def reject_pending_action(
    record_id: str,
    payload: RejectionRequest,
    current_admin: dict = Depends(get_current_admin),
    db: TenantAwareFirestore = Depends(get_tenant_db),
):
    """
    Reject a pending action.
    """
    engine = HITLEngine(db=db)
    try:
        record = engine.reject(
            admin_user_id=current_admin.get("user_id", "admin"),
            record_id=record_id,
            reason=payload.reason,
        )
        return {"status": "success", "message": f"Record {record_id} rejected.", "record": record}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
