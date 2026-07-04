"""
Cliente de referência opcional: supervisor LangGraph sobre o MCP Server.

Princípio preservado do modelo (§3.1): o MCP Server só expõe tools — todo o
raciocínio/roteamento acontece aqui, no cliente, usando a LLM que o cliente
escolher (model-agnostic via `init_chat_model`). O servidor nunca embarca LLM.

`MultiServerMCPClient` (langchain-mcp-adapters) carrega as tools do MCP
Server via Streamable HTTP e as converte em `BaseTool` do LangChain. Um supervisor
(`langgraph-supervisor`) roteia para um sub-agente por projeto — nesta fatia,
apenas o sub-agente do P2 (Linkage Criminal). O supervisor só roteia; as
tools rodam no servidor via MCP.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph_supervisor import create_supervisor

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8080/mcp")
CLIENT_MODEL = os.getenv("MCP_CLIENT_MODEL", "anthropic:claude-sonnet-4-6")

# Tools do P2 expostas pelo servidor (server/tools/p2_linkage.py).
P2_TOOL_NAMES = {
    "buscar_ocorrencias_similares",
    "obter_razoes_similaridade",
    "agrupar_serie_criminal",
}

# Tools do P1 Observatório (server/tools/p1_observatorio.py).
P1_TOOL_NAMES = {
    "detectar_anomalias_estatisticas",
    "calcular_taxa_elucidacao",
    "listar_delegacias_com_alerta",
    "subscrever_alertas",
}

# Tools do P4 Atlas de Vulnerabilidade (server/tools/p4_atlas.py).
P4_TOOL_NAMES = {
    "calcular_indice_vulnerabilidade",
    "gerar_atlas_vulnerabilidade",
}

P2_AGENT_PROMPT = (
    "Você é o agente especialista em Linkage Criminal (P2). Use as tools "
    "disponíveis para buscar ocorrências similares, explicar por que dois "
    "BOs foram vinculados, ou agrupar uma possível série criminal. "
    "Responda de forma objetiva, citando bo_id e scores quando relevante."
)

P1_AGENT_PROMPT = (
    "Você é o agente especialista no Observatório (P1). Use as tools "
    "disponíveis para detectar anomalias estatísticas (volume de BOs com "
    "z-score acima do limiar), calcular a taxa de elucidação, listar "
    "delegacias com alerta ou subscrever alertas do snapshot noturno. "
    "Responda de forma objetiva, citando município/delegacia, natureza e "
    "os valores (z-score, taxa) quando relevante."
)

P4_AGENT_PROMPT = (
    "Você é o agente especialista no Atlas de Vulnerabilidade (P4). Use as "
    "tools disponíveis para calcular o Índice de Vulnerabilidade Criminal "
    "(IVC) por hexágono H3 ou gerar o atlas em GeoJSON com a classificação "
    "Jenks. Responda de forma objetiva, citando hex_id, IVC e a classe de "
    "vulnerabilidade quando relevante."
)

SUPERVISOR_PROMPT = (
    "Você é o supervisor da plataforma de inteligência em segurança "
    "pública. Roteie cada pedido do usuário para o sub-agente apropriado, "
    "sem nunca executar tools diretamente — delegue sempre.\n"
    "- Linkage Criminal (P2): ocorrências similares, vínculos entre BOs, "
    "séries criminais.\n"
    "- Observatório (P1): anomalias estatísticas, taxa de elucidação, "
    "delegacias com alerta, subscrição de alertas.\n"
    "- Atlas de Vulnerabilidade (P4): Índice de Vulnerabilidade Criminal "
    "(IVC) por hexágono H3, mapa/atlas em GeoJSON."
)


async def build_supervisor():
    """
    Conecta ao MCP Server, carrega as tools e monta o supervisor LangGraph
    com um sub-agente por projeto: P2 (Linkage Criminal), P1 (Observatório)
    e P4 (Atlas de Vulnerabilidade).

    Para adicionar um novo projeto, basta filtrar `all_tools` por nome (como
    nos conjuntos `P*_TOOL_NAMES`), criar mais um `create_agent` com seu
    `system_prompt` e incluí-lo na lista passada a `create_supervisor`.
    """
    client = MultiServerMCPClient(
        {
            "bnbo": {
                "url": MCP_SERVER_URL,
                "transport": "streamable_http",
            }
        }
    )
    all_tools = await client.get_tools()
    p2_tools = [t for t in all_tools if t.name in P2_TOOL_NAMES]
    p1_tools = [t for t in all_tools if t.name in P1_TOOL_NAMES]
    p4_tools = [t for t in all_tools if t.name in P4_TOOL_NAMES]

    model = init_chat_model(CLIENT_MODEL)

    p2_agent = create_agent(
        model,
        tools=p2_tools,
        name="p2_linkage_agent",
        system_prompt=P2_AGENT_PROMPT,
    )

    p1_agent = create_agent(
        model,
        tools=p1_tools,
        name="p1_observatorio_agent",
        system_prompt=P1_AGENT_PROMPT,
    )

    p4_agent = create_agent(
        model,
        tools=p4_tools,
        name="p4_atlas_agent",
        system_prompt=P4_AGENT_PROMPT,
    )

    supervisor = create_supervisor(
        agents=[p2_agent, p1_agent, p4_agent],
        model=model,
        prompt=SUPERVISOR_PROMPT,
    ).compile()

    return supervisor
