CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    year TEXT NOT NULL,
    location TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS image_tags (
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'vision',
    confidence REAL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (image_id, tag_id)
);

CREATE TABLE IF NOT EXISTS tag_edges (
    parent_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    child_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_id, child_id),
    CHECK (parent_id <> child_id)
);

CREATE TABLE IF NOT EXISTS failure_log (
    source_path TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    stage TEXT NOT NULL,
    error_type TEXT,
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 1,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_image_tags_tag ON image_tags (tag_id);

CREATE INDEX IF NOT EXISTS idx_tag_edges_child ON tag_edges (child_id);

CREATE INDEX IF NOT EXISTS idx_images_year ON images (year);

CREATE INDEX IF NOT EXISTS idx_failure_log_open ON failure_log (resolved_at);