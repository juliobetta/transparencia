# Limites para contratação direta / dispensa de licitação (Art. 75, Lei 14.133/2021)
# Atualizado pelo Decreto nº 12.807/2025 (IPCA-E 4,41%); em vigor desde 01/01/2026
THRESHOLD_OBRAS_ENGENHARIA = 130_984.20
THRESHOLD_COMPRAS_SERVICOS = 65_492.11
THRESHOLD_VEICULOS = 10_478.74  # Art. 75 §7º; também o limite para contratos verbais (Art. 95)

# Limite padrão para análises que não conseguem categorizar o tipo de contrato
THRESHOLD_DEFAULT = THRESHOLD_COMPRAS_SERVICOS

# Faixa de proximidade usada para sinalizar potencial fracionamento de licitação (contratos precificados logo abaixo do limite)
NEAR_THRESHOLD_PCT = 0.20

# Limites da LRF para gasto com pessoal — Poder Executivo municipal (LC 101/2000)
LRF_PESSOAL_LIMITE_LEGAL = 54.0  # Art. 20, III, b
LRF_PESSOAL_LIMITE_PRUDENCIAL = 51.3  # Art. 22, parágrafo único (95% × 54%)
LRF_PESSOAL_LIMITE_ALERTA = 48.6  # Art. 59, §1º, I (90% × 54%)

# Palavras-chave usadas para detectar contratos de manutenção de veículos a partir do campo objeto
_VEHICLE_TERMS = (
    "veículo",
    "veiculo",
    "automóvel",
    "automovel",
    "motocicleta",
    "caminhão",
    "caminhao",
    "ônibus",
    "onibus",
    "frota",
)

# Elemento de despesa para folha de pagamento (Pessoal)
ELEMENTO_FOLHA_PESSOAL = "11"

# Natureza da despesa para Subvenções Sociais
ELEMENTO_SUBVENCOES_SOCIAIS = "43"

# Mapeamento de elementos de despesa
FORNECEDORES_NATUREZA_MAP = {
    "30": "30 - Material de Consumo",
    "36": "36 - Serv. Terceiros (Pessoa Física)",
    "39": "39 - Serv. Terceiros (Pessoa Jurídica)",
    "52": "52 - Equipamentos e Mat. Permanente",
}

DESPESAS_MAP = {
    **FORNECEDORES_NATUREZA_MAP,
    ELEMENTO_SUBVENCOES_SOCIAIS: "43 - Subvenções Sociais",
    ELEMENTO_FOLHA_PESSOAL: "11 - Folha de Pagamento (Pessoal)",
}


def dispensation_threshold(numobra: str | None, tipocoobra: str | None, objeto: str | None) -> float:
    """Retorna o limite de dispensa aplicável (Decreto 12.807/2025) para um contrato.

    Prioridade: obras/engenharia > manutenção de veículos > compras/serviços (padrão conservador).
    """
    if (numobra and str(numobra).strip()) or (tipocoobra and str(tipocoobra).strip()):
        return THRESHOLD_OBRAS_ENGENHARIA
    obj = str(objeto or "").lower()
    if any(term in obj for term in _VEHICLE_TERMS):
        return THRESHOLD_VEICULOS
    return THRESHOLD_COMPRAS_SERVICOS
