"""Testes unitários de ml.stats — apenas a parte sem dependência de banco."""

from ml.stats import _calcular_z_scores


def test_calcular_z_scores_serie_curta_retorna_none():
    assert _calcular_z_scores([1, 2]) is None


def test_calcular_z_scores_sem_variacao_retorna_none():
    assert _calcular_z_scores([5, 5, 5, 5]) is None


def test_calcular_z_scores_detecta_pico():
    z_scores = _calcular_z_scores([10, 11, 9, 10, 50])
    assert z_scores is not None
    assert max(z_scores, key=abs) == z_scores[-1]
    assert z_scores[-1] > 1.5


if __name__ == "__main__":
    test_calcular_z_scores_serie_curta_retorna_none()
    test_calcular_z_scores_sem_variacao_retorna_none()
    test_calcular_z_scores_detecta_pico()
    print("Todos os testes de stats passaram.")
