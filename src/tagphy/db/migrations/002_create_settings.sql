CREATE TABLE IF NOT EXISTS settings (
    config TEXT PRIMARY KEY,
    value TEXT NOT NULL CHECK (value <> '')
);

INSERT OR IGNORE INTO settings (config, value)
VALUES ('privacy_pre_check', 'true');
