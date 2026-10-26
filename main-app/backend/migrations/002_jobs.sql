CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    incident_id UUID REFERENCES incidents(id),
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    lease_until TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS jobs_claimable ON jobs (status, lease_until, created_at);

CREATE TABLE IF NOT EXISTS page_delivery_attempts (
    id UUID PRIMARY KEY,
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE (page_id, attempt_number)
);
