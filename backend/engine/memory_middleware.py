import logging

from engine.embedding import embedding_service
from engine.vector_db import vector_db


logger = logging.getLogger(__name__)


class MemoryMiddleware:
    """
    Injects Neural Memory (RAG) into Swarm Tasks by retrieving past experiences.
    Allows agents to learn from historical data.
    """

    def __init__(self):
        self.vector_db = vector_db
        self.embedder = embedding_service

    async def augment_task(self, task_prompt: str) -> str:
        try:
            logger.info("🧠 MemoryMiddleware: Fetching relevant past experiences...")
            # 1. Convert task to embedding
            vector = await self.embedder.generate_embedding(task_prompt)

            # 2. Query past experiences
            experiences = await self.vector_db.find_similar_experiences(vector, top_k=2)

            if getattr(self.vector_db, "degraded", False):
                # বাংলা: এটা "কোনো past experience নেই" এর মতো না — memory backend নিজেই
                # অনুপস্থিত/down। agent-কে ভুল করে "clean slate" ভাবতে দেওয়া যাবে না,
                # তাই error-level এ স্পষ্টভাবে জানানো হচ্ছে যাতে health monitoring ধরতে পারে।
                logger.error("🧠 MemoryMiddleware: vector memory backend is DEGRADED — proceeding WITHOUT historical context.")
                return task_prompt

            if not experiences:
                logger.info("🧠 MemoryMiddleware: No relevant past experiences found.")
                return task_prompt

            # 3. Add context
            logger.info(f"🧠 MemoryMiddleware: Found {len(experiences)} relevant memory chunks. Augmenting prompt.")
            memory_context = "\n".join([f"- Past insight: {exp['metadata'].get('solution', 'Unknown')}" for exp in experiences])
            return f"{task_prompt}\n\n--- RELEVANT PAST EXPERIENCE ---\n{memory_context}\n--------------------------------"
        except Exception as e:  # noqa: BLE001
            logger.error(f"❌ Failed to augment task with memory (proceeding WITHOUT historical context): {str(e)}")
            return task_prompt  # Fallback to original prompt, but now logged as ERROR not silent


memory_mw = MemoryMiddleware()
