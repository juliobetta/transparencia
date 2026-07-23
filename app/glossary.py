TERMS: dict[str, str] = {
    "Dotação Orçamentária": "O total do orçamento aprovado pela Câmara Municipal para o ano — o limite de gastos.",
    "Dotação Atualizada": "O orçamento aprovado, somado aos créditos adicionais e subtraído pelas anulações. É como o limite de um cartão de crédito: o valor pode subir com um aumento de limite ou descer com um bloqueio.",
    "Empenho": "Reserva formal de recursos para garantir o pagamento de um fornecedor. É como um 'cheque assinado mas não entregue': o valor está reservado, mas o dinheiro ainda não saiu da conta da prefeitura.",
    "Liquidação": "A confirmação de que o serviço ou produto foi entregue. É como um 'atestado de entrega': a prefeitura confere o serviço para autorizar o pagamento final.",
    "Pagamento": "O dinheiro efetivamente saiu da conta da prefeitura. É o pagamento final da fatura.",
    "Resto a Pagar": "Valores empenhados ou liquidados que não foram quitados até o fim do ano. É como uma 'fatura que ficou para o mês seguinte': despesas de um ano anterior pagas com o orçamento do ano novo.",
    "Licitação": "Processo de concorrência pública onde fornecedores disputam um contrato. Obrigatório por [Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/) acima de R$ 62.725,59 para bens e serviços.",
    "Dispensa de Licitação": "Isenção legal da licitação permitida para contratos de baixo valor (até R$ 62.725,59 para bens e serviços, conforme [Lei 14.133/21, Art. 75, I](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm)) ou situações específicas como emergências. O uso excessivo acima desse limite é um sinal de alerta.",
    "Inexigibilidade": "Contratação direta sem licitação quando há fornecedor exclusivo ou notória especialização. Deve ser justificada.",
    "Fornecedor": "Empresa ou pessoa física que presta serviços ou fornece produtos à prefeitura.",
    "Órgão": "Secretaria ou departamento municipal (ex.: Secretaria de Saúde).",
    "Unidade": "Subdivisão dentro de um órgão.",
    "Receita Própria": "Receita que a prefeitura gera com impostos e taxas locais. Quanto maior, menor a dependência de repasses.",
    "FPM (Fundo de Participação dos Municípios)": "Repasse federal do qual a maioria dos pequenos municípios brasileiros depende muito.",
    "Diária": "Valor pago a servidor por viagem a serviço. O uso excessivo pode indicar irregularidade.",
    "Emenda Impositiva": "Recurso que parlamentares destinam ao orçamento federal para obras e serviços em suas bases, com execução obrigatória pelo governo.",
    "Adesão de Ata (Carona)": "Contratação direta aproveitando uma licitação já realizada por outro órgão. Evita nova licitação, mas o uso excessivo — especialmente na Saúde — pode indicar fuga ao controle.",
    "Pregão Eletrônico": "Modalidade de licitação feita pela internet, voltada para aquisição de bens e serviços comuns, garantindo ampla concorrência.",
    "Pregão Presencial": "Modalidade de licitação feita presencialmente, também voltada para bens e serviços comuns.",
}


def tooltip(term: str) -> str:
    return TERMS.get(term, "")
