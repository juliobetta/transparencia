from typing import Optional

from sqlmodel import Field, SQLModel


class Empresa(SQLModel, table=True):
    __tablename__ = "empresas"
    id: int = Field(primary_key=True)
    nome: Optional[str] = None


class Metadata(SQLModel, table=True):
    __tablename__ = "metadata"
    portal_slug: str = Field(primary_key=True)
    key: str = Field(primary_key=True)
    value: Optional[str] = None


class DespesaPorOrgao(SQLModel, table=True):
    __tablename__ = "despesas_por_orgao"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    empenhado: Optional[str] = None
    liquidado: Optional[str] = None
    pago: Optional[str] = None
    dotac: Optional[str] = None
    altdo: Optional[str] = None
    dotacao_atualizada: Optional[str] = None


class DespesaPorUnidade(SQLModel, table=True):
    __tablename__ = "despesas_por_unidade"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    empenhado: Optional[str] = None
    liquidado: Optional[str] = None
    pago: Optional[str] = None
    dotac: Optional[str] = None
    altdo: Optional[str] = None
    dotacao_atualizada: Optional[str] = None


class DespesaPorFornecedor(SQLModel, table=True):
    __tablename__ = "despesas_por_fornecedor"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    empenhado: Optional[str] = None
    liquidado: Optional[str] = None
    pago: Optional[str] = None
    insmf: Optional[str] = None
    cepci: Optional[str] = None


class DespesaGeral(SQLModel, table=True):
    __tablename__ = "despesas_gerais"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    descricao: Optional[str] = None
    fornecedor: Optional[str] = None
    empenhado: Optional[str] = None
    liquidado: Optional[str] = None
    pago: Optional[str] = None
    data_empenho: Optional[str] = None
    orgao: Optional[str] = None
    mes: Optional[str] = None
    pkemp: Optional[str] = None
    pkempa: Optional[str] = None
    codigo: Optional[str] = None
    tpem: Optional[str] = None
    codif: Optional[str] = None
    nomefor: Optional[str] = None
    fongruponome: Optional[str] = None
    foncodigonome: Optional[str] = None
    descfonrec: Optional[str] = None
    proc: Optional[str] = None
    codlo: Optional[str] = None
    cfpro: Optional[str] = None
    funcao: Optional[str] = None
    funcaonome: Optional[str] = None
    subfuncao: Optional[str] = None
    subfuncaonome: Optional[str] = None
    catec: Optional[str] = None
    fongrupo: Optional[str] = None
    fongrupodesc: Optional[str] = None
    foncodigo: Optional[str] = None
    foncodigodesc: Optional[str] = None
    fonro: Optional[str] = None
    fonrodesc: Optional[str] = None
    fonte_stn: Optional[str] = None
    fonte_stndesc: Optional[str] = None
    natureza: Optional[str] = None
    datae: Optional[str] = None
    nomeempresa: Optional[str] = None
    programa: Optional[str] = None
    programanome: Optional[str] = None
    projativ: Optional[str] = None
    projeto_atividade_nome: Optional[str] = None
    categoria: Optional[str] = None
    gruponatureza: Optional[str] = None
    modalidade: Optional[str] = None
    elemento: Optional[str] = None
    numlicit: Optional[str] = None
    licit: Optional[str] = None
    desclicit_detalhesempenho: Optional[str] = None
    produ: Optional[str] = None
    cpfformatado: Optional[str] = None
    empenhado_ate_a_data: Optional[str] = None
    liquidado_ate_a_data: Optional[str] = None
    pago_ate_a_data: Optional[str] = None
    anulado: Optional[str] = None
    reforco: Optional[str] = None
    dotac: Optional[str] = None
    altdo: Optional[str] = None
    dotacatualizada: Optional[str] = None
    ficha: Optional[str] = None
    vingrupo_vincodigo: Optional[str] = None
    vincodigonome: Optional[str] = None


class DespesaRestoPagar(SQLModel, table=True):
    __tablename__ = "despesas_restos_pagar"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    descricao: Optional[str] = None
    codigo: Optional[str] = None
    empenhado: Optional[str] = None
    liquidado: Optional[str] = None
    pago: Optional[str] = None


class DespesaExtraOrcamentaria(SQLModel, table=True):
    __tablename__ = "despesas_extra_orcamentaria"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    descricao: Optional[str] = None
    fornecedor: Optional[str] = None
    valor: Optional[str] = None
    codigo: Optional[str] = None
    datae: Optional[str] = None
    nomeempresa: Optional[str] = None
    nomenclatura: Optional[str] = None
    descricaodespesa: Optional[str] = None
    historico: Optional[str] = None
    numeroguia: Optional[str] = None
    dataguia: Optional[str] = None
    insmf: Optional[str] = None
    codigoadotado: Optional[str] = None
    pago: Optional[str] = None
    mes: Optional[str] = None


class DespesaPorExigibilidade(SQLModel, table=True):
    __tablename__ = "despesas_por_exigibilidade"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    tipo: str = Field(primary_key=True)
    empenho: str = Field(primary_key=True)
    valor: Optional[str] = None
    tipolista: Optional[str] = None
    codentidade: Optional[str] = None
    entidade: Optional[str] = None
    ficha: Optional[str] = None
    codlo: Optional[str] = None
    catec: Optional[str] = None
    fornecedor: Optional[str] = None
    vadem: Optional[str] = None
    vapag: Optional[str] = None
    desco: Optional[str] = None
    anula: Optional[str] = None
    pagliq: Optional[str] = None
    venci: Optional[str] = None
    dtpag: Optional[str] = None
    foninduso: Optional[str] = None
    fongrupo: Optional[str] = None
    foncodigo: Optional[str] = None
    vingrupo: Optional[str] = None
    vincodigo: Optional[str] = None
    fonro: Optional[str] = None
    justificativa: Optional[str] = None
    datajusti: Optional[str] = None
    justificativa_texto: Optional[str] = None
    tit_just: Optional[str] = None
    quebrou: Optional[str] = None
    fonte_nome: Optional[str] = None
    unidade_nome: Optional[str] = None
    contrato: Optional[str] = None
    contrato_categoria: Optional[str] = None
    contrato_categoria_descr: Optional[str] = None
    processoadm: Optional[str] = None
    proclic: Optional[str] = None
    numsub: Optional[str] = None
    dtatesto: Optional[str] = None
    cgc: Optional[str] = None
    dtprocesso: Optional[str] = None
    autorizadordespesa: Optional[str] = None
    insmf: Optional[str] = None
    cpf_autorizadordespesa: Optional[str] = None
    notas: Optional[str] = None
    nempg: Optional[str] = None
    anoemp: Optional[str] = None
    tpem: Optional[str] = None
    tit_hist: Optional[str] = None
    produ: Optional[str] = None
    valor_empenho: Optional[str] = None
    licit: Optional[str] = None
    pkemp: Optional[str] = None
    tipoquebra: Optional[str] = None
    motivo: Optional[str] = None
    ordem_liquidacao: Optional[str] = None


class Diaria(SQLModel, table=True):
    __tablename__ = "diarias"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    beneficiario: Optional[str] = None
    valor: Optional[str] = None
    destino: Optional[str] = None
    data: Optional[str] = None
    nempg: Optional[str] = None
    numeroliquidacao: Optional[str] = None
    ordempagamento: Optional[str] = None
    valoranulado: Optional[str] = None
    descricao: Optional[str] = None
    nome_elemento: Optional[str] = None
    pkemp: Optional[str] = None
    codorgao: Optional[str] = None
    nomeorgao: Optional[str] = None
    orgao: Optional[str] = None
    codunidade: Optional[str] = None
    nomeunidade: Optional[str] = None
    unidade: Optional[str] = None
    codif: Optional[str] = None
    favorecido: Optional[str] = None
    cargo: Optional[str] = None
    cpfformatado: Optional[str] = None
    quant: Optional[str] = None


class ReceitaOrcamentaria(SQLModel, table=True):
    __tablename__ = "receita_orcamentaria"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    previsto: Optional[str] = None
    arrecadado: Optional[str] = None
    ordem: Optional[str] = None
    empresanome: Optional[str] = None
    vincodigo: Optional[str] = None
    fontestn: Optional[str] = None
    fonte: Optional[str] = None
    nome: Optional[str] = None
    previsao_inicial: Optional[str] = None
    previsao_atualizada: Optional[str] = None
    arrecadado_periodo: Optional[str] = None
    arrecadado_total: Optional[str] = None


class ReceitaUniao(SQLModel, table=True):
    __tablename__ = "receita_uniao"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    previsto: Optional[str] = None
    arrecadado: Optional[str] = None
    ordem: Optional[str] = None
    nome: Optional[str] = None
    previsao_inicial: Optional[str] = None
    previsao_atualizada: Optional[str] = None
    arrecadado_periodo: Optional[str] = None
    arrecadado_total: Optional[str] = None


class ReceitaEstado(SQLModel, table=True):
    __tablename__ = "receita_estado"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    previsto: Optional[str] = None
    arrecadado: Optional[str] = None
    ordem: Optional[str] = None
    nome: Optional[str] = None
    previsao_inicial: Optional[str] = None
    previsao_atualizada: Optional[str] = None
    arrecadado_periodo: Optional[str] = None
    arrecadado_total: Optional[str] = None


class ReceitaExtraOrcamentaria(SQLModel, table=True):
    __tablename__ = "receita_extra_orcamentaria"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    valor: Optional[str] = None
    extra: Optional[str] = None
    dtlan: Optional[str] = None
    empresanome: Optional[str] = None
    origem: Optional[str] = None
    nomenclatura: Optional[str] = None
    historico: Optional[str] = None


class ReceitaDetalhe(SQLModel, table=True):
    __tablename__ = "receita_detalhes"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    previsto: Optional[str] = None
    arrecadado: Optional[str] = None
    nlanc: Optional[str] = None
    codre: Optional[str] = None
    fonte_recurso: Optional[str] = None
    nome_receita: Optional[str] = None
    historico: Optional[str] = None
    conta: Optional[str] = None
    agencia: Optional[str] = None
    banco: Optional[str] = None
    data_receita: Optional[str] = None
    valor: Optional[str] = None


class Licitacao(SQLModel, table=True):
    __tablename__ = "licitacoes"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    modalidade: Optional[str] = None
    objeto: Optional[str] = None
    valor: Optional[str] = None
    situacao: Optional[str] = None
    data_abertura: Optional[str] = None
    carona: Optional[str] = None
    discr: Optional[str] = None
    proclicitacao: Optional[str] = None
    nlicitacao: Optional[str] = None
    numlic: Optional[str] = None
    proclic: Optional[str] = None
    licit: Optional[str] = None
    datae: Optional[str] = None
    dtenc: Optional[str] = None
    registropreco: Optional[str] = None
    discr10: Optional[str] = None
    licitacao: Optional[str] = None
    comp: Optional[str] = None
    arquivo: Optional[str] = None
    especietce: Optional[str] = None
    especietce_nro: Optional[str] = None
    dtenv: Optional[str] = None
    horenv: Optional[str] = None
    chamadapub: Optional[str] = None
    codtce: Optional[str] = None
    orcamento_sigiloso: Optional[str] = None
    valor1: Optional[str] = None
    edital: Optional[str] = None
    participantes: Optional[str] = None
    cpfcnpj: Optional[str] = None
    nomeempresa: Optional[str] = None
    artigo_inciso: Optional[str] = None
    dtpropostaini: Optional[str] = None
    dtpropostafim: Optional[str] = None
    mes: Optional[str] = None


class Contrato(SQLModel, table=True):
    __tablename__ = "contratos"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    fornecedor: Optional[str] = None
    objeto: Optional[str] = None
    valor: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    licitacao_numero: Optional[str] = None
    codigo: Optional[str] = None
    fundlegal: Optional[str] = None
    licit: Optional[str] = None
    proclic: Optional[str] = None
    modali: Optional[str] = None
    numlicmod: Optional[str] = None
    nproli: Optional[str] = None
    valcon: Optional[str] = None
    dtassi: Optional[str] = None
    tipoco: Optional[str] = None
    regexe: Optional[str] = None
    garant: Optional[str] = None
    vigeni: Optional[str] = None
    vigenf: Optional[str] = None
    respon: Optional[str] = None
    respon_doc: Optional[str] = None
    objeto_completo: Optional[str] = None
    numobra: Optional[str] = None
    entidade: Optional[str] = None
    tipocoobra: Optional[str] = None
    balco_debito: Optional[str] = None
    cpftra: Optional[str] = None
    cpfleg: Optional[str] = None
    contratonum: Optional[str] = None
    multa_rescisoria: Optional[str] = None
    multa_inadimplencia: Optional[str] = None
    empenhadoant: Optional[str] = None
    empenhado: Optional[str] = None
    liquidadoant: Optional[str] = None
    liquidado: Optional[str] = None
    aditado: Optional[str] = None
    saldoempenhar: Optional[str] = None
    saldoliquidar: Optional[str] = None
    numlic: Optional[str] = None
    codtce: Optional[str] = None
    insmf: Optional[str] = None
    respon2: Optional[str] = None
    dtpubl: Optional[str] = None
    codlo_gestor: Optional[str] = None
    codlo_gestornome: Optional[str] = None
    vencimento_atual: Optional[str] = None
    dtanula: Optional[str] = None
    tipoanu: Optional[str] = None
    mes: Optional[str] = None


class Transferencia(SQLModel, table=True):
    __tablename__ = "transferencias"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    codigo: str = Field(primary_key=True)
    descricao: Optional[str] = None
    valor: Optional[str] = None
    mes: Optional[str] = None
    entidade_pagadora: Optional[str] = None
    entidade_recebedora: Optional[str] = None
    cnpjpagadora: Optional[str] = None
    cnpjrecebedora: Optional[str] = None
    repasse: Optional[str] = None
    devolucao: Optional[str] = None
    entidadedestino: Optional[str] = None
    previsto: Optional[str] = None
    dtlan: Optional[str] = None


class EmendaImpositiva(SQLModel, table=True):
    __tablename__ = "emendas_impositivas"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    descricao: Optional[str] = None
    valor: Optional[str] = None


class EmendaCad(SQLModel, table=True):
    __tablename__ = "emendas_cad"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    numero: str = Field(primary_key=True)
    descricao: Optional[str] = None
    valor: Optional[str] = None
    pk_ep_emenda: Optional[str] = None
    numero_emenda: Optional[str] = None
    data: Optional[str] = None
    resumo: Optional[str] = None
    valor_total: Optional[str] = None
    tipo_emenda: Optional[str] = None
    nomeempresa: Optional[str] = None
    tipo_emenda_descr: Optional[str] = None
    esfera_origem: Optional[str] = None
    esfera_origem_descr: Optional[str] = None
    tipo_transferencia: Optional[str] = None
    tipo_transferencia_descr: Optional[str] = None
    ato_normativo: Optional[str] = None
    destinacao: Optional[str] = None
    destinacao_descr: Optional[str] = None
    receitaant: Optional[str] = None
    receita: Optional[str] = None
    empenhadoant: Optional[str] = None
    empenhado: Optional[str] = None
    liquidadoant: Optional[str] = None
    liquidado: Optional[str] = None
    autor: Optional[str] = None
    beneficiario: Optional[str] = None
    objeto: Optional[str] = None


class Pessoal(SQLModel, table=True):
    __tablename__ = "pessoal"
    ano: int = Field(primary_key=True)
    empresa: str = Field(primary_key=True)
    mes: str = Field(primary_key=True)
    matricula: str = Field(primary_key=True)
    nome: Optional[str] = None
    cargo: Optional[str] = None
    remuneracao: Optional[str] = None
    registro: Optional[str] = None
    referencia: Optional[str] = None
    referencia_nome: Optional[str] = None
    id: Optional[str] = None
    contrato: Optional[str] = None
    nome_social: Optional[str] = None
    divisao: Optional[str] = None
    subdivisao: Optional[str] = None
    unidade: Optional[str] = None
    vinculo: Optional[str] = None
    categoriafuncional: Optional[str] = None
    dataadmissao: Optional[str] = None
    datadesligamento: Optional[str] = None
    refsalatual: Optional[str] = None
    nomerefsalatual: Optional[str] = None
    atoadmissao: Optional[str] = None
    atodemissao: Optional[str] = None
    dataadmissaocomissao: Optional[str] = None
    atoadmissaocomissao: Optional[str] = None
    proventos: Optional[str] = None
    descontos: Optional[str] = None
    natureza: Optional[str] = None
    formaprovimento: Optional[str] = None
    numdoccriacaocargo: Optional[str] = None
    tiporegime: Optional[str] = None
    situacaofuncional: Optional[str] = None
    horasemanal: Optional[str] = None
    tipocontrato: Optional[str] = None
    dttermino: Optional[str] = None
    cpf: Optional[str] = None
    cpfformatado: Optional[str] = None
    cargoinicio: Optional[str] = None
    atividade: Optional[str] = None
    nomeatividade: Optional[str] = None
    localdetrabalho: Optional[str] = None
    valor_he: Optional[str] = None
    valorinicialcargo: Optional[str] = None
    liquido_isnull_proventos_0_isnull_descontos_0: Optional[str] = None
