"""Tasks Celery — reindexação de embeddings, alertas noturnos do Observatório."""

from jobs.celery_app import celery_app
from data.db import get_connection
from ml import stats
from ml.embeddings import EmbeddingEngine


@celery_app.task(bind=True, name="jobs.reindexar_embeddings")
def reindexar_embeddings(self, batch_size: int = 100):
    """Recalcula embeddings de todos os BOs (ex.: após troca de modelo de embedding)."""
    engine = EmbeddingEngine()
    total = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM bo")
            total_rows = cur.fetchone()[0]

        offset = 0
        while True:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, relato FROM bo ORDER BY id LIMIT %s OFFSET %s",
                    (batch_size, offset),
                )
                rows = cur.fetchall()
            if not rows:
                break

            ids = [r[0] for r in rows]
            relatos = [r[1] for r in rows]
            vetores = engine.embed_passages(relatos)

            with conn.cursor() as cur:
                for bo_id, vetor in zip(ids, vetores):
                    cur.execute(
                        "UPDATE bo SET embedding = %s WHERE id = %s",
                        (vetor, bo_id),
                    )
            conn.commit()

            total += len(rows)
            offset += batch_size
            self.update_state(state="PROGRESS", meta={"processados": total, "total": total_rows})

    return {"status": "concluido", "processados": total}


@celery_app.task(name="jobs.calcular_alertas_noturnos")
def calcular_alertas_noturnos(limiar_z: float = 2.0):
    """Recalcula anomalias estatísticas para todos os estados e persiste o
    snapshot em `alerta_observatorio`, para leitura por `subscrever_alertas`."""
    alertas = stats.detectar_anomalias_estatisticas(limiar_z=limiar_z)

    with get_connection() as conn:
        with conn.cursor() as cur:
            for alerta in alertas:
                cur.execute(
                    """
                    INSERT INTO alerta_observatorio (estado, municipio, dominio, natureza, mes, z_score)
                    VALUES (%(estado)s, %(municipio)s, %(dominio)s, %(natureza)s, %(mes)s, %(z_score)s)
                    """,
                    alerta,
                )
        conn.commit()

    return {"status": "concluido", "alertas_gerados": len(alertas)}
