CREATE TABLE IF NOT EXISTS crawls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawling_date TEXT NOT NULL,
  filename TEXT,
  total INTEGER NOT NULL DEFAULT 0,
  total_negative INTEGER NOT NULL DEFAULT 0,
  total_positive INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  crawl_id INTEGER NOT NULL REFERENCES crawls(id) ON DELETE CASCADE,
  priority INTEGER NOT NULL,
  tanggal TEXT NOT NULL,
  platform TEXT NOT NULL,
  kategori TEXT NOT NULL,
  topik TEXT NOT NULL,
  sentimen TEXT NOT NULL,
  url TEXT NOT NULL,
  react TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
