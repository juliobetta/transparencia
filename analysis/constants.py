# Thresholds for contratação direta / dispensa de licitação (Art. 75, Lei 14.133/2021)
# Updated by Decreto nº 12.807/2025 (IPCA-E 4,41%); effective 01/01/2026
THRESHOLD_OBRAS_ENGENHARIA = 130_984.20
THRESHOLD_COMPRAS_SERVICOS = 65_492.11
THRESHOLD_VEICULOS = 10_478.74  # Art. 75 §7º; also the verbal contract ceiling (Art. 95)

# Default threshold for analyses that cannot categorize contract type
THRESHOLD_DEFAULT = THRESHOLD_COMPRAS_SERVICOS

# Proximity band used to flag potential bid-splitting (contracts priced just below the limit)
NEAR_THRESHOLD_PCT = 0.20

# Keywords used to detect vehicle-maintenance contracts from the objeto field
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


def dispensation_threshold(numobra: str | None, tipocoobra: str | None, objeto: str | None) -> float:
    """Return the applicable dispensation threshold (Decreto 12.807/2025) for a contract.

    Priority: obras/engineering > vehicle maintenance > compras/services (conservative default).
    """
    if (numobra and str(numobra).strip()) or (tipocoobra and str(tipocoobra).strip()):
        return THRESHOLD_OBRAS_ENGENHARIA
    obj = str(objeto or "").lower()
    if any(term in obj for term in _VEHICLE_TERMS):
        return THRESHOLD_VEICULOS
    return THRESHOLD_COMPRAS_SERVICOS
