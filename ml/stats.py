"""
Observatório (P1) — detecção de anomalias estatísticas e taxa de elucidação.
"""

from typing import Any

import numpy as np


def _calcular_z_scores(volumes: list[float]) -> list[float] | None:
    """Z-score de uma série de volumes mensais; None se a série for curta
    demais (<3 pontos) ou tiver desvio padrão zero (sem variação)."""
    if len(volumes) < 3:
        return None
    array = np.array(volumes, dtype=float)
    media, desvio = array.mean(), array.std()
    if desvio == 0:
        return None
    return list((array - media) / desvio)


def detectar_anomalias_estatisticas(
    estado: str | None = None,
    dominio: str | None = None,
    natureza: str | None = None,
    limiar_z: float = 2.0,
) -> list[dict[str, Any]]:
    """Calcula z-score mensal de volume de BOs por (estado, município, domínio, natureza)
    e retorna os meses cujo desvio excede `limiar_z`."""
    filtros = []
    params: list[Any] = []
    if estado:
        filtros.append("estado = %s")
        params.append(estado)
    if dominio:
        filtros.append("dominio = %s")
        params.append(dominio)
    if natureza:
        filtros.append("natureza = %s")
        params.append(natureza)
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    from data.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT estado, municipio, dominio, natureza,
                       date_trunc('month', data_hora)::date AS mes,
                       count(*) AS total
                FROM bo
                {where}
                GROUP BY estado, municipio, dominio, natureza, mes
                ORDER BY estado, municipio, dominio, natureza, mes
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            linhas = [dict(zip(cols, row)) for row in cur.fetchall()]

    series: dict[tuple, list[dict]] = {}
    for linha in linhas:
        chave = (linha["estado"], linha["municipio"], linha["dominio"], linha["natureza"])
        series.setdefault(chave, []).append(linha)

    alertas = []
    for chave, meses in series.items():
        z_scores = _calcular_z_scores([m["total"] for m in meses])
        if z_scores is None:
            continue
        for mes, z in zip(meses, z_scores):
            if abs(z) >= limiar_z:
                alertas.append({
                    "estado": mes["estado"],
                    "municipio": mes["municipio"],
                    "dominio": mes["dominio"],
                    "natureza": mes["natureza"],
                    "mes": mes["mes"].isoformat(),
                    "total_ocorrencias": mes["total"],
                    "z_score": round(float(z), 4),
                })

    alertas.sort(key=lambda a: abs(a["z_score"]), reverse=True)
    return alertas


def calcular_taxa_elucidacao(
    estado: str | None = None,
    delegacia: str | None = None,
    natureza: str | None = None,
) -> list[dict[str, Any]]:
    """Calcula a taxa de elucidação (inquéritos concluídos / total) por delegacia,
    estado e natureza do BO associado."""
    filtros = []
    params: list[Any] = []
    if estado:
        filtros.append("i.estado = %s")
        params.append(estado)
    if delegacia:
        filtros.append("i.delegacia = %s")
        params.append(delegacia)
    if natureza:
        filtros.append("b.natureza = %s")
        params.append(natureza)
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    from data.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT i.delegacia, i.estado, b.natureza,
                       count(*) AS total_inqueritos,
                       count(*) FILTER (WHERE i.status = 'concluido') AS concluidos
                FROM inquerito i
                JOIN bo b ON b.id = i.bo_id
                {where}
                GROUP BY i.delegacia, i.estado, b.natureza
                ORDER BY i.estado, i.delegacia, b.natureza
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            linhas = [dict(zip(cols, row)) for row in cur.fetchall()]

    resultado = []
    for linha in linhas:
        taxa = linha["concluidos"] / linha["total_inqueritos"] if linha["total_inqueritos"] else 0.0
        resultado.append({
            "delegacia": linha["delegacia"],
            "estado": linha["estado"],
            "natureza": linha["natureza"],
            "total_inqueritos": linha["total_inqueritos"],
            "concluidos": linha["concluidos"],
            "taxa_elucidacao": round(taxa, 4),
        })

    resultado.sort(key=lambda r: r["taxa_elucidacao"])
    return resultado
