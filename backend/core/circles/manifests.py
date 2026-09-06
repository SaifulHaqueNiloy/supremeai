from .contracts import CapabilityRef, CircleManifest, CircleName, RiskLevel


def default_manifests() -> tuple[CircleManifest, ...]:
    return (
        CircleManifest(
            name=CircleName.GATEWAY,
            display_name="Gateway and orchestration",
            owner="backend/core/orchestration",
            capabilities=(CapabilityRef(name="gateway.execute", owner_circle=CircleName.GATEWAY),),
        ),
        CircleManifest(
            name=CircleName.LLM,
            display_name="LLM model fleet",
            owner="backend/brain",
            capabilities=(CapabilityRef(name="llm.generate", owner_circle=CircleName.LLM),),
        ),
        CircleManifest(
            name=CircleName.MEMORY,
            display_name="Memory and knowledge",
            owner="backend/memory",
            capabilities=(CapabilityRef(name="memory.recall", owner_circle=CircleName.MEMORY),),
        ),
        CircleManifest(
            name=CircleName.TASK,
            display_name="Tasks and workers",
            owner="backend/core/queue",
            capabilities=(
                CapabilityRef(
                    name="task.submit", owner_circle=CircleName.TASK, risk_level=RiskLevel.MEDIUM
                ),
            ),
        ),
        CircleManifest(
            name=CircleName.BROWSER,
            display_name="Browser automation",
            owner="backend/core/browser_session_manager.py",
            capabilities=(
                CapabilityRef(
                    name="browser.navigate",
                    owner_circle=CircleName.BROWSER,
                    risk_level=RiskLevel.HIGH,
                    approval_required=True,
                ),
            ),
        ),
        CircleManifest(
            name=CircleName.MCP,
            display_name="MCP external tools",
            owner="infrastructure/mcp-control-plane",
            capabilities=(
                CapabilityRef(
                    name="mcp.invoke",
                    owner_circle=CircleName.MCP,
                    risk_level=RiskLevel.HIGH,
                    approval_required=True,
                ),
            ),
        ),
        CircleManifest(
            name=CircleName.ADMIN,
            display_name="Admin governance",
            owner="backend/api/routes/approval_manager.py",
            capabilities=(
                CapabilityRef(
                    name="admin.approve",
                    owner_circle=CircleName.ADMIN,
                    risk_level=RiskLevel.CRITICAL,
                    approval_required=True,
                ),
            ),
        ),
        CircleManifest(
            name=CircleName.REALTIME,
            display_name="Realtime events",
            owner="backend/api/routes/stream_hitl_sse.py",
            capabilities=(
                CapabilityRef(name="realtime.publish", owner_circle=CircleName.REALTIME),
            ),
        ),
        CircleManifest(
            name=CircleName.ARTIFACT,
            display_name="Artifacts and projects",
            owner="backend/storage",
            capabilities=(
                CapabilityRef(name="artifact.describe", owner_circle=CircleName.ARTIFACT),
            ),
        ),
        CircleManifest(
            name=CircleName.EVOLUTION,
            display_name="Evolution and learning",
            owner="backend/evolution",
            capabilities=(
                CapabilityRef(
                    name="evolution.evaluate",
                    owner_circle=CircleName.EVOLUTION,
                    risk_level=RiskLevel.HIGH,
                    approval_required=True,
                ),
            ),
        ),
    )
