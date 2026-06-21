"""Configuração do Celery — broker/backend Redis para jobs assíncronos do MCP server."""

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("bnbo_jobs", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_track_started = True

# Job noturno do Observatório (P1): recalcula anomalias estatísticas e persiste
# o snapshot lido por `subscrever_alertas_tool`. Requer `celery beat` rodando.
celery_app.conf.beat_schedule = {
    "calcular-alertas-noturnos": {
        "task": "jobs.calcular_alertas_noturnos",
        "schedule": 24 * 60 * 60,
    },
}
