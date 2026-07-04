"""Testes unitários de services.atlas — apenas a parte sem dependência de banco."""

from services.atlas import classificar_jenks, _classe_para_valor


def test_classificar_jenks_limites():
    valores = [0.1, 0.15, 0.5, 0.55, 0.9, 0.95]
    breaks = classificar_jenks(valores, n_classes=3)
    assert breaks[0] == min(valores)
    assert breaks[-1] == max(valores)
    assert breaks == sorted(breaks)
    assert len(breaks) == 4


def test_classificar_jenks_menos_valores_que_classes():
    breaks = classificar_jenks([0.2, 0.8], n_classes=5)
    assert breaks[0] == 0.2
    assert breaks[-1] == 0.8


def test_classe_para_valor():
    breaks = [0.0, 0.3, 0.6, 1.0]
    assert _classe_para_valor(0.0, breaks) == 1
    assert _classe_para_valor(0.4, breaks) == 2
    assert _classe_para_valor(1.0, breaks) == 3


if __name__ == "__main__":
    test_classificar_jenks_limites()
    test_classificar_jenks_menos_valores_que_classes()
    test_classe_para_valor()
    print("Todos os testes de atlas passaram.")
