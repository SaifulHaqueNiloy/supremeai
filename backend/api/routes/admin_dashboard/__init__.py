"""Admin Dashboard API — ``/admin-api`` router package.

Refactored (final-test 2026-09-13, task 8-b) from the monolithic
``api/routes/admin_dashboard.py`` (~1774 lines) into domain modules with zero
behavioral change. Import compatibility is fully preserved:

    from api.routes.admin_dashboard import router      # combined router
    from api.routes.admin_dashboard import load_users  # legacy module names

Layout:
    router.py        — combined APIRouter (prefix ``/admin-api``, admin deps)
    _shared.py       — shared stores/helpers (users.json, cost caps, env
                       etag/write-lock, generic JSON IO)
    observability.py — logs stream, health map, metrics, providers,
                       model-router, live dashboard ``/ws``
    costs.py         — cost report/breakdown, cost-caps/budget-caps
    users.py         — user CRUD, tenant usage reset, impersonation
    ops.py           — deploy triggers, backups, exports, events/reports feeds
    security.py      — security scan endpoints
    deployment.py    — god-mode gate override, CI logs/report ingestion
    config.py        — feature flags, roles/permissions, workspaces, settings,
                       sessions, customers, dashboard config
    commandcenter.py — CommandCenter bridges (agents, swarm, deploy-gate, audit,
                       approvals, rules, skills, rate-limits, memory,
                       knowledge, alerts)

Every module-level name that other modules/tests previously imported from the
monolithic ``admin_dashboard`` module is re-exported below.
"""

from fastapi.responses import StreamingResponse  # noqa: F401  (legacy surface)
from api.dependencies import get_current_admin  # noqa: F401  (legacy surface)
from api.routes.admin_auth import (  # noqa: F401  (re-exported: browser.py, config_routes.py, tests)
    admin_rate_limit,
    require_admin_token,
)
from tools.billing.cost_auditor import CostAuditor  # noqa: F401  (legacy surface)
from tools.knowledge.codebase_exporter import (  # noqa: F401  (legacy surface)
    export_codebase_to_markdown,
)

from .router import router  # noqa: F401

# ── Backward-compatible re-exports (original module-level names) ────────
from ._shared import (  # noqa: F401
    COST_CAPS_FILE,
    USERS_FILE,
    _acquire_env_lock,
    _load_json_data,
    _release_env_lock,
    _save_json_data,
    get_env_etag,
    load_cost_caps,
    load_users,
    save_cost_caps,
    save_users,
)
from .config import (  # noqa: F401
    CUSTOMERS_FILE,
    SESSIONS_FILE,
    SETTINGS_FILE,
    WORKSPACES_FILE,
)
from .observability import (  # noqa: F401
    RouterOverrideRequest,
    admin_websocket,
    get_health_map,
    get_metrics,
    get_model_router,
    get_providers,
    logs_stream,
    set_router_override,
)
from .costs import (  # noqa: F401
    get_cost_caps,
    get_costs,
    get_costs_breakdown,
    update_cost_caps,
)
from .users import (  # noqa: F401
    ImpersonateRequest,
    UserUpdate,
    create_user,
    delete_user,
    get_users,
    impersonate_by_payload,
    impersonate_user,
    reset_tenant_usage_bridge,
)
from .ops import (  # noqa: F401
    create_backup,
    emergency_deploy,
    get_backups,
    get_codebase_export,
    get_events,
    get_full_data_export,
    list_reports,
    restore_backup,
    trigger_backup,
    trigger_deploy,
)
from .security import get_security_findings, run_security_scan  # noqa: F401
from .deployment import (  # noqa: F401
    GateOverridePayload,
    execute_manual_gate_override,
    get_ci_logs,
    receive_ci_report,
)
from .config import (  # noqa: F401
    _FEATURE_FLAGS,
    ConfigUpdate,
    create_feature_flag,
    create_workspace,
    delete_workspace,
    get_config,
    get_customers,
    get_feature_flags,
    get_permissions,
    get_roles,
    get_sessions,
    get_settings,
    get_workspaces,
    update_config,
    update_feature_flag,
    update_settings,
    update_workspace,
)
from .commandcenter import (  # noqa: F401
    AlertAcknowledgePayload,
    ApprovalActionPayload,
    ApprovalDecisionPayload,
    DeployGateToggle,
    acknowledge_alert,
    decide_commandcenter_approval,
    get_admin_audit_logs,
    # Resolves to the MCP control-tower variant, exactly like the monolith where
    # the second same-named ``def get_commandcenter_approvals`` shadowed the 1st.
    get_commandcenter_approvals,
    get_commandcenter_knowledge_stats,
    get_commandcenter_memory_stats,
    get_commandcenter_rate_limits,
    get_commandcenter_roi_dashboard,
    get_commandcenter_rules,
    get_commandcenter_skills,
    get_command_swarm,
    get_deploy_gate,
    list_command_agents,
    resolve_commandcenter_approval,
    toggle_deploy_gate,
    update_commandcenter_rules,
)
