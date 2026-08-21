"""
Dynamic Schema & Entity Builder (Strapi Headless & Content-Type Pattern).
Allows SupremeAI agents to dynamically create, register, and query database entities,
schemas, and collections at runtime without hardcoding static tables.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from loguru import logger


@dataclass
class SchemaField:
    name: str
    field_type: str = "string"  # string, integer, float, boolean, json, text
    required: bool = False
    unique: bool = False
    default: Any = None


@dataclass
class DynamicEntitySchema:
    collection_name: str
    display_name: str
    fields: list[SchemaField]
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DynamicSchemaBuilder:
    """
    Dynamic Content-Type and Schema Generator for SupremeAI.
    Manages custom user entities, memory schemas, and dynamic storage tables.
    """

    def __init__(self, db_path: str | Path = "checkpoints.db"):
        self.db_path = str(db_path)
        self.registered_schemas: dict[str, DynamicEntitySchema] = {}
        self._init_registry()

    def _init_registry(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dynamic_schema_registry (
                        collection_name TEXT PRIMARY KEY,
                        schema_definition TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
            self._load_registered_schemas()
        except Exception as exc:
            logger.warning(f"Failed to init dynamic schema registry: {exc}")

    def _load_registered_schemas(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT collection_name, schema_definition FROM dynamic_schema_registry")
                for col_name, raw_json in cursor.fetchall():
                    data = json.loads(raw_json)
                    fields = [SchemaField(**f) for f in data.get("fields", [])]
                    self.registered_schemas[col_name] = DynamicEntitySchema(
                        collection_name=col_name,
                        display_name=data.get("display_name", col_name),
                        fields=fields,
                        description=data.get("description", ""),
                    )
        except Exception as exc:
            logger.warning(f"Could not load schemas from registry: {exc}")

    def register_schema(self, schema: DynamicEntitySchema) -> dict[str, Any]:
        """
        Creates the table if it does not exist and saves the schema definition.
        """
        sql_types = {
            "string": "TEXT",
            "text": "TEXT",
            "integer": "INTEGER",
            "float": "REAL",
            "boolean": "INTEGER",
            "json": "TEXT",
        }

        col_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT", "_created_at TEXT NOT NULL"]
        for f in schema.fields:
            st = sql_types.get(f.field_type.lower(), "TEXT")
            req = " NOT NULL" if f.required else ""
            uniq = " UNIQUE" if f.unique else ""
            col_defs.append(f"{f.name} {st}{req}{uniq}")

        create_sql = f"CREATE TABLE IF NOT EXISTS dyn_{schema.collection_name} ({', '.join(col_defs)})"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(create_sql)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dynamic_schema_registry (collection_name, schema_definition, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (
                        schema.collection_name,
                        json.dumps({
                            "collection_name": schema.collection_name,
                            "display_name": schema.display_name,
                            "fields": [f.__dict__ for f in schema.fields],
                            "description": schema.description,
                        }),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()

            self.registered_schemas[schema.collection_name] = schema
            logger.info(f"Registered dynamic entity schema: dyn_{schema.collection_name}")
            return {"success": True, "collection": schema.collection_name, "sql": create_sql}
        except Exception as exc:
            logger.error(f"Failed to register dynamic schema [{schema.collection_name}]: {exc}")
            return {"success": False, "error": str(exc)}

    def insert_entry(self, collection_name: str, data: dict[str, Any]) -> dict[str, Any]:
        table_name = f"dyn_{collection_name}"
        now = datetime.now(timezone.utc).isoformat()
        fields = ["_created_at"]
        values = [now]
        placeholders = ["?"]

        schema = self.registered_schemas.get(collection_name)
        for k, v in data.items():
            fields.append(k)
            # Serialize dict/list to JSON string if needed
            if isinstance(v, (dict, list)):
                values.append(json.dumps(v))
            else:
                values.append(v)
            placeholders.append("?")

        sql = f"INSERT INTO {table_name} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
                inserted_id = cursor.lastrowid
            return {"success": True, "id": inserted_id, "collection": collection_name}
        except Exception as exc:
            logger.error(f"Failed to insert into [{collection_name}]: {exc}")
            return {"success": False, "error": str(exc)}

    def query_entries(self, collection_name: str, limit: int = 50) -> list[dict[str, Any]]:
        table_name = f"dyn_{collection_name}"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            logger.warning(f"Query on [{collection_name}] failed: {exc}")
            return []
