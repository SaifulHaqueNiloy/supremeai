# SupremeAI 2.0 - Episodic Memory Engine
# বাংলা মন্তব্য: এটি ব্যবহারকারীর সমস্ত অতীত টাস্ক এক্সিকিউশন হিস্ট্রি ও সাফল্য/ব্যর্থতার অভিজ্ঞতা সংরক্ষণ ও ভেক্টর সার্চের জন্য ব্যবহৃত হয়।

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from memory.chromadb_store import ChromaDBStore

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Episodic Memory Engine for SupremeAI 2.0.
    Stores task execution records, inputs, responses, latency, and success metrics.
    Supports similarity search to retrieve relevant past solutions.
    """

    def __init__(self, vector_store: Optional[ChromaDBStore] = None, db_path: Optional[str] = None, session_id: Optional[str] = None, **kwargs):
        self.session_id = session_id or "default"
        self.vector_store = vector_store or ChromaDBStore(collection_name="supremeai_episodic_memory", db_path=db_path or ":memory:")
        self._episodes: List[Dict[str, Any]] = []

    def store_episode(self, task_type: str = "general", input_data: Any = None, output_data: Any = None, success: bool = True, latency_ms: float = 0.0, tags: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        episode = {
            "id": f"ep_{len(self._episodes)+1}",
            "task_type": task_type,
            "input_data": input_data,
            "output_data": output_data,
            "success": success,
            "latency_ms": latency_ms,
            "tags": tags or [],
            "timestamp": time.time(),
        }
        self._episodes.append(episode)
        return episode

    def recall_episodes(self, task_type: Optional[str] = None, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        episodes = self._episodes
        if task_type:
            episodes = [e for e in episodes if e.get("task_type") == task_type]
        return episodes[:limit]

    def summarize_recent(self, limit: int = 5, **kwargs) -> str:
        recent = self.recall_episodes(limit=limit)
        if not recent:
            return "No recent episodes."
        return f"Recent episodes ({len(recent)}): " + ", ".join(f"{e.get('task_type')}" for e in recent)

    async def record_task(
        self,
        task_id: str,
        prompt: str,
        response: str,
        success: bool = True,
        latency_ms: float = 0.0,
        model_used: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record a task execution event into episodic memory.
        """
        try:
            meta = {
                "task_id": task_id,
                "success": str(success).lower(),
                "latency_ms": float(latency_ms),
                "model_used": model_used,
                "timestamp": time.time(),
                "category": "episodic_memory",
            }
            if metadata:
                meta.update(metadata)

            content_text = f"Prompt: {prompt}\nResponse: {response}"
            self.vector_store.add_document(doc_id=f"episode_{task_id}", text=content_text, metadata=meta)
            logger.info(f"Recorded episodic memory for task: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to record episodic memory: {e}")
            return False

    async def get_similar_past_tasks(self, query: str, n: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-N similar past task execution records for cognitive reflection.
        """
        try:
            results = self.vector_store.query(query_text=query, n_results=n)
            past_tasks = []
            for doc_id, score, doc_data in results:
                past_tasks.append(
                    {
                        "doc_id": doc_id,
                        "similarity_score": score,
                        "content": doc_data.get("text", ""),
                        "metadata": doc_data.get("metadata", {}),
                    }
                )
            return past_tasks
        except Exception as e:
            logger.error(f"Failed to query episodic memory: {e}")
            return []