"""
Linkage Criminal (P2) — busca por similaridade semântica + estrutural,
explicabilidade das razões de vínculo, e agrupamento de série criminal.
"""

import math
from typing import Any

from data.db import get_connection
from ml.embeddings import EmbeddingEngine

PESOS_RERANK = {
    "semantico": 0.5,
    "faixa_horaria": 0.15,
    "instrumento": 0.15,
    "perfil_vitima": 0.1,
    "proximidade_espacial": 0.1,
}

RAIO_PROXIMIDADE_KM = 5.0


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    if None in (lat1, lng1, lat2, lng2):
        return float("inf")
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _faixa_horaria(dt) -> str:
    h = dt.hour
    if 5 <= h < 12:
        return "manha"
    if 12 <= h < 18:
        return "tarde"
    if 18 <= h < 24:
        return "noite"
    return "madrugada"


def _score_estrutural(base: dict, candidato: dict) -> dict[str, float]:
    razoes = {}
    razoes["faixa_horaria"] = 1.0 if _faixa_horaria(base["data_hora"]) == _faixa_horaria(candidato["data_hora"]) else 0.0
    razoes["instrumento"] = 1.0 if base.get("instrumento") and base.get("instrumento") == candidato.get("instrumento") else 0.0
    razoes["perfil_vitima"] = 1.0 if base.get("vitima_perfil") == candidato.get("vitima_perfil") else 0.0
    dist_km = _haversine_km(base.get("lat"), base.get("lng"), candidato.get("lat"), candidato.get("lng"))
    razoes["proximidade_espacial"] = max(0.0, 1.0 - dist_km / RAIO_PROXIMIDADE_KM) if dist_km != float("inf") else 0.0
    return razoes


def _buscar_por_vetor(conn, vetor: list[float], limit: int, excluir_id: str | None) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, bo_numero, estado, municipio, data_hora, lat, lng, dominio,
                   natureza, relato, vitima_perfil, autor_perfil, instrumento, status,
                   1 - (embedding <=> %s::vector) AS score_semantico
            FROM bo
            WHERE (%s::uuid IS NULL OR id != %s::uuid)
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (vetor, excluir_id, excluir_id, vetor, limit),
        )
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _buscar_bo_por_id(conn, bo_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM bo WHERE id = %s::uuid", (bo_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [c.name for c in cur.description]
        return dict(zip(cols, row))


def buscar_ocorrencias_similares(
    bo_id: str | None = None,
    texto_livre: str | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Busca BOs similares por bo_id (vetor já indexado) ou texto_livre (nova query)."""
    if not bo_id and not texto_livre:
        raise ValueError("Informe bo_id ou texto_livre.")

    engine = EmbeddingEngine()
    with get_connection() as conn:
        base = None
        if bo_id:
            base = _buscar_bo_por_id(conn, bo_id)
            if base is None:
                raise ValueError(f"BO {bo_id} não encontrado.")
            vetor = list(base["embedding"])
        else:
            vetor = engine.embed_query(texto_livre)

        candidatos = _buscar_por_vetor(conn, vetor, limit=top_k * 3, excluir_id=bo_id)

        resultados = []
        for candidato in candidatos:
            razoes_estruturais = _score_estrutural(base, candidato) if base else {}
            score_final = candidato["score_semantico"] * PESOS_RERANK["semantico"]
            for chave, valor in razoes_estruturais.items():
                score_final += valor * PESOS_RERANK[chave]

            resultados.append({
                "bo_id": str(candidato["id"]),
                "bo_numero": candidato["bo_numero"],
                "natureza": candidato["natureza"],
                "estado": candidato["estado"],
                "municipio": candidato["municipio"],
                "relato": candidato["relato"],
                "data_hora": candidato["data_hora"].isoformat(),
                "score_semantico": round(candidato["score_semantico"], 4),
                "score_final": round(score_final, 4),
                "razoes_estruturais": razoes_estruturais,
            })

        resultados.sort(key=lambda r: r["score_final"], reverse=True)
        return resultados[:top_k]


def obter_razoes_similaridade(bo_id_a: str, bo_id_b: str) -> dict[str, Any]:
    """Explica as dimensões e pesos que vinculam dois BOs."""
    with get_connection() as conn:
        bo_a = _buscar_bo_por_id(conn, bo_id_a)
        bo_b = _buscar_bo_por_id(conn, bo_id_b)
        if bo_a is None or bo_b is None:
            raise ValueError("Um ou ambos os BOs informados não foram encontrados.")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 - (%s::vector <=> %s::vector)",
                (list(bo_a["embedding"]), list(bo_b["embedding"])),
            )
            score_semantico = cur.fetchone()[0]

        razoes_estruturais = _score_estrutural(bo_a, bo_b)
        contribuicoes = {"semantico": score_semantico * PESOS_RERANK["semantico"]}
        for chave, valor in razoes_estruturais.items():
            contribuicoes[chave] = valor * PESOS_RERANK[chave]

        return {
            "bo_id_a": bo_id_a,
            "bo_id_b": bo_id_b,
            "score_semantico": round(score_semantico, 4),
            "razoes_estruturais": razoes_estruturais,
            "contribuicoes_pesadas": {k: round(v, 4) for k, v in contribuicoes.items()},
            "score_final": round(sum(contribuicoes.values()), 4),
        }


def agrupar_serie_criminal(
    bo_id: str | None = None,
    texto_livre: str | None = None,
    top_k: int = 30,
    eps: float = 0.35,
    min_samples: int = 2,
) -> dict[str, Any]:
    """Agrupa candidatos similares via DBSCAN sobre o espaço (1 - score_final), com score de coesão."""
    from sklearn.cluster import DBSCAN
    import numpy as np

    candidatos = buscar_ocorrencias_similares(bo_id=bo_id, texto_livre=texto_livre, top_k=top_k)
    if not candidatos:
        return {"clusters": [], "ruido": []}

    distancias = np.array([[1 - c["score_final"]] for c in candidatos])
    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean").fit_predict(distancias)

    clusters: dict[int, list[dict]] = {}
    ruido = []
    for candidato, label in zip(candidatos, labels):
        if label == -1:
            ruido.append(candidato)
        else:
            clusters.setdefault(label, []).append(candidato)

    clusters_formatados = []
    for label, membros in clusters.items():
        coesao = sum(m["score_final"] for m in membros) / len(membros)
        clusters_formatados.append({
            "cluster_id": int(label),
            "tamanho": len(membros),
            "coesao_media": round(coesao, 4),
            "membros": membros,
        })

    clusters_formatados.sort(key=lambda c: c["coesao_media"], reverse=True)
    return {"clusters": clusters_formatados, "ruido": ruido}
