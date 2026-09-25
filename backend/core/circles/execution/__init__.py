"""backend/core/circles/execution/__init__.py — Execution Circle Boundary Facade.

Governs:
- Tasks, Agents, Scrapers, Browser automation, Tool invocations
"""


from core.circles.contracts import CircleName


class ExecutionCircleFacade:
    """Bounded facade for Execution operations."""

    name = CircleName.TASK


execution_circle = ExecutionCircleFacade()
