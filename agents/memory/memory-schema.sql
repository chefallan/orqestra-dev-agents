-- Persistent agent memory with searchable context.

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_key TEXT NOT NULL UNIQUE,
    memory_type TEXT NOT NULL,
    tags TEXT,
    content TEXT NOT NULL,
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    memory_key,
    memory_type,
    tags,
    content,
    source,
    content='memories',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
  INSERT INTO memories_fts(rowid, memory_key, memory_type, tags, content, source)
  VALUES (new.id, new.memory_key, new.memory_type, new.tags, new.content, new.source);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, memory_key, memory_type, tags, content, source)
  VALUES('delete', old.id, old.memory_key, old.memory_type, old.tags, old.content, old.source);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, memory_key, memory_type, tags, content, source)
  VALUES('delete', old.id, old.memory_key, old.memory_type, old.tags, old.content, old.source);
  INSERT INTO memories_fts(rowid, memory_key, memory_type, tags, content, source)
  VALUES (new.id, new.memory_key, new.memory_type, new.tags, new.content, new.source);
END;
