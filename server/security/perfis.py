"""
Perfis de acesso. Ordem crescente de privilégio: público < analista < investigador.

O perfil NUNCA é aceito como parâmetro de input de uma tool — ele é resolvido
a partir do contexto de autenticação da requisição (ver `contexto.py`), para
que um cliente não possa se autoatribuir um nível de acesso maior.
"""

PUBLICO = "publico"
ANALISTA = "analista"
INVESTIGADOR = "investigador"

NIVEL = {
    PUBLICO: 0,
    ANALISTA: 1,
    INVESTIGADOR: 2,
}


def nivel(perfil: str) -> int:
    return NIVEL.get(perfil, NIVEL[PUBLICO])


def tem_acesso_minimo(perfil: str, minimo: str) -> bool:
    return nivel(perfil) >= nivel(minimo)
