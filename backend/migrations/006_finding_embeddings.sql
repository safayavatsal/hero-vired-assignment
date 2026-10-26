CREATE TABLE IF NOT EXISTS finding_embeddings (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL,
    investigation_id UUID NOT NULL,
    service TEXT,
    category TEXT NOT NULL,
    statement TEXT NOT NULL,
    suggested_next_step TEXT,
    embedding JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS finding_embeddings_created ON finding_embeddings (created_at DESC);
