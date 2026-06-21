"""
Auditoria de acesso — registra cliente/perfil/tool/parâmetros/timestamp em
`audit_log` para toda chamada de tool do servidor. Desacoplada da lógica de
cada tool: aplicada via decorator na própria função MCP.
"""

import functools
import json

from data.db import get_connection
from server.security.contexto import get_cliente_atual, get_perfil_atual


def log_acesso(tool_name: str, parametros: dict) -> None:
    cliente = get_cliente_atual()
    perfil = get_perfil_atual()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_log (cliente, perfil, tool_name, parametros)
                VALUES (%s, %s, %s, %s)
                """,
                (cliente, perfil, tool_name, json.dumps(parametros, default=str)),
            )
        conn.commit()


def com_auditoria(tool_name: str):
    """Decorator que registra a chamada em `audit_log` antes de executar a tool."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                log_acesso(tool_name, kwargs if kwargs else {"args": args})
            except Exception:
                # Falha de auditoria não deve impedir a execução da tool.
                pass
            return func(*args, **kwargs)

        return wrapper

    return decorator
