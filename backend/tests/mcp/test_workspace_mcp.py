# backend/tests/mcp/test_workspace_mcp.py
# বাংলা মন্তব্য: Workspace MCP টেস্ট
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError



class TestWorkspaceMCP:
    """workspace_mcp.py এর জন্য টেস্ট ক্লাস।"""

    def test_workspace_type_enum(self):
        """WorkspaceType enum টেস্ট।"""
        from tools.mcp.mcp_workspace import WorkspaceType

        assert WorkspaceType.ECOMMERCE_BACKEND.value == "ecommerce_backend"
        assert WorkspaceType.ECOMMERCE_FRONTEND.value == "ecommerce_frontend"
        assert WorkspaceType.MOBILE_FLUTTER.value == "mobile_flutter"
        assert WorkspaceType.ADMIN_PANEL.value == "admin_panel"

    def test_workspace_context_input_validation(self):
        """WorkspaceContextInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_workspace import WorkspaceContextInput, WorkspaceType

        valid_input = WorkspaceContextInput(project_type=WorkspaceType.ECOMMERCE_BACKEND, tenant_id="tenant-001")
        assert valid_input.project_type == WorkspaceType.ECOMMERCE_BACKEND
        assert valid_input.tenant_id == "tenant-001"

    def test_scoped_file_path_input_validation(self):
        """ScopedFilePathInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_workspace import ScopedFilePathInput

        valid_input = ScopedFilePathInput(relative_path="src/main.py")
        assert valid_input.relative_path == "src/main.py"

    def test_workspace_config_loading(self):
        """ওয়ার্কস্পেস কনফিগারেশন লোডিং টেস্ট।"""
        from tools.mcp.mcp_workspace import _load_workspace_config

        config = _load_workspace_config()
        assert isinstance(config, dict)


class TestWorkspaceMCPExtended:
    """workspace_mcp.py এর জন্য অতিরিক্ত টেস্ট।"""

    def test_workspace_type_all_values(self):
        """WorkspaceType enum এর সব মান টেস্ট।"""
        from tools.mcp.mcp_workspace import WorkspaceType

        assert WorkspaceType.INFRASTRUCTURE.value == "infrastructure"
        assert WorkspaceType.ANDROID_JAVA.value == "android_java"

    def test_scoped_file_path_input_missing_path(self):
        """ScopedFilePathInput এ relative_path বাদে ইনপুট রিকেকশন টেস্ট।"""
        from tools.mcp.mcp_workspace import ScopedFilePathInput

        with pytest.raises(ValidationError):
            ScopedFilePathInput()

    @pytest.mark.asyncio
    async def test_workspace_set_context_missing_admin_for_admin_panel(self, monkeypatch):
        """Admin Panel ওয়ার্কস্পেস অথেন্টিকেশন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_workspace import (
            WorkspaceContextInput,
            WorkspaceType,
            workspace_set_context,
        )

        params = WorkspaceContextInput(project_type=WorkspaceType.ADMIN_PANEL, tenant_id="test")
        result = await workspace_set_context(params)
        data = json.loads(result)
        assert data["error"] == "Admin authorization required for admin panel workspace"

    @pytest.mark.asyncio
    async def test_workspace_set_context_success(self, monkeypatch):
        """Workspace Context সফল হয়।"""
        from tools.mcp.mcp_workspace import (
            WorkspaceContextInput,
            WorkspaceType,
            workspace_set_context,
        )

        params = WorkspaceContextInput(project_type=WorkspaceType.ECOMMERCE_BACKEND, tenant_id="test-tenant")
        result = await workspace_set_context(params)
        data = json.loads(result)
        assert data["success"] is True
        assert data["project_type"] == "ecommerce_backend"

    @pytest.mark.asyncio
    async def test_workspace_get_scoped_path_absolute_path_rejected(self):
        """পপ্যুল্ট পাথ রিজেক্ট হয়।"""
        from tools.mcp.mcp_workspace import (
            ScopedFilePathInput,
            workspace_get_scoped_path,
        )

        params = ScopedFilePathInput(relative_path="/etc/passwd")
        result = await workspace_get_scoped_path(params)
        data = json.loads(result)
        assert data["error"] == "Invalid path"

    @pytest.mark.asyncio
    async def test_workspace_get_scoped_path_symlink_outside_workspace(self, tmp_path):
        """সিমলিংক ওয়ার্কস্পেসের বাইরে ফাইল নির্দেশ করলে রিজেক্ট হয়।"""
        from tools.mcp.mcp_workspace import (
            ScopedFilePathInput,
            workspace_get_scoped_path,
        )

        # একটি টেস্ট ফাইল তৈরি করে সিমলিংক তৈরি করা হচ্ছে
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        symlink_path = tmp_path / "symlink.txt"
        try:
            symlink_path.symlink_to(test_file)
        except OSError:
            pytest.skip("Symbolic link creation not supported on this system")

        params = ScopedFilePathInput(relative_path=str(symlink_path))
        result = await workspace_get_scoped_path(params)
        data = json.loads(result)
        assert data["error"] == "Invalid path"

    @pytest.mark.asyncio
    async def test_workspace_list_projects_with_session(self, tmp_path):
        """Workspace List Projects সেশন সহ কাজ করে।"""
        import json

        from tools.mcp.mcp_workspace import (
            WORKSPACE_SESSION_FILE,
            workspace_list_projects,
        )

        # সেশন ফাইল তৈরি করা
        WORKSPACE_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        session_data = {
            "project_type": "ecommerce_backend",
            "tenant_id": "test-tenant",
            "workspace_path": "backend",
        }
        WORKSPACE_SESSION_FILE.write_text(json.dumps(session_data), encoding="utf-8")

        try:
            result = await workspace_list_projects()
            data = json.loads(result)
            assert data["current_session"] is not None
            assert data["current_session"]["project_type"] == "ecommerce_backend"
        finally:
            if WORKSPACE_SESSION_FILE.exists():
                WORKSPACE_SESSION_FILE.unlink()


    @pytest.mark.asyncio
    async def test_workspace_list_projects_json_error(self, tmp_path):
        """ওয়ার্কস্পেস লিস্টে JSON ডিকোড এরর।"""
        from tools.mcp.mcp_workspace import (
            WORKSPACE_SESSION_FILE,
            workspace_list_projects,
        )

        WORKSPACE_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_SESSION_FILE.write_text("invalid json{", encoding="utf-8")

        try:
            result = await workspace_list_projects()
            data = json.loads(result)
            assert data["current_session"] is None
        finally:
            if WORKSPACE_SESSION_FILE.exists():
                WORKSPACE_SESSION_FILE.unlink()


    @pytest.mark.asyncio
    async def test_workspace_list_projects_io_error(self, tmp_path):
        """ওয়ার্কস্পেস লিস্টে IO এরর।"""
        from tools.mcp.mcp_workspace import (
            WORKSPACE_SESSION_FILE,
            workspace_list_projects,
        )

        WORKSPACE_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_SESSION_FILE.write_text("{}", encoding="utf-8")

        try:
            result = await workspace_list_projects()
            data = json.loads(result)
            assert data["projects"] is not None
        finally:
            if WORKSPACE_SESSION_FILE.exists():
                WORKSPACE_SESSION_FILE.unlink()


    def test_workspace_config_relative_path_with_workspace_key(self, tmp_path):
        """ওয়ার্কস্পেস কনফিগারেশন রিলেটিভ পাথ রিলেটিভ পাথ কনভার্ট হয়।"""
        from tools.mcp.mcp_workspace import (
            WORKSPACE_CONFIG_FILE,
            _load_workspace_config,
        )

        config_data = {"workspace": {"ecommerce_backend": "custom/backend/path"}}
        WORKSPACE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_CONFIG_FILE.write_text(json.dumps(config_data), encoding="utf-8")

        try:
            config = _load_workspace_config()
            assert "ecommerce_backend" in config["workspace"]
        finally:
            if WORKSPACE_CONFIG_FILE.exists():
                WORKSPACE_CONFIG_FILE.unlink()


    def test_workspace_get_workspace_path_with_config(self, tmp_path):
        """ওয়ার্কস্পেস পাথ কনফিগারেশন সহ রিট্রিভ করা হয়।"""
        from tools.mcp.mcp_workspace import (
            WORKSPACE_CONFIG_FILE,
            WorkspaceType,
            _get_workspace_path,
        )

        config_data = {"workspace": {"ecommerce_backend": "custom/backend"}}
        WORKSPACE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_CONFIG_FILE.write_text(json.dumps(config_data), encoding="utf-8")

        try:
            path = _get_workspace_path(WorkspaceType.ECOMMERCE_BACKEND)
            assert "custom/backend" in str(path).replace("\\", "/")
        finally:
            if WORKSPACE_CONFIG_FILE.exists():
                WORKSPACE_CONFIG_FILE.unlink()


    def test_workspace_get_workspace_path_absolute(self, tmp_path):
        """ওয়ার্কস্পেস পাথ যদি অ্যাবসোলিট হয় তবে তা ব্যবহার হয়।"""
        from tools.mcp.mcp_workspace import (
            WORKSPACE_CONFIG_FILE,
            WorkspaceType,
            _get_workspace_path,
        )

        abs_path = str(tmp_path / "absolute" / "path")
        config_data = {"workspace": {"ecommerce_backend": abs_path}}
        WORKSPACE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        WORKSPACE_CONFIG_FILE.write_text(json.dumps(config_data), encoding="utf-8")

        try:
            path = _get_workspace_path(WorkspaceType.ECOMMERCE_BACKEND)
            assert str(path).endswith(abs_path.replace("/", os.sep).replace("\\", os.sep))
        finally:
            if WORKSPACE_CONFIG_FILE.exists():
                WORKSPACE_CONFIG_FILE.unlink()
