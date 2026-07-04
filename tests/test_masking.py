from utils.masking import is_cpf, mask_cpf, mask_name


def test_is_cpf():
    assert is_cpf("12345678901") is True
    assert is_cpf("123.456.789-01") is True
    assert is_cpf("123456789") is False  # CNPJ curto
    assert is_cpf("12345678901234") is False  # CNPJ longo


def test_mask_cpf():
    assert mask_cpf("12345678901") == "123.XXX.XXX-01"
    assert mask_cpf("123.456.789-01") == "123.XXX.XXX-01"
    assert mask_cpf("invalid") == "invalid"


def test_mask_name():
    assert mask_name("JOAO SILVA") == "JS"
    assert mask_name("MARIA") == "M"
    assert mask_name("JOAO GILBERTO SILVA") == "JGS"
