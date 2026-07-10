-- ============================================
-- AgesAI — Migration 004: Create Reviews & Findings
-- ============================================

CREATE TABLE reviews (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    pr_number       TEXT,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'analyzing', 'completed', 'failed')),
    review_type     TEXT NOT NULL DEFAULT 'full' CHECK (review_type IN ('security', 'quality', 'performance', 'full')),
    findings_count  INTEGER NOT NULL DEFAULT 0,
    critical_count  INTEGER NOT NULL DEFAULT 0,
    high_count      INTEGER NOT NULL DEFAULT 0,
    medium_count    INTEGER NOT NULL DEFAULT 0,
    low_count       INTEGER NOT NULL DEFAULT 0,
    model_used      TEXT,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    total_cost_usd  NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    summary         JSONB NOT NULL DEFAULT '{}',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_repo_id ON reviews(repository_id);
CREATE INDEX idx_reviews_status ON reviews(status);

-- Review Findings
CREATE TABLE review_findings (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id     UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    severity      TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    category      TEXT NOT NULL CHECK (category IN ('security', 'performance', 'quality', 'style', 'dependency')),
    file_path     TEXT NOT NULL,
    line_start    INTEGER,
    line_end      INTEGER,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL,
    suggestion    TEXT,
    code_snippet  TEXT,
    confidence    REAL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    cwe_id        TEXT,
    is_resolved   BOOLEAN NOT NULL DEFAULT false,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_findings_review_id ON review_findings(review_id);
CREATE INDEX idx_review_findings_severity ON review_findings(severity);
CREATE INDEX idx_review_findings_category ON review_findings(category);
