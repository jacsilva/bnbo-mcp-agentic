# BNBO MCP Agentic — Plataforma de Inteligência em Segurança Pública

Servidor MCP (Model Context Protocol) sobre uma base nacional de Boletins de
Ocorrência (BOs), expondo tools de inteligência criminal para a LLM do
cliente. O servidor é puro: nenhuma LLM roda nele — apenas tools (busca
vetorial, linkage, jobs assíncronos). Raciocínio e roteamento ficam do lado
do cliente.

Esta fatia da implementação entrega o **P2 — Linkage Criminal**: busca de
ocorrências similares (semântica + estrutural), explicabilidade dos vínculos
e agrupamento de séries criminais.

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │  (LLM própria do cliente; opcionalmente supervisor LangGraph)
└──────┬──────┘
       │ MCP (STDIO/SSE)
       ▼
┌─────────────────────────────────────────────┐
│           MCP Server (sem LLM)               │
│  buscar_ocorrencias_similares                │
│  obter_razoes_similaridade                   │
│  agrupar_serie_criminal                      │
│  reindexar_embeddings (assíncrona, Celery)   │
│  consultar_job_status                        │
└──────────────┬────────────────┬──────────────┘
               │                │
               ▼                ▼
      ┌─────────────────┐  ┌─────────┐
      │ PostgreSQL 16    │  │ Redis 7 │
      │ + pgvector HNSW  │  │ cache + │
      │ (embeddings 768d)│  │ Celery  │
      └─────────────────┘  └─────────┘
```

- **Vetorial/relacional:** PostgreSQL 16 + pgvector (HNSW, cosseno).
- **Embeddings:** `intfloat/multilingual-e5-large` (768d), prefixos
  obrigatórios `query:`/`passage:`, cache no Redis por SHA-256 (TTL 24h).
- **Jobs assíncronos:** Celery + Redis (ex.: reindexação de embeddings).

## 🚀 Instalação

### Pré-requisitos

- Python 3.10+
- Docker e Docker Compose

### Passo a passo

```bash
cp .env.example .env   # ajuste se necessário

# 1. Subir PostgreSQL (pgvector) + Redis
docker compose up -d

# 2. Ambiente virtual e dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Popular a base com BOs sintéticos
python3 -m data.synthetic --n 500
```

## 🚀 Como usar

### Servidor

```bash
# STDIO (padrão)
python3 mcp_server.py

# SSE/HTTP
MCP_TRANSPORT=sse python3 mcp_server.py
```

### Worker Celery (necessário para `reindexar_embeddings`)

```bash
celery -A jobs.celery_app worker --loglevel=info
```

### Clientes de teste

```bash
# Testes diretos da lógica (sem MCP/sem servidor)
python3 test_client.py

# Testes das tools (assume servidor SSE rodando)
python3 test_tools.py

# Cliente MCP oficial via STDIO
python3 mcp_client.py

# Cliente MCP via SSE/HTTP (requer MCP_TRANSPORT=sse)
python3 mcp_client_http.py
```

## 🛠️ Tools expostas (P2 — Linkage Criminal)

| Tool | Tipo | Descrição |
|---|---|---|
| `buscar_ocorrencias_similares` | atômica | ANN por `bo_id` ou `texto_livre`; reranking semântico + estrutural |
| `obter_razoes_similaridade` | atômica | Explicabilidade: dimensões e pesos que vincularam dois BOs |
| `agrupar_serie_criminal` | composta | DBSCAN sobre candidatos similares, com score de coesão |
| `reindexar_embeddings` | assíncrona (Celery) | Recalcula embeddings de todos os BOs |
| `consultar_job_status` | transversal | Polling de status de jobs assíncronos por `job_id` |

## 📁 Estrutura do projeto

```
bnbo-mcp-agentic/
├── mcp_server.py          # Servidor MCP (STDIO/SSE) — registra as tools do domínio
├── mcp_client.py          # Cliente MCP oficial (STDIO)
├── mcp_client_http.py     # Cliente MCP via SSE/HTTP
├── test_client.py         # Testes diretos da lógica (ml.linkage)
├── test_tools.py          # Testes das funções *_tool do servidor
├── server/
│   └── tools/
│       ├── p2_linkage.py  # Tools MCP do P2 (wrappers sobre ml.linkage)
│       └── util_jobs.py   # Tools transversais de jobs assíncronos
├── ml/
│   ├── embeddings.py      # e5-large + prefixos query:/passage: + cache Redis
│   └── linkage.py         # Busca vetorial, reranking, explicabilidade, DBSCAN
├── jobs/
│   ├── celery_app.py      # Configuração do Celery (broker/backend Redis)
│   └── tasks.py           # Task reindexar_embeddings
├── data/
│   ├── db.py               # Pool de conexões PostgreSQL/pgvector
│   ├── schema.sql           # Tabela `bo` particionada, índice HNSW
│   └── synthetic.py          # Gerador de BOs sintéticos para dev/teste
├── docker-compose.yml      # PostgreSQL 16 (pgvector) + Redis 7
├── requirements.txt
└── start_server.sh
```

> Nota de simplificação (Fatia 0): a tabela `bo` é particionada por RANGE em
> `ano` (não pelo composto `(estado, ano)` do modelo completo); `estado` fica
> indexado em vez de particionado. Revisitar nas fatias de generalização.

## 🐛 Troubleshooting

### "connection refused" ao conectar no PostgreSQL/Redis
- Verifique se os containers estão rodando: `docker compose ps`
- Suba os serviços: `docker compose up -d`

### Modelo de embedding demora para carregar
- `multilingual-e5-large` é ~2GB; na primeira execução o download pode levar
  alguns minutos. Execuções subsequentes usam o cache local do HuggingFace.

### `reindexar_embeddings` fica em `PENDING`
- Confirme que há um worker Celery rodando: `celery -A jobs.celery_app worker`
