"""
Coerção numérica defensiva para tools MCP.

Alguns LLMs de cliente (ex.: modelos Llama servidos pela Groq) serializam
argumentos numéricos como string no tool call — ex.: `{"meses": "0"}` em vez
de `{"meses": 0}`. Quando o provedor valida o tool call contra o schema da
tool no lado dele, um schema estritamente `integer`/`number` rejeita a string
com HTTP 400 antes mesmo de a tool ser executada.

Mitigação (alinhada ao risco previsto no modelo — "a LLM do cliente pode
interpretar mal os schemas"): os parâmetros numéricos são anotados como
`int | str` / `float | str` (o schema passa a aceitar ambos) e este decorator
normaliza o valor para número antes de a tool rodar. O contrato semântico
continua sendo "número"; apenas toleramos a serialização como string.
"""

import functools
import inspect
from typing import get_args


def _tipo_numerico(annotation):
    """Para anotações `int | str` / `float | str` (em qualquer grafia de União),
    retorna `int`/`float`; para qualquer outra anotação, retorna `None`."""
    membros = get_args(annotation)
    if str in membros:
        for tipo in (int, float):
            if tipo in membros:
                return tipo
    return None


def coage_numericos(func):
    """Coage para int/float os argumentos string dos parâmetros anotados como
    `int | str` / `float | str`. Valores não-string ou já numéricos passam
    intactos; strings vazias ou não-numéricas são deixadas para a validação
    da própria tool tratar."""
    sig = inspect.signature(func)
    alvos = {nome: _tipo_numerico(p.annotation) for nome, p in sig.parameters.items()}
    alvos = {nome: tipo for nome, tipo in alvos.items() if tipo is not None}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for nome, tipo in alvos.items():
            valor = kwargs.get(nome)
            if isinstance(valor, str) and valor.strip():
                try:
                    kwargs[nome] = tipo(valor)
                except ValueError:
                    pass
        return func(*args, **kwargs)

    return wrapper
