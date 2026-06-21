"""
Atlas de Vulnerabilidade (P4) — agregação por hexágono H3, cálculo do Índice
de Vulnerabilidade Criminal (IVC) e classificação em faixas (Jenks natural
breaks), exportável como GeoJSON.
"""

from typing import Any

import h3

# Peso por domínio na composição do IVC: crimes contra a pessoa pesam mais
# que crimes patrimoniais na percepção de vulnerabilidade.
PESO_DOMINIO = {
    "pessoa": 2.0,
    "patrimonio": 1.0,
}


def _agregar_por_hexagono(estado: str | None, meses: int | None) -> list[dict[str, Any]]:
    from data.db import get_connection

    filtros = ["hex_id_res8 IS NOT NULL"]
    params: list[Any] = []
    if estado:
        filtros.append("estado = %s")
        params.append(estado)
    if meses:
        filtros.append("data_hora >= now() - (%s || ' months')::interval")
        params.append(meses)
    where = f"WHERE {' AND '.join(filtros)}"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT hex_id_res8, estado, municipio, dominio, count(*) AS total
                FROM bo
                {where}
                GROUP BY hex_id_res8, estado, municipio, dominio
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def calcular_indice_vulnerabilidade(estado: str | None = None, meses: int | None = None) -> list[dict[str, Any]]:
    """Calcula o IVC por hexágono H3 (resolução 8): soma ponderada de ocorrências
    por domínio, normalizada pelo hexágono de maior incidência (0 a 1)."""
    linhas = _agregar_por_hexagono(estado, meses)

    por_hexagono: dict[str, dict[str, Any]] = {}
    for linha in linhas:
        hex_id = linha["hex_id_res8"]
        entrada = por_hexagono.setdefault(hex_id, {
            "hex_id": hex_id,
            "estado": linha["estado"],
            "municipio": linha["municipio"],
            "total_ocorrencias": 0,
            "score_bruto": 0.0,
        })
        peso = PESO_DOMINIO.get(linha["dominio"], 1.0)
        entrada["total_ocorrencias"] += linha["total"]
        entrada["score_bruto"] += linha["total"] * peso

    if not por_hexagono:
        return []

    maximo = max(e["score_bruto"] for e in por_hexagono.values()) or 1.0
    resultado = []
    for entrada in por_hexagono.values():
        entrada["ivc"] = round(entrada["score_bruto"] / maximo, 4)
        del entrada["score_bruto"]
        resultado.append(entrada)

    resultado.sort(key=lambda e: e["ivc"], reverse=True)
    return resultado


def classificar_jenks(valores: list[float], n_classes: int = 5) -> list[float]:
    """Calcula os pontos de corte (breaks) de Jenks natural breaks para `valores`.

    Retorna uma lista de `n_classes + 1` limites (do mínimo ao máximo) que
    minimizam a variância intra-classe — algoritmo de Fisher-Jenks clássico.
    """
    dados = sorted(valores)
    n = len(dados)
    if n == 0:
        return []
    n_classes = min(n_classes, n)
    if n_classes <= 1:
        return [dados[0], dados[-1]]

    # matriz[i][j] = soma de quadrados dos desvios do melhor agrupamento dos
    # primeiros i valores em j classes; rastro[i][j] = índice de início da
    # última classe nessa solução.
    matriz_variancia = [[float("inf")] * (n_classes + 1) for _ in range(n + 1)]
    matriz_indice = [[0] * (n_classes + 1) for _ in range(n + 1)]
    matriz_variancia[0][0] = 0.0

    for i in range(1, n + 1):
        soma = soma_quadrados = 0.0
        for j in range(1, i + 1):
            valor = dados[i - j]
            soma += valor
            soma_quadrados += valor * valor
            variancia = soma_quadrados - (soma * soma) / j
            k = i - j
            if k != 0:
                for classe in range(1, n_classes + 1):
                    if matriz_variancia[k][classe - 1] != float("inf") and (
                        matriz_variancia[i][classe] == float("inf")
                        or matriz_variancia[k][classe - 1] + variancia < matriz_variancia[i][classe]
                    ):
                        matriz_variancia[i][classe] = matriz_variancia[k][classe - 1] + variancia
                        matriz_indice[i][classe] = k
            elif j == i:
                if variancia < matriz_variancia[i][1]:
                    matriz_variancia[i][1] = variancia
                    matriz_indice[i][1] = 0

    cortes = [0] * (n_classes + 1)
    cortes[n_classes] = n - 1
    k = n
    for classe in range(n_classes, 0, -1):
        origem = matriz_indice[k][classe]
        cortes[classe - 1] = origem
        k = origem

    breaks = [dados[0]] + [dados[c] for c in cortes[1:]]
    return breaks


def _classe_para_valor(valor: float, breaks: list[float]) -> int:
    for classe in range(len(breaks) - 1, 0, -1):
        if valor >= breaks[classe - 1]:
            return classe
    return 1


def gerar_atlas_geojson(estado: str | None = None, meses: int | None = None, n_classes: int = 5) -> dict[str, Any]:
    """Gera um FeatureCollection GeoJSON com um polígono por hexágono H3,
    contendo o IVC e a classe Jenks (1=menor vulnerabilidade, n_classes=maior)."""
    hexagonos = calcular_indice_vulnerabilidade(estado=estado, meses=meses)
    if not hexagonos:
        return {"type": "FeatureCollection", "features": []}

    breaks = classificar_jenks([h["ivc"] for h in hexagonos], n_classes=n_classes)

    features = []
    for hexagono in hexagonos:
        boundary = h3.h3_to_geo_boundary(hexagono["hex_id"], geo_json=True)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [boundary]},
            "properties": {
                "hex_id": hexagono["hex_id"],
                "estado": hexagono["estado"],
                "municipio": hexagono["municipio"],
                "total_ocorrencias": hexagono["total_ocorrencias"],
                "ivc": hexagono["ivc"],
                "classe_vulnerabilidade": _classe_para_valor(hexagono["ivc"], breaks),
            },
        })

    return {"type": "FeatureCollection", "features": features}
