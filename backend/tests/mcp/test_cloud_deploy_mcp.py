# backend/tests/mcp/test_cloud_deploy_mcp.py
# বাংলা মন্তব্য: Cloud Deploy MCP (Render/Railway/Oracle) টেস্ট
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import importlib
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError



class TestCloudDeployMCP:
    """cloud_deploy_mcp.py এর জন্য টেস্ট ক্লাস।"""

    def test_deploy_service_input_validation(self):
        """DeployServiceInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        # বৈধ ইনপুট
        valid_input = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test-service", branch="main")
        assert valid_input.provider == CloudProvider.RENDER
        assert valid_input.service_name == "test-service"
        assert valid_input.branch == "main"

    def test_deploy_service_input_missing_provider(self):
        """প্রোভাইডার বাদে ইনপুট রিকেকশন টেস্ট।"""
        from tools.mcp.mcp_cloud_deploy import DeployServiceInput

        with pytest.raises(ValidationError):
            DeployServiceInput(service_name="test-service", branch="main")

    def test_get_logs_input_validation(self):
        """GetLogsInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, GetLogsInput

        valid_input = GetLogsInput(provider=CloudProvider.RAILWAY, service_name="my-service", lines=500)
        assert valid_input.lines == 500

    def test_cloud_provider_enum(self):
        """CloudProvider enum টেস্ট।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider

        assert CloudProvider.RENDER.value == "render"
        assert CloudProvider.RAILWAY.value == "railway"
        assert CloudProvider.ORACLE.value == "oracle"


class TestCloudDeployMCPExtended:
    """cloud_deploy_mcp.py এর জন্য অতিরিক্ত টেস্ট।"""

    @pytest.mark.asyncio
    async def test_deploy_service_missing_admin_auth(self, monkeypatch):
        """অ্যাডমিন অথেন্টিকেশন না থাকলে ডিপ্লয় ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
        result = await cloud_deploy_service(params)
        data = json.loads(result)
        assert data["error"] == "Admin authorization required for deployments"

    @pytest.mark.asyncio
    async def test_deploy_service_missing_render_api_key(self, monkeypatch):
        """RENDER_API_KEY না থাকলে ডিপ্লয় ব্যর্থ হয়।"""
        monkeypatch.setenv("RENDER_API_KEY", "")
        import tools.mcp.mcp_cloud_deploy

        import importlib
        importlib.reload(tools.mcp.mcp_cloud_deploy)
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
        result = await cloud_deploy_service(params)
        data = json.loads(result)
        assert data["error"] == "RENDER_API_KEY not configured"

    @pytest.mark.asyncio
    async def test_deploy_service_missing_railway_token(self, monkeypatch):
        """RAILWAY_TOKEN না থাকলে ডিপ্লয় ব্যর্থ হয়।"""
        monkeypatch.setenv("RAILWAY_TOKEN", "")
        import tools.mcp.mcp_cloud_deploy

        import importlib
        importlib.reload(tools.mcp.mcp_cloud_deploy)
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        params = DeployServiceInput(provider=CloudProvider.RAILWAY, service_name="test")
        result = await cloud_deploy_service(params)
        data = json.loads(result)
        assert data["error"] == "RAILWAY_TOKEN not configured"

    @pytest.mark.asyncio
    async def test_deploy_service_missing_oracle_api_key(self, monkeypatch):
        """ORACLE_CLOUD_API_KEY না থাকলে ডিপ্লয় ব্যর্থ হয়।"""
        monkeypatch.setenv("ORACLE_CLOUD_API_KEY", "")
        import tools.mcp.mcp_cloud_deploy

        import importlib
        importlib.reload(tools.mcp.mcp_cloud_deploy)
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        params = DeployServiceInput(provider=CloudProvider.ORACLE, service_name="test")
        result = await cloud_deploy_service(params)
        data = json.loads(result)
        assert data["error"] == "ORACLE_CLOUD_API_KEY not configured"

    @pytest.mark.asyncio
    async def test_deploy_service_api_error_401(self, monkeypatch):
        """API এরর 401 হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Invalid API key" in result

    @pytest.mark.asyncio
    async def test_deploy_service_api_error_404(self, monkeypatch):
        """API এরর 404 হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Service not found" in result

    @pytest.mark.asyncio
    async def test_deploy_service_api_error_429(self, monkeypatch):
        """API এরর 429 (Rate Limit) হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Rate limit exceeded" in result

    @pytest.mark.asyncio
    async def test_deploy_service_generic_error(self, monkeypatch):
        """জেনেরিক এরর হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(side_effect=Exception("Network error"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_get_logs_missing_api_key(self, monkeypatch):
        """Get Logs এ API কী না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("RENDER_API_KEY", "")
        import tools.mcp.mcp_cloud_deploy

        import importlib
        importlib.reload(tools.mcp.mcp_cloud_deploy)
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        params = GetLogsInput(provider=CloudProvider.RENDER, service_name="test")
        result = await cloud_get_deployment_logs(params)
        data = json.loads(result)
        assert data["error"] == "RENDER_API_KEY not configured"

    @pytest.mark.asyncio
    async def test_get_logs_api_error(self, monkeypatch):
        """Get Logs এ API এরর হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = GetLogsInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_get_deployment_logs(params)
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_list_services_success(self, monkeypatch):
        """Services তালিকা লোড করা যায়।"""
        monkeypatch.setenv("RAILWAY_TOKEN", "")
        monkeypatch.setenv("ORACLE_CLOUD_API_KEY", "")
        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "serviceName": "service1",
                "status": "active",
                "url": "https://example.com",
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_list_services_exception(self, monkeypatch):
        """Services তালিকা লোড করতে ব্যর্থ হলে একখানে থাকে।"""
        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 0


    def test_deploy_service_input_branch_default(self):
        """DeployServiceInput এ ব্রাঞ্চের ডিফল্ট মান।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
        assert params.branch == "main"


    def test_deploy_service_input_strip_whitespace(self):
        """DeployServiceInput এ হোয়াইটস্পেস স্ট্রিপ হয়।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="  test-service  ")
        assert params.service_name == "test-service"


    def test_deploy_service_input_service_name_pattern(self):
        """DeployServiceInput এ সার্ভিস নেম প্যাটার্ন ভ্যালিডেশন।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        with pytest.raises(ValidationError):
            DeployServiceInput(provider=CloudProvider.RENDER, service_name="invalid name!")


    def test_get_logs_input_lines_default(self):
        """GetLogsInput এ লাইনসের ডিফল্ট মান।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, GetLogsInput

        params = GetLogsInput(provider=CloudProvider.RENDER, service_name="test")
        assert params.lines == 100


    def test_get_logs_input_lines_validation(self):
        """GetLogsInput এ লাইনসের ভ্যালিডেশন।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, GetLogsInput

        with pytest.raises(ValidationError):
            GetLogsInput(provider=CloudProvider.RENDER, service_name="test", lines=0)

        with pytest.raises(ValidationError):
            GetLogsInput(provider=CloudProvider.RENDER, service_name="test", lines=1001)


    def test_deploy_service_input_invalid_branch(self):
        """DeployServiceInput এ অবৈধ ব্রাঞ্চ রিজেক্ট হয়।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, DeployServiceInput

        with pytest.raises(ValidationError):
            DeployServiceInput(
                provider=CloudProvider.RENDER,
                service_name="test",
                branch="invalid;branch",
            )


    def test_get_logs_input_invalid_lines(self):
        """GetLogsInput এ অবৈধ লাইনস রিজেক্ট হয়।"""
        from tools.mcp.mcp_cloud_deploy import CloudProvider, GetLogsInput

        with pytest.raises(ValidationError):
            GetLogsInput(provider=CloudProvider.RENDER, service_name="test", lines=-1)


    @pytest.mark.asyncio
    async def test_deploy_service_render_success(self, monkeypatch):
        """Render-এ সফল ডিপ্লয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "created",
            "url": "https://render.com/test",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test-service")
            result = await cloud_deploy_service(params)
            data = json.loads(result)
            assert data["success"] is True


    @pytest.mark.asyncio
    async def test_deploy_service_railway_success(self, monkeypatch):
        """Railway-এ সফল ডিপ্লয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "deploying",
            "url": "https://railway.app/test",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RAILWAY, service_name="test-service")
            result = await cloud_deploy_service(params)
            data = json.loads(result)
            assert data["success"] is True


    @pytest.mark.asyncio
    async def test_deploy_service_oracle_success(self, monkeypatch):
        """Oracle-এ সফল ডিপ্লয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "accepted",
            "url": "https://oracle.com/test",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.ORACLE, service_name="test-service")
            result = await cloud_deploy_service(params)
            data = json.loads(result)
            assert data["success"] is True


    @pytest.mark.asyncio
    async def test_get_logs_render_success(self, monkeypatch):
        """Render-এ সফল লগ রিট্রিভাল।"""
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"logs": ["log line 1", "log line 2"]}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = GetLogsInput(provider=CloudProvider.RENDER, service_name="test-service", lines=50)
            result = await cloud_get_deployment_logs(params)
            data = json.loads(result)
            assert data["provider"] == "render"


    @pytest.mark.asyncio
    async def test_get_logs_railway_success(self, monkeypatch):
        """Railway-এ সফল লগ রিট্রিভাল।"""
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"logs": "log content"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = GetLogsInput(provider=CloudProvider.RAILWAY, service_name="test-service")
            result = await cloud_get_deployment_logs(params)
            data = json.loads(result)
            assert data["provider"] == "railway"


    @pytest.mark.asyncio
    async def test_get_logs_oracle_success(self, monkeypatch):
        """Oracle-এ সফল লগ রিট্রিভাল।"""
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"logs": ["log1", "log2"]}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = GetLogsInput(provider=CloudProvider.ORACLE, service_name="test-service")
            result = await cloud_get_deployment_logs(params)
            data = json.loads(result)
            assert data["provider"] == "oracle"


    @pytest.mark.asyncio
    async def test_list_services_render_only(self, monkeypatch):
        """কেবলমাত্র Render সার্ভিস লিস্ট করা হয়।"""
        monkeypatch.setenv("RAILWAY_TOKEN", "")
        monkeypatch.setenv("ORACLE_CLOUD_API_KEY", "")

        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"serviceName": "svc1", "status": "active", "url": "https://test.com"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 1


    @pytest.mark.asyncio
    async def test_list_services_railway_only(self, monkeypatch):
        """কেবলমাত্র Railway সার্ভিস লিস্ট করা হয়।"""
        monkeypatch.setenv("RENDER_API_KEY", "")
        monkeypatch.setenv("ORACLE_CLOUD_API_KEY", "")

        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "svc1", "status": "active", "url": "https://test.com"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 1


    @pytest.mark.asyncio
    async def test_list_services_render_error(self, monkeypatch):
        """Render API এ রিকোয়েস্ট ফেইল করে।"""
        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 0


    @pytest.mark.asyncio
    async def test_list_services_railway_error(self, monkeypatch):
        """Railway API এ রিকোয়েস্ট ফেইল করে।"""
        monkeypatch.setenv("RENDER_API_KEY", "test-key")

        from tools.mcp.mcp_cloud_deploy import cloud_list_services

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await cloud_list_services()
            data = json.loads(result)
            assert data["count"] == 0


    @pytest.mark.asyncio
    async def test_deploy_service_api_error_500(self, monkeypatch):
        """API এরর 500 হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Error" in result


    @pytest.mark.asyncio
    async def test_deploy_service_api_error_503(self, monkeypatch):
        """API এরর 503 হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            DeployServiceInput,
            cloud_deploy_service,
        )

        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = DeployServiceInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_deploy_service(params)
            assert "Error" in result


    @pytest.mark.asyncio
    async def test_get_logs_api_error_500(self, monkeypatch):
        """Get Logs এ API এরর 500 হ্যান্ডল হয়।"""
        from tools.mcp.mcp_cloud_deploy import (
            CloudProvider,
            GetLogsInput,
            cloud_get_deployment_logs,
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = GetLogsInput(provider=CloudProvider.RENDER, service_name="test")
            result = await cloud_get_deployment_logs(params)
            assert "Error" in result
