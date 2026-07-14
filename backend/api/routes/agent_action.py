from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user_token
from core.orchestration.swarm_orchestrator import MorphicOrchestrator
from core.security.security_vault import decrypt_token
from database.session import get_db_session
from models.integration import Integration


router = APIRouter(tags=["Agent Action"])


class ActionPayload(BaseModel):
    target_platform: str  # "slack", "notion", "github"
    content: str
    context: dict[str, Any] = {}


@router.post("/agent/action")
async def run_agent_action(
    payload: ActionPayload,
    token_payload: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Unified endpoint for executing AI agent actions targeting external platforms.
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    platform = payload.target_platform.lower()

    # 1. Fetch encrypted token from database
    try:
        stmt = select(Integration).where(
            Integration.user_id == user_id,
            Integration.provider == platform,
        )
        result = await db.execute(stmt)
        integration = result.scalar_one_or_none()

        if not integration or not integration.encrypted_access_token:
            raise HTTPException(status_code=400, detail=f"Integration for {platform} not found. Please connect {platform} in your settings.")

        # 2. Decrypt token securely in the API layer (Stateless injection)
        plain_token = decrypt_token(integration.encrypted_access_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching integration for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Database or Decryption error") from e

    # 3. Setup Intent and kwargs for the Orchestrator
    intent = f"sync_to_{platform}"
    kwargs = {
        f"{platform}_token": plain_token,
        "content": payload.content,
        "context": payload.context,
    }

    # 4. Trigger Morphic Orchestrator
    try:
        logger.info(f"Triggering MorphicOrchestrator for intent '{intent}'")
        orchestrator = MorphicOrchestrator()

        # Pass the kwargs to be available in the workspace execution
        workspace = await orchestrator.execute_task(
            prompt=f"Execute {intent} action.",
            user_id=user_id,
        )

        # Inject the custom intent and kwargs, overriding the generic one from `execute_task`
        workspace.intent = intent
        workspace.kwargs = kwargs

        # Rerun execute_task logic but with our custom DAG
        # Since execute_task already runs, maybe we should not call execute_task directly
        # but just use the underlying method or we can create the workspace directly.

        import uuid

        from models.shared_workspace import SharedWorkspace

        custom_workspace = SharedWorkspace(task_id=str(uuid.uuid4()), original_prompt=payload.content, intent=intent)
        custom_workspace.kwargs = kwargs

        dag = await orchestrator._get_dag_for_intent(intent)

        completed_tasks = set()
        import asyncio

        while len(completed_tasks) < len(dag):
            ready_tasks = [task for task, deps in dag.items() if task not in completed_tasks and all(d in completed_tasks for d in deps)]
            if not ready_tasks:
                raise RuntimeError("DAG execution error: No ready tasks found.")

            tasks_to_run = [orchestrator.agents[task].run(custom_workspace, user_id) for task in ready_tasks if task in orchestrator.agents]
            if tasks_to_run:
                await asyncio.gather(*tasks_to_run)
            completed_tasks.update(ready_tasks)

        result = custom_workspace.work_product.get("integration_result", {})
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Integration Execution Failed"))

        return {"status": "success", "workspace_logs": custom_workspace.logs, "result": result}

    except Exception as e:
        logger.error(f"Failed to execute agent action: {e}")
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {e}") from e
