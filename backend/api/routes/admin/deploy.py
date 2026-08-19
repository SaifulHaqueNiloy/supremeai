"""Admin → Deploy & Emergency Deploy endpoints."""
import os

from fastapi import APIRouter
from loguru import logger

router = APIRouter()


@router.post("/deploy")
def trigger_deploy():
    logger.info("Production deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Deployment pipeline triggered successfully.",
    }


@router.post("/emergency-deploy")
def emergency_deploy():
    logger.warning("Emergency deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Emergency deployment pipeline triggered. All services will restart shortly.",
    }
