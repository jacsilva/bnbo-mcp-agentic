"""Configuração do Celery — broker/backend Redis para jobs assíncronos do MCP server."""

import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("bnbo_jobs", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_track_started = True
