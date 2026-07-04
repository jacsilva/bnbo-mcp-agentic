"""
Validação de entrada das tools via contrato Pydantic.

`valida_entrada(Model)` faz o bind dos argumentos da tool contra o modelo de
argumentos (`server.schemas.entrada`), aplicando as restrições de domínio
declaradas ali. Em caso de violação, a `pydantic.ValidationError` propaga e é
convertida em resposta de erro padronizada pelo `tratar_erros`.

Deve ser o decorator mais interno (abaixo de `coage_numericos`), para validar
o valor já coagido para número:

    @com_auditoria("...")
    @tratar_erros
    @coage_numericos
    @valida_entrada(EntradaModel)
    def minha_tool(...): ...
"""

import functools
import inspect


def valida_entrada(modelo):
    def decorator(func):
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            validado = modelo(**bound.arguments)
            return func(**validado.model_dump())

        return wrapper

    return decorator
