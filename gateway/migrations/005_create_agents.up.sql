-- ============================================
-- AgesAI — Migration 005: Create Agents & Agent Runs
-- ============================================

CREATE TABLE agents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL UNIQUE,
    description   TEXT NOT NULL,
    graph_type    TEXT NOT NULL CHECK (graph_type IN ('coding', 'research', 'planning', 'review', 'deployment')),
    capabilities  JSONB NOT NULL DEFAULT '[]',
    default_config JSONB NOT NULL DEFAULT '{}',
    is_active     BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id          UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id   UUID REFERENCES conversations(id) ON DELETE SET NULL,
    status            TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    input             JSONB NOT NULL,
    output            JSONB,
    steps             JSONB NOT NULL DEFAULT '[]',
    model_used        TEXT,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    total_cost_usd    NUMERIC(10, 6) NOT NULL DEFAULT 0.0,
    duration_ms       INTEGER,
    error_message     TEXT,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_agent_runs_user_id ON agent_runs(user_id);
CREATE INDEX idx_agent_runs_agent_id ON agent_runs(agent_id);
CREATE INDEX idx_agent_runs_status ON agent_runs(status);
CREATE INDEX idx_agent_runs_active ON agent_runs(user_id) WHERE status IN ('queued', 'running');

-- Seed default agents
INSERT INTO agents (name, description, graph_type, capabilities) VALUES
    ('Coding Agent', 'Generates production-quality code with context from your codebase', 'coding',
     '["code_generation", "code_modification", "test_generation"]'::jsonb),
    ('Research Agent', 'Explores and explains your codebase architecture and patterns', 'research',
     '["codebase_search", "dependency_analysis", "architecture_mapping"]'::jsonb),
    ('Planning Agent', 'Breaks down feature requests into actionable development tasks', 'planning',
     '["task_decomposition", "effort_estimation", "dependency_mapping"]'::jsonb),
    ('Review Agent', 'Performs automated code review for quality, security, and performance', 'review',
     '["code_quality", "security_analysis", "performance_review"]'::jsonb);
