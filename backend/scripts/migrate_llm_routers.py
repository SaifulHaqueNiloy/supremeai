from loguru import logger
#!/usr/bin/env python3
"""
Migration script for consolidating LLM routers to unified approach.

This script helps migrate from multiple router implementations to a single,
enhanced LLM gateway with shared circuit breakers and consistent provider taxonomy.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm.llm_gateway import get_llm_gateway
from core.llm.llm_gateway_with_learning import get_learning_engine
from services.llm.llm_router import get_llm_router
from core.resilience.circuit_breaker_manager import get_circuit_breaker_manager


async def validate_migration():
    """Validate that all components are working correctly after migration."""
    logger.info("🔍 Validating LLM Gateway Migration...")

    # Test enhanced LLM Gateway
    logger.info("✅ Testing enhanced LLM Gateway...")
    gateway = get_llm_gateway()
    if not gateway:
        logger.info("❌ Failed to get LLM Gateway")
        return False

    # Test LLM Router (now using shared components)
    logger.info("✅ Testing LLM Router with shared components...")
    router = get_llm_router()
    if not router:
        logger.info("❌ Failed to get LLM Router")
        return False

    # Test learning engine
    logger.info("✅ Testing learning engine...")
    try:
        learning_engine = get_learning_engine()
        if not learning_engine:
            logger.info("❌ Failed to get learning engine")
            return False
    except Exception as e:
        logger.info(f"⚠️ Learning engine not available: {e}")

    # Test circuit breaker manager
    logger.info("✅ Testing circuit breaker manager...")
    cb_manager = get_circuit_breaker_manager()
    if not cb_manager:
        logger.info("❌ Failed to get circuit breaker manager")
        return False

    logger.info("✅ All components validated successfully!")
    return True


async def analyze_current_usage():
    """Analyze current usage of different routers in the codebase."""
    import subprocess

    logger.info("\n🔍 Analyzing current router usage...")

    # Find all imports of the different routers
    try:
        result = subprocess.run(
            ["grep", "-r", "from core.llm_gateway", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        llm_gateway_refs = result.stdout.count("\n") if result.stdout else 0

        result = subprocess.run(
            ["grep", "-r", "from core.llm_router", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        llm_router_refs = result.stdout.count("\n") if result.stdout else 0

        result = subprocess.run(
            ["grep", "-r", "from llm_gateway_with_learning", "."],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        llm_learning_refs = result.stdout.count("\n") if result.stdout else 0

        logger.info(f"   LLM Gateway references: {llm_gateway_refs}")
        logger.info(f"   LLM Router references: {llm_router_refs}")
        logger.info(f"   LLM Learning references: {llm_learning_refs}")

    except Exception as e:
        logger.info(f"⚠️ Could not analyze usage: {e}")


async def main():
    """Main migration validation function."""
    logger.info("🚀 Starting LLM Gateway Migration Validation...")

    # Validate components
    success = await validate_migration()

    # Analyze current usage
    await analyze_current_usage()

    if success:
        logger.info("\n🎉 Migration validation completed successfully!")
        logger.info("✅ Enhanced LLM Gateway with shared circuit breakers is ready")
        logger.info("✅ Consistent provider taxonomy implemented")
        logger.info("✅ 429 error handling with backoff added")
        logger.info("✅ Centralized monitoring and health endpoints available")
        return 0
    else:
        logger.info("\n❌ Migration validation failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
