# Define allowed automation workflows here.
# Key: The workflow_key used in AutomationEvent.
# Value: The webhook path or internal ID for the provider to route the event.
AUTOMATION_REGISTRY: dict[str, str] = {
    "USER_REGISTERED": "/webhook/user-registered",
    "SECURITY_ALERT": "/webhook/security-alert",
    "HITL_REQUIRED": "/webhook/hitl-required",
    "PAYMENT_SUCCESS": "/webhook/payment-success",
    "PAYMENT_FAILED": "/webhook/payment-failed",
    "SYS_HEALTH_DEGRADED": "/webhook/sys-health-degraded",
}


def is_valid_workflow(workflow_key: str) -> bool:
    """Check if the provided key is registered in the system."""
    return workflow_key in AUTOMATION_REGISTRY


def get_workflow_route(workflow_key: str) -> str:
    """Get the target route for a registered workflow key."""
    if not is_valid_workflow(workflow_key):
        raise ValueError(f"Unknown workflow key: {workflow_key}")
    return AUTOMATION_REGISTRY[workflow_key]
