"""
Tools MCP do projeto P2 — Linkage Criminal.

Cada tool é registrada no `mcp_server` em `mcp_server.py`. As descriptions
abaixo são o contrato lido pela LLM do cliente para decidir quando/como
chamar cada tool — devem ser precisas.
"""

import json

from ml import linkage
from server.security.auditoria import com_auditoria
from server.security.contexto import get_perfil_atual
from server.security.redacao import redigir_lista


@com_auditoria("buscar_ocorrencias_similares")
def buscar_ocorrencias_similares_tool(bo_id: str = "", texto_livre: str = "", top_k: int = 10) -> str:
    """
    Busca Boletins de Ocorrência semanticamente e estruturalmente similares a um
    BO existente (por bo_id) ou a uma descrição livre (texto_livre).

    Use esta tool quando o usuário quiser encontrar ocorrências parecidas com
    um caso já registrado, ou relacionadas a uma descrição de fato.

    Args:
        bo_id (str): UUID do BO de referência. Use isto OU texto_livre.
        texto_livre (str): Descrição livre do fato a buscar. Use isto OU bo_id.
        top_k (int): Número máximo de resultados a retornar (default 10).

    Returns:
        str: JSON com a lista de BOs similares, score semântico, score final
             (reranking ponderado) e razões estruturais de cada candidato.
    """
    resultados = linkage.buscar_ocorrencias_similares(
        bo_id=bo_id or None, texto_livre=texto_livre or None, top_k=top_k
    )
    resultados = redigir_lista(resultados, get_perfil_atual())
    return json.dumps(resultados, ensure_ascii=False, default=str)


@com_auditoria("obter_razoes_similaridade")
def obter_razoes_similaridade_tool(bo_id_a: str, bo_id_b: str) -> str:
    """
    Explica por que dois BOs foram considerados similares, detalhando as
    dimensões (semântica, faixa horária, instrumento, perfil da vítima,
    proximidade espacial) e o peso de cada uma no score final.

    Use esta tool quando o usuário pedir explicabilidade sobre um vínculo
    apontado por `buscar_ocorrencias_similares_tool` ou `agrupar_serie_criminal_tool`.

    Args:
        bo_id_a (str): UUID do primeiro BO.
        bo_id_b (str): UUID do segundo BO.

    Returns:
        str: JSON com score semântico, razões estruturais, contribuições
             ponderadas de cada dimensão e o score final agregado.
    """
    resultado = linkage.obter_razoes_similaridade(bo_id_a, bo_id_b)
    return json.dumps(resultado, ensure_ascii=False, default=str)


@com_auditoria("agrupar_serie_criminal")
def agrupar_serie_criminal_tool(
    bo_id: str = "", texto_livre: str = "", top_k: int = 30, eps: float = 0.35, min_samples: int = 2
) -> str:
    """
    Agrupa BOs similares a um caso de referência em possíveis séries
    criminais, usando DBSCAN sobre os scores de similaridade.

    Use esta tool quando o usuário quiser identificar um padrão/série de
    ocorrências (ex.: mesmo autor, mesmo modus operandi) a partir de um BO
    ou de uma descrição livre, em vez de apenas uma lista de similares.

    Args:
        bo_id (str): UUID do BO de referência. Use isto OU texto_livre.
        texto_livre (str): Descrição livre do fato a buscar. Use isto OU bo_id.
        top_k (int): Quantos candidatos buscar antes de agrupar (default 30).
        eps (float): Raio de vizinhança do DBSCAN no espaço de distância (default 0.35).
        min_samples (int): Mínimo de membros para formar um cluster (default 2).

    Returns:
        str: JSON com a lista de clusters (cada um com score de coesão média
             e membros) e a lista de candidatos classificados como ruído.
    """
    resultado = linkage.agrupar_serie_criminal(
        bo_id=bo_id or None, texto_livre=texto_livre or None, top_k=top_k, eps=eps, min_samples=min_samples
    )
    perfil = get_perfil_atual()
    for cluster in resultado["clusters"]:
        cluster["membros"] = redigir_lista(cluster["membros"], perfil)
    resultado["ruido"] = redigir_lista(resultado["ruido"], perfil)
    return json.dumps(resultado, ensure_ascii=False, default=str)
