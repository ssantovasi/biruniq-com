-- D1 schema for biruniq.com sign-ups (2026-11-08). The raw IP is never stored, only a salted hash used for the hourly limit.
CREATE TABLE IF NOT EXISTS signups (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at    TEXT NOT NULL,
  name          TEXT NOT NULL,
  email         TEXT NOT NULL,
  organisation  TEXT NOT NULL,
  role          TEXT,
  country       TEXT,
  interests     TEXT,          -- JSON array of edition names
  message       TEXT,
  consent_text  TEXT,          -- the exact consent wording the visitor ticked
  page          TEXT,
  ip_hash       TEXT NOT NULL,
  user_agent    TEXT
);
CREATE INDEX IF NOT EXISTS signups_ip_time ON signups (ip_hash, created_at);
CREATE INDEX IF NOT EXISTS signups_email ON signups (email);
