# MCP-Powered Agentic RAG Application

Uma aplicação inteligente de Retrieval-Augmented Generation (RAG) que usa o Model Context Protocol (MCP) para decidir automaticamente entre buscar informações em uma base de conhecimento privada ou realizar buscas na web.

## 🎯 Visão Geral

Esta aplicação implementa um agente inteligente que pode:
- **Buscar em base de conhecimento privada**: Usa um banco de dados vetorial (Qdrant) para consultar FAQs sobre Python
- **Buscar na web**: Usa a API Firecrawl para obter informações atualizadas da internet
- **Decidir automaticamente**: O agente escolhe a ferramenta apropriada com base na consulta do usuário

## 🏗️ Arquitetura

```
┌─────────────┐
│   Usuário   │
└──────┬──────┘
       │ Query
       ▼
┌─────────────────┐
│  MCP Cliente    │
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────────────┐
│        MCP Server (Agente)          │
│  ┌───────────────────────────────┐  │
│  │  Decisão Inteligente de Tool  │  │
│  └───────────┬───────────────────┘  │
│              │                      │
│      ┌───────┴────────┐             │
│      ▼                ▼             │
│  ┌────────┐      ┌─────────┐        │
│  │Vector  │      │   Web   │        │
│  │DB Tool │      │Search   │        │
│  └────┬───┘      └────┬────┘        │
└───────┼───────────────┼─────────────┘
        │               │
        ▼               ▼
   ┌─────────┐    ┌──────────┐
   │ Qdrant  │    │Firecrawl │
   │  (FAQ)  │    │   API    │
   └─────────┘    └──────────┘
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- Docker e Docker Compose
- Chave API do Firecrawl (obtenha em [firecrawl.dev](https://www.firecrawl.dev/))

### Passo a Passo

1. **Clone ou navegue até o diretório do projeto**
   ```bash
   cd /home/seaddados/projetos/mcp-agentic-rag
   ```

2. **Configure as variáveis de ambiente**
   ```bash
   # Edite o arquivo .env e adicione sua chave API
   nano .env
   ```
   
   Adicione:
   ```
   FIRECRAWL_API_KEY=sua_chave_api_aqui
   ```

3. **Inicie o Qdrant (banco de dados vetorial)**
   ```bash
   docker-compose up -d
   ```
   
   Verifique se está rodando:
   ```bash
   curl http://localhost:6334/
   ```

4. **Crie um ambiente virtual e instale as dependências**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Linux/Mac
   # ou
   # venv\Scripts\activate  # No Windows
   
   pip install -r requirements.txt
   ```

## 🚀 Como Usar

### Método 1: Cliente MCP Oficial (⭐ Recomendado para Produção)

```bash
cd /home/seaddados/projetos/mcp-agentic-rag
source venv/bin/activate

# Terminal 1 - Servidor
python3 mcp_server.py

# Terminal 2 - Cliente
python3 mcp_client.py
```

**Vantagens:**
- ✅ Usa protocolo MCP oficial
- ✅ Comunicação STDIO nativa
- ✅ Lista ferramentas automaticamente
- ✅ Testa todas as 3 ferramentas (FAQ, Web Search, Shell)

### Método 2: Testes Diretos (🔧 Recomendado para Desenvolvimento)

```bash
python3 test_tools.py
```

**Vantagens:**
- ✅ Mais rápido
- ✅ Não precisa de servidor
- ✅ Testa lógica diretamente
- ✅ Ideal para debug

### 🔧 Configuração de Transport

O servidor suporta dois modos de transporte:

#### STDIO (Padrão)
```bash
python3 mcp_server.py
# Usa STDIO para clientes MCP oficiais
```

#### SSE (HTTP)
```bash
MCP_TRANSPORT=sse python3 mcp_server.py
# Usa SSE para testes HTTP

# Em outro terminal
python3 mcp_client_http.py
```

### Saída do Servidor

**Modo STDIO:**
```
============================================================
MCP AGENTIC RAG APPLICATION
============================================================

Initializing FAQ Engine and setting up Qdrant collection...
Embedding model loaded. Vector dimension: 384
Connected to Qdrant.

============================================================
Starting MCP server
============================================================

Available Tools:
  1. python_faq_retrieval_tool - Search Python FAQ knowledge base
  2. firecrawl_web_search_tool - Search the web for information
  3. execute_shell_command - Execute shell commands

✓ Transport: STDIO
Server is ready to accept STDIO connections!
```

**Modo HTTP/SSE:**
```
✓ Transport: SSE (HTTP)
✓ Server URL: http://127.0.0.1:8080/sse
Server is ready to accept HTTP connections!
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

## 🎯 Diferenças Entre os Clientes

| Cliente | Protocolo | SDK | Uso | Vantagem |
|---------|-----------|-----|-----|----------|
| **mcp_client.py** ⭐ | MCP via STDIO | MCP Python SDK oficial | Produção, integração real | Protocolo nativo, robusto |
| **mcp_client_http.py** 🌐 | HTTP/SSE | MCP Python SDK (SSE) | Testes, debugging | Fácil inspeção HTTP |
| **test_tools.py** 🔧 | Import direto | Nenhum | Desenvolvimento rápido | Simples, sem overhead |
| **test_client.py** ⚠️ | HTTP/SSE (legado) | Requests | Não recomendado | Protocolo SSE complexo |

## 📁 Estrutura do Projeto

```
mcp-agentic-rag/
├── mcp_server.py          # Servidor MCP (STDIO/SSE)
├── mcp_client.py          # ⭐ Cliente MCP oficial (STDIO)
├── mcp_client_http.py     # 🌐 Cliente MCP HTTP (SSE)
├── rag_app.py             # Pipeline RAG com Qdrant
├── test_tools.py          # Testes diretos das ferramentas
├── test_client.py         # Cliente HTTP legado
├── .env                   # Variáveis de ambiente
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Qdrant
├── README.md              # Esta documentação
├── TROUBLESHOOTING.md     # Guia de resolução de problemas
└── start_server.sh        # Script de inicialização
```

**Exemplo 1: Consulta sobre Python (usa Vector DB)**
```bash
curl -X POST http://127.0.0.1:8080/mcp \
-H "Content-Type: application/json" \
-d '{
  "messages": [
    {
      "role": "user",
      "content": "Can you explain list comprehensions in Python?"
    }
  ]
}'
```

**Exemplo 2: Consulta geral (usa Web Search)**
```bash
curl -X POST http://127.0.0.1:8080/mcp \
-H "Content-Type: application/json" \
-d '{
  "messages": [
    {
      "role": "user",
      "content": "What is the new Polars DataFrame library?"
    }
  ]
}'
```

## 🛠️ Componentes

### 1. RAG Pipeline (`rag_app.py`)

- **FAQEngine**: Classe principal para embeddings e busca vetorial
- **PYTHON_FAQ_TEXT**: Base de conhecimento com FAQs sobre Python
- **batch_generator**: Processamento eficiente em lotes

### 2. MCP Server (`mcp_server.py`)

Servidor que implementa três ferramentas MCP:

- **python_faq_retrieval_tool**: Busca na base de conhecimento privada (Qdrant)
- **firecrawl_web_search_tool**: Busca informações na web via Firecrawl API
- **execute_shell_command**: Executa comandos shell no workspace

**Suporte a múltiplos transportes:**
- **STDIO** (padrão): Para integração com clientes MCP oficiais
- **HTTP/SSE**: Para testes e debugging via HTTP

### 3. MCP Clients

#### `mcp_client.py` - Cliente STDIO

Cliente oficial usando transporte STDIO. Inclui:
- `call_tool()`: Função genérica para ferramentas com parâmetro `query`
- `call_tool_cmd()`: Função especializada para `execute_shell_command` (usa parâmetro `cmd`)
- `list_available_tools()`: Lista todas as ferramentas disponíveis

#### `mcp_client_http.py` - Cliente HTTP/SSE

Cliente HTTP usando Server-Sent Events. Mesmas funcionalidades do cliente STDIO, mas via HTTP.

**Exemplo de uso da função `call_tool_cmd`:**
```python
# Para ferramentas que usam 'query' (FAQ e Web Search)
await call_tool(session, "python_faq_retrieval_tool", "What are decorators?")

# Para ferramentas que usam 'cmd' (Shell Commands)
await call_tool_cmd(session, "execute_shell_command", "ls -la")
```

## 🔧 Configuração

### Variáveis de Ambiente (`.env`)

```bash
# Obrigatório para busca web
FIRECRAWL_API_KEY=sua_chave_aqui

# Opcional (para futuras melhorias)
OPENAI_API_KEY=sk-...
```

### Configurações do Servidor (`mcp_server.py`)

```python
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "python_faq_collection"
HOST = "127.0.0.1"
PORT = 8080
```

## 📊 Interface Web do Qdrant

Acesse o dashboard do Qdrant em: http://localhost:6334/

Aqui você pode:
- Visualizar coleções
- Inspecionar vetores
- Monitorar o desempenho

## 🧪 Testes

Ambos os clientes (`mcp_client.py` e `mcp_client_http.py`) incluem 5 casos de teste:

1. **List Comprehensions** → Python FAQ Tool (Vector DB)
2. **Python Decorators** → Python FAQ Tool (Vector DB)
3. **== vs is** → Python FAQ Tool (Vector DB)
4. **Polars Library** → Web Search Tool
5. **List files (ls -la)** → Shell Command Tool

**Executar testes:**
```bash
# Modo STDIO
python mcp_client.py

# Modo HTTP/SSE (requer servidor em modo SSE)
python mcp_client_http.py
```

## 🐛 Troubleshooting

### Erro: "FIRECRAWL_API_KEY environment variable is not set"
- Verifique se o arquivo `.env` existe e contém a chave API
- Certifique-se de que o arquivo está no mesmo diretório que `mcp_server.py`

### Erro: "Error connecting to Qdrant"
- Verifique se o Docker está rodando: `docker ps`
- Inicie o Qdrant: `docker-compose up -d`
- Verifique os logs: `docker-compose logs qdrant`

### Modelo de embedding demora para carregar
- Na primeira execução, o modelo (~500MB) será baixado
- Execuções subsequentes serão mais rápidas (modelo em cache)

## 📚 Recursos Adicionais

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Firecrawl API](https://www.firecrawl.dev/)
- [LlamaIndex](https://docs.llamaindex.ai/)

## ✨ Melhorias Implementadas

Durante o desenvolvimento, os seguintes problemas foram resolvidos:

| Problema | Solução |
|----------|---------|
| ⏱️ Timeout HuggingFace | Modelo menor (384 dim) `all-MiniLM-L6-v2` |
| 🔢 Vector dimension mismatch | Coleção Qdrant recriada com dimensão correta |
| ⚠️ Qdrant API deprecated | Atualizado com fallback para compatibilidade |
| 🔌 Transport incompatível | STDIO + SSE suportados simultaneamente |
| ❌ Cliente HTTP falho | Cliente MCP oficial criado com SDK ✅ |
| 🛠️ Shell commands | Nova ferramenta `execute_shell_command` adicionada |

## 🎓 Próximos Passos Sugeridos

### 1. Adicionar Mais FAQs

```bash
# Edite PYTHON_FAQ_TEXT em rag_app.py
# Execute para recriar a coleção:
python3 -c "from rag_app import FAQEngine, PYTHON_FAQ_TEXT; \
            engine = FAQEngine('http://localhost:6333', 'python_faq_collection'); \
            engine.setup_collection(PYTHON_FAQ_TEXT)"
```

### 2. Integrar com Claude Desktop

Adicione ao arquivo de configuração do Claude Desktop:

```json
{
  "mcpServers": {
    "python-faq": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "cwd": "/home/seaddados/projetos/mcp-agentic-rag",
      "env": {
        "FIRECRAWL_API_KEY": "sua_chave_aqui"
      }
    }
  }
}
```

### 3. Adicionar Novas Ferramentas MCP

Exemplo de como criar uma nova ferramenta:

```python
@mcp_server.tool()
def nova_ferramenta(parametro: str) -> str:
    """
    Descrição detalhada da ferramenta.
    Use esta ferramenta quando...
    
    Args:
        parametro: Descrição do parâmetro
        
    Returns:
        Resultado da operação
    """
    # Implementação
    resultado = processar(parametro)
    return resultado
```

### 4. Expandir Base de Conhecimento

- Adicionar documentação de outras linguagens (JavaScript, Go, Rust)
- Incluir best practices e design patterns
- Adicionar troubleshooting guides específicos

### 5. Melhorar Busca Web

- Implementar cache de resultados
- Adicionar mais fontes de busca (DuckDuckGo, Brave Search)
- Filtrar resultados por relevância

## 🤝 Contribuindo

Sinta-se à vontade para:
- Adicionar mais FAQs à base de conhecimento
- Implementar novas ferramentas MCP
- Melhorar a lógica de seleção de ferramentas
- Adicionar testes adicionais

## 📝 Licença

Este projeto é baseado no artigo "Building MCP-Powered Agentic RAG Application" de Youssef Hosni.

---

**Desenvolvido com ❤️ usando Model Context Protocol**
