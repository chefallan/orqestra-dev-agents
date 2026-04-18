from __future__ import annotations

import sqlite3
from pathlib import Path


class MemoryStore:
    def __init__(self, repo_root: Path) -> None:
        self.db_path = repo_root / "agents" / "memory" / "agent_memory.db"
        self.schema_path = repo_root / "agents" / "memory" / "memory-schema.sql"

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        schema = self.schema_path.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema)

    def upsert(
        self,
        key: str,
        memory_type: str,
        tags: str,
        content: str,
        source: str,
        now: str,
        tenant_id: str,
    ) -> None:
        tagged = self._with_tenant_tag(tags, tenant_id)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories(memory_key, memory_type, tags, content, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_key) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    tags=excluded.tags,
                    content=excluded.content,
                    source=excluded.source,
                    updated_at=excluded.updated_at
                """,
                (key, memory_type, tagged, content, source, now, now),
            )

    def search(self, query: str, limit: int = 8, tenant_id: str = "") -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.memory_key, m.memory_type, m.tags, m.source, m.updated_at,
                    snippet(memories_fts, 3, '[', ']', '...', 20) AS snippet
                FROM memories_fts
                JOIN memories m ON m.id = memories_fts.rowid
                WHERE memories_fts MATCH ?
                AND m.tags LIKE ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, f"%tenant:{tenant_id}%", limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def _with_tenant_tag(self, tags: str, tenant_id: str) -> str:
        tenant_tag = f"tenant:{tenant_id}"
        clean = [token.strip() for token in tags.split(",") if token.strip()]
        if tenant_tag not in clean:
            clean.append(tenant_tag)
        return ",".join(clean)
