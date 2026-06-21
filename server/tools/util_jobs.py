"""
Tools transversais de jobs assíncronos — disparo e acompanhamento via Celery.
"""

import json

from celery.result import AsyncResult

from jobs.celery_app import celery_app
from jobs.tasks import reindexar_embeddings
from server.security.auditoria import com_auditoria
from server.security.contexto import get_perfil_atual
from server.security.perfis import ANALISTA, tem_acesso_minimo
from server.tools._erros import tratar_erros


@com_auditoria("reindexar_embeddings")
@tratar_erros
def reindexar_embeddings_tool(batch_size: int = 100) -> str:
    """
    Dispara, de forma assíncrona, a reindexação dos embeddings de todos os BOs
    (por exemplo, após uma troca do modelo de embedding).

    Use esta tool quando o usuário pedir para recalcular/atualizar os
    embeddings da base. Esta tool retorna imediatamente um job_id; use
    `consultar_job_status_tool` para acompanhar o progresso.

    Args:
        batch_size (int): Tamanho do lote processado por vez (default 100).

    Returns:
        str: JSON com o job_id do job assíncrono disparado.
    """
    if not tem_acesso_minimo(get_perfil_atual(), ANALISTA):
        return json.dumps({"erro": "Perfil insuficiente para disparar reindexação. Requer analista ou investigador."})

    job = reindexar_embeddings.delay(batch_size=batch_size)
    return json.dumps({"job_id": job.id, "status": "disparado"})


@com_auditoria("consultar_job_status")
@tratar_erros
def consultar_job_status_tool(job_id: str) -> str:
    """
    Consulta o status de um job assíncrono disparado por outra tool
    (ex.: reindexar_embeddings_tool).

    Use esta tool para fazer polling do progresso/conclusão de um job_id
    retornado anteriormente.

    Args:
        job_id (str): Identificador do job retornado na chamada assíncrona.

    Returns:
        str: JSON com o estado do job (PENDING/PROGRESS/SUCCESS/FAILURE) e,
             quando disponível, o resultado ou progresso parcial.
    """
    result = AsyncResult(job_id, app=celery_app)
    payload = {"job_id": job_id, "estado": result.state}
    if result.state == "PROGRESS":
        payload["progresso"] = result.info
    elif result.state == "SUCCESS":
        payload["resultado"] = result.result
    elif result.state == "FAILURE":
        payload["erro"] = str(result.info)
    return json.dumps(payload, ensure_ascii=False, default=str)
