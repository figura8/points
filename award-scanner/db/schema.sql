PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    airline TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    cabin TEXT NOT NULL,
    program TEXT NOT NULL,
    miles_cost INTEGER NOT NULL,
    taxes_fees REAL NOT NULL DEFAULT 0,
    seats INTEGER NOT NULL DEFAULT 1,
    currency TEXT NOT NULL DEFAULT 'USD',
    last_seen_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(source, airline, origin, destination, departure_date, cabin, program, miles_cost, taxes_fees)
);

CREATE INDEX IF NOT EXISTS idx_awards_route_date ON awards(origin, destination, departure_date);
CREATE INDEX IF NOT EXISTS idx_awards_active ON awards(is_active);

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    run_after TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    UNIQUE(source, origin, destination, departure_date)
);

CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status_date ON crawl_jobs(status, departure_date);
