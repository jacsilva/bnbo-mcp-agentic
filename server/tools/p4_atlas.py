"""
Tools MCP do projeto P4 — Atlas de Vulnerabilidade.

Agrega BOs por hexágono H3 (resolução 8) e calcula um Índice de
Vulnerabilidade Criminal (IVC) ponderado por domínio, classificado em
faixas via Jenks natural breaks, exportável como GeoJSON para mapas.
"""

import json

from ml import atlas
from server.security.auditoria import com_auditoria
from server.tools._erros import tratar_erros


@com_auditoria("calcular_indice_vulnerabilidade")
@tratar_erros
def calcular_indice_vulnerabilidade_tool(estado: str = "", meses: int = 0) -> str:
    """
    Calcula o Índice de Vulnerabilidade Criminal (IVC) por hexágono H3
    (resolução 8), ponderando ocorrências contra a pessoa mais que
    patrimoniais, normalizado entre 0 e 1 pelo hexágono de maior incidência.

    Use esta tool quando o usuário quiser um ranking de áreas mais
    vulneráveis, sem precisar de geometria para mapa (use
    `gerar_atlas_vulnerabilidade_tool` para isso).

    Args:
        estado (str): Filtra por UF (opcional).
        meses (int): Considera apenas BOs dos últimos N meses (opcional; 0 = todos).

    Returns:
        str: JSON com a lista de hexágonos ordenada por IVC decrescente
             (hex_id, estado, município, total de ocorrências, ivc).
    """
    resultado = atlas.calcular_indice_vulnerabilidade(estado=estado or None, meses=meses or None)
    return json.dumps(resultado, ensure_ascii=False, default=str)


@com_auditoria("gerar_atlas_vulnerabilidade")
@tratar_erros
def gerar_atlas_vulnerabilidade_tool(estado: str = "", meses: int = 0, n_classes: int = 5) -> str:
    """
    Gera o Atlas de Vulnerabilidade como GeoJSON: um polígono hexagonal (H3,
    resolução 8) por área, com o IVC e a classe Jenks (1=menor
    vulnerabilidade, n_classes=maior) prontos para plotagem em mapa.

    Use esta tool quando o usuário quiser visualizar a distribuição espacial
    da vulnerabilidade criminal, em vez de apenas um ranking textual.

    Args:
        estado (str): Filtra por UF (opcional).
        meses (int): Considera apenas BOs dos últimos N meses (opcional; 0 = todos).
        n_classes (int): Número de classes Jenks para a legenda (default 5).

    Returns:
        str: GeoJSON (FeatureCollection) com um Feature por hexágono, contendo
             hex_id, estado, município, total_ocorrencias, ivc e
             classe_vulnerabilidade nas properties.
    """
    geojson = atlas.gerar_atlas_geojson(estado=estado or None, meses=meses or None, n_classes=n_classes)
    return json.dumps(geojson, ensure_ascii=False, default=str)
