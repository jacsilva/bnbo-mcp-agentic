"""Testes unitários do decorator de tratamento de erros das tools."""

import json

from server.tools._erros import tratar_erros


@tratar_erros
def _levanta_value_error():
    raise ValueError("parâmetro inválido")


@tratar_erros
def _levanta_excecao_generica():
    raise RuntimeError("falha inesperada")


@tratar_erros
def _ok(x):
    return x * 2


def test_tratar_erros_value_error_retorna_json_erro():
    resultado = json.loads(_levanta_value_error())
    assert resultado == {"erro": "parâmetro inválido"}


def test_tratar_erros_excecao_generica_retorna_json_erro():
    resultado = json.loads(_levanta_excecao_generica())
    assert "erro" in resultado


def test_tratar_erros_sucesso_passa_adiante():
    assert _ok(21) == 42


if __name__ == "__main__":
    test_tratar_erros_value_error_retorna_json_erro()
    test_tratar_erros_excecao_generica_retorna_json_erro()
    test_tratar_erros_sucesso_passa_adiante()
    print("Todos os testes de erros passaram.")
