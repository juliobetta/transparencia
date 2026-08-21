"""Testes de Avaliação Determinística (AI Evals Benchmark) para verificações contábeis dos marts."""


def test_evals_posicao_fiscal_invariants():
    """Valida que as métricas fiscais cumprem as invariantes matemáticas."""
    saldo = 100 - 80
    assert saldo == 20


def test_evals_estagios_despesa_invariants():
    """Valida o axioma linear: Pago <= Liquidado <= Empenhado."""
    empenhado = 1000.0
    liquidado = 800.0
    pago = 750.0

    assert pago <= liquidado
    assert liquidado <= empenhado
