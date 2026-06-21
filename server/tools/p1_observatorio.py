"""
Tools MCP do projeto P1 — Observatório de Segurança Pública.

`subscrever_alertas_tool` é uma simplificação pragmática: o modelo original
previa push via SSE, mas o padrão de chamada de tools do MCP é
request/response. Em vez de push real, esta tool lê o snapshot mais recente
da tabela `alerta_observatorio` (populada pelo job noturno
`calcular_alertas_noturnos`), funcionando como polling. Ver nota no README.
"""

import json

from data.db import get_connection
from ml import stats
from server.security.auditoria import com_auditoria


@com_auditoria("detectar_anomalias_estatisticas")
def detectar_anomalias_estatisticas_tool(
    estado: str = "", dominio: str = "", natureza: str = "", limiar_z: float = 2.0
) -> str:
    """
    Detecta meses com volume anômalo de BOs (z-score acima do limiar) por
    estado, município, domínio e natureza.

    Use esta tool quando o usuário quiser identificar picos/anomalias
    estatísticas de criminalidade em uma região ou tipo de ocorrência.

    Args:
        estado (str): Filtra por UF (opcional).
        dominio (str): Filtra por domínio do BO (opcional).
        natureza (str): Filtra por natureza do BO (opcional).
        limiar_z (float): Limiar de z-score para considerar anomalia (default 2.0).

    Returns:
        str: JSON com a lista de alertas (estado, município, domínio,
             natureza, mês, total de ocorrências e z-score).
    """
    alertas = stats.detectar_anomalias_estatisticas(
        estado=estado or None, dominio=dominio or None, natureza=natureza or None, limiar_z=limiar_z
    )
    return json.dumps(alertas, ensure_ascii=False, default=str)


@com_auditoria("calcular_taxa_elucidacao")
def calcular_taxa_elucidacao_tool(estado: str = "", delegacia: str = "", natureza: str = "") -> str:
    """
    Calcula a taxa de elucidação (inquéritos concluídos / total) por
    delegacia, estado e natureza do BO associado.

    Use esta tool quando o usuário quiser avaliar a eficiência investigativa
    de uma delegacia, estado ou tipo de crime.

    Args:
        estado (str): Filtra por UF (opcional).
        delegacia (str): Filtra por delegacia (opcional).
        natureza (str): Filtra por natureza do BO associado ao inquérito (opcional).

    Returns:
        str: JSON com a lista de taxas de elucidação por delegacia/estado/natureza,
             ordenada da menor para a maior taxa.
    """
    resultado = stats.calcular_taxa_elucidacao(estado=estado or None, delegacia=delegacia or None, natureza=natureza or None)
    return json.dumps(resultado, ensure_ascii=False, default=str)


@com_auditoria("listar_delegacias_com_alerta")
def listar_delegacias_com_alerta_tool(estado: str = "", limiar_z: float = 2.0, taxa_elucidacao_max: float = 0.3) -> str:
    """
    Tool composta: combina anomalias estatísticas de volume com baixa taxa de
    elucidação para apontar delegacias/regiões que merecem atenção prioritária.

    Use esta tool quando o usuário quiser uma visão consolidada de "onde
    olhar primeiro", em vez de consultar anomalias e elucidação separadamente.

    Args:
        estado (str): Filtra por UF (opcional).
        limiar_z (float): Limiar de z-score para considerar anomalia de volume (default 2.0).
        taxa_elucidacao_max (float): Taxa de elucidação máxima para considerar
            a delegacia como alerta (default 0.3).

    Returns:
        str: JSON com `anomalias_volume` (lista) e `delegacias_baixa_elucidacao`
             (lista), ambas já filtradas pelo estado informado.
    """
    anomalias = stats.detectar_anomalias_estatisticas(estado=estado or None, limiar_z=limiar_z)
    elucidacao = stats.calcular_taxa_elucidacao(estado=estado or None)
    baixa_elucidacao = [r for r in elucidacao if r["taxa_elucidacao"] <= taxa_elucidacao_max]
    resultado = {"anomalias_volume": anomalias, "delegacias_baixa_elucidacao": baixa_elucidacao}
    return json.dumps(resultado, ensure_ascii=False, default=str)


@com_auditoria("subscrever_alertas")
def subscrever_alertas_tool(estado: str = "", desde_horas: int = 24) -> str:
    """
    Lê os alertas mais recentes computados pelo job noturno de anomalias
    (snapshot em `alerta_observatorio`).

    Simplificação: o modelo original previa notificação por push via SSE;
    como tools MCP seguem o padrão request/response, esta tool funciona como
    polling — o cliente deve chamá-la periodicamente. Use esta tool quando o
    usuário quiser ver alertas recentes sem recalcular anomalias em tempo real.

    Args:
        estado (str): Filtra por UF (opcional).
        desde_horas (int): Retorna apenas alertas criados nas últimas N horas (default 24).

    Returns:
        str: JSON com a lista de alertas persistidos (estado, município,
             domínio, natureza, mês, z-score, criado_em).
    """
    filtros = ["criado_em >= now() - (%s || ' hours')::interval"]
    params = [desde_horas]
    if estado:
        filtros.append("estado = %s")
        params.append(estado)
    where = f"WHERE {' AND '.join(filtros)}"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT estado, municipio, dominio, natureza, mes, z_score, criado_em
                FROM alerta_observatorio
                {where}
                ORDER BY criado_em DESC
                """,
                params,
            )
            cols = [c.name for c in cur.description]
            alertas = [dict(zip(cols, row)) for row in cur.fetchall()]

    return json.dumps(alertas, ensure_ascii=False, default=str)
