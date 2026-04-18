#!/usr/bin/env python3
"""Simple persistent memory CLI for autonomous agent workflows.

Usage:
  python scripts/memory_cli.py init
  python scripts/memory_cli.py upsert --key k --type decision --tags "api,auth" --content "..." --source ticket-12
  python scripts/memory_cli.py search --query "auth token refresh" --limit 8
  python scripts/memory_cli.py get --key k
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "agents" / "memory" / "agent_memory.db"
SCHEMA_PATH = ROOT / "agents" / "memory" / "memory-schema.sql"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with connect() as conn:
        conn.executescript(schema)


def upsert_memory(key: str, memory_type: str, tags: str, content: str, source: str) -> None:
    now = utc_now()
    with connect() as conn:
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
            (key, memory_type, tags, content, source, now, now),
        )


def search_memories(query: str, limit: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT m.memory_key, m.memory_type, m.tags, m.source, m.updated_at,
                   snippet(memories_fts, 3, '[', ']', '...', 20) AS snippet
            FROM memories_fts
            JOIN memories m ON m.id = memories_fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def get_memory(key: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT memory_key, memory_type, tags, content, source, created_at, updated_at
            FROM memories
            WHERE memory_key = ?
            """,
            (key,),
        ).fetchone()
    return dict(row) if row else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Persistent memory CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize memory database")

    upsert = sub.add_parser("upsert", help="Create or update a memory")
    upsert.add_argument("--key", required=True)
    upsert.add_argument("--type", required=True)
    upsert.add_argument("--tags", default="")
    upsert.add_argument("--content", required=True)
    upsert.add_argument("--source", default="")

    search = sub.add_parser("search", help="Full-text search memories")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=8)

    get = sub.add_parser("get", help="Fetch one memory by key")
    get.add_argument("--key", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print(f"Initialized memory DB at {DB_PATH}")
        return

    if args.command == "upsert":
        upsert_memory(args.key, args.type, args.tags, args.content, args.source)
        print(f"Upserted memory '{args.key}'")
        return

    if args.command == "search":
        results = search_memories(args.query, args.limit)
        print(json.dumps(results, indent=2))
        return

    if args.command == "get":
        result = get_memory(args.key)
        print(json.dumps(result, indent=2))
        return

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
