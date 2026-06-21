"""
MCP Server Module
Servidor MCP do domínio de segurança pública (BOs) — Fatia 1: P2 Linkage Criminal.

O servidor expõe apenas tools (sem LLM embarcada); o raciocínio/roteamento
fica no cliente, conforme o princípio de desacoplamento de modelo.
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.tools.p2_linkage import (
    buscar_ocorrencias_similares_tool,
    obter_razoes_similaridade_tool,
    agrupar_serie_criminal_tool,
)
from server.tools.util_jobs import (
    reindexar_embeddings_tool,
    consultar_job_status_tool,
)

load_dotenv()

HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8080"))

mcp_server = FastMCP("MCP-BNBO-Seguranca-Publica", host=HOST, port=PORT)

mcp_server.tool(name="buscar_ocorrencias_similares")(buscar_ocorrencias_similares_tool)
mcp_server.tool(name="obter_razoes_similaridade")(obter_razoes_similaridade_tool)
mcp_server.tool(name="agrupar_serie_criminal")(agrupar_serie_criminal_tool)
mcp_server.tool(name="reindexar_embeddings")(reindexar_embeddings_tool)
mcp_server.tool(name="consultar_job_status")(consultar_job_status_tool)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    print("=" * 60)
    print("MCP BNBO - SEGURANCA PUBLICA (P2 LINKAGE CRIMINAL)")
    print("=" * 60)
    print("\nTools registradas:")
    print("  1. buscar_ocorrencias_similares")
    print("  2. obter_razoes_similaridade")
    print("  3. agrupar_serie_criminal")
    print("  4. reindexar_embeddings (assincrona, Celery)")
    print("  5. consultar_job_status")

    if transport == "sse":
        print(f"\nTransport: SSE (HTTP) em http://{HOST}:{PORT}/sse")
    else:
        print("\nTransport: STDIO")

    print("Press CTRL+C to stop the server.\n")
    mcp_server.run(transport)
