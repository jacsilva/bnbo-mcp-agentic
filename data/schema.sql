-- Schema da Fundação P2 (Fatia 0) — base nacional de Boletins de Ocorrência (BOs)
--
-- Simplificação assumida nesta fatia: particionamento por RANGE em `ano` apenas
-- (em vez do composto `(estado, ano)` do modelo completo), para manter a criação
-- de partições estática e simples no slice inicial. `estado` fica indexado em
-- vez de particionado. Revisar quando as Fatias 2+ generalizarem a ingestão.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS bo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bo_numero       TEXT,
    estado          TEXT NOT NULL,
    municipio       TEXT,
    data_hora       TIMESTAMPTZ NOT NULL,
    ano             INTEGER NOT NULL GENERATED ALWAYS AS (EXTRACT(YEAR FROM data_hora)::INTEGER) STORED,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    hex_id_res8     TEXT,
    dominio         TEXT NOT NULL,
    natureza        TEXT NOT NULL,
    relato          TEXT NOT NULL,
    vitima_perfil   JSONB,
    autor_perfil    JSONB,
    instrumento     TEXT,
    status          TEXT NOT NULL DEFAULT 'registrado',
    inquerito_id    UUID,
    embedding       vector(768),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (ano);

CREATE TABLE IF NOT EXISTS bo_2023 PARTITION OF bo FOR VALUES FROM (2023) TO (2024);
CREATE TABLE IF NOT EXISTS bo_2024 PARTITION OF bo FOR VALUES FROM (2024) TO (2025);
CREATE TABLE IF NOT EXISTS bo_2025 PARTITION OF bo FOR VALUES FROM (2025) TO (2026);
CREATE TABLE IF NOT EXISTS bo_2026 PARTITION OF bo FOR VALUES FROM (2026) TO (2027);
CREATE TABLE IF NOT EXISTS bo_default PARTITION OF bo DEFAULT;

CREATE INDEX IF NOT EXISTS idx_bo_estado ON bo (estado);
CREATE INDEX IF NOT EXISTS idx_bo_dominio_data ON bo (dominio, data_hora);
CREATE INDEX IF NOT EXISTS idx_bo_hex ON bo (hex_id_res8);

-- Índice HNSW para busca vetorial (cosseno), conforme decisão fixada.
CREATE INDEX IF NOT EXISTS idx_bo_embedding_hnsw ON bo
    USING hnsw (embedding vector_cosine_ops)
    WITH (ef_construction = 200);

COMMENT ON COLUMN bo.embedding IS 'Embedding multilingual-e5-large (768d) do relato, prefixo passage: aplicado na ingestão.';

-- Fundação completa (Fatia 2) ------------------------------------------------

CREATE TABLE IF NOT EXISTS inquerito (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bo_id           UUID REFERENCES bo (id),
    numero          TEXT,
    delegacia       TEXT,
    estado          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'em_andamento',
    aberto_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    concluido_em    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_inquerito_bo_id ON inquerito (bo_id);
CREATE INDEX IF NOT EXISTS idx_inquerito_delegacia_status ON inquerito (delegacia, status);

CREATE TABLE IF NOT EXISTS tco (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bo_id           UUID REFERENCES bo (id),
    numero          TEXT,
    estado          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'registrado',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tco_bo_id ON tco (bo_id);

-- Trilha de auditoria de acesso às tools (camada de segurança transversal).
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente         TEXT,
    perfil          TEXT NOT NULL,
    tool_name       TEXT NOT NULL,
    parametros      JSONB,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_tool_data ON audit_log (tool_name, criado_em);

-- Fatia 3 — Observatório (P1) -------------------------------------------------

-- Snapshot persistido pelo job noturno de detecção de anomalias; lido pelas
-- tools `listar_delegacias_com_alerta` e `subscrever_alertas` (polling, não
-- push real — ver nota de simplificação no README).
CREATE TABLE IF NOT EXISTS alerta_observatorio (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estado          TEXT NOT NULL,
    municipio       TEXT,
    dominio         TEXT NOT NULL,
    natureza        TEXT NOT NULL,
    mes             DATE NOT NULL,
    z_score         DOUBLE PRECISION NOT NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerta_observatorio_estado_mes ON alerta_observatorio (estado, mes);
CREATE INDEX IF NOT EXISTS idx_alerta_observatorio_criado_em ON alerta_observatorio (criado_em);
