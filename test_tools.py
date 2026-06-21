"""
Suíte de testes das tools do servidor MCP — chama as funções `*_tool`
diretamente (sem o transporte MCP), para validar contrato e formato JSON.
"""

import json
import os

import requests

from server.tools.p2_linkage import (
    buscar_ocorrencias_similares_tool,
    obter_razoes_similaridade_tool,
    agrupar_serie_criminal_tool,
)
from server.tools.util_jobs import (
    reindexar_embeddings_tool,
    consultar_job_status_tool,
)


def test_server_health():
    print("\n" + "=" * 70)
    print("TEST 0: MCP SERVER HEALTH CHECK")
    print("=" * 70)
    try:
        response = requests.get("http://127.0.0.1:8080/sse", timeout=5)
        if response.status_code == 200:
            print("\n✓ MCP Server is RUNNING on port 8080")
        else:
            print(f"\n⚠ Server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n✗ MCP Server is NOT running")
        print("  Start it with: MCP_TRANSPORT=sse python3 mcp_server.py")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    print("=" * 70)


def test_buscar_ocorrencias_similares_tool():
    print("\n" + "=" * 70)
    print("TEST 1: buscar_ocorrencias_similares_tool")
    print("=" * 70)
    resultado_json = buscar_ocorrencias_similares_tool(
        texto_livre="roubo de celular com uso de faca em via pública", top_k=5
    )
    resultado = json.loads(resultado_json)
    assert isinstance(resultado, list)
    print(json.dumps(resultado, indent=2, ensure_ascii=False)[:1000])
    print("\n✓ SUCCESS")
    return resultado


def test_obter_razoes_similaridade_tool(bo_id_a: str, bo_id_b: str):
    print("\n" + "=" * 70)
    print("TEST 2: obter_razoes_similaridade_tool")
    print("=" * 70)
    resultado_json = obter_razoes_similaridade_tool(bo_id_a, bo_id_b)
    resultado = json.loads(resultado_json)
    assert "score_final" in resultado
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    print("\n✓ SUCCESS")


def test_agrupar_serie_criminal_tool():
    print("\n" + "=" * 70)
    print("TEST 3: agrupar_serie_criminal_tool")
    print("=" * 70)
    resultado_json = agrupar_serie_criminal_tool(
        texto_livre="furto de bicicleta em via pública", top_k=20
    )
    resultado = json.loads(resultado_json)
    assert "clusters" in resultado
    print(json.dumps(resultado, indent=2, ensure_ascii=False)[:1000])
    print("\n✓ SUCCESS")


def test_jobs_async():
    print("\n" + "=" * 70)
    print("TEST 4: reindexar_embeddings_tool + consultar_job_status_tool")
    print("=" * 70)
    # reindexar_embeddings exige perfil analista+. O perfil NUNCA e parametro de
    # tool; vem do token (placeholder: env MCP_PERFIL_ATUAL). Aqui simulamos um
    # token de analista para exercitar o caminho privilegiado.
    os.environ["MCP_PERFIL_ATUAL"] = "analista"
    disparo = json.loads(reindexar_embeddings_tool(batch_size=50))
    print(f"Job disparado: {disparo}")
    assert "job_id" in disparo, f"esperado job_id, veio: {disparo}"
    status = json.loads(consultar_job_status_tool(disparo["job_id"]))
    print(f"Status inicial: {status}")
    assert "estado" in status
    print("\n✓ SUCCESS")


def main():
    print("\n" + "=" * 70)
    print("MCP BNBO - SUITE DE TESTES DAS TOOLS (P2 LINKAGE CRIMINAL)")
    print("=" * 70)

    test_server_health()
    candidatos = test_buscar_ocorrencias_similares_tool()
    if len(candidatos) >= 2:
        test_obter_razoes_similaridade_tool(candidatos[0]["bo_id"], candidatos[1]["bo_id"])
    test_agrupar_serie_criminal_tool()
    test_jobs_async()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
