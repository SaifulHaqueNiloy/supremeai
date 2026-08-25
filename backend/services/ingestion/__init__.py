"""Context ingestion services package."""

# FIX: original used 'from backend.services.ingestion.context_collector import ...'
# which only works when CWD is the project root. Use relative import.
from .context_collector import DeveloperContextCollector, WorkspaceSnapshot

__all__ = ["DeveloperContextCollector", "WorkspaceSnapshot"]
