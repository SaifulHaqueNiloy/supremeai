"""SupremeAI 2.0 Unified Memory and Knowledge Matrix.

Centralized persistence and retrieval layer encapsulating:
- UnifiedDBManager (Multi-cloud transaction manager)
- SupabaseStore & SQLiteMemoryStore / SQLiteStore
- EpisodicMemory & LongTermMemory (pgvector / sqlite)
- SlidingWindowMemory & CheckpointResume
- RAGPipeline
"""

from __future__ import annotations

from memory.checkpoint_resume import CheckpointResume
from memory.cloud_postgres_store import CloudPostgresStore
from memory.episodic_memory import EpisodicMemory
from memory.long_term_memory import LongTermMemory, MemoryManager
from memory.rag_pipeline import RAGPipeline
from memory.sliding_window import SlidingWindowConfig, SlidingWindowMemory
from memory.sqlite_store import SQLiteMemoryStore, SQLiteStore
from memory.supabase_store import SupabaseStore
from memory.self_evolve_service import SelfEvolveService
from memory.unified_db_manager import UnifiedDBManager, get_db, unified_db
from memory.vector_store_config import VectorStoreConfig, get_vector_store_config

__all__ = [
    "CheckpointResume",
    "CloudPostgresStore",
    "EpisodicMemory",
    "LongTermMemory",
    "MemoryManager",
    "RAGPipeline",
    "SQLiteMemoryStore",
    "SQLiteStore",
    "SlidingWindowConfig",
    "SlidingWindowMemory",
    "SupabaseStore",
    "UnifiedDBManager",
    "SelfEvolveService",
    "VectorStoreConfig",
    "get_db",
    "get_vector_store_config",
    "unified_db",
]
