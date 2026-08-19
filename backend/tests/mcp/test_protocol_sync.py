# backend/tests/mcp/test_protocol_sync.py
# বাংলা মন্তব্য: MCP সার্ভার সিকনেশন/সিঙ্ক ও হেল্পার টেস্ট
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError
import importlib



class TestMCPServerSync:
    """MCP সার্ভারগুলোর সিকনেশন টেস্ট।"""

    def test_all_mcp_servers_importable(self):
        """সব MCP সার্ভার ইম্পোর্ট করা যায় কিনা টেস্ট।"""
        import importlib.util

        servers = [
            "mcp_cloud_deploy",
            "mcp_github_cicd",
            "mcp_supabase",
            "mcp_workspace",
        ]
        for server in servers:
            spec = importlib.util.find_spec(f"tools.mcp.{server}")
            assert spec is not None, f"tools.{server} module not found"

    def test_mcp_servers_have_fastmcp_instance(self):
        """MCP সার্ভারগুলোতে FastMCP ইনস্ট্যান্স আছে কিনা টেস্ট।"""
        from tools.mcp import (
            mcp_cloud_deploy,
            mcp_github_cicd,
            mcp_supabase,
            mcp_workspace,
        )

        assert hasattr(mcp_cloud_deploy, "mcp")
        assert hasattr(mcp_github_cicd, "mcp")
        assert hasattr(mcp_supabase, "mcp")
        assert hasattr(mcp_workspace, "mcp")

    def test_mcp_servers_have_tools(self):
        """MCP সার্ভারগুলোতে টুলস আছে কিনা টেস্ট।"""
        from tools.mcp import (
            mcp_cloud_deploy,
            mcp_github_cicd,
            mcp_supabase,
            mcp_workspace,
        )

        # cloud_deploy_mcp টুলস
        assert hasattr(mcp_cloud_deploy, "cloud_deploy_service")
        assert hasattr(mcp_cloud_deploy, "cloud_get_deployment_logs")
        assert hasattr(mcp_cloud_deploy, "cloud_list_services")

        # github_cicd_mcp টুলস
        assert hasattr(mcp_github_cicd, "github_create_pull_request")
        assert hasattr(mcp_github_cicd, "github_run_auto_fix")
        assert hasattr(mcp_github_cicd, "github_list_issues")
        assert hasattr(mcp_github_cicd, "github_get_ci_status")

        # supabase_mcp টুলস
        assert hasattr(mcp_supabase, "supabase_execute_sql")
        assert hasattr(mcp_supabase, "supabase_create_table")
        assert hasattr(mcp_supabase, "supabase_run_migration")
        assert hasattr(mcp_supabase, "supabase_list_tables")

        # workspace_mcp টুলস
        assert hasattr(mcp_workspace, "workspace_set_context")
        assert hasattr(mcp_workspace, "workspace_get_scoped_path")
        assert hasattr(mcp_workspace, "workspace_list_projects")

    def test_mcp_servers_run(self):
        """MCP সার্ভারগুলো run() মেথড কল করলে রান হয় কিনা যাচাই।"""
        from tools import mcp_cloud_deploy, mcp_supabase

        with patch.object(mcp_cloud_deploy.mcp, "run") as mock_run_cloud:
            mcp_cloud_deploy.mcp.run()
            mock_run_cloud.assert_called_once()

        with patch.object(mcp_supabase.mcp, "run") as mock_run_sb:
            mcp_supabase.mcp.run()
            mock_run_sb.assert_called_once()

    def test_service_name_validation_fails(self):
        """ভুল ফরম্যাটের সার্ভিস নেম রিজেক্ট হচ্ছে কিনা টেস্ট।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        with pytest.raises(ValidationError):
            DeployServiceInput(
                provider=CloudProvider.RENDER,
                service_name="invalid;injection",
                branch="main",
            )

    @pytest.mark.asyncio
    async def test_workspace_path_traversal_fails(self):
        """পাথ ট্রাভার্সাল আক্রমণ রিজেক্ট হচ্ছে কিনা টেস্ট।"""
        from tools.mcp.mcp_workspace import (
            ScopedFilePathInput,
            workspace_get_scoped_path,
        )

        params = ScopedFilePathInput(relative_path="../../sensitive_file.txt")
        result = await workspace_get_scoped_path(params)
        assert "Path traversal not allowed" in result


class TestHelperFunctions:
    """MCP সার্ভারগুলোর হেল্পার ফাংশনগুলোর টেস্ট।"""

    def test_check_admin_auth_true(self, monkeypatch):
        """অ্যাডমিন অথেন্টিকেশন সঠিকভাবে চেক হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import _check_admin_auth

        assert _check_admin_auth() is True

    def test_check_admin_auth_false(self, monkeypatch):
        """অ্যাডমিন অথেন্টিকেশন না থাকলে False রিটার্ন করে।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_cloud_deploy import _check_admin_auth

        assert _check_admin_auth() is False

    def test_check_admin_auth_default(self):
        """অ্যাডমিন অথেন্টিকেশন ডিফল্টভাবে False।"""
        import os

        # যদি ভ্যারিয়েবল না থাকে
        if "ADMIN_AUTHORIZED" in os.environ:
            del os.environ["ADMIN_AUTHORIZED"]

        from tools.mcp.mcp_cloud_deploy import _check_admin_auth

        assert _check_admin_auth() is False

    def test_handle_api_error_401(self):
        """API এরর 401 স্ট্যান্ডার্ডাইজ্ড হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import _handle_api_error

        result = _handle_api_error(Exception("error"), 401)
        assert "Invalid API key" in result

    def test_handle_api_error_404(self):
        """API এরর 404 স্ট্যান্ডার্ডাইজ্ড হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import _handle_api_error

        result = _handle_api_error(Exception("error"), 404)
        assert "Service not found" in result

    def test_handle_api_error_429(self):
        """API এরর 429 স্ট্যান্ডার্ডাইজ্ড হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import _handle_api_error

        result = _handle_api_error(Exception("error"), 429)
        assert "Rate limit exceeded" in result

    def test_handle_api_error_generic(self):
        """জেনেরিক API এরর স্ট্যান্ডার্ডাইজ্ড হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import _handle_api_error

        result = _handle_api_error(ValueError("test error"))
        assert "Error" in result
