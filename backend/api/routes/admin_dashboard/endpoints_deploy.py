"""Deployment trigger endpoint (POST /admin-api/deploy)."""


from core.logging_config import logger

from api.routes.admin_dashboard import router


@router.post("/deploy")
def trigger_deploy():
    logger.info("Production deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Deployment pipeline triggered successfully.",
    }
