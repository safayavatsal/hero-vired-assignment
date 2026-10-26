CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY,
    fingerprint TEXT NOT NULL UNIQUE,
    service TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    source_event_id TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL,
    source TEXT NOT NULL,
    service TEXT NOT NULL,
    severity TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    labels JSONB NOT NULL,
    description TEXT NOT NULL,
    lifecycle TEXT NOT NULL,
    source_time TIMESTAMPTZ NOT NULL,
    received_time TIMESTAMPTZ NOT NULL,
    raw_payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS timeline_events (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    event_type TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    received_time TIMESTAMPTZ NOT NULL,
    sequence_number INTEGER NOT NULL,
    payload JSONB NOT NULL,
    UNIQUE (incident_id, sequence_number)
);

CREATE INDEX IF NOT EXISTS timeline_events_incident_order
    ON timeline_events (incident_id, event_time, received_time, sequence_number);

CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    scenario_id TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    model_status TEXT NOT NULL,
    model_error TEXT,
    model_analysis JSONB,
    prompt_version TEXT NOT NULL DEFAULT 'investigation-v1',
    UNIQUE (incident_id)
);

CREATE TABLE IF NOT EXISTS investigation_evidence (
    id TEXT NOT NULL,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    availability TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    items JSONB NOT NULL,
    PRIMARY KEY (investigation_id, id)
);

CREATE TABLE IF NOT EXISTS investigation_findings (
    id TEXT NOT NULL,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    statement TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    suggested_next_step TEXT NOT NULL,
    evidence_ids JSONB NOT NULL,
    uncertainty TEXT,
    PRIMARY KEY (investigation_id, id)
);

CREATE TABLE IF NOT EXISTS pages (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    level TEXT NOT NULL,
    responder TEXT NOT NULL,
    fallback_responder TEXT NOT NULL,
    status TEXT NOT NULL,
    deadline_at TIMESTAMPTZ NOT NULL,
    response_type TEXT,
    response_text TEXT,
    incident_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (incident_id, level)
);

CREATE TABLE IF NOT EXISTS action_proposals (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    scenario_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target TEXT NOT NULL,
    parameters JSONB NOT NULL,
    status TEXT NOT NULL,
    approval_expires_at TIMESTAMPTZ,
    approved_by TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    simulator_action_id UUID,
    result JSONB,
    incident_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

ALTER TABLE investigations ADD COLUMN IF NOT EXISTS model_error TEXT;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS model_analysis JSONB;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS prompt_version TEXT NOT NULL DEFAULT 'investigation-v1';
ALTER TABLE pages ADD COLUMN IF NOT EXISTS incident_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS incident_version INTEGER NOT NULL DEFAULT 1;
