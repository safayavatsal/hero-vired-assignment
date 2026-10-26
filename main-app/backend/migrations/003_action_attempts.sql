CREATE TABLE IF NOT EXISTS action_attempts (
    id UUID PRIMARY KEY,
    action_proposal_id UUID NOT NULL REFERENCES action_proposals(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    simulator_action_id UUID,
    result JSONB,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    UNIQUE (action_proposal_id, attempt_number)
);

CREATE TABLE IF NOT EXISTS verifications (
    id UUID PRIMARY KEY,
    action_attempt_id UUID NOT NULL REFERENCES action_attempts(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    observed_state JSONB NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL
);
