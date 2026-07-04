"""
Testes unitários do contrato de validação Pydantic (entrada + saída).

Não dependem de banco/rede: exercitam os modelos de `server.schemas` e a
pilha de decorators (`tratar_erros` + `coage_numericos` + `valida_entrada`)
sobre uma tool fake.
"""

import datetime
import json

from server.schemas import saida
from server.schemas.entrada import BuscarOcorrenciasSimilaresArgs, ExportarResultadoArgs
from server.tools._coercao import coage_numericos
from server.tools._erros import tratar_erros
from server.tools._validacao import valida_entrada


@tratar_erros
@coage_numericos
@valida_entrada(BuscarOcorrenciasSimilaresArgs)
def _tool_fake(bo_id: str = "", texto_livre: str = "", top_k: "int | str" = 10) -> str:
    return json.dumps({"top_k": top_k, "tipo": type(top_k).__name__})


def test_entrada_valida_passa_e_normaliza():
    m = BuscarOcorrenciasSimilaresArgs(texto_livre="x", top_k=5)
    assert m.top_k == 5


def test_entrada_top_k_fora_da_faixa_e_rejeitada():
    resultado = json.loads(_tool_fake(texto_livre="x", top_k=999))
    assert "erro" in resultado and "top_k" in resultado["erro"]


def test_entrada_exige_bo_id_ou_texto_livre():
    resultado = json.loads(_tool_fake())
    assert "erro" in resultado
    assert "bo_id" in resultado["erro"] or "texto_livre" in resultado["erro"]


def test_coercao_numerica_string_ainda_funciona():
    resultado = json.loads(_tool_fake(texto_livre="x", top_k="7"))
    assert resultado == {"top_k": 7, "tipo": "int"}


def test_formato_invalido_em_exportar_e_rejeitado():
    erros = []
    try:
        ExportarResultadoArgs(dados_json="[]", formato="xml")
    except Exception as e:
        erros.append(e)
    assert erros, "formato='xml' deveria ser rejeitado pelo Literal"


def test_saida_lista_ocorrencias_preserva_acentos():
    registros = [{
        "bo_id": "a1", "bo_numero": "BO-1", "natureza": "Roubo", "estado": "SP",
        "municipio": "São Paulo", "relato": "furto na praça",
        "data_hora": "2024-01-01T10:00:00", "score_semantico": 0.9,
        "score_final": 0.85, "razoes_estruturais": {"instrumento": 1.0},
    }]
    out = saida.ListaOcorrenciasSimilares.dump_json(
        saida.ListaOcorrenciasSimilares.validate_python(registros)
    ).decode()
    assert "São Paulo" in out and "praça" in out
    assert json.loads(out)[0]["score_final"] == 0.85


def test_saida_alerta_serializa_data_e_datetime():
    alertas = [{
        "estado": "SP", "municipio": "X", "dominio": "pessoa", "natureza": "Y",
        "mes": datetime.date(2024, 1, 1), "z_score": 3.1,
        "criado_em": datetime.datetime(2024, 1, 2, 8, 0, 0),
    }]
    out = json.loads(
        saida.ListaAlertas.dump_json(saida.ListaAlertas.validate_python(alertas)).decode()
    )
    assert out[0]["mes"] == "2024-01-01"
    assert out[0]["criado_em"].startswith("2024-01-02T08:00:00")


if __name__ == "__main__":
    test_entrada_valida_passa_e_normaliza()
    test_entrada_top_k_fora_da_faixa_e_rejeitada()
    test_entrada_exige_bo_id_ou_texto_livre()
    test_coercao_numerica_string_ainda_funciona()
    test_formato_invalido_em_exportar_e_rejeitado()
    test_saida_lista_ocorrencias_preserva_acentos()
    test_saida_alerta_serializa_data_e_datetime()
    print("Todos os testes de validação passaram.")
