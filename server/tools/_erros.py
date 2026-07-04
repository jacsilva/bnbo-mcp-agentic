"""
Tratamento de erros transversal para tools MCP.

Tools MCP devem sempre retornar uma string (JSON), nunca propagar uma
exceção — isso quebraria o transporte com o cliente. Este decorator
converte exceções esperadas (`ValidationError` do contrato Pydantic de
entrada e `ValueError` de validação de domínio) e inesperadas em uma
resposta JSON de erro padronizada.
"""

import functools
import json

from pydantic import ValidationError


def _formatar_validation_error(e: ValidationError) -> str:
    """Resume a ValidationError do Pydantic numa mensagem legível por campo,
    em vez do dump técnico padrão."""
    partes = []
    for erro in e.errors():
        campo = ".".join(str(p) for p in erro["loc"]) or "(corpo)"
        partes.append(f"{campo}: {erro['msg']}")
    return "; ".join(partes)


def tratar_erros(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return json.dumps({"erro": _formatar_validation_error(e)}, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"erro": str(e)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"erro": f"Erro interno ao executar {func.__name__}: {e}"}, ensure_ascii=False)
    return wrapper
