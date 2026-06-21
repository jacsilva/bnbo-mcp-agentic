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

### Celery beat (job noturno do Observatório — `calcular_alertas_noturnos`)

```bash
celery -A jobs.celery_app beat --loglevel=info
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

### Cliente de referência LangGraph (opcional)

Supervisor que orquestra as tools do MCP Server usando a LLM do cliente —
ver [`client_reference/README.md`](client_reference/README.md). Deps
isoladas; o servidor MCP não depende de LangChain/LangGraph.

```bash
MCP_TRANSPORT=sse python3 mcp_server.py &
pip install -r client_reference/requirements.txt
python3 -m client_reference.run_supervisor "Busque ocorrências similares a roubo de celular com faca"
```

## 🛠️ Tools expostas

| Tool | Tipo | Descrição |
|---|---|---|
| `buscar_ocorrencias_similares` | atômica (P2) | ANN por `bo_id` ou `texto_livre`; reranking semântico + estrutural |
| `obter_razoes_similaridade` | atômica (P2) | Explicabilidade: dimensões e pesos que vincularam dois BOs |
| `agrupar_serie_criminal` | composta (P2) | DBSCAN sobre candidatos similares, com score de coesão |
| `reindexar_embeddings` | assíncrona (Celery) | Recalcula embeddings de todos os BOs — requer perfil `analista` ou `investigador` |
| `consultar_job_status` | transversal | Polling de status de jobs assíncronos por `job_id` |
| `exportar_resultado` | transversal | Converte o JSON de outra tool para CSV/JSON/GeoJSON |
| `listar_regioes_disponiveis` | transversal | Lista estados/municípios com BOs cadastrados |
| `detectar_anomalias_estatisticas` | atômica (P1) | Z-score mensal de volume de BOs por estado/município/domínio/natureza |
| `calcular_taxa_elucidacao` | atômica (P1) | Taxa de inquéritos concluídos por delegacia/estado/natureza |
| `listar_delegacias_com_alerta` | composta (P1) | Combina anomalias de volume + baixa elucidação numa visão de prioridade |
| `subscrever_alertas` | transversal (P1) | Lê o snapshot mais recente do job noturno de anomalias (polling, não push) |

## 🔐 Camada de segurança transversal (Fatia 2)

- **Perfis** (`server/security/perfis.py`): `publico < analista < investigador`.
  O perfil nunca é aceito como parâmetro de tool — é resolvido a partir do
  contexto de autenticação (`server/security/contexto.py`). Nesta fatia, a
  resolução real de token (JWT/OAuth) ainda não está implementada; usa-se um
  placeholder via variável de ambiente `MCP_PERFIL_ATUAL`, documentado como
  decisão pendente do modelo.
- **Redação de PII** (`server/security/redacao.py`): mascara CPF, telefone e
  e-mail em campos de texto livre (`relato`) para perfis `publico`/`analista`;
  `investigador` recebe o texto integral. Aplicada nas tools do P2 antes da
  resposta sair do servidor.
- **Auditoria** (`server/security/auditoria.py`): decorator `com_auditoria`
  aplicado a toda tool, registrando cliente/perfil/tool/parâmetros/timestamp
  na tabela `audit_log`.

## 📁 Estrutura do projeto

```
bnbo-mcp-agentic/
├── mcp_server.py          # Servidor MCP (STDIO/SSE) — registra as tools do domínio
├── mcp_client.py          # Cliente MCP oficial (STDIO)
├── mcp_client_http.py     # Cliente MCP via SSE/HTTP
├── test_client.py         # Testes diretos da lógica (ml.linkage)
├── test_tools.py          # Testes das funções *_tool do servidor
├── server/
│   ├── tools/
│   │   ├── p1_observatorio.py # Tools MCP do P1 (wrappers sobre ml.stats)
│   │   ├── p2_linkage.py    # Tools MCP do P2 (wrappers sobre ml.linkage)
│   │   ├── util_jobs.py     # Tools transversais de jobs assíncronos
│   │   └── util_dominio.py  # exportar_resultado, listar_regioes_disponiveis
│   └── security/
│       ├── perfis.py        # Perfis publico/analista/investigador
│       ├── contexto.py       # Resolução do perfil a partir do token (placeholder)
│       ├── redacao.py         # Redação de PII em campos de texto livre
│       └── auditoria.py        # Decorator com_auditoria + log em audit_log
├── ml/
│   ├── embeddings.py      # e5-large + prefixos query:/passage: + cache Redis
│   ├── linkage.py         # Busca vetorial, reranking, explicabilidade, DBSCAN
│   └── stats.py           # Anomalias estatísticas (z-score) e taxa de elucidação (P1)
├── jobs/
│   ├── celery_app.py      # Configuração do Celery (broker/backend Redis) + beat_schedule
│   └── tasks.py           # Tasks reindexar_embeddings, calcular_alertas_noturnos
├── data/
│   ├── db.py               # Pool de conexões PostgreSQL/pgvector
│   ├── schema.sql           # Tabelas bo/inquerito/tco/audit_log, índice HNSW
│   └── synthetic.py          # Gerador de BOs sintéticos para dev/teste
├── client_reference/       # OPCIONAL: supervisor LangGraph (deps isoladas), usa a LLM do cliente
│   ├── supervisor.py
│   ├── run_supervisor.py
│   └── requirements.txt
├── docker-compose.yml      # PostgreSQL 16 (pgvector) + Redis 7
├── requirements.txt
└── start_server.sh
```

> Nota de simplificação (Fatia 0): a tabela `bo` é particionada por RANGE em
> `ano` (não pelo composto `(estado, ano)` do modelo completo); `estado` fica
> indexado em vez de particionado. Revisitar nas fatias de generalização.

> Nota de simplificação (Fatia 2): `inquerito` e `tco` já existem no schema e
> se ligam a `bo` por `bo_id`, mas a ETL de matching para os casos em que o
> `bo_id` está ausente (heurística por proximidade temporal/espacial/natureza)
> ainda não foi implementada — fica para uma generalização futura da
> ingestão. A resolução de perfil via token real (JWT/OAuth) também é um
> placeholder, conforme descrito na seção de segurança.

> Nota de simplificação (Fatia 3): o modelo original previa notificação de
> alertas via push (SSE); como tools MCP seguem o padrão request/response,
> `subscrever_alertas` lê um snapshot persistido em `alerta_observatorio`,
> recalculado pelo job noturno `calcular_alertas_noturnos` (requer `celery
> beat` rodando) — funcionando como polling em vez de push real.

## 🐛 Troubleshooting

### "connection refused" ao conectar no PostgreSQL/Redis
- Verifique se os containers estão rodando: `docker compose ps`
- Suba os serviços: `docker compose up -d`

### Modelo de embedding demora para carregar
- `multilingual-e5-large` é ~2GB; na primeira execução o download pode levar
  alguns minutos. Execuções subsequentes usam o cache local do HuggingFace.

### `reindexar_embeddings` fica em `PENDING`
- Confirme que há um worker Celery rodando: `celery -A jobs.celery_app worker`
