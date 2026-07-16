import os
import sqlite3
import json
import ast
import math
import importlib.util
from typing import Any, Dict, List
from loguru import logger

HAS_SENTENCE_TRANSFORMERS = importlib.util.find_spec("sentence_transformers") is not None

def hash_vectorize(text: str, size: int = 384) -> List[float]:
    """
    Pure Python Feature Hashing (Hashing Trick) to convert text into a 384-dimensional vector.
    Serves as a robust, zero-cost fallback when SentenceTransformer is unavailable.
    """
    vector = [0.0] * size
    words = [w.lower() for w in text.split() if len(w) > 1]
    if not words:
        # Return a non-empty unit vector to prevent division by zero
        vector[0] = 1.0
        return vector

    for word in words:
        # Generate stable hash key using fnv1a style simple hashing
        h = abs(hash(word)) % size
        sign = 1 if (abs(hash(word)) // size) % 2 == 0 else -1
        vector[h] += sign

    # L2 Normalization
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector

class CascadeMemoryService:
    """
    Handles context memory operations for SupremeAI using a local SQLite vector-store fallback.
    Optimized to store and retrieve 'Summary of Functions' and 'File Structure'
    to save API tokens.
    """

    def __init__(self, db_path: str = "data/memory.db"):
        # Ensure directories exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()
        self.encoder = None

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                from sentence_transformers import SentenceTransformer
                self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Initialized SentenceTransformer encoder for memory service")
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer: {e}. Using hash fallback.")

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS file_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    content TEXT,
                    summary TEXT,
                    structure TEXT,
                    embedding TEXT
                )
                """
            )
            conn.commit()

    def _embed(self, text: str) -> List[float]:
        if self.encoder:
            try:
                return self.encoder.encode(text).tolist()
            except Exception as e:
                logger.warning(f"Embedding failed: {e}. Falling back to hash vectorizer.")
        return hash_vectorize(text)

    def _parse_code_structure(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Parses Python file AST structure and extracts function/class names and docstrings.
        """
        if not file_path.endswith(".py"):
            # Simple line-based fallback for non-python files
            lines = content.splitlines()
            summary = f"File: {file_path}\nLines: {len(lines)}"
            return {
                "summary": summary,
                "structure": json.dumps({"lines": len(lines)})
            }

        try:
            tree = ast.parse(content)
            summary_parts = [f"File: {file_path}"]
            structure = {"classes": [], "functions": []}

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "docstring": ast.get_docstring(node) or ""
                    }
                    summary_parts.append(f"Class: {node.name}")
                    if class_info["docstring"]:
                        summary_parts.append(f"  Docstring: {class_info['docstring']}")

                    for subnode in node.body:
                        if isinstance(subnode, ast.FunctionDef):
                            method_info = {
                                "name": subnode.name,
                                "docstring": ast.get_docstring(subnode) or ""
                            }
                            class_info["methods"].append(method_info)
                            summary_parts.append(f"  Method: {subnode.name}")
                            if method_info["docstring"]:
                                summary_parts.append(f"    Docstring: {method_info['docstring']}")
                    structure["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or ""
                    }
                    summary_parts.append(f"Function: {node.name}")
                    if func_info["docstring"]:
                        summary_parts.append(f"  Docstring: {func_info['docstring']}")
                    structure["functions"].append(func_info)

            return {
                "summary": "\n".join(summary_parts),
                "structure": json.dumps(structure)
            }
        except Exception as e:
            logger.warning(f"AST parsing failed for {file_path}: {e}")
            return {
                "summary": f"File: {file_path} (AST parsing error)",
                "structure": json.dumps({"error": str(e)})
            }

    def chunk_and_embed(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Parses raw code, extracts function summaries and structure,
        generates vector embeddings, and saves them to the local SQLite database.
        """
        logger.info(f"Extracting summary and embedding for {file_path}")
        parsed_data = self._parse_code_structure(file_path, content)
        summary = parsed_data["summary"]
        structure = parsed_data["structure"]

        # Generate embedding for the structural summary
        embedding = self._embed(summary)
        embedding_str = json.dumps(embedding)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO file_memories (file_path, content, summary, structure, embedding)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    content=excluded.content,
                    summary=excluded.summary,
                    structure=excluded.structure,
                    embedding=excluded.embedding
                """,
                (file_path, content, summary, structure, embedding_str)
            )
            conn.commit()

        return [{"file": file_path, "summary": summary, "vector": embedding}]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)

    def query_context(self, prompt: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Takes the user's prompt, embeds it, and queries local SQLite for the top_k
        most relevant structural contexts using cosine similarity.
        """
        logger.info(f"Querying context for prompt: {prompt[:30]}...")
        query_vector = self._embed(prompt)

        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, summary, structure, embedding FROM file_memories")
            rows = cursor.fetchall()

            for row in rows:
                try:
                    stored_vector = json.loads(row["embedding"])
                    score = self._cosine_similarity(query_vector, stored_vector)
                    results.append({
                        "file": row["file_path"],
                        "summary": row["summary"],
                        "structure": json.loads(row["structure"]),
                        "score": score
                    })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for {row['file_path']}: {e}")

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# Global instance
memory_service = CascadeMemoryService()

# Test Execution (If run directly)
if __name__ == "__main__":
    import tempfile

    # Run audit/test with temporary DB to verify functionality without corrupting live DB
    temp_db = tempfile.mktemp(suffix=".db")
    test_service = CascadeMemoryService(db_path=temp_db)

    test_code = """
class DataAnalyzer:
    \"\"\"Analyzes numerical datasets.\"\"\"
    def __init__(self, data):
        self.data = data

    def run_analysis(self):
        \"\"\"Runs complex calculations on data.\"\"\"
        return sum(self.data)

def helper_utils():
    \"\"\"Helper logic.\"\"\"
    return True
"""
    # 1. Test indexing
    indexed = test_service.chunk_and_embed("test_file.py", test_code)
    print("Indexed output:", indexed)

    # 2. Test semantic search query
    matches = test_service.query_context("Need a class to calculate and analyze data", top_k=1)
    print("Semantic search match:", matches)

    # Clean up temp file
    try:
        if os.path.exists(temp_db):
            os.remove(temp_db)
    except Exception as e:
        logger.debug(f"Temporary DB cleanup skipped: {e}")
