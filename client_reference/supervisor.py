"""
Cliente de referência opcional: supervisor LangGraph sobre o MCP Server.

Princípio preservado do modelo (§3.1): o MCP Server só expõe tools — todo o
raciocínio/roteamento acontece aqui, no cliente, usando a LLM que o cliente
escolher (model-agnostic via `init_chat_model`). O servidor nunca embarca LLM.

`MultiServerMCPClient` (langchain-mcp-adapters) carrega as tools do MCP
Server via SSE/HTTP e as converte em `BaseTool` do LangChain. Um supervisor
(`langgraph-supervisor`) roteia para um sub-agente por projeto — nesta fatia,
apenas o sub-agente do P2 (Linkage Criminal). O supervisor só roteia; as
tools rodam no servidor via MCP.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8080/sse")
CLIENT_MODEL = os.getenv("MCP_CLIENT_MODEL", "anthropic:claude-sonnet-4-6")

# Tools do P2 expostas pelo servidor (server/tools/p2_linkage.py).
P2_TOOL_NAMES = {
    "buscar_ocorrencias_similares",
    "obter_razoes_similaridade",
    "agrupar_serie_criminal",
}

P2_AGENT_PROMPT = (
    "Você é o agente especialista em Linkage Criminal (P2). Use as tools "
    "disponíveis para buscar ocorrências similares, explicar por que dois "
    "BOs foram vinculados, ou agrupar uma possível série criminal. "
    "Responda de forma objetiva, citando bo_id e scores quando relevante."
)

SUPERVISOR_PROMPT = (
    "Você é o supervisor da plataforma de inteligência em segurança "
    "pública. Roteie cada pedido do usuário para o sub-agente apropriado. "
    "Nesta fatia, apenas o agente de Linkage Criminal (P2) está disponível: "
    "use-o para qualquer pergunta sobre ocorrências similares, vínculos "
    "entre BOs ou séries criminais. Você nunca executa tools diretamente; "
    "delegue sempre ao sub-agente."
)


async def build_supervisor():
    """
    Conecta ao MCP Server, carrega as tools do P2 e monta o supervisor
    LangGraph com um único sub-agente (P2 Linkage Criminal).

    Ao adicionar as tools do P1 (Observatório) e P4 (Atlas) nas próximas
    fatias, basta filtrar `all_tools` por nome (como feito para o P2) e
    criar um `create_react_agent` adicional para cada um, passando a lista
    de agentes para `create_supervisor`.
    """
    client = MultiServerMCPClient(
        {
            "bnbo": {
                "url": MCP_SERVER_URL,
                "transport": "sse",
            }
        }
    )
    all_tools = await client.get_tools()
    p2_tools = [t for t in all_tools if t.name in P2_TOOL_NAMES]

    model = init_chat_model(CLIENT_MODEL)

    p2_agent = create_react_agent(
        model,
        tools=p2_tools,
        name="p2_linkage_agent",
        prompt=P2_AGENT_PROMPT,
    )

    supervisor = create_supervisor(
        agents=[p2_agent],
        model=model,
        prompt=SUPERVISOR_PROMPT,
    ).compile()

    return supervisor
