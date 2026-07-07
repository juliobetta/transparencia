import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    SPARK_CFG,
    fmt_compact,
    fmt_currency,
    get_conn,
    get_data_extracao,
    pct_delta,
    render_aviso_ano_parcial,
    render_sidebar,
    sparkline,
)
from sqlalchemy.engine import Engine

from analysis import analise_despesas, concentracao_fornecedores, posicao_fiscal
from analysis.analise_despesas import get_diarias_pesquisaveis
from analysis.concentracao_fornecedores import piechart_concentracao
from analysis.posicao_fiscal import get_pendentes_por_exercicio, piechart_pendentes, resumo_pendentes

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _metricas(conn, year, _extracted_at):
    return analise_despesas.get_metricas_gerais_despesas(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _por_unidade(conn, year, _extracted_at):
    return analise_despesas.get_despesas_por_unidade(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _impacto(conn, year, _extracted_at):
    return analise_despesas.get_impacto_gastos_locais(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_fornecedores(conn, year, _extracted_at):
    return analise_despesas.get_principais_fornecedores_detalhados(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _concentracao(conn, year, _extracted_at):
    return concentracao_fornecedores.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _gastos_por_municipio(conn, year, _extracted_at):
    return analise_despesas.get_gastos_por_municipio(conn, year, top_n=5)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _resumo_diarias(conn, year, _extracted_at):
    return analise_despesas.get_resumo_diarias(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _top_diarias(conn, year, _extracted_at):
    return analise_despesas.get_principais_beneficiarios_diarias(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fornecedores_pendentes(conn, year, _extracted_at):
    return posicao_fiscal.get_fornecedores_pendentes(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _restos_baixo_valor(conn, year, _extracted_at):
    return posicao_fiscal.get_restos_baixo_valor(conn, year=year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _metricas_por_ano(conn, years, _extracted_at):
    return analise_despesas.get_metricas_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _impacto_por_ano(conn, years, _extracted_at):
    return analise_despesas.get_impacto_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _hhi_por_ano(conn, years, _extracted_at):
    return concentracao_fornecedores.hhi_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _resumo_diarias_por_ano(conn, years, _extracted_at):
    return analise_despesas.get_resumo_diarias_por_ano(conn, list(years))


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencia_pendentes(conn, years, _extracted_at):
    return posicao_fiscal.get_tendencia_fornecedores_pendentes(conn, list(years))


conn = get_conn()
year = render_sidebar()
_extracted_at = get_data_extracao(conn)

_all_years = list(range(2022, year + 1))
_hist_metricas = _metricas_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_impacto = _impacto_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_hhi = _hhi_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_diarias = _resumo_diarias_por_ano(conn, tuple(_all_years), _extracted_at)
_hist_pendentes = _tendencia_pendentes(conn, tuple(_all_years), _extracted_at)

st.title("Portal de Despesas Detalhadas")
st.caption("Detalhes sobre onde e como os recursos públicos estão sendo aplicados.")

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

# Layout de abas
t1, t2, t3, t4, t5 = st.tabs(
    [
        ":material/corporate_fare: Unidades Administrativas",
        ":material/handshake: Fornecedores e Compras Locais",
        ":material/hourglass: Restos a Pagar",
        ":material/flight_takeoff: Diárias e Viagens",
        ":material/manage_search: Consulta de Transações",
    ]
)

# Tab 1: Unidades Administrativas
with t1:
    st.subheader("Análise de Despesas por Unidade do Governo")

    metricas = _metricas(conn, year, _extracted_at)

    _emp_serie = [_hist_metricas[y]["empenhado"] for y in _all_years]
    _liq_serie = [_hist_metricas[y]["liquidado"] for y in _all_years]
    _pago_serie = [_hist_metricas[y]["pago"] for y in _all_years]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Total Empenhado",
            fmt_currency(metricas["empenhado"]),
            delta=pct_delta(_emp_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
            help=(
                "Valor total que a prefeitura reservou formalmente para pagar despesas. O empenho é a "
                "primeira etapa do gasto público: a administração reconhece a obrigação e reserva o "
                "recurso no orçamento. Pense como um 'cheque pré-aprovado' — o dinheiro foi comprometido, "
                "mas ainda não necessariamente saiu do caixa."
            ),
        )
        st.plotly_chart(
            sparkline(_all_years, _emp_serie, "#2196F3"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_emp",
        )
    with c2:
        st.metric(
            "Total Liquidado",
            fmt_currency(metricas["liquidado"]),
            delta=pct_delta(_liq_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
            help=(
                "Valor correspondente a serviços ou produtos que já foram efetivamente entregues e "
                "verificados pela prefeitura. A liquidação confirma que o município recebeu aquilo que "
                "contratou e que a nota fiscal ou documento equivalente foi aprovado. É o estágio "
                "intermediário entre reservar e pagar."
            ),
        )
        st.plotly_chart(
            sparkline(_all_years, _liq_serie, "#4CAF50"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_liq",
        )
    with c3:
        st.metric(
            "Total Pago Real",
            fmt_currency(metricas["pago"]),
            delta=pct_delta(_pago_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
            help=(
                "Valor que de fato saiu do caixa da prefeitura e foi transferido ao fornecedor ou "
                "servidor. É o estágio final do gasto público — o dinheiro efetivamente deixou os "
                "cofres municipais. Em uma gestão saudável, o valor pago tende a se aproximar do "
                "liquidado ao longo do exercício."
            ),
        )
        st.plotly_chart(
            sparkline(_all_years, _pago_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_pago",
        )

    df_unidades = _por_unidade(conn, year, _extracted_at)
    if not df_unidades.empty:
        st.markdown("---")
        fig = px.bar(
            df_unidades.head(15),
            x="pago",
            y="descricao",
            orientation="h",
            title="Top 15 Unidades Administrativas por Valor Pago (R$)",
            labels={"pago": "Pago (R$)", "descricao": "Unidade Administrativa"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_unidades.rename(
                columns={
                    "descricao": "Unidade Administrativa",
                    "empenhado": "Empenhado (R$)",
                    "liquidado": "Liquidado (R$)",
                    "pago": "Pago (R$)",
                    "dotacao_atualizada": "Dotação Atualizada (R$)",
                }
            ),
            column_config={
                "Empenhado (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Liquidado (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Dotação Atualizada (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhuma despesa orçamentária registrada para este exercício.")

# Tab 2: Fornecedores
with t2:
    st.subheader("Concentração e Impacto Econômico de Fornecedores")
    st.caption(
        "Analisa para onde vai o dinheiro público: quanto fica na economia local, "
        "quanto vai para empresas de fora e se há concentração excessiva em poucos fornecedores. "
        "**Esta aba exibe apenas despesas de compras, materiais, serviços e investimentos.** "
        "Foram excluídos pagamentos de folha de pessoal, previdência e dívidas."
    )

    impacto = _impacto(conn, year, _extracted_at)
    concentracao = _concentracao(conn, year, _extracted_at)

    _local_serie = [_hist_impacto[y]["local_pago"] for y in _all_years]
    _ext_serie = [_hist_impacto[y]["externo_pago"] for y in _all_years]
    _pct_local_serie = [_hist_impacto[y]["pct_local"] for y in _all_years]
    _hhi_serie = [_hist_hhi[y] for y in _all_years]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Efetivamente Pago — Empresas Locais",
            fmt_compact(impacto["local_pago"]),
            delta=pct_delta(_local_serie) if year != ANO_ATUAL else "—",
            delta_color="normal" if year != ANO_ATUAL else "off",
        )
        st.plotly_chart(
            sparkline(_all_years, _local_serie, "#4CAF50"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_local",
        )
    with c2:
        st.metric(
            "Efetivamente Pago — Empresas Externas",
            fmt_compact(impacto["externo_pago"]),
            delta=pct_delta(_ext_serie) if year != ANO_ATUAL else "—",
            delta_color="inverse" if year != ANO_ATUAL else "off",
        )
        st.plotly_chart(
            sparkline(_all_years, _ext_serie, "#F44336"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_ext",
        )
    with c3:
        st.metric(
            "Índice de Compras Locais",
            f"{impacto['pct_local']:.2f}%",
            delta=pct_delta(_pct_local_serie) if year != ANO_ATUAL else "—",
            delta_color="normal" if year != ANO_ATUAL else "off",
            help="Percentual de recursos mantidos na economia local de Porciúncula.",
        )
        st.plotly_chart(
            sparkline(_all_years, _pct_local_serie, "#2196F3"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_pct_local",
        )
    with c4:
        st.metric(
            "HHI (concentração)",
            f"{concentracao['hhi']:,.0f}",
            delta=pct_delta(_hhi_serie) if year != ANO_ATUAL else "—",
            delta_color="inverse" if year != ANO_ATUAL else "off",
            help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
        )
        st.plotly_chart(
            sparkline(_all_years, _hhi_serie, "#9C27B0"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_hhi",
        )

    if impacto["total_pago"] > 0:
        df_mercado = pd.DataFrame(
            {
                "Mercado": ["Negócios Locais (Porciúncula)", "Prestadores Externos"],
                "Pago (R$)": [impacto["local_pago"], impacto["externo_pago"]],
            }
        )
        fig_pie = px.pie(
            df_mercado,
            values="Pago (R$)",
            names="Mercado",
            color="Mercado",
            color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f", "Prestadores Externos": "#a12c2c"},
            title="Destino Geográfico dos Recursos Públicos Pagos",
            hole=0.5,
        )

        df_cidades = _gastos_por_municipio(conn, year, _extracted_at)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            if not df_cidades.empty:
                fig_cities = px.pie(
                    df_cidades,
                    values="pago",
                    names="cidade",
                    color="cidade",
                    color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f"},
                    title="Top 5 Cidades Externas + Outros",
                    hole=0.5,
                )
                st.plotly_chart(fig_cities, use_container_width=True)
    else:
        df_cidades = _gastos_por_municipio(conn, year, _extracted_at)
        if not df_cidades.empty:
            fig_cities = px.pie(
                df_cidades,
                values="pago",
                names="cidade",
                color="cidade",
                color_discrete_map={"Negócios Locais (Porciúncula)": "#2b5c8f"},
                title="Top 5 Cidades Externas + Outros",
                hole=0.5,
            )
            st.plotly_chart(fig_cities, use_container_width=True)

    if concentracao["dominante"]:
        st.warning(
            f"{concentracao['dominante']} recebeu mais de 40% do total empenhado a fornecedores.",
            icon=":material/warning:",
        )

    top10_concentracao = concentracao["top10"].copy()

    # Garantir que df_sup esteja definido antes de ser usado
    df_fornecedores = _top_fornecedores(conn, year, _extracted_at)

    # Adicionar o Pie Chart de Natureza da Despesa
    st.markdown("### Distribuição das Compras e Serviços")

    # Criar colunas para exibir os gráficos lado a lado
    col_nat, col_conc = st.columns(2)

    with col_nat:
        df_natureza = df_fornecedores.groupby("elemento")["pago"].sum().reset_index()
        # Adicionar label descritiva para o elemento no gráfico usando a nova função
        df_natureza["label"] = df_natureza["elemento"].apply(analise_despesas.get_elemento_label)

        fig_natureza = px.pie(df_natureza, values="pago", names="label", title="Por Elemento de Despesa", hole=0.5)
        st.plotly_chart(fig_natureza, use_container_width=True)

    with col_conc:
        pizza_concentracao = piechart_concentracao(top10_concentracao, concentracao["total_all"])
        fig_concentracao = px.pie(
            pizza_concentracao,
            values="empenhado",
            names="Fornecedor",
            title="Distribuição por Fornecedor (Top 10)",
            hole=0.5,
        )
        st.plotly_chart(fig_concentracao, use_container_width=True)

    st.markdown("### Top 10 Maiores Prestadores de Serviços / Fornecedores")
    st.caption(
        "Exibindo apenas despesas classificadas como Contratações/Serviços (3.3.xx) ou Investimentos/Obras (4.4.xx)."
    )

    if not df_fornecedores.empty:
        fig_sup = px.bar(
            df_fornecedores.head(10),
            x="pago",
            y="fornecedor",
            orientation="h",
            title="Top 10 Fornecedores por Valor Pago (R$)",
            labels={"pago": "Pago (R$)", "fornecedor": "Nome do Fornecedor"},
        )
        fig_sup.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_sup, use_container_width=True)

        st.dataframe(
            df_fornecedores.rename(
                columns={
                    "fornecedor": "Fornecedor",
                    "insmf": "CNPJ/CPF",
                    "cidade": "Cidade",
                    "codigo": "Código",
                    "descricao": "Descrição",
                    "pago": "Total Pago (R$)",
                }
            )[["Fornecedor", "CNPJ/CPF", "Cidade", "Descrição", "Total Pago (R$)"]],
            column_config={"Total Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum dado de fornecedor encontrado para as categorias de contratação/obras neste exercício.")

# Tab 3: Restos a Pagar
with t3:
    st.subheader("Restos a Pagar — Obrigações de Exercícios Anteriores")
    st.info(
        "**O que são Restos a Pagar?** São despesas que a prefeitura empenhou (reservou) em anos anteriores "
        "mas ainda não pagou. Não são contas atrasadas do ano atual — são compromissos legais de exercícios "
        "passados que continuam válidos até serem pagos ou cancelados. "
        "A tabela abaixo consolida todos os fornecedores com saldo pendente acumulado até o ano selecionado.",
        icon=":material/info:",
    )

    df_por_exercicio = get_pendentes_por_exercicio(conn)
    if not df_por_exercicio.empty:
        with st.expander("Ver pendências por exercício fiscal"):
            st.dataframe(
                df_por_exercicio,
                column_config={
                    "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pendente": st.column_config.NumberColumn(format="R$ %,.2f"),
                },
                use_container_width=True,
                hide_index=True,
            )

    df_pendentes = _fornecedores_pendentes(conn, year, _extracted_at)
    if not df_pendentes.empty:
        resumo = resumo_pendentes(df_pendentes)

        _val_pendentes = _hist_pendentes["total_pendente"].tolist() if not _hist_pendentes.empty else []
        _cnt_pendentes = _hist_pendentes["num_fornecedores"].tolist() if not _hist_pendentes.empty else []
        _anos_pendentes = _hist_pendentes["ano"].tolist() if not _hist_pendentes.empty else []

        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.metric(
                "Total Pendente",
                fmt_currency(resumo["total"]),
                delta=pct_delta(_val_pendentes) if year != ANO_ATUAL else "—",
                delta_color="inverse" if year != ANO_ATUAL else "off",
                help="Soma de todos os empenhos ainda não quitados.",
            )
            if _val_pendentes:
                st.plotly_chart(
                    sparkline(_anos_pendentes, _val_pendentes, "#E91E63"),
                    use_container_width=True,
                    config=SPARK_CFG,
                    key="spark_desp_rp_total",
                )
        with rc2:
            st.metric(
                "Fornecedores aguardando",
                resumo["count"],
                delta=pct_delta(_cnt_pendentes) if year != ANO_ATUAL else "—",
                delta_color="inverse" if year != ANO_ATUAL else "off",
            )
            if _cnt_pendentes:
                st.plotly_chart(
                    sparkline(_anos_pendentes, _cnt_pendentes, "#FF5722"),
                    use_container_width=True,
                    config=SPARK_CFG,
                    key="spark_desp_rp_count",
                )
        with rc3:
            st.metric("Dívida mais antiga desde", str(resumo["oldest"]))

        df_pizza_pendentes = piechart_pendentes(df_pendentes)
        fig_pendentes = px.pie(
            df_pizza_pendentes,
            values="Pendente",
            names="Fornecedor",
            title="Top 10 Fornecedores com Maior Pendência",
            hole=0.5,
        )
        st.plotly_chart(fig_pendentes, use_container_width=True)

        st.dataframe(
            df_pendentes.rename(
                columns={
                    "descricao": "Fornecedor",
                    "aguardando_desde": "Aguardando desde",
                    "num_registros": "Nº registros",
                    "total_empenhado": "Total Empenhado",
                    "total_pago": "Total Pago",
                    "pendente": "Pendente",
                }
            )[["Fornecedor", "Aguardando desde", "Nº registros", "Total Empenhado", "Total Pago", "Pendente"]],
            column_config={
                "Total Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Total Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Pendente": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum fornecedor com pagamento pendente para este exercício.")

    df_baixo_valor = _restos_baixo_valor(conn, year, _extracted_at)
    if not df_baixo_valor.empty:
        with st.expander(
            f":material/warning: {len(df_baixo_valor)} registro(s) com empenhado abaixo de R$ 10,00 — verificar"
        ):
            st.warning(
                "Estes registros possuem valores empenhados muito baixos e podem indicar erros de lançamento ou dados inconsistentes na fonte."
            )
            st.dataframe(
                df_baixo_valor,
                column_config={
                    "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
                },
                use_container_width=True,
                hide_index=True,
            )

# Tab 4: Diárias
with t4:
    st.subheader("Diárias e Auxílios de Viagem a Serviço")

    resumo_diarias_data = _resumo_diarias(conn, year, _extracted_at)

    _diarias_val_serie = [_hist_diarias[y]["total_valor"] for y in _all_years]
    _diarias_cnt_serie = [_hist_diarias[y]["total_viajantes"] for y in _all_years]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            "Total Pago em Diárias",
            fmt_currency(resumo_diarias_data["total_valor"]),
            delta=pct_delta(_diarias_val_serie) if year != ANO_ATUAL else "—",
            delta_color="inverse" if year != ANO_ATUAL else "off",
        )
        st.plotly_chart(
            sparkline(_all_years, _diarias_val_serie, "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_diarias",
        )
    with c2:
        st.metric(
            "Total de Servidores Beneficiários",
            int(resumo_diarias_data["total_viajantes"]),
            delta=pct_delta(_diarias_cnt_serie) if year != ANO_ATUAL else "—",
            delta_color="off",
        )
        st.plotly_chart(
            sparkline(_all_years, _diarias_cnt_serie, "#607D8B"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_desp_viajantes",
        )
    with c3:
        st.metric(
            "Média de Reembolso por Viagem",
            fmt_currency(resumo_diarias_data["media_reembolso"]),
            help=(
                "Valor médio pago por deslocamento a serviço. Calculado dividindo o total gasto em "
                "diárias pelo número de registros de viagem no período. Cada registro corresponde a "
                "um pagamento de diária — servidores com múltiplas viagens aparecem mais de uma vez "
                "nessa conta. Valores muito acima da média podem indicar viagens de longa duração ou "
                "deslocamentos para destinos mais distantes."
            ),
        )

    st.markdown("---")
    df_top_diarias = _top_diarias(conn, year, _extracted_at)
    if not df_top_diarias.empty:
        st.markdown("### Top 10 Servidores que Receberam Diárias")
        st.dataframe(
            df_top_diarias.rename(
                columns={
                    "favorecido": "Servidor Público",
                    "cargo": "Cargo",
                    "valor": "Total Recebido (R$)",
                    "viagens": "Qtd Viagens",
                }
            ),
            column_config={"Total Recebido (R$)": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Histórico e Detalhes dos Pagamentos de Diárias")
        st.info("Insira o nome do servidor ou departamento abaixo para buscar viagens específicas.")

        busca_diaria = st.text_input("Buscar Diária (Nome do Servidor ou Unidade):", "")
        df_lista_diarias = get_diarias_pesquisaveis(conn, year, busca_diaria)
        if not df_lista_diarias.empty:
            st.dataframe(
                df_lista_diarias.rename(
                    columns={
                        "data": "Data",
                        "servidor": "Servidor",
                        "cargo": "Cargo/Função",
                        "valor": "Valor (R$)",
                        "unidade": "Unidade Administrativa",
                        "historico": "Justificativa da Viagem",
                    }
                ),
                column_config={
                    "Valor (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Nenhuma viagem correspondente encontrada.")
    else:
        st.info("Nenhum pagamento de diárias registrado para este exercício.")

# Tab 5: Consulta Geral de Transações
with t5:
    st.subheader("Pesquisa Geral de Transações Financeiras (Contábeis)")
    st.markdown(
        "Pesquise diretamente no livro caixa e no razão da prefeitura. "
        "Você pode buscar por nome de empresa, órgão ou termos específicos (ex: *asfalto*, *combustível*, *medicamento*)."
    )

    busca_termo = st.text_input("Termo de Busca:", placeholder="Digite para pesquisar...")
    limite_resultados = st.slider("Qtd. Máxima de Resultados:", min_value=50, max_value=1000, value=250, step=50)

    if busca_termo.strip() or year:
        df_transacoes = analise_despesas.get_transacoes_pesquisaveis(conn, year, busca_termo, limite_resultados)
        if not df_transacoes.empty:
            st.markdown(f"Exibindo os **{len(df_transacoes)}** maiores pagamentos contábeis correspondentes:")
            st.dataframe(
                df_transacoes.rename(
                    columns={
                        "data": "Data Empenho",
                        "fornecedor": "Fornecedor / Favorecido",
                        "pago": "Valor Pago (R$)",
                        "unidade": "Unidade",
                        "descricao": "Justificativa Contábil (Histórico)",
                    }
                ),
                column_config={
                    "Valor Pago (R$)": st.column_config.NumberColumn(format="R$ %,.2f"),
                    "Data Empenho": st.column_config.DateColumn(format="DD/MM/YYYY"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("Nenhum pagamento correspondente encontrado para a busca.")
