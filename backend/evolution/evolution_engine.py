# backend/evolution/evolution_engine.py
"""Event-Driven Evolution Engine for SupremeAI.

Provides:
- EvolutionEngine: Self-healing system triggered by error events
- Event-driven architecture replacing CPU-blocking while loops
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import settings
from core.messaging.event_bus import ErrorContext, ErrorEvent, error_event_bus
from evolution.auto_skill_creator import AutoSkillCreator, MaliciousCodeError, SkillExecutionError


class EvolutionEngine:
    """
    Event-driven engine for self-healing and system upgrades.

    বাংলা মন্তব্য: আগে যেখানে `while True` লুপ দিয়ে সিপিইউ নষ্ট করা হতো, সেখানে এখন সিস্টেমটি শুধু ইভেন্টের জন্য অপেক্ষা করবে।
    """

    def __init__(self) -> None:
        self.skill_creator = AutoSkillCreator()
        self._healing_in_progress: set[str] = set()  # Prevent infinite healing loops

    async def handle_error_event(self, error_data: dict[str, Any]) -> None:
        """
        Triggered when ErrorEventBus receives a critical error.
        Attempts autonomous self-healing.

        Args:
            error_data: Dictionary containing error information
        """
        component = error_data.get("component", "unknown")
        error_msg = error_data.get("message", "unknown error")

        # Avoid infinite healing loops
        if component in self._healing_in_progress:
            logger.warning(f"EvolutionEngine: Skipping healing for {component} - already in progress")
            return

        if component == "AutoSkillCreator":
            return

        self._healing_in_progress.add(component)

        try:
            # 1. Analyze error via LLM (Mocked here, connect to llm_gateway)
            logger.info(f"🧠 Evolution Engine analyzing failure in {component}: {error_msg[:100]}")

            # 2. Generate fix (Mocked code generation - in production, use LLM)
            # This would typically call llm_gateway.generate_response() with a prompt
            patch_code = self._generate_fix_code(component, error_msg)

            # 3. Test patch safely
            skill_name = f"patch_{component}_{settings.env}"
            await self.skill_creator.save_and_test_skill(skill_name, patch_code)
            logger.info(f"✅ Successfully created and verified patch for {component}")

        except MaliciousCodeError as e:
            error_event_bus.emit(
                ErrorEvent(
                    module="EvolutionEngine",
                    error_type="MALICIOUS_CODE_BLOCKED",
                    message=str(e)[:500],
                    severity="CRITICAL",
                    context={"target_component": component, "error": str(e)},
                    structured_context=ErrorContext(
                        module="evolution.evolution_engine",
                        env=settings.env,
                    ),
                )
            )
            logger.error(f"EvolutionEngine: Malicious code blocked for {component}")

        except SkillExecutionError as e:
            error_event_bus.emit(
                ErrorEvent(
                    module="EvolutionEngine",
                    error_type="PATCH_EXECUTION_FAILED",
                    message=str(e)[:500],
                    severity="ERROR",
                    context={"target_component": component, "error": str(e)},
                    structured_context=ErrorContext(
                        module="evolution.evolution_engine",
                        env=settings.env,
                    ),
                )
            )
            logger.error(f"EvolutionEngine: Patch execution failed for {component}")

        except Exception as e:
            error_event_bus.emit(
                ErrorEvent(
                    module="EvolutionEngine",
                    error_type="EVOLUTION_ERROR",
                    message=str(e)[:500],
                    severity="ERROR",
                    context={"target_component": component},
                    structured_context=ErrorContext(
                        module="evolution.evolution_engine",
                        env=settings.env,
                    ),
                )
            )
            logger.error(f"EvolutionEngine: Unexpected error for {component}: {e}")

        finally:
            # Remove from healing set after delay to allow retry
            self._healing_in_progress.discard(component)

    def _generate_fix_code(self, component: str, error_msg: str) -> str:
        """
        Generate fix code for a component.

        In production, this would call the LLM gateway to generate actual fix code.
        For now, returns a simple mock fix.
        """
        # This is a placeholder - in production, integrate with llm_gateway
        return f'''# Auto-generated fix for {component}
# Error: {error_msg[:100]}

def fix():
    """Auto-generated fix for {component}."""
    return "healed"

if __name__ == "__main__":
    result = fix()
    print(result)
'''


# Register as error event listener
evolution_engine = EvolutionEngine()


async def _evolution_error_handler(event: ErrorEvent) -> None:
    """Async handler wrapper for ErrorEventBus."""
    if event.severity in ("CRITICAL", "ERROR"):
        await evolution_engine.handle_error_event(
            {
                "component": event.module,
                "message": event.message,
                "error_type": event.error_type,
            }
        )


# Register the evolution engine to listen to error events
error_event_bus.register_listener(_evolution_error_handler)
