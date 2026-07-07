# BNBO MCP Agentic — Plataforma de Inteligência em Segurança Pública

Servidor MCP (Model Context Protocol) sobre uma base nacional de Boletins de
Ocorrência (BOs), expondo tools de inteligência criminal para a LLM do
cliente. O servidor é puro: nenhuma LLM roda nele — apenas tools (busca
vetorial, linkage, jobs assíncronos). Raciocínio e roteamento ficam do lado
do cliente.

A implementação cobre três projetos de inteligência criminal:

- **P1 — Observatório:** anomalias estatísticas de volume (z-score), taxa de
  elucidação e priorização de delegacias com alerta.
- **P2 — Linkage Criminal:** busca de ocorrências similares (semântica +
  estrutural), explicabilidade dos vínculos e agrupamento de séries criminais.
- **P4 — Atlas de Vulnerabilidade:** Índice de Vulnerabilidade Criminal (IVC)
  por hexágono H3, com classificação Jenks e saída GeoJSON.

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │  (LLM própria do cliente; opcionalmente supervisor LangGraph)
└──────┬──────┘
       │ MCP (STDIO/Streamable HTTP)
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
      │ (embeddings1024d)│  │ Celery  │
      └─────────────────┘  └─────────┘
```

- **Vetorial/relacional:** PostgreSQL 16 + pgvector (HNSW, cosseno).
- **Embeddings:** `intfloat/multilingual-e5-large` (1024d), prefixos
  obrigatórios `query:`/`passage:`, cache no Redis por SHA-256 (TTL 24h).
- **Jobs assíncronos:** Celery + Redis (ex.: reindexação de embeddings).

## 🚀 Execução — do zero até testar as tools

### 1. Pré-requisitos

- Python 3.10+
- Docker e Docker Compose

### 2. Configuração inicial

```bash
git clone <seu-repo> && cd bnbo-mcp-agentic
cp .env.example .env   # ajuste DATABASE_URL/REDIS_URL/EMBED_MODEL_NAME se precisar
```

### 3. Subir infraestrutura (Postgres+pgvector e Redis)

```bash
docker compose up -d
docker compose ps   # confirme os dois serviços "healthy"
```

O schema (`data/schema.sql`) é aplicado automaticamente na criação do
container Postgres.

### 4. Ambiente Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Popular a base com BOs sintéticos

```bash
python3 -m data.synthetic --n 500
```

Gera BOs com embeddings (e5-large), hexágonos H3 e uma fração com inquéritos
vinculados.

### 6. Subir o servidor MCP

```bash
# STDIO (padrão, para uso com cliente MCP local)
python3 -m server.mcp_server

# ou Streamable HTTP (necessário para o cliente LangGraph de referência)
MCP_TRANSPORT=streamable-http python3 -m server.mcp_server
```

### 7. Worker e beat do Celery (jobs assíncronos)

Em terminais separados, se for usar `reindexar_embeddings` ou os alertas
noturnos do Observatório:

```bash
celery -A jobs.celery_app worker --loglevel=info
celery -A jobs.celery_app beat --loglevel=info   # job calcular_alertas_noturnos
```

### 8. Testar

```bash
# Testes unitários sem dependência de infra (rápidos)
python3 -m tests.test_security
python3 -m tests.test_stats
python3 -m tests.test_atlas
python3 -m tests.test_erros

# Testes diretos da lógica de domínio (requer Postgres/Redis rodando)
python3 test_client.py

# Testes das tools via MCP (requer servidor Streamable HTTP rodando)
python3 test_tools.py

# Cliente MCP oficial via STDIO
python3 -m client.stdio.mcp_client

# Cliente MCP via Streamable HTTP (requer servidor Streamable HTTP rodando)
python3 -m client.http.mcp_client_http
```

#### Inspecionar via MCP Inspector (UI web)

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) é a UI
oficial para navegar e testar Tools/Resources/Prompts do servidor. Roda via
`npx` (requer Node 18+) e abre em `http://localhost:6274` com um token de
sessão na URL.

```bash
# A) STDIO — o Inspector sobe e gerencia o servidor.
#    Use o python do venv (senão faltam mcp e as demais deps).
npx @modelcontextprotocol/inspector venv/bin/python3 -m server.mcp_server

# B) Streamable HTTP — conecta num servidor já no ar.
#    Suba o servidor antes (MCP_TRANSPORT=streamable-http python3 -m server.mcp_server),
#    depois abra o Inspector e configure na UI:
#      Transport Type: Streamable HTTP
#      URL:            http://127.0.0.1:8080/mcp
npx @modelcontextprotocol/inspector
```

### 9. (Opcional) Cliente supervisor LangGraph

Supervisor que orquestra as tools do MCP Server usando a LLM do cliente —
ver [`client/reference/README.md`](client/reference/README.md). Deps
isoladas; o servidor MCP não depende de LangChain/LangGraph.

```bash
MCP_TRANSPORT=streamable-http python3 -m server.mcp_server &
pip install -r client/reference/requirements.txt
export ANTHROPIC_API_KEY=...   # ou configure outro provider em MCP_CLIENT_MODEL
python3 -m client.reference.run_supervisor "Busque ocorrências similares a roubo de celular com faca"
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
| `calcular_indice_vulnerabilidade` | atômica (P4) | Ranking de hexágonos H3 por Índice de Vulnerabilidade Criminal (IVC) |
| `gerar_atlas_vulnerabilidade` | composta (P4) | GeoJSON do Atlas: hexágonos H3 com IVC e classe Jenks, prontos para mapa |

## 📚 Resources expostos

Dados de referência read-only do domínio (navegáveis pelo host/cliente como
contexto, complementares às tools). Definidos em `server/recursos/`.

| URI | Tipo | Conteúdo |
|---|---|---|
| `bnbo://dominio/glossario` | markdown | Glossário do domínio (BO, inquérito, TCO, H3, IVC, série criminal…) |
| `bnbo://dominio/metodologia-ivc` | markdown | Metodologia e pesos do IVC (ponderação por domínio, H3 res. 8, Jenks) |
| `bnbo://dominio/perfis` | JSON | Hierarquia de perfis e visibilidade de PII por perfil |
| `bnbo://dominio/regioes` | JSON | Estados/municípios com BOs cadastrados |

> `regioes` existe como **tool** (`listar_regioes_disponiveis`, invocada pelo
> modelo) **e** como **resource** (navegável pelo host); ambos compartilham a
> mesma leitura (`server/recursos/dominio.consultar_regioes`).

## 💬 Prompt Templates expostos

Atalhos de tarefa invocados pelo usuário (um por tarefa-chave), que orientam o
modelo a chamar a tool certa com os limites de parâmetro e cuidados de PII.
Definidos em `server/prompts/templates.py`.

| Prompt | Argumentos | Tool-alvo |
|---|---|---|
| `analisar_ocorrencias_similares` | `bo_id`/`texto_livre`, `top_k` | `buscar_ocorrencias_similares` (+ razões) |
| `mapear_serie_criminal` | `bo_id`/`texto_livre` | `agrupar_serie_criminal` |
| `detectar_anomalias` | `estado`, `dominio`, `natureza` | `detectar_anomalias_estatisticas` |
| `avaliar_taxa_elucidacao` | `estado`, `delegacia` | `calcular_taxa_elucidacao` |
| `priorizar_delegacias` | `estado` | `listar_delegacias_com_alerta` |
| `gerar_atlas_vulnerabilidade` | `estado`, `meses` | `calcular_indice_vulnerabilidade` / `gerar_atlas_vulnerabilidade` |

## 🔐 Camada de segurança transversal

- **Perfis** (`server/security/perfis.py`): `publico < analista < investigador`.
  O perfil nunca é aceito como parâmetro de tool — é resolvido a partir do
  contexto de autenticação (`server/security/contexto.py`). Por ora, a
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

## ✅ Qualidade

- **Contrato de validação Pydantic** (`server/schemas/`): cada tool tem um
  modelo de **entrada** (`entrada.py`) com as restrições de domínio declaradas
  (faixas numéricas via `Field(ge=…, le=…)`, valores permitidos via `Literal`,
  campos obrigatórios, exigência de `bo_id` OU `texto_livre`) e um modelo de
  **saída** (`saida.py`) que valida e serializa o retorno. A entrada é validada
  pelo decorator `valida_entrada` (`server/tools/_validacao.py`), o mais interno
  da pilha, logo após `coage_numericos` — assim a *assinatura* das tools segue
  aceitando `int | str`/`float | str` (tolerância a número serializado como
  string por LLMs cliente, ver `_coercao.py`) e a faixa é validada depois da
  coerção. A saída é serializada via `model_dump_json()`/`TypeAdapter`, em vez
  de `json.dumps` cru, garantindo que o formato entregue bate com o contrato.
- **Tratamento de erros transversal** (`server/tools/_erros.py`): decorator
  `tratar_erros` aplicado a toda tool, convertendo `pydantic.ValidationError`
  (contrato de entrada) e `ValueError` (validação de domínio — ex.: BO não
  encontrado) e exceções inesperadas em uma resposta JSON `{"erro": "..."}` em
  vez de propagar e quebrar o transporte MCP. Aplicado como decorator externo a
  `valida_entrada`, com `com_auditoria` por fora — a auditoria do acesso ocorre
  mesmo quando a tool falha.
- **Testes unitários sem dependência de infraestrutura**
  (`tests/test_security.py`, `tests/test_stats.py`, `tests/test_atlas.py`,
  `tests/test_erros.py`, `tests/test_validacao.py`): cobrem redação de PII,
  perfis, z-score (`services.stats._calcular_z_scores`), classificação Jenks
  (`services.atlas.classificar_jenks`), o decorator de erros e o contrato de
  validação Pydantic (entrada/saída) — todos executáveis
  com `python3 -m tests.<modulo>` sem Postgres/Redis. Para viabilizar esses
  testes, `services/atlas.py` e `services/stats.py` importam `data.db.get_connection` de
  forma local (dentro das funções que acessam o banco), em vez de no topo do
  módulo.

## 📁 Estrutura do projeto

```
bnbo-mcp-agentic/
├── server/                # === ADAPTADOR: PROTOCOLO MCP ===
│   ├── mcp_server.py      # Entrypoint MCP (STDIO/Streamable HTTP) — registra tools/resources/prompts
│   ├── tools/
│   │   ├── p1_observatorio.py # Tools MCP do P1 (wrappers sobre services.stats)
│   │   ├── p2_linkage.py    # Tools MCP do P2 (wrappers sobre services.linkage)
│   │   ├── p4_atlas.py      # Tools MCP do P4 (wrappers sobre services.atlas)
│   │   ├── util_jobs.py     # Tools transversais de jobs assíncronos
│   │   ├── util_dominio.py  # exportar_resultado, listar_regioes_disponiveis
│   │   ├── _coercao.py      # Coerção numérica (tolera número como string)
│   │   ├── _validacao.py    # Decorator valida_entrada (contrato Pydantic)
│   │   └── _erros.py        # Decorator tratar_erros (ValidationError/ValueError → JSON)
│   ├── schemas/
│   │   ├── entrada.py       # Modelos Pydantic de argumentos das tools
│   │   └── saida.py         # Modelos Pydantic de resposta das tools
│   ├── recursos/
│   │   ├── dominio.py       # Provedores dos Resources (glossário/IVC/perfis/regiões)
│   │   └── conteudo/        # Markdown estático (glossario.md, metodologia_ivc.md)
│   ├── prompts/
│   │   └── templates.py     # Prompt Templates por tarefa
│   └── security/
│       ├── perfis.py        # Perfis publico/analista/investigador
│       ├── contexto.py      # Resolução do perfil a partir do token (placeholder)
│       ├── redacao.py       # Redação de PII em campos de texto livre
│       └── auditoria.py     # Decorator com_auditoria + log em audit_log
├── client/                # === ADAPTADOR: CLIENTES MCP ===
│   ├── stdio/
│   │   └── mcp_client.py   # Cliente MCP oficial (STDIO)
│   ├── http/
│   │   └── mcp_client_http.py # Cliente MCP via Streamable HTTP
│   └── reference/          # OPCIONAL: supervisor LangGraph (deps isoladas), usa a LLM do cliente
│       ├── supervisor.py
│       ├── run_supervisor.py
│       └── requirements.txt
├── services/              # === DOMÍNIO: serviços chamados pelas tools ===
│   ├── embeddings.py      # e5-large + prefixos query:/passage: + cache Redis
│   ├── linkage.py         # Busca vetorial, reranking, explicabilidade, DBSCAN
│   ├── stats.py           # Anomalias estatísticas (z-score) e taxa de elucidação (P1)
│   └── atlas.py           # IVC por hexágono H3, classificação Jenks, GeoJSON (P4)
├── data/                  # === PERSISTÊNCIA ===
│   ├── db.py              # Pool de conexões PostgreSQL/pgvector
│   ├── schema.sql         # Tabelas bo/inquerito/tco/audit_log, índice HNSW
│   └── synthetic.py       # Gerador de BOs sintéticos para dev/teste
├── jobs/                  # === INFRA ASSÍNCRONA ===
│   ├── celery_app.py      # Configuração do Celery (broker/backend Redis) + beat_schedule
│   └── tasks.py           # Tasks reindexar_embeddings, calcular_alertas_noturnos
├── tests/                 # Suíte pytest (test_security, test_stats, test_atlas, test_erros, …)
├── test_client.py         # Harness direto da lógica de domínio (services.linkage)
├── test_tools.py          # Harness das funções *_tool do servidor
├── docs/                  # Documentação técnica (ex.: análise de auth MCP)
├── docker-compose.yml     # PostgreSQL 16 (pgvector) + Redis 7
├── requirements.txt
└── start_server.sh
```

> Nota de simplificação (particionamento): a tabela `bo` é particionada por
> RANGE em `ano` (não pelo composto `(estado, ano)` do modelo completo);
> `estado` fica indexado em vez de particionado. Revisitar em uma
> generalização futura.

> Nota de simplificação (vínculos e perfis): `inquerito` e `tco` já existem no schema e
> se ligam a `bo` por `bo_id`, mas a ETL de matching para os casos em que o
> `bo_id` está ausente (heurística por proximidade temporal/espacial/natureza)
> ainda não foi implementada — fica para uma generalização futura da
> ingestão. A resolução de perfil via token real (JWT/OAuth) também é um
> placeholder, conforme descrito na seção de segurança.

> Nota de simplificação (alertas por polling): o modelo original previa notificação de
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
