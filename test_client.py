"""
Cliente de teste simples — chama as funções de services.linkage diretamente
(sem passar pelo transporte MCP), para validar a lógica do slice P2.
"""

import json

from services import linkage


def test_buscar_similares():
    print("\n" + "=" * 70)
    print("TEST 1: buscar_ocorrencias_similares (texto_livre)")
    print("=" * 70)
    resultados = linkage.buscar_ocorrencias_similares(
        texto_livre="roubo de celular com uso de faca em via pública", top_k=5
    )
    print(json.dumps(resultados, indent=2, ensure_ascii=False, default=str)[:1500])
    assert isinstance(resultados, list)
    print("\n✓ SUCCESS")


def test_agrupar_serie_criminal():
    print("\n" + "=" * 70)
    print("TEST 2: agrupar_serie_criminal (texto_livre)")
    print("=" * 70)
    resultado = linkage.agrupar_serie_criminal(
        texto_livre="furto de bicicleta em via pública", top_k=20
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str)[:1500])
    assert "clusters" in resultado and "ruido" in resultado
    print("\n✓ SUCCESS")


def main():
    print("\n" + "=" * 70)
    print("MCP BNBO - TESTE DIRETO (services.linkage)")
    print("=" * 70)
    print("\nPré-requisito: docker compose up -d e base populada com data/synthetic.py\n")

    test_buscar_similares()
    test_agrupar_serie_criminal()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
