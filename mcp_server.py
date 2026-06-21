"""
MCP Server Module
Servidor MCP do domínio de segurança pública (BOs) — Fatias 0-2: fundação +
P2 Linkage Criminal + camada de segurança transversal (perfis/PII/auditoria).

O servidor expõe apenas tools (sem LLM embarcada); o raciocínio/roteamento
fica no cliente, conforme o princípio de desacoplamento de modelo.
"""

import os
import sys

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
from server.tools.util_dominio import (
    exportar_resultado_tool,
    listar_regioes_disponiveis_tool,
)
from server.tools.p1_observatorio import (
    detectar_anomalias_estatisticas_tool,
    calcular_taxa_elucidacao_tool,
    listar_delegacias_com_alerta_tool,
    subscrever_alertas_tool,
)
from server.tools.p4_atlas import (
    calcular_indice_vulnerabilidade_tool,
    gerar_atlas_vulnerabilidade_tool,
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
mcp_server.tool(name="exportar_resultado")(exportar_resultado_tool)
mcp_server.tool(name="listar_regioes_disponiveis")(listar_regioes_disponiveis_tool)
mcp_server.tool(name="detectar_anomalias_estatisticas")(detectar_anomalias_estatisticas_tool)
mcp_server.tool(name="calcular_taxa_elucidacao")(calcular_taxa_elucidacao_tool)
mcp_server.tool(name="listar_delegacias_com_alerta")(listar_delegacias_com_alerta_tool)
mcp_server.tool(name="subscrever_alertas")(subscrever_alertas_tool)
mcp_server.tool(name="calcular_indice_vulnerabilidade")(calcular_indice_vulnerabilidade_tool)
mcp_server.tool(name="gerar_atlas_vulnerabilidade")(gerar_atlas_vulnerabilidade_tool)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    # IMPORTANTE: no transporte STDIO o stdout E o canal JSON-RPC. Qualquer texto
    # impresso em stdout corrompe o protocolo (o cliente tenta parsear como JSON).
    # Por isso o banner vai todo para stderr via `log()`.
    def log(msg: str = "") -> None:
        print(msg, file=sys.stderr)

    log("=" * 60)
    log("MCP BNBO - SEGURANCA PUBLICA (P2 LINKAGE CRIMINAL)")
    log("=" * 60)
    log("\nTools registradas:")
    log("  1. buscar_ocorrencias_similares")
    log("  2. obter_razoes_similaridade")
    log("  3. agrupar_serie_criminal")
    log("  4. reindexar_embeddings (assincrona, Celery; requer perfil analista+)")
    log("  5. consultar_job_status")
    log("  6. exportar_resultado (csv/json/geojson)")
    log("  7. listar_regioes_disponiveis")
    log("  8. detectar_anomalias_estatisticas (P1)")
    log("  9. calcular_taxa_elucidacao (P1)")
    log(" 10. listar_delegacias_com_alerta (P1)")
    log(" 11. subscrever_alertas (P1, polling de snapshot noturno)")
    log(" 12. calcular_indice_vulnerabilidade (P4)")
    log(" 13. gerar_atlas_vulnerabilidade (P4, GeoJSON por hexágono H3)")

    if transport == "sse":
        log(f"\nTransport: SSE (HTTP) em http://{HOST}:{PORT}/sse")
    else:
        log("\nTransport: STDIO")

    log("Press CTRL+C to stop the server.\n")
    mcp_server.run(transport)
