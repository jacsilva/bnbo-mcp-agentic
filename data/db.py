"""
Camada de acesso a dados — pool de conexões PostgreSQL/pgvector.
"""

import os
from contextlib import contextmanager
from typing import Generator

from psycopg_pool import ConnectionPool
from pgvector.psycopg import register_vector

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://bnbo:bnbo@localhost:5432/bnbo"
)

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            configure=register_vector,
        )
    return _pool


@contextmanager
def get_connection() -> Generator:
    pool = get_pool()
    with pool.connection() as conn:
        yield conn
