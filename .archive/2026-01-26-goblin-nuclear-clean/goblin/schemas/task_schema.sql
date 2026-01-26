-- Task Scheduler Database Schema
-- Organic cron model: Plant → Sprout → Prune → Trellis → Harvest → Compost

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    schedule TEXT NOT NULL,  -- cron-like or organic (daily, weekly, monthly, etc.)
    state TEXT DEFAULT 'plant',  -- plant|sprout|prune|trellis|harvest|compost
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_runs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    state TEXT DEFAULT 'sprout',  -- sprout|prune|trellis|harvest|compost
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT,  -- success|failed
    output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    run_id TEXT REFERENCES task_runs(id),
    state TEXT DEFAULT 'pending',  -- pending|processing|completed|failed
    scheduled_for TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_task_runs_task_id ON task_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_state ON task_runs(state);
CREATE INDEX IF NOT EXISTS idx_task_queue_state ON task_queue(state);
CREATE INDEX IF NOT EXISTS idx_task_queue_task_id ON task_queue(task_id);
