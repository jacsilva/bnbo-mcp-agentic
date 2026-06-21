# Cliente de Referência — Supervisor LangGraph (opcional)

Demonstra como orquestrar as tools do MCP Server usando um supervisor
LangGraph do lado do **cliente**, com a LLM escolhida pelo próprio cliente.
O servidor MCP permanece puro (sem LLM); este pacote só consome as tools via
MCP/SSE — não é importado pelo servidor e tem dependências isoladas.

## Por que isso existe

O modelo prevê que o servidor MCP nunca incorpore um LLM (evita lock-in de
modelo). Mas a LLM do cliente pode interpretar mal os schemas das tools. Este
cliente de referência entrega uma orquestração testada — supervisor →
sub-agente por projeto → tools via MCP — sem impor qual modelo usar.

## Instalação (isolada do servidor)

```bash
cd client_reference
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install langchain-anthropic   # ou langchain-openai, etc., conforme MCP_CLIENT_MODEL
```

## Configuração

No `.env` (raiz do projeto) ou variáveis de ambiente:

```bash
MCP_SERVER_URL=http://127.0.0.1:8080/sse
MCP_CLIENT_MODEL=anthropic:claude-sonnet-4-6   # qualquer modelo suportado por init_chat_model
ANTHROPIC_API_KEY=...                          # ou a chave do provedor escolhido
```

## Uso

```bash
# Terminal 1 — servidor MCP (raiz do projeto)
MCP_TRANSPORT=sse python3 mcp_server.py

# Terminal 2 — supervisor
python3 -m client_reference.run_supervisor "Busque ocorrências similares a roubo de celular com faca"
```

## Estrutura

- `supervisor.py` — monta o `MultiServerMCPClient`, filtra as tools do P2,
  cria o sub-agente `p2_linkage_agent` e o supervisor.
- `run_supervisor.py` — CLI de exemplo.

## Expandindo para P1/P4

Quando as tools de Observatório (P1) e Atlas (P4) forem registradas no
servidor (Fatias 3 e 4), adicione em `supervisor.py`:

1. Um novo conjunto `P1_TOOL_NAMES` / `P4_TOOL_NAMES`.
2. Um `create_react_agent` por projeto, com seu próprio prompt.
3. Inclua os novos agentes na lista passada a `create_supervisor`.

Trocar a LLM do cliente (`MCP_CLIENT_MODEL`) não exige nenhuma mudança no
servidor — é a validação central deste padrão de desacoplamento.
