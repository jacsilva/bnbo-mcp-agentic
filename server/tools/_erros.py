"""
Tratamento de erros transversal para tools MCP.

Tools MCP devem sempre retornar uma string (JSON), nunca propagar uma
exceção — isso quebraria o transporte com o cliente. Este decorator
converte exceções esperadas (`ValueError`, de validação de domínio) e
inesperadas em uma resposta JSON de erro padronizada.
"""

import functools
import json


def tratar_erros(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return json.dumps({"erro": str(e)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"erro": f"Erro interno ao executar {func.__name__}: {e}"}, ensure_ascii=False)
    return wrapper
