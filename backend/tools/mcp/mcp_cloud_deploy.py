"""
MCP Server for Cloud Deployment Integration in SupremeAI 2.0.

এই সার্ভারটি এজেন্টকে Render, Railway, Oracle Cloud-এ সরাসরে
কোড ডিপ্লয় ও লগ মনিটর করার ক্ষমতা দেয়।
"""

import json

# বাংলা মন্তব্য: পরিবেশের ভেরিয়েবল চেক করার জন্য os মডিউল ইমপোর্ট করা হলো
import os
from enum import StrEnum

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from core.config import settings
from core.logging_config import logger

# শেয়ার্ড ইউটিলিটি — ডুপ্লিকেট কোড দূর করতে কেন্দ্রীয় মডিউল থেকে ইম্পোর্ট
from utils.environment import is_admin_authorized
from utils.http_client import handle_api_error
from utils.json_helpers import json_error

mcp = FastMCP("cloud_deploy_mcp")

CHARACTER_LIMIT = 25000


def _get_render_api_key() -> str:
    # বাংলা মন্তব্য: settings-এ না থাকলে os.environ থেকে RENDER_API_KEY চেক করা হবে
    return getattr(settings, "render_api_key", "") or os.environ.get("RENDER_API_KEY", "")


# বাংলা মন্তব্য (#3077): Railway ও Oracle প্রোভাইডার সম্পূর্ণ সরানো হয়েছে —
#   ১. Railway: "https://back-end.railway.app/v2/services" Railway-এর API host নয় (লাইভ প্রোব → 404);
#      RAILWAY_TOKEN Bearer হিসেবে ভুল host-এ যেত = credential-মিসডিরেকশন ঝুঁকি।
#   ২. Oracle: "containerengine.<region>.oraclecloud.com/api/v1/deploy" কোনো বাস্তব OCI endpoint নয় —
#      dead-by-construction।
# সক্রিয় ডিপ্লয়-প্ল্যাটফর্ম (deploy-train.yml): Render + Cloudflare + Firebase।


class CloudProvider(StrEnum):
    """সমর্থিত ক্লাউড প্রোভাইডার।"""

    RENDER = "render"


class ResponseFormat(StrEnum):
    """আউটপুট ফরম্যাট।"""

    MARKDOWN = "markdown"
    JSON = "json"


class DeployServiceInput(BaseModel):
    """সার্ভিস ডিপ্লয়ের জন্য ইনপুট।"""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    provider: CloudProvider = Field(..., description="ডিপ্লয় করার ক্লাউড প্রোভাইডার")
    service_name: str = Field(
        ...,
        description="সার্ভিসের নাম",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9\-_]+$",
    )
    branch: str | None = Field(default="main", description="ডিপ্লয় ব্রাঞ্চ", pattern=r"^[^\s;]+$")


class GetLogsInput(BaseModel):
    """লগ রিট্রিভালের জন্য ইনপুট।"""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    provider: CloudProvider = Field(..., description="ক্লাউড প্রোভাইডার")
    service_name: str = Field(
        ..., description="সার্ভিসের নাম", min_length=1, pattern=r"^[a-zA-Z0-9\-_]+$"
    )
    lines: int = Field(default=100, description="রিট্রিভ করার লাইন সংখ্যা", ge=1, le=1000)


def _check_admin_auth() -> bool:
    """Backwards-compatible wrapper for admin authorization checks."""
    return is_admin_authorized()


def _handle_api_error(exc: Exception, status_code: int | None = None) -> str:
    """Backwards-compatible wrapper for shared API error formatting."""
    return handle_api_error(exc, status_code)


@mcp.tool(
    name="cloud_deploy_service",
    annotations={
        "title": "Deploy Service to Cloud",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def cloud_deploy_service(params: DeployServiceInput) -> str:
    """
    ক্লাউড প্রোভাইডারে নতুন সার্ভিস ডিপ্লয় করে।

    # বাংলা মন্তব্য (#3077): এই টুল এখন শুধু Render ডিপ্লয় সমর্থন করে —
    # Railway/Oracle ভুয়া endpoint (টোকেন-মিসডিরেকশন) বন্ধ।

    Args:
        params (DeployServiceInput): ইনপুট প্যারামিটার সম্বলিত:
            - provider (CloudProvider): ক্লাউড প্রোভাইডার
            - service_name (str): সার্ভিসের নাম
            - branch (Optional[str]): ডিপ্লয় ব্রাঞ্চ

    Returns:
        str: ডিপ্লয় স্ট্যাটাস ও ইনফরমেশন
    """
    if not is_admin_authorized():
        return json.dumps(
            {
                "error": "Admin authorization required for deployments",
                "message": "Set ADMIN_AUTHORIZED=true in environment",
            },
            ensure_ascii=False,
        )

    headers = {}
    api_url = ""

    if params.provider == CloudProvider.RENDER:
        render_api_key = _get_render_api_key()
        if not render_api_key:
            return json_error("RENDER_API_KEY not configured")
        api_url = "https://api.render.com/v1/services"
        headers = {"Authorization": f"Bearer {render_api_key}"}

    # বাংলা মন্তব্য (#3077): Railway/Oracle ব্রাঞ্চ সরানো — ভুয়া endpoint, বিস্তারিত CloudProvider-এর উপরে।

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json={"serviceName": params.service_name, "branch": params.branch},
            )
            response.raise_for_status()
            data = response.json()

            return json.dumps(
                {
                    "success": True,
                    "provider": params.provider.value,
                    "service": params.service_name,
                    "status": data.get("status", "deploying"),
                    "url": data.get("url", ""),
                    "message": f"Deployment initiated for '{params.service_name}' on {params.provider.value}",
                },
                ensure_ascii=False,
            )

    except httpx.HTTPStatusError as e:
        return handle_api_error(e, e.response.status_code)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="cloud_get_deployment_logs",
    annotations={
        "title": "Get Deployment Logs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def cloud_get_deployment_logs(params: GetLogsInput) -> str:
    """
    ক্লাউড সার্ভিসের ডিপ্লয়মেন্ট লগ রিট্রিভ করে।

    Args:
        params (GetLogsInput): ইনপুট প্যারামিটার সম্বলিত:
            - provider (CloudProvider): ক্লাউড প্রোভাইডার
            - service_name (str): সার্ভিসের নাম
            - lines (int): রিট্রিভ করার লাইন সংখ্যা

    Returns:
        str: সার্ভিসের লগ
    """
    api_url = ""
    headers = {}

    if params.provider == CloudProvider.RENDER:
        render_api_key = _get_render_api_key()
        if not render_api_key:
            return json_error("RENDER_API_KEY not configured")
        api_url = f"https://api.render.com/v1/services/{params.service_name}/logs"
        headers = {"Authorization": f"Bearer {render_api_key}"}

    # বাংলা মন্তব্য (#3077): Railway/Oracle লগ-ব্রাঞ্চ সরানো — ভুয়া endpoint।

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url, headers=headers, params={"lines": params.lines})
            response.raise_for_status()
            data = response.json()

            logs = data.get("logs", []) if isinstance(data, dict) else data

            return json.dumps(
                {
                    "provider": params.provider.value,
                    "service": params.service_name,
                    "logs": logs[: params.lines],
                    "total_lines": len(logs),
                },
                ensure_ascii=False,
            )

    except httpx.HTTPStatusError as e:
        return handle_api_error(e, e.response.status_code)
    except Exception as e:
        return handle_api_error(e)


@mcp.tool(
    name="cloud_list_services",
    annotations={
        "title": "List Cloud Services",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def cloud_list_services() -> str:
    """
    সব ক্লাউড প্রোভাইডারে ডিপ্লট করা সার্ভিসের তালিকা দেখায়।

    Returns:
        str: সার্ভিস তালিকা
    """
    services = []

    render_api_key = _get_render_api_key()
    if render_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.render.com/v1/services",
                    headers={"Authorization": f"Bearer {render_api_key}"},
                )
                if response.status_code == 200:
                    for svc in response.json():
                        services.append(
                            {
                                "provider": "render",
                                "name": svc.get("serviceName"),
                                "status": svc.get("status"),
                                "url": svc.get("url", ""),
                            }
                        )
        except Exception as e:
            logger.error(f"Failed to list services from Render: {e}")

    # বাংলা মন্তব্য (#3077): Railway লিস্টিং-লেগ সরানো — ভুয়া host, টোকেন পাঠানোই যাবে না।

    return json.dumps({"services": services, "count": len(services)}, ensure_ascii=False)


@mcp.tool(
    name="get_render_account_status",
    annotations={
        "title": "Get Render Account Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def get_render_account_status_tool(account_role: str | None = None) -> str:
    """
    রিটার্ন করে নির্দিষ্ট বা সমস্ত Render অ্যাকাউন্ট রোলের বর্তমান স্ট্যাটাস ও কোটা লিমিট।
    """
    from backend.services.render_preflight_service import RenderPreflightService

    svc = RenderPreflightService()
    result = svc.get_account_status(account_role)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="refresh_render_account_status",
    annotations={
        "title": "Refresh Render Account Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def refresh_render_account_status_tool(account_role: str, force: bool = False) -> str:
    """
    Render API কুয়েরি করে নির্দিষ্ট অ্যাকাউন্ট রোলের স্ট্যাটাস রিফ্রেশ ও অডিট ইভেন্ট রেকর্ড করে।
    """
    if force and not is_admin_authorized():
        return json.dumps(
            {"error": "Admin authorization required for force refresh"}, ensure_ascii=False
        )

    from backend.services.render_preflight_service import RenderPreflightService

    svc = RenderPreflightService()
    api_key = _get_render_api_key()
    svc_id = os.getenv("RENDER_PRIMARY_SVC_ID", "")

    result = svc.refresh_account_status(
        account_role=account_role,
        service_id=svc_id,
        api_key=api_key,
        force=force,
    )
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    name="get_render_deploy_preflight",
    annotations={
        "title": "Get Render Deploy Preflight Summary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def get_render_deploy_preflight_tool() -> str:
    """
    সমস্ত কনফিগার করা Render রোলের সামারি, ব্লকিং কারণ ও ডিপ্লয় অনুমতি রিটার্ন করে।
    """
    from backend.services.render_preflight_service import RenderPreflightService

    svc = RenderPreflightService()
    result = svc.get_deploy_preflight()
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
