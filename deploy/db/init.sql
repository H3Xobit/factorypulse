-- FactoryPulse schema (M1+M2)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sensor_samples (
    time            TIMESTAMPTZ       NOT NULL,
    machine         TEXT              NOT NULL,
    metric          TEXT              NOT NULL,
    value           DOUBLE PRECISION  NOT NULL,
    fault_tag       TEXT
);

CREATE INDEX IF NOT EXISTS idx_sensor_samples_machine_metric_time
    ON sensor_samples (machine, metric, time DESC);

CREATE TABLE IF NOT EXISTS audio_chunks (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    machine         TEXT NOT NULL,
    path            TEXT NOT NULL,
    label           TEXT,
    fault_tag       TEXT
);

CREATE TABLE IF NOT EXISTS anomaly_events (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_id        UUID NOT NULL UNIQUE,
    machine         TEXT NOT NULL,
    source          TEXT NOT NULL,
    severity        TEXT NOT NULL,
    fault_code      TEXT,
    score           DOUBLE PRECISION NOT NULL,
    summary         TEXT NOT NULL,
    evidence        JSONB NOT NULL DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'open'
);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_created_at
    ON anomaly_events (created_at DESC);

-- RAG corpus
CREATE TABLE IF NOT EXISTS rag_chunks (
    id              BIGSERIAL PRIMARY KEY,
    doc_id          TEXT NOT NULL,
    section_id      TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    machine         TEXT,
    fault_code      TEXT,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding       vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_fault_code ON rag_chunks (fault_code);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks (doc_id, section_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_hnsw ON rag_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS triage_reports (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    report_id       UUID NOT NULL UNIQUE,
    event_id        UUID,
    machine         TEXT NOT NULL,
    root_cause      TEXT NOT NULL,
    confidence      DOUBLE PRECISION NOT NULL,
    recommended_action TEXT NOT NULL,
    estimated_downtime_risk TEXT NOT NULL,
    evidence        JSONB NOT NULL DEFAULT '[]'::jsonb,
    report_en       TEXT NOT NULL,
    report_ja       TEXT NOT NULL,
    unsupported_claims INT NOT NULL DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb
);
