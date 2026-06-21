"""Tasks Celery — reindexação de embeddings e consulta de status de jobs."""

from jobs.celery_app import celery_app
from data.db import get_connection
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
