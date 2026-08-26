import asyncio
import logging
import os

from dotenv import load_dotenv
from loguru import logger

# Ensure we are in the backend directory
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("../.env"):
    load_dotenv("../.env")

logging.basicConfig(level=logging.INFO)


async def migrate_embeddings():
    """
    Fetches all records from the ai_memory table in Supabase,
    re-encodes their summaries using the new 1536-dim (text-embedding-3-small) model via core.embeddings,
    and updates the database.
    """
    try:
        from supabase import create_client

        from core.embeddings import embed_for_pgvector

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

        if not url or not key:
            logger.error(
                "Supabase credentials not found. Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set."
            )
            return

        supabase = create_client(url, key)

        # Fetch all records
        logger.info("Fetching existing records from ai_memory...")
        response = await supabase.table("ai_memory").select("id, summary, embedding").execute()
        records = response.data

        if not records:
            logger.info("No records found in ai_memory.")
            return

        logger.info(f"Found {len(records)} records. Re-encoding to 1536 dimensions...")

        for i, record in enumerate(records):
            record_id = record.get("id")
            summary = record.get("summary")

            if not summary:
                logger.warning(f"Record {record_id} has no summary. Skipping.")
                continue

            try:
                # Generate new 1536-dim embedding natively via LiteLLM
                new_embedding = embed_for_pgvector(summary, pg_dim=1536)

                if new_embedding:
                    # Update record in Supabase
                    await supabase.table("ai_memory").update({"embedding": new_embedding}).eq(
                        "id", record_id
                    ).execute()
                    logger.info(
                        f"[{i + 1}/{len(records)}] Successfully re-encoded record {record_id}."
                    )
                else:
                    logger.warning(
                        f"[{i + 1}/{len(records)}] Failed to generate new embedding for record {record_id}."
                    )
            except Exception as e:
                logger.error(f"Error processing record {record_id}: {e}")

        logger.info("Migration complete!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(migrate_embeddings())
