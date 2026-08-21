"""
Unified Meta-Engine Router (DeerFlow 2.0 + Medusa v2 + Gitea + Strapi + Keycloak).
Exposes REST and SSE endpoints for long-horizon autonomous tasks, durable workflows,
dynamic schema management, and thin-client token issuance.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from brain.dynamic_schema_builder import DynamicEntitySchema, DynamicSchemaBuilder, SchemaField
from brain.super_harness import SupremeSuperHarness
from brain.workflows.durable_workflow import DurableWorkflowEngine
from core.token_security_broker import ActionScope, ClientRole, TokenSecurityBroker
from sandbox.git_lifecycle_manager import GitLifecycleManager

router = APIRouter(prefix="/meta-engine", tags=["MetaEngine"])

super_harness = SupremeSuperHarness()
durable_workflow = DurableWorkflowEngine()
schema_builder = DynamicSchemaBuilder()
token_broker = TokenSecurityBroker()
git_manager = GitLifecycleManager()


class RunTaskRequest(BaseModel):
    goal: str = Field(..., description="The objective for the autonomous multi-agent harness")
    context: dict[str, Any] = Field(default_factory=dict, description="Initial context or file paths")


class IssueTokenRequest(BaseModel):
    user_id: str
    role: str = "developer"
    custom_scopes: list[str] | None = None
    ttl_seconds: int = 3600


class CreateSchemaRequest(BaseModel):
    collection_name: str
    display_name: str
    fields: list[dict[str, Any]]
    description: str = ""


@router.post("/run")
async def run_meta_engine_task(
    req: RunTaskRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """
    Executes a Long-Horizon Multi-Agent task (DeerFlow 2.0 pattern).
    """
    # Verify token if present
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        if not token_broker.authorize(token, ActionScope.WORKFLOW_RUN):
            raise HTTPException(status_code=403, detail="Unauthorized action scope.")

    res = await super_harness.run_long_horizon_task(
        goal=req.goal,
        initial_context=req.context,
    )
    return res


@router.post("/token/issue")
async def issue_thin_client_token(req: IssueTokenRequest) -> dict[str, Any]:
    """
    Issues a scoped action token for Thin Client / VS Code (Keycloak pattern).
    """
    role = ClientRole(req.role) if req.role in [r.value for r in ClientRole] else ClientRole.DEVELOPER
    scopes = [ActionScope(s) for s in req.custom_scopes] if req.custom_scopes else None

    token = token_broker.generate_action_token(
        user_id=req.user_id,
        role=role,
        custom_scopes=scopes,
        ttl_seconds=req.ttl_seconds,
    )
    return {"token": token, "user_id": req.user_id, "role": role.value}


@router.post("/schema/create")
async def register_dynamic_schema(req: CreateSchemaRequest) -> dict[str, Any]:
    """
    Dynamically registers a new schema/entity at runtime (Strapi pattern).
    """
    fields = [
        SchemaField(
            name=f["name"],
            field_type=f.get("field_type", "string"),
            required=f.get("required", False),
            unique=f.get("unique", False),
        )
        for f in req.fields
    ]
    schema = DynamicEntitySchema(
        collection_name=req.collection_name,
        display_name=req.display_name,
        fields=fields,
        description=req.description,
    )
    return schema_builder.register_schema(schema)


@router.get("/schema/{collection_name}")
async def query_dynamic_schema_entries(
    collection_name: str,
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    return schema_builder.query_entries(collection_name, limit=limit)


@router.get("/git/branch")
async def get_current_git_status() -> dict[str, Any]:
    """
    Checks active Git sandbox status (Gitea pattern).
    """
    return {
        "current_branch": git_manager.get_current_branch(),
        "repo_path": git_manager.repo_path,
    }
