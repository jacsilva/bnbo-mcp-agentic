"""Testes unitários da camada de segurança (sem dependência de banco/rede)."""

from server.security.perfis import ANALISTA, INVESTIGADOR, PUBLICO, tem_acesso_minimo
from server.security.redacao import redigir_dict, redigir_lista, redigir_texto


def test_redigir_texto_mascara_cpf_telefone_email():
    texto = "Vítima CPF 123.456.789-00, tel (11) 91234-5678, email vitima@exemplo.com."
    redigido = redigir_texto(texto)
    assert "[CPF_REDIGIDO]" in redigido
    assert "[TELEFONE_REDIGIDO]" in redigido
    assert "[EMAIL_REDIGIDO]" in redigido
    assert "123.456.789-00" not in redigido


def test_redigir_dict_preserva_investigador():
    registro = {"relato": "CPF 123.456.789-00 da vítima."}
    assert redigir_dict(registro, INVESTIGADOR) == registro
    assert redigir_dict(registro, PUBLICO)["relato"] != registro["relato"]


def test_redigir_lista():
    registros = [{"relato": "contato vitima@exemplo.com"}]
    redigidos = redigir_lista(registros, PUBLICO)
    assert "[EMAIL_REDIGIDO]" in redigidos[0]["relato"]


def test_tem_acesso_minimo():
    assert tem_acesso_minimo(INVESTIGADOR, ANALISTA)
    assert tem_acesso_minimo(ANALISTA, ANALISTA)
    assert not tem_acesso_minimo(PUBLICO, ANALISTA)


if __name__ == "__main__":
    test_redigir_texto_mascara_cpf_telefone_email()
    test_redigir_dict_preserva_investigador()
    test_redigir_lista()
    test_tem_acesso_minimo()
    print("Todos os testes de segurança passaram.")
