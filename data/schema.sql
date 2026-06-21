-- Schema da Fundação P2 (Fatia 0) — base nacional de Boletins de Ocorrência (BOs)
--
-- Simplificação assumida nesta fatia: tabela `bo` NÃO particionada. O modelo
-- completo prevê particionamento por (estado, ano), mas no Postgres a chave de
-- partição precisa entrar em toda PK/UNIQUE — o que (a) impede uma PK simples por
-- `id` e (b) força as FKs de `inquerito`/`tco` a referenciar a chave composta.
-- Para o slice com dados sintéticos isso não traz benefício, então `estado` e o
-- ano ficam apenas indexados. Revisar quando as Fatias 2+ generalizarem a ingestão.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS bo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bo_numero       TEXT,
    estado          TEXT NOT NULL,
    municipio       TEXT,
    data_hora       TIMESTAMPTZ NOT NULL,
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
    embedding       vector(1024),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indice por ano (substitui o particionamento por ano deste slice). Imutavel via
-- AT TIME ZONE 'UTC' para poder ser usado em indice de expressao.
CREATE INDEX IF NOT EXISTS idx_bo_ano ON bo ((EXTRACT(YEAR FROM (data_hora AT TIME ZONE 'UTC'))::INTEGER));

CREATE INDEX IF NOT EXISTS idx_bo_estado ON bo (estado);
CREATE INDEX IF NOT EXISTS idx_bo_dominio_data ON bo (dominio, data_hora);
CREATE INDEX IF NOT EXISTS idx_bo_hex ON bo (hex_id_res8);

-- Índice HNSW para busca vetorial (cosseno), conforme decisão fixada.
CREATE INDEX IF NOT EXISTS idx_bo_embedding_hnsw ON bo
    USING hnsw (embedding vector_cosine_ops)
    WITH (ef_construction = 200);

COMMENT ON COLUMN bo.embedding IS 'Embedding multilingual-e5-large (1024d) do relato, prefixo passage: aplicado na ingestão.';

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
