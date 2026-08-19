# backend/tests/mcp/test_github_cicd_mcp.py
# বাংলা মন্তব্য: GitHub CICD MCP টেস্ট
# --- test_mcp_servers_integration.py থেকে স্প্লিট করা হয়েছে ---

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError



class TestGithubCICDMCP:
    """github_cicd_mcp.py এর জন্য টেস্ট ক্লাস।"""

    def test_create_pr_input_validation(self):
        """CreatePRInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_github_cicd import CreatePRInput

        valid_input = CreatePRInput(
            title="Test PR",
            body="This is a test PR",
            head="feature-branch",
            base="develop",
        )
        assert valid_input.title == "Test PR"
        assert valid_input.base == "develop"

    def test_create_pr_input_missing_title(self):
        """শিরোনাম বাদে ইনপুট রিকেকশন টেস্ট।"""
        from tools.mcp.mcp_github_cicd import CreatePRInput

        with pytest.raises(ValidationError):
            CreatePRInput(body="Test body", head="feature-branch")

    def test_fix_issue_input_validation(self):
        """FixIssueInput মডেলের ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_github_cicd import FixIssueInput

        valid_input = FixIssueInput(issue_number=42, branch="fix/issue-42")
        assert valid_input.issue_number == 42

    def test_response_format_enum(self):
        """ResponseFormat enum টেস্ট।"""
        from tools.mcp.mcp_github_cicd import ResponseFormat

        assert ResponseFormat.MARKDOWN.value == "markdown"
        assert ResponseFormat.JSON.value == "json"


class TestGithubCICDMCPExtended:
    """github_cicd_mcp.py এর জন্য অতিরিক্ত টেস্ট।"""

    @pytest.mark.asyncio
    async def test_create_pr_missing_admin_auth(self, monkeypatch):
        """অ্যাডমিন অথেন্টিকেশন না থাকলে PR তৈরি ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "false")
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        params = CreatePRInput(title="Test", body="Test PR", head="feature", base="main")
        result = await github_create_pull_request(params)
        data = json.loads(result)
        assert data["error"] == "Admin authorization required for PR creation"

    @pytest.mark.asyncio
    async def test_create_pr_missing_token(self, monkeypatch):
        """GITHUB_TOKEN না থাকলে PR তৈরি ব্যর্থ হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        monkeypatch.setenv("GITHUB_TOKEN", "")
        import tools.mcp.mcp_github_cicd

        importlib.reload(tools.mcp.mcp_github_cicd)
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        params = CreatePRInput(title="Test", body="Test PR", head="feature", base="main")
        result = await github_create_pull_request(params)
        data = json.loads(result)
        assert data["error"] == "GITHUB_TOKEN not configured"

    @pytest.mark.asyncio
    async def test_create_pr_api_error_401(self, monkeypatch):
        """PR তৈরি করতে 401 এরর হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = CreatePRInput(title="Test", body="Test PR", head="feature", base="main")
            result = await github_create_pull_request(params)
            assert "Invalid API key" in result

    @pytest.mark.asyncio
    async def test_create_pr_api_error_403(self, monkeypatch):
        """PR তৈরি করতে 403 এরর হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = CreatePRInput(title="Test", body="Test PR", head="feature", base="main")
            result = await github_create_pull_request(params)
            assert "Permission denied" in result

    @pytest.mark.asyncio
    async def test_run_auto_fix_missing_auth(self, monkeypatch):
        """Auto-fix অথেন্টিকেশন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("AUTOFIX_AUTHORIZED", "false")
        from tools.mcp.mcp_github_cicd import FixIssueInput, github_run_auto_fix

        params = FixIssueInput(issue_number=1, branch="fix/issue-1")
        result = await github_run_auto_fix(params)
        data = json.loads(result)
        assert data["error"] == "Auto-fix authorization required"

    @pytest.mark.asyncio
    async def test_list_issues_missing_token(self, monkeypatch):
        """List Issues এ টোকেন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("GITHUB_TOKEN", "")
        from tools.mcp.mcp_github_cicd import github_list_issues

        result = await github_list_issues()
        data = json.loads(result)
        assert data["error"] == "GITHUB_TOKEN not configured"

    @pytest.mark.asyncio
    async def test_list_issues_invalid_state(self, monkeypatch):
        """List Issues এ অবৈধ স্টেট প্যারামিটার ডিফল্ট হয়।"""
        from tools.mcp.mcp_github_cicd import github_list_issues

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_list_issues(state="invalid_state")
            data = json.loads(result)
            assert data["count"] == 0

    @pytest.mark.asyncio
    async def test_get_ci_status_missing_token(self, monkeypatch):
        """Get CI Status এ টোকেন না থাকলে ব্যর্থ হয়।"""
        monkeypatch.setenv("GITHUB_TOKEN", "")
        from tools.mcp.mcp_github_cicd import github_get_ci_status

        result = await github_get_ci_status()
        data = json.loads(result)
        assert data["error"] == "GITHUB_TOKEN not configured"

    @pytest.mark.asyncio
    async def test_get_ci_status_api_error(self, monkeypatch):
        """Get CI Status এ API এরর হ্যান্ডল হয়।"""
        from tools.mcp.mcp_github_cicd import github_get_ci_status

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_get_ci_status()
            assert "Error" in result


    def test_create_pr_input_validation_complete(self):
        """CreatePRInput এর সম্পূর্ণ ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_github_cicd import CreatePRInput

        with pytest.raises(ValidationError):
            CreatePRInput(title="", body="Test", head="feature", base="main")

        with pytest.raises(ValidationError):
            CreatePRInput(title="Test", body="", head="feature", base="main")

        with pytest.raises(ValidationError):
            CreatePRInput(title="Test", body="Test", head="", base="main")


    def test_fix_issue_input_validation_complete(self):
        """FixIssueInput এর সম্পূর্ণ ভ্যালিডেশন টেস্ট।"""
        from tools.mcp.mcp_github_cicd import FixIssueInput

        with pytest.raises(ValidationError):
            FixIssueInput(issue_number=0, branch="fix")

        with pytest.raises(ValidationError):
            FixIssueInput(issue_number=1, branch="")


    @pytest.mark.asyncio
    async def test_github_create_pr_success(self, monkeypatch):
        """GitHub-এ সফল PR তৈরি।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 42,
            "html_url": "https://github.com/test/pull/42",
            "state": "open",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = CreatePRInput(title="Test PR", body="Test body", head="feature", base="develop")
            result = await github_create_pull_request(params)
            data = json.loads(result)
            assert data["success"] is True
            assert data["pr_number"] == 42


    @pytest.mark.asyncio
    async def test_github_create_pr_api_error_404(self, monkeypatch):
        """PR তৈরি করতে 404 এরর হ্যান্ডল হয়।"""
        monkeypatch.setenv("ADMIN_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import CreatePRInput, github_create_pull_request

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = CreatePRInput(title="Test", body="Test PR", head="feature", base="main")
            result = await github_create_pull_request(params)
            assert "not found" in result.lower()


    @pytest.mark.asyncio
    async def test_github_run_auto_fix_success(self, monkeypatch):
        """GitHub-এ সফল অটো-ফিক্স।"""
        monkeypatch.setenv("AUTOFIX_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import FixIssueInput, github_run_auto_fix

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=MagicMock())
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = FixIssueInput(issue_number=42, branch="fix/issue-42")
            result = await github_run_auto_fix(params)
            data = json.loads(result)
            assert data["success"] is True


    @pytest.mark.asyncio
    async def test_github_run_auto_fix_api_error(self, monkeypatch):
        """অটো-ফিক্স এ এপিআই এরর।"""
        monkeypatch.setenv("AUTOFIX_AUTHORIZED", "true")
        from tools.mcp.mcp_github_cicd import FixIssueInput, github_run_auto_fix

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            params = FixIssueInput(issue_number=42, branch="fix/issue-42")
            result = await github_run_auto_fix(params)
            assert "Error" in result


    @pytest.mark.asyncio
    async def test_github_list_issues_success(self, monkeypatch):
        """GitHub-এ সফল ইস্যু লিস্ট।"""
        from tools.mcp.mcp_github_cicd import github_list_issues

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Issue 1",
                "state": "open",
                "labels": [],
                "html_url": "https://github.com/test/issues/1",
            },
            {
                "number": 2,
                "title": "Issue 2",
                "state": "closed",
                "labels": [{"name": "bug"}],
                "html_url": "https://github.com/test/issues/2",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_list_issues(state="all")
            data = json.loads(result)
            assert data["count"] == 2


    @pytest.mark.asyncio
    async def test_github_list_issues_with_labels(self, monkeypatch):
        """লেবেল ফিল্টার সহ ইস্যু লিস্ট।"""
        from tools.mcp.mcp_github_cicd import github_list_issues

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Bug",
                "state": "open",
                "labels": [{"name": "bug"}],
                "html_url": "https://github.com/test/issues/1",
            }
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_list_issues(state="open", labels="bug")
            data = json.loads(result)
            assert data["count"] == 1


    @pytest.mark.asyncio
    async def test_github_list_issues_api_error(self, monkeypatch):
        """ইস্যু লিস্টে এপিআই এরর।"""
        from tools.mcp.mcp_github_cicd import github_list_issues

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_list_issues()
            assert "Error" in result


    @pytest.mark.asyncio
    async def test_github_get_ci_status_success(self, monkeypatch):
        """GitHub-এ সফল CI স্ট্যাটাস।"""
        from tools.mcp.mcp_github_cicd import github_get_ci_status

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "success",
            "statuses": [{"context": "ci/test", "state": "success"}],
            "total_count": 1,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_get_ci_status(branch="main")
            data = json.loads(result)
            assert data["state"] == "success"


    @pytest.mark.asyncio
    async def test_github_get_ci_status_api_error(self, monkeypatch):
        """CI স্ট্যাটাসে এপিআই এরর।"""
        from tools.mcp.mcp_github_cicd import github_get_ci_status

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)

            result = await github_get_ci_status()
            assert "Error" in result
