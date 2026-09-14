import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.plugins.capability_resolver import CapabilityResolver
from core.plugins.manifest_registry import PluginManifestRegistry
from database.session import async_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_capabilities():
    async with async_session_maker() as session:
        # Just testing the import and logic
        tools = await CapabilityResolver.resolve_user_capabilities(session, "test_user")
        logger.info(f"Resolved tools: {tools}")


if __name__ == "__main__":
    asyncio.run(verify_capabilities())
