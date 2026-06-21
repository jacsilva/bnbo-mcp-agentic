"""
Resolução do perfil de acesso a partir do token de autenticação da requisição.

IMPORTANTE: o perfil nunca deve ser aceito como parâmetro de tool (isso
permitiria que o próprio cliente se autoatribuísse um nível de acesso maior).
Ele deve vir de um token validado (JWT/OAuth) anexado à conexão MCP.

Esta implementação é um placeholder para a Fatia 2: a validação real de
token (assinatura, expiração, claims) e a integração com o provedor de
identidade do cliente ficam fora do escopo deste slice e estão listadas
como decisão pendente do modelo. Por ora, resolve o perfil a partir da
variável de ambiente `MCP_PERFIL_ATUAL`, simulando o claim que um token
validado traria.
"""

import os

from server.security.perfis import PUBLICO

PERFIS_VALIDOS = {"publico", "analista", "investigador"}


def get_perfil_atual() -> str:
    """Retorna o perfil de acesso da requisição atual (placeholder)."""
    perfil = os.getenv("MCP_PERFIL_ATUAL", PUBLICO)
    return perfil if perfil in PERFIS_VALIDOS else PUBLICO


def get_cliente_atual() -> str:
    """Identificador do cliente autenticado (placeholder)."""
    return os.getenv("MCP_CLIENTE_ATUAL", "desconhecido")
