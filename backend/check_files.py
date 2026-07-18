import os

files = [
    "scratch_push_env.py",
    ".github/scripts/ci-decision-engine.py",
    "backend/api/routes/dock_actions.py",
    "scripts/codegraph_integration.py",
    "backend/core/decision_engine.py",
    "backend/core/observability/telemetry.py",
    "backend/core/security/rbac.py",
    "backend/core/security/secret_vault.py",
    "backend/core/orchestration/agent_orchestrator.py",
    "backend/api/routes/payments.py",
    "backend/api/routes/billing_api.py",
    "backend/api/routes/auth.py",
    "backend/api/routes/api_keys.py",
    "backend/core/security/auth_middleware.py",
    "backend/api/routes/admin.py",
    "backend/api/routes/tenant_admin.py",
    "backend/api/routes/cloud_mesh.py",
    "backend/api/routes/execution_policies.py",
    "backend/api/routes/llm_gateway.py",
    "backend/api/routes/metrics.py",
    "backend/api/routes/selector_healing.py",
    "backend/api/routes/site_actions.py",
    "backend/api/routes/traffic_monitor.py",
]
base = r"c:\Users\n\supremeai\supremeai_2.0"
for f in files:
    exists = "EXISTS" if os.path.exists(os.path.join(base, f)) else "NOT FOUND"
