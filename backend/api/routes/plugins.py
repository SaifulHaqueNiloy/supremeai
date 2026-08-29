from typing import Any

from api.dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.plugins.lifecycle_manager import PluginLifecycleManager
from core.plugins.manifest_registry import PluginManifestRegistry
from database.session import get_db

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


class InstallRequest(BaseModel):
    plugin_id: str
    granted_capabilities: list[str]


@router.get("/marketplace")
async def list_marketplace_plugins(db: AsyncSession = Depends(get_db)):
    """Returns all available plugins in the marketplace."""
    manifests = await PluginManifestRegistry.get_all_manifests(db, active_only=True)
    return {"plugins": manifests}


@router.get("/installed")
async def list_installed_plugins(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """Returns plugins installed by the current user."""
    installations = await PluginLifecycleManager.get_user_installations(db, user.uid)
    return {"installations": installations}


@router.post("/install")
async def install_plugin(
    req: InstallRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """Installs a plugin for the user."""
    manifest = await PluginManifestRegistry.get_manifest_by_id(db, req.plugin_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Plugin not found")

    installation = await PluginLifecycleManager.install_plugin(
        session=db,
        user_id=user.uid,
        plugin_id=req.plugin_id,
        granted_capabilities=req.granted_capabilities,
    )
    return {"message": "Plugin installed successfully", "installation_id": str(installation.id)}


@router.delete("/uninstall/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    """Uninstalls a plugin for the user."""
    success = await PluginLifecycleManager.uninstall_plugin(db, user.uid, plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail="Installation not found")
    return {"message": "Plugin uninstalled successfully"}
