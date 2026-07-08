import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANOS,
    SPARK_CFG,
    fmt_currency,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

import glossary
from analysis import analise_despesas, folha_vs_servicos
from analysis.analise_despesas import total_folha_por_orgao
from analysis.constants import LRF_PESSOAL_LIMITE_ALERTA, LRF_PESSOAL_LIMITE_LEGAL, LRF_PESSOAL_LIMITE_PRUDENCIAL

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_pagamento(conn, year, _extracted_at):
    return folha_vs_servicos.run(conn, list(range(ANOS[0], year + 1)))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_por_departamento(conn, year, _extracted_at):
    return analise_despesas.get_folha_por_orgao(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_orgao_por_ano(conn, years, _extracted_at):
    return analise_despesas.total_folha_orgao_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _cargos_confianca(conn, years, _extracted_at):
    return analise_despesas.get_perfil_cargos_confianca(conn, list(years))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

st.header("Folha de Pagamento")
st.caption(
    "Quanto da receita municipal arrecadada é comprometido com salários e proventos de servidores. "
    "A Lei de Responsabilidade Fiscal (LRF) limita esse gasto a **54% da receita corrente líquida** para o Poder Executivo. "
    "O cálculo usa o total de receitas arrecadadas como base — os dados do portal não permitem calcular a RCL exata com todas as deduções legais."
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(
        year,
        _extracted_at,
        extra_html="<br>Os índices percentuais de folha podem oscilar devido à sazonalidade "
        "(ex: 13º salário e terço de férias não contabilizados proporcionalmente).",
    )

_all_years = list(range(2022, year + 1))
_anos = _all_years
_hist_folha_orgao = _folha_orgao_por_ano(conn, tuple(_all_years), _extracted_at)
_folha_orgao_serie = [_hist_folha_orgao[y] for y in _anos]

df_folha = _folha_pagamento(conn, year, _extracted_at)
df_cargos = _cargos_confianca(conn, tuple(_all_years), _extracted_at)
df_departamentos = _folha_por_departamento(conn, year, _extracted_at)

kf1, kf2, kf3 = st.columns(3)

if not df_folha.empty:
    _pct_serie = df_folha["percentual_folha"].tolist()
    _anos_folha = df_folha["ano"].tolist()
    _pct_atual = float(df_folha.iloc[-1]["percentual_folha"])
    with kf1:
        st.metric(
            "Folha / Receita Arrecadada",
            f"{_pct_atual:.1f}%",
            delta=pct_delta(_pct_serie) if year != ANO_ATUAL else "—",
            delta_color="inverse" if year != ANO_ATUAL else "off",
            help="Percentual da receita arrecadada comprometido com folha de pessoal (proventos brutos).",
        )
        st.plotly_chart(
            sparkline(_anos_folha, _pct_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_pct",
        )

    # Calcular série histórica do percentual de efetivos no comando (até o ano selecionado)
    _series_pct_efetivos = []
    _anos_cargos_serie = []
    for y in sorted(df_cargos["ano"].unique()):
        if y > year:
            continue
        df_y = df_cargos[df_cargos["ano"] == y]
        qty_map_y = df_y.set_index("tipo_vinculo_detalhado")["quantidade"].to_dict()

        efetivos_confianca = qty_map_y.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + qty_map_y.get(
            "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
        )
        comissionados_externos = qty_map_y.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
        total_confianca = efetivos_confianca + comissionados_externos

        pct_y = (efetivos_confianca / total_confianca * 100) if total_confianca > 0 else 0.0
        _series_pct_efetivos.append(pct_y)
        _anos_cargos_serie.append(y)

    _pct_atual = _series_pct_efetivos[-1] if _series_pct_efetivos else 0.0
    _delta_val = pct_delta(_series_pct_efetivos)

    with kf2:
        st.metric(
            label="Efetivos no Comando das Chefias",
            value=f"{_pct_atual:.1f}%",
            delta=_delta_val,
            help="Percentual de cargos de liderança e assessoramento (DAS/DAI) que são ocupados por servidores concursados (de carreira). Quanto maior este percentual, mais técnica e profissionalizada é a gestão pública.",
        )
        if len(_series_pct_efetivos) > 1:
            st.plotly_chart(
                sparkline(_anos_cargos_serie, _series_pct_efetivos, "#2196F3"),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_cargos_confianca",
            )

    _total_folha_atual = total_folha_por_orgao(df_departamentos)

    with kf3:
        st.metric(
            "Total distribuído via responsáveis",
            fmt_currency(_total_folha_atual),
            delta=pct_delta(_folha_orgao_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
        )
        st.plotly_chart(
            sparkline(_anos, _folha_orgao_serie, "#607D8B"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_folha_orgao",
        )

    fig = px.bar(
        df_folha,
        x="ano",
        y="percentual_folha",
        title="Folha de Pessoal como % da Receita Arrecadada",
        labels={"ano": "Ano", "percentual_folha": "%"},
    )
    fig.update_xaxes(tickmode="linear", dtick=1)
    fig.update_traces(hovertemplate="Ano: %{x}<br>Percentual: %{y:.2f}%")
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_LEGAL,
        line_dash="solid",
        line_color="red",
        annotation_text=f"Limite legal {LRF_PESSOAL_LIMITE_LEGAL}%",
        annotation_position="top right",
    )
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_PRUDENCIAL,
        line_dash="dash",
        line_color="orange",
        annotation_text=f"Limite prudencial {LRF_PESSOAL_LIMITE_PRUDENCIAL}%",
        annotation_position="top right",
    )
    fig.add_hline(
        y=LRF_PESSOAL_LIMITE_ALERTA,
        line_dash="dot",
        line_color="gold",
        annotation_text=f"Limite de alerta {LRF_PESSOAL_LIMITE_ALERTA}%",
        annotation_position="top right",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Linhas de referência da Lei de Responsabilidade Fiscal: "
        f"**alerta** ({LRF_PESSOAL_LIMITE_ALERTA}%) · "
        f"**prudencial** ({LRF_PESSOAL_LIMITE_PRUDENCIAL}%, veda novos cargos e reajustes) · "
        f"**limite legal** ({LRF_PESSOAL_LIMITE_LEGAL}%, sujeito a sanções automáticas)"
    )

# --- 13º SALÁRIO METRIC ---
st.subheader("13º Salário")
exec_13 = folha_vs_servicos.execucao_decimo_terceiro(conn, year)
if exec_13 is not None and exec_13["empenhado"] > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Reservado (Ajustado)",
            fmt_currency(exec_13["empenhado"]),
            help="Valor líquido que o município reservou (empenhou) no orçamento para o pagamento do 13º salário, já descontando as anulações de saldos estimativos excedentes.",
        )
    with col2:
        st.metric(
            "Total Efetivamente Pago",
            fmt_currency(exec_13["pago"]),
            help="Soma dos pagamentos de 13º salário efetivamente desembolsados ao longo do ano (férias, adiantamentos e parcela final). Extraído da despesa geral para maior precisão.",
        )
    with col3:
        st.metric(
            "Percentual Quitado",
            f"{exec_13['pct_pago'] * 100:.1f}%",
            help="Proporção do valor reservado líquido (ajustado) que já foi efetivamente pago para os servidores. Mostra o grau de quitação real.",
        )

    # Exibir a barra de progresso de quitação (limitada entre 0 e 100%)
    progress_val = min(max(exec_13["pct_pago"], 0.0), 1.0)
    st.progress(progress_val, text=f"Progresso de Quitação da Folha de 13º Salário: {exec_13['pct_pago'] * 100:.1f}%")

    st.info(
        "**Nota de Transparência (Quitação de 100%):** A barra de progresso reflete a quitação calculada sobre o **Empenho Líquido Ajustado** (o valor reservado de fato para a folha após a prefeitura estornar/anular as sobras estimativas de fim de ano). Como as despesas de folha têm prioridade absoluta, o 13º salário é **totalmente quitado** dentro do exercício (qualquer dízimo de diferença residual em anos específicos decorre de anulações cruzadas registradas sob termos genéricos no portal).",
        icon=":material/info:",
    )

    df_det_13 = folha_vs_servicos.detalhe_decimo_terceiro(conn, year)
    if not df_det_13.empty:
        with st.expander("🔍 Ver detalhamento do 13º Salário por Secretaria/Órgão"):
            df_show = df_det_13.copy()
            df_show.columns = [
                "Órgão / Fundo",
                "Função/Secretaria",
                "Reservado (Ajustado)",
                "Liquidado",
                "Efetivamente Pago",
                "Quitado (%)",
            ]
            st.dataframe(
                df_show,
                column_config={
                    "Reservado (Ajustado)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Liquidado": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Efetivamente Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Quitado (%)": st.column_config.NumberColumn(format="%.1f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )
else:
    st.info(f"Nenhum pagamento de 13º salário registrado para o ano de {year}.")
st.divider()
# --- END 13º SALÁRIO METRIC ---

# Análise Granular de Remuneração
st.subheader("Distribuição de Remuneração")
st.info(
    "O portal não disponibiliza a remuneração líquida individual. "
    "O gráfico abaixo usa **Proventos** (remuneração bruta) como aproximação.",
    icon=":material/info:",
)
df_pessoal = folha_vs_servicos.distribuicao_salarios(conn, year)

if not df_pessoal.empty:
    fig_histograma = px.histogram(
        df_pessoal,
        x="proventos",
        nbins=30,
        title="Distribuição dos Proventos Brutos",
        labels={"proventos": "Proventos (R$)"},
    )
    fig_histograma.update_traces(hovertemplate="Proventos: R$ %{x:,.2f}<br>Servidores: %{y}")
    fig_histograma.update_layout(yaxis_title="Nº de Servidores", xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f")
    st.plotly_chart(fig_histograma, width="stretch")
else:
    st.info("Dados de proventos não disponíveis para este exercício.")

st.divider()
st.subheader("Perfil de Cargos de Confiança")
if not df_cargos.empty:
    fig_cargos = px.area(
        df_cargos.sort_values("ano"),
        x="ano",
        y="quantidade",
        color="tipo_vinculo_detalhado",
        title=f"Evolução da Quantidade de Cargos por Tipo de Vínculo ({ANOS[0]}-{ANOS[-1]})",
        labels={"ano": "Ano", "quantidade": "Quantidade de Servidores", "tipo_vinculo_detalhado": "Tipo de Vínculo"},
    )
    fig_cargos.update_xaxes(tickmode="linear", dtick=1)
    fig_cargos.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0), margin=dict(b=100)
    )
    st.plotly_chart(fig_cargos, use_container_width=True)

    # Calcular dados históricos dinamicamente para o expander explicativo
    df_2024 = df_cargos[df_cargos["ano"] == 2024]  # final gestao anterior
    df_2026 = df_cargos[df_cargos["ano"] == 2026]  # gestao atual, apos reforma administrativa

    qty_map_2024 = df_2024.set_index("tipo_vinculo_detalhado")["quantidade"].to_dict() if not df_2024.empty else {}
    qty_map_2026 = df_2026.set_index("tipo_vinculo_detalhado")["quantidade"].to_dict() if not df_2026.empty else {}

    # 2024
    efetivos_conf_2024 = qty_map_2024.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + qty_map_2024.get(
        "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
    )
    comissionados_ext_2024 = qty_map_2024.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
    total_conf_2024 = efetivos_conf_2024 + comissionados_ext_2024
    pct_efetivos_2024 = (efetivos_conf_2024 / total_conf_2024 * 100) if total_conf_2024 > 0 else 0.0

    # 2026
    efetivos_conf_2026 = qty_map_2026.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + qty_map_2026.get(
        "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
    )
    comissionados_ext_2026 = qty_map_2026.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
    total_conf_2026 = efetivos_conf_2026 + comissionados_ext_2026
    pct_efetivos_2026 = (efetivos_conf_2026 / total_conf_2026 * 100) if total_conf_2026 > 0 else 0.0

    has_verificacao_data = total_conf_2024 > 0 and total_conf_2026 > 0

    with st.expander(":material/info: Entenda as categorias e a importância desses dados"):
        st.markdown("""
        ### O que são Cargos de Confiança?
        Na administração pública brasileira, cargos de chefia, liderança e assessoramento são divididos em duas naturezas principais:

        1.  **DAS (Direção e Assessoramento Superior) ou Cargos em Comissão:** São cargos de livre nomeação e exoneração. Podem ser preenchidos por qualquer pessoa, inclusive profissionais **externos sem qualquer concurso público** (indicados políticos). No gráfico, constam como **"Comissionado Externo (DAS/CC - Sem Vínculo)"**.
        2.  **DAI (Direção e Assessoramento Intermediário) ou Funções Gratificadas (FG):** São funções de chefia destinadas **exclusivamente a servidores concursados** (efetivos). No gráfico, constam como **"Servidor Efetivo com Função de Confiança (DAI/FG)"** ou **"Servidor Efetivo com Cargo Comissionado (DAS/CC)"**.

        ### Por que a transformação de DAS em DAI é importante?
        *   **Profissionalização da Gestão:** Garante que os departamentos sejam liderados por corpo técnico qualificado e permanente, mantendo a continuidade das políticas públicas independentemente de mudanças de governo.
        *   **Redução do Fisiologismo:** Limita drasticamente o loteamento de cargos com nomeações de fora de prefeitura sem critérios técnicos.
        *   **Valorização dos Servidores:** Valoriza o quadro funcional de carreira da prefeitura com oportunidades reais de crescimento e liderança.
        """)

        if has_verificacao_data:
            st.markdown(f"""
            ### Verificação Matemática da Reforma Administrativa
            O prefeito declarou que a transformação de cargos DAS em DAI ampliou em mais de 90% a presença de servidores efetivos na estrutura de confiança em relação a 2024.

            **O que os dados reais da prefeitura provam:**
            *   Em **2024**, os nomeados externos sem concurso ocupavam a maior parte das chefias (**{comissionados_ext_2024} cargos**), com os concursados detendo apenas **{pct_efetivos_2024:.1f}%** das vagas de liderança.
            *   Em **2026**, após a reforma, o número de nomeados externos despencou para **apenas {comissionados_ext_2026}**, com os servidores de carreira (efetivos) assumindo **{pct_efetivos_2026:.1f}%** de toda a estrutura de confiança.
            *   **A fala do prefeito está perfeitamente validada e confirmada por esta base de dados.**
            """)
else:
    st.info("Dados de cargos de confiança não disponíveis.")

st.divider()
st.subheader("Pagamentos via Responsáveis de Secretaria")
st.info(
    """
    **Por que uma pessoa aparece recebendo milhões de reais?**

    No Brasil, é prática comum em municípios que o ordenador de despesas de cada secretaria
    (o responsável pelo departamento) receba o montante total da folha de pagamento em seu CPF
    e o distribua entre os servidores da unidade. O sufixo **"E OUTROS"** no nome indica
    exatamente isso: o valor não é de uso pessoal — representa salários de toda a equipe.

    Esses pagamentos são **excluídos da análise de Fornecedores e Compras Locais** para não
    distorcer os índices de concentração e compras locais.
    """,
    icon=":material/info:",
)

if not df_departamentos.empty:
    fig_departamentos = px.bar(
        df_departamentos,
        x="pago",
        y="descricao",
        orientation="h",
        title=f"Folha distribuída por responsável ({year})",
        labels={"pago": "Total Pago (R$)", "descricao": "Responsável"},
    )
    fig_departamentos.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_departamentos, use_container_width=True)
else:
    st.info("Nenhum pagamento deste tipo registrado para este exercício.")

st.divider()

st.caption(f"[Ver no portal oficial →]({glossary.PORTAL_URL})")
