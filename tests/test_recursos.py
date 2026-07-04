"""
Testes dos Resources de domínio.

Os resources estáticos (glossário, metodologia) e o de perfis não dependem de
infraestrutura. O de regiões é exercitado com `consultar_regioes` substituída,
validando apenas a serialização pelo modelo `RegioesDisponiveis`.
"""

import json

from server.recursos import dominio
from server.schemas.saida import RegioesDisponiveis
from server.security.perfis import ANALISTA, INVESTIGADOR, PUBLICO


def test_glossario_retorna_markdown_nao_vazio():
    texto = dominio.recurso_glossario()
    assert texto.strip()
    assert "BO" in texto and "IVC" in texto


def test_metodologia_ivc_descreve_pesos():
    texto = dominio.recurso_metodologia_ivc()
    assert "IVC" in texto
    assert "pessoa" in texto and "patrimonio" in texto
    assert "H3" in texto and "Jenks" in texto


def test_perfis_expoe_hierarquia_e_visibilidade_pii():
    payload = json.loads(dominio.recurso_perfis())
    assert payload["ordem"] == [PUBLICO, ANALISTA, INVESTIGADOR]
    perfis = payload["perfis"]
    assert perfis[PUBLICO]["nivel"] < perfis[ANALISTA]["nivel"] < perfis[INVESTIGADOR]["nivel"]
    assert perfis[INVESTIGADOR]["pii_visivel"] is True
    assert perfis[PUBLICO]["pii_visivel"] is False
    assert perfis[ANALISTA]["pii_visivel"] is False


def test_regioes_serializa_com_modelo_regioes_disponiveis(monkeypatch):
    fixture = {"SP": ["São Paulo", "Campinas"], "RJ": ["Niterói"]}
    monkeypatch.setattr(dominio, "consultar_regioes", lambda: fixture)
    out = dominio.recurso_regioes()
    esperado = RegioesDisponiveis.dump_json(RegioesDisponiveis.validate_python(fixture)).decode()
    assert out == esperado
    assert "São Paulo" in out


if __name__ == "__main__":
    test_glossario_retorna_markdown_nao_vazio()
    test_metodologia_ivc_descreve_pesos()
    test_perfis_expoe_hierarquia_e_visibilidade_pii()
    print("Testes de resources (estáticos/perfis) passaram.")
