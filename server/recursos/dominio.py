"""
Provedores de conteúdo dos Resources de domínio.

Conteúdo estático (glossário, metodologia do IVC) é lido de arquivos markdown
em `conteudo/`; conteúdo dinâmico (perfis, regiões) é derivado das camadas de
segurança e do banco. A leitura de regiões é compartilhada com a tool
`listar_regioes_disponiveis_tool` para não duplicar SQL.
"""

import json
from importlib import resources

from data.db import get_connection
from server.schemas.saida import RegioesDisponiveis
from server.security.perfis import ANALISTA, INVESTIGADOR, NIVEL, PUBLICO

_CONTEUDO = resources.files("server.recursos") / "conteudo"


def _ler_markdown(nome: str) -> str:
    return (_CONTEUDO / nome).read_text(encoding="utf-8")


def recurso_glossario() -> str:
    """Glossário do domínio (markdown)."""
    return _ler_markdown("glossario.md")


def recurso_metodologia_ivc() -> str:
    """Metodologia e pesos do IVC (markdown)."""
    return _ler_markdown("metodologia_ivc.md")


def recurso_perfis() -> str:
    """Modelo de perfis de acesso e visibilidade de PII (JSON)."""
    perfis = {
        nome: {
            "nivel": nivel,
            "pii_visivel": nome == INVESTIGADOR,
            "descricao": _DESC_PERFIL[nome],
        }
        for nome, nivel in sorted(NIVEL.items(), key=lambda kv: kv[1])
    }
    payload = {
        "ordem": [PUBLICO, ANALISTA, INVESTIGADOR],
        "perfis": perfis,
        "observacao": (
            "O perfil nunca é aceito como input de tool; é resolvido do contexto "
            "de autenticação. Campos textuais (ex.: relato) têm CPF, telefone e "
            "e-mail mascarados para publico e analista."
        ),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


_DESC_PERFIL = {
    PUBLICO: "Acesso público; relato com PII mascarada.",
    ANALISTA: "Analista; relato com PII mascarada; pode disparar reindexação.",
    INVESTIGADOR: "Investigador; vê o relato integral, sem redação de PII.",
}


def consultar_regioes() -> dict[str, list[str]]:
    """Lista estados e, para cada um, os municípios com BOs cadastrados.

    Função compartilhada entre o resource `bnbo://dominio/regioes` e a tool
    `listar_regioes_disponiveis`.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT estado, municipio FROM bo ORDER BY estado, municipio")
            rows = cur.fetchall()

    regioes: dict[str, list[str]] = {}
    for estado, municipio in rows:
        regioes.setdefault(estado, [])
        if municipio:
            regioes[estado].append(municipio)
    return regioes


def recurso_regioes() -> str:
    """Estados e municípios disponíveis (JSON)."""
    return RegioesDisponiveis.dump_json(RegioesDisponiveis.validate_python(consultar_regioes())).decode()
