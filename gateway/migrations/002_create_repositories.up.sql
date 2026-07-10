-- ============================================
-- AgesAI — Migration 002: Create Repositories & Indexed Files
-- ============================================

CREATE TABLE repositories (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name              TEXT NOT NULL,
    url               TEXT,
    source            TEXT NOT NULL DEFAULT 'github' CHECK (source IN ('github', 'upload', 'local')),
    default_branch    TEXT NOT NULL DEFAULT 'main',
    primary_language  TEXT,
    status            TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'cloning', 'parsing', 'embedding', 'ready', 'failed', 'deleting')),
    error_message     TEXT,
    file_count        INTEGER NOT NULL DEFAULT 0,
    chunk_count       INTEGER NOT NULL DEFAULT 0,
    embedding_count   INTEGER NOT NULL DEFAULT 0,
    size_bytes        BIGINT NOT NULL DEFAULT 0,
    metadata          JSONB NOT NULL DEFAULT '{}',
    last_indexed_at   TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_repositories_user_id ON repositories(user_id);
CREATE INDEX idx_repositories_status ON repositories(status);
CREATE INDEX idx_repositories_active ON repositories(user_id) WHERE status = 'ready';

CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON repositories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Indexed Files
CREATE TABLE indexed_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,
    language        TEXT,
    content_hash    TEXT,
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    line_count      INTEGER,
    size_bytes      BIGINT,
    ast_metadata    JSONB NOT NULL DEFAULT '{}',
    indexed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_indexed_files_repo_id ON indexed_files(repository_id);
CREATE INDEX idx_indexed_files_content_hash ON indexed_files(content_hash);
CREATE INDEX idx_indexed_files_fts ON indexed_files USING GIN(to_tsvector('english', file_path));

-- Unique constraint: one entry per file per repo
CREATE UNIQUE INDEX idx_indexed_files_repo_path ON indexed_files(repository_id, file_path);
