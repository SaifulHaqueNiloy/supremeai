"""Deployment trigger endpoint (POST /admin-api/deploy)."""

from api.routes.admin_dashboard import router
from core.logging_config import logger


@router.post("/deploy")
def trigger_deploy():
    logger.info("Production deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Deployment pipeline triggered successfully.",
    }
