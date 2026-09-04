"""Validate and import the approved SupremeAI knowledge manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import uuid
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED = {
    "knowledge_key",
    "title",
    "domain",
    "namespace",
    "content",
    "source_document",
    "source_section",
    "confidence",
    "risk_level",
    "status",
    "tags",
}
ALLOWED_STATUS = {"draft", "approved", "deprecated"}
ALLOWED_RISK = {"low", "medium", "high", "critical"}


def validate(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    keys: set[str] = set()
    for i, record in enumerate(records):
        missing = REQUIRED - record.keys()
        if missing:
            errors.append(f"record[{i}] missing: {sorted(missing)}")
        key = str(record.get("knowledge_key", ""))
        if not re.fullmatch(r"[a-z0-9_.-]{3,120}", key):
            errors.append(f"record[{i}] invalid knowledge_key")
        if key in keys:
            errors.append(f"duplicate knowledge_key: {key}")
        keys.add(key)
        confidence = record.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append(f"record[{i}] invalid confidence")
        if record.get("status") not in ALLOWED_STATUS:
            errors.append(f"record[{i}] invalid status")
        if record.get("risk_level") not in ALLOWED_RISK:
            errors.append(f"record[{i}] invalid risk_level")
        if not isinstance(record.get("tags"), list):
            errors.append(f"record[{i}] tags must be a list")
        if any(
            secret in json.dumps(record).lower()
            for secret in ("api_key=", "sk-", "bearer ", "password=")
        ):
            errors.append(f"record[{i}] possible secret")
    return errors


def content_hash(record: dict[str, Any]) -> str:
    canonical = json.dumps(
        {k: record[k] for k in sorted(record) if k not in {"status"}},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest", nargs="?", default="backend/data/supremeai_long_term_knowledge_v1.json"
    )
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    payload = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    records = payload.get("records", [])
    errors = validate(records)
    result = {
        "manifest_version": payload.get("manifest_version"),
        "record_count": len(records),
        "errors": errors,
        "manifest_hash": hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),
    }
    if errors:
        print(json.dumps(result, indent=2))
        return 2
    if args.validate_only:
        print(json.dumps(result, indent=2))
        return 0
    try:
        import psycopg2
    except ImportError:
        raise SystemExit(
            "psycopg2 is required for database import; use --validate-only for offline validation"
        )
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    rollback_id = f"knowledge-import-{uuid.uuid4()}"
    with conn:
        with conn.cursor() as cur:
            for record in records:
                digest = content_hash(record)
                metadata = {
                    k: record[k]
                    for k in ("when_to_use", "decision_rules", "anti_patterns", "tags")
                    if k in record
                }
                cur.execute(
                    """INSERT INTO knowledge_base (id, knowledge_key, title, domain, namespace, content, source, metadata, content_hash, status, confidence, risk_level, source_version, review_after, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,NOW()+INTERVAL '180 days',NOW()) ON CONFLICT (knowledge_key) DO UPDATE SET title=EXCLUDED.title, domain=EXCLUDED.domain, content=EXCLUDED.content, source=EXCLUDED.source, metadata=EXCLUDED.metadata, content_hash=EXCLUDED.content_hash, source_version=EXCLUDED.source_version, updated_at=NOW() WHERE knowledge_base.status <> 'approved' OR knowledge_base.content_hash = EXCLUDED.content_hash""",
                    (
                        record["knowledge_key"],
                        record["knowledge_key"],
                        record["title"],
                        record["domain"],
                        record["namespace"],
                        record["content"],
                        f"{record['source_document']}#{record['source_section']}",
                        json.dumps(metadata),
                        digest,
                        record["status"],
                        record["confidence"],
                        record["risk_level"],
                        payload["source_version"],
                    ),
                )
            cur.execute(
                "INSERT INTO knowledge_import_audits (manifest_hash, source_version, imported_count, rollback_id, evidence) VALUES (%s,%s,%s,%s,%s::jsonb)",
                (
                    result["manifest_hash"],
                    payload["source_version"],
                    len(records),
                    rollback_id,
                    json.dumps(
                        {
                            "tool": "import_knowledge_base.py",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    ),
                ),
            )
    print(json.dumps({**result, "rollback_id": rollback_id}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
