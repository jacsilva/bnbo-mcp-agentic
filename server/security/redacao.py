"""
Redação de PII — desacoplada da lógica de domínio.

Aplica-se sobre os campos textuais livres (ex.: `relato`) retornados pelas
tools, antes da resposta sair do servidor. O perfil `investigador` vê o
texto integral; `analista` e `publico` recebem o texto com PII mascarada.
"""

import re

from server.security.perfis import INVESTIGADOR

_PADROES_PII = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF_REDIGIDO]"),
    (re.compile(r"\(\d{2}\)\s?\d{4,5}-?\d{4}\b"), "[TELEFONE_REDIGIDO]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL_REDIGIDO]"),
]


def redigir_texto(texto: str) -> str:
    """Mascara CPF, telefone e e-mail em um texto livre."""
    if not texto:
        return texto
    for padrao, substituto in _PADROES_PII:
        texto = padrao.sub(substituto, texto)
    return texto


def redigir_campo(valor, perfil: str):
    """Aplica redação a um valor textual de acordo com o perfil."""
    if perfil == INVESTIGADOR or not isinstance(valor, str):
        return valor
    return redigir_texto(valor)


def redigir_dict(registro: dict, perfil: str, campos: tuple[str, ...] = ("relato",)) -> dict:
    """Retorna uma cópia do dict com os `campos` redigidos conforme o perfil."""
    if perfil == INVESTIGADOR:
        return registro
    redigido = dict(registro)
    for campo in campos:
        if campo in redigido:
            redigido[campo] = redigir_campo(redigido[campo], perfil)
    return redigido


def redigir_lista(registros: list[dict], perfil: str, campos: tuple[str, ...] = ("relato",)) -> list[dict]:
    return [redigir_dict(r, perfil, campos) for r in registros]
