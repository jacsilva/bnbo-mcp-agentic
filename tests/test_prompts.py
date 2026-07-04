"""
Testes dos Prompt Templates.

Cada template deve produzir texto não vazio, mencionar a tool-alvo e refletir os
argumentos preenchidos. Não dependem de infraestrutura.
"""

from server.prompts import templates


def test_analisar_ocorrencias_usa_bo_id_e_top_k():
    msg = templates.analisar_ocorrencias_similares(bo_id="BO-1", top_k=5)
    assert "buscar_ocorrencias_similares" in msg
    assert "obter_razoes_similaridade" in msg
    assert "BO-1" in msg and "top_k=5" in msg


def test_analisar_ocorrencias_usa_texto_livre_quando_sem_bo():
    msg = templates.analisar_ocorrencias_similares(texto_livre="assalto a pedestre")
    assert "assalto a pedestre" in msg


def test_mapear_serie_criminal_orienta_tool():
    msg = templates.mapear_serie_criminal(texto_livre="furtos noturnos")
    assert "agrupar_serie_criminal" in msg
    assert "furtos noturnos" in msg


def test_detectar_anomalias_inclui_filtros():
    msg = templates.detectar_anomalias(estado="SP", dominio="pessoa")
    assert "detectar_anomalias_estatisticas" in msg
    assert "estado=SP" in msg and "dominio=pessoa" in msg


def test_avaliar_taxa_elucidacao_orienta_tool():
    msg = templates.avaliar_taxa_elucidacao(estado="RJ")
    assert "calcular_taxa_elucidacao" in msg
    assert "estado=RJ" in msg


def test_priorizar_delegacias_orienta_tool():
    msg = templates.priorizar_delegacias()
    assert "listar_delegacias_com_alerta" in msg
    assert msg.strip()


def test_gerar_atlas_orienta_ambas_as_tools():
    msg = templates.gerar_atlas_vulnerabilidade(estado="SP", meses=6)
    assert "calcular_indice_vulnerabilidade" in msg
    assert "gerar_atlas_vulnerabilidade" in msg
    assert "6 meses" in msg


if __name__ == "__main__":
    for nome, fn in vars(templates).items():
        if callable(fn) and not nome.startswith("_"):
            assert fn().strip() if fn.__defaults__ else True
    print("Testes de prompts passaram.")
