PORTAL_URL = "https://transparencia.porciuncula.rj.gov.br/transparencia/"

TERMS: dict[str, str] = {
    "Dotação Orçamentária": "O total do orçamento aprovado pela Câmara Municipal para o ano — o limite de gastos.",
    "Dotação Atualizada": "O orçamento após ajustes (acréscimos ou cortes) feitos durante o ano.",
    "Empenho": "Reserva formal de recursos — a prefeitura se compromete a pagar um fornecedor. O dinheiro ainda não saiu.",
    "Liquidação": "A prefeitura confirma que o serviço ou produto foi entregue. O pagamento está agora autorizado.",
    "Pagamento": "O dinheiro efetivamente saiu da conta da prefeitura.",
    "Resto a Pagar": "Valores empenhados ou liquidados que não foram pagos até o fim do ano — passam para o ano seguinte.",
    "Licitação": "Processo de concorrência pública onde fornecedores disputam um contrato. Obrigatório por lei acima de certos valores.",
    "Dispensa de Licitação": "Isenção legal da licitação — permitida apenas em situações específicas (emergências, contratos de baixo valor). O uso excessivo é um sinal de alerta.",
    "Inexigibilidade": "Contratação direta sem licitação quando há fornecedor exclusivo ou notória especialização. Deve ser justificada.",
    "Fornecedor": "Empresa ou pessoa física que presta serviços ou fornece produtos à prefeitura.",
    "Órgão": "Secretaria ou departamento municipal (ex.: Secretaria de Saúde).",
    "Unidade": "Subdivisão dentro de um órgão.",
    "Receita Própria": "Receita que a prefeitura gera com impostos e taxas locais. Quanto maior, menor a dependência de repasses.",
    "FPM (Fundo de Participação dos Municípios)": "Repasse federal do qual a maioria dos pequenos municípios brasileiros depende muito.",
    "Diária": "Valor pago a servidor por viagem a serviço. O uso excessivo pode indicar irregularidade.",
    "Emenda Impositiva": "Recurso que vereadores têm o direito de destinar ao orçamento municipal.",
    "Extra-orçamentário": "Movimentação financeira fora do orçamento aprovado, como depósitos de terceiros.",
}


def tooltip(term: str) -> str:
    return TERMS.get(term, "")
