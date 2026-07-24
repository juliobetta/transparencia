import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    ANOS,
    COLOR_ALERT,
    SPARK_CFG,
    fmt_compact,
    fmt_currency,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    plotly_card_end,
    plotly_card_layout,
    plotly_card_start,
    render_aviso_ano_parcial,
    render_sidebar,
    section_heading,
    sparkline,
)
from sqlalchemy.engine import Engine

import constants
from app.analytics import analise_despesas, folha_vs_servicos
from app.analytics.analise_despesas import total_folha_por_orgao
from app.analytics.constants import LRF_PESSOAL_LIMITE_ALERTA, LRF_PESSOAL_LIMITE_LEGAL, LRF_PESSOAL_LIMITE_PRUDENCIAL

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_pagamento(conn, year, empresa_ids, _extracted_at):
    return folha_vs_servicos.run(conn, list(range(ANOS[0], year + 1)), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_por_departamento(conn, year, empresa_ids, _extracted_at):
    return analise_despesas.get_folha_por_orgao(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha_orgao_por_ano(conn, years, empresa_ids, _extracted_at):
    return analise_despesas.total_folha_orgao_por_ano(conn, list(years), empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _cargos_confianca(conn, years, _extracted_at):
    return analise_despesas.get_perfil_cargos_confianca(conn, list(years))


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Administrativo · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")
st.html(
    page_header(
        _eyebrow,
        "Folha de Pagamento",
        "Quanto da receita arrecadada é comprometido com salários e proventos. A Lei de Responsabilidade Fiscal limita esse gasto a "
        "<strong style='color:#1a1d21'>54% da receita corrente líquida</strong> para o Poder Executivo.",
    )
)

if year == ANO_ATUAL:
    render_aviso_ano_parcial(
        year,
        _extracted_at,
        extra_html="<br>Os índices percentuais de folha podem oscilar devido à sazonalidade "
        "(ex: 13º salário e terço de férias não contabilizados proporcionalmente).",
    )

_all_years = list(range(ANO_INICIAL, year + 1))
_anos = _all_years
_hist_folha_orgao = _folha_orgao_por_ano(conn, tuple(_all_years), empresa_ids, _extracted_at)
_folha_orgao_serie = [_hist_folha_orgao[y] for y in _anos]

df_folha = _folha_pagamento(conn, year, empresa_ids, _extracted_at)
df_cargos = _cargos_confianca(conn, tuple(_all_years), _extracted_at)
df_departamentos = _folha_por_departamento(conn, year, empresa_ids, _extracted_at)

if not df_folha.empty:
    _pct_serie = df_folha["percentual_folha"].tolist()
    _anos_folha = df_folha["ano"].tolist()
    _pct_folha_val = float(df_folha.iloc[-1]["percentual_folha"])

    # Calcular série histórica do percentual de efetivos no comando
    _series_pct_efetivos = []
    _anos_cargos_serie = []
    for _y in sorted(df_cargos["ano"].unique()):
        if _y > year:
            continue
        df_y = df_cargos[df_cargos["ano"] == _y]
        qty_map_y = df_y.set_index("tipo_vinculo_detalhado")["quantidade"].to_dict()
        efetivos_confianca = qty_map_y.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + qty_map_y.get(
            "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
        )
        comissionados_externos = qty_map_y.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
        total_confianca = efetivos_confianca + comissionados_externos
        _series_pct_efetivos.append((efetivos_confianca / total_confianca * 100) if total_confianca > 0 else 0.0)
        _anos_cargos_serie.append(_y)

    _pct_efetivos_val = _series_pct_efetivos[-1] if _series_pct_efetivos else 0.0
    _total_folha_atual = total_folha_por_orgao(df_departamentos)
    _sub_lrf = (
        f"abaixo do teto de {LRF_PESSOAL_LIMITE_LEGAL}%"
        if _pct_folha_val < LRF_PESSOAL_LIMITE_LEGAL
        else f"acima do limite de {LRF_PESSOAL_LIMITE_LEGAL}%"
    )

    st.html(
        kpi_grid(
            kpi_card(
                "Folha / Receita Arrecadada",
                f"{_pct_folha_val:.1f}%",
                sub=_sub_lrf,
                risk=_pct_folha_val >= LRF_PESSOAL_LIMITE_LEGAL,
            ),
            kpi_card(
                "Efetivos no Comando das Chefias", f"{_pct_efetivos_val:.1f}%", sub="cargos de liderança concursados"
            ),
            kpi_card("Total Pago em Folha", fmt_compact(_total_folha_atual), sub=pct_delta(_folha_orgao_serie) or ""),
            cols=3,
        )
    )
    kf1, kf2, kf3 = st.columns(3)
    with kf1:
        st.plotly_chart(
            sparkline(_anos_folha, _pct_serie, COLOR_ALERT),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_pct",
        )
    with kf2:
        if len(_series_pct_efetivos) > 1:
            st.plotly_chart(
                sparkline(_anos_cargos_serie, _series_pct_efetivos),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_cargos_confianca",
            )
    with kf3:
        st.plotly_chart(
            sparkline(_anos, _folha_orgao_serie),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pes_folha_orgao",
        )

    st.html(section_heading("Folha como % da receita, ano a ano"))
    _chart_h = 170
    _max_ref = max(float(LRF_PESSOAL_LIMITE_LEGAL) * 1.08, max(_pct_serie, default=0) * 1.05)

    def _ref_top(pct: float) -> int:
        return _chart_h - int(pct / _max_ref * _chart_h)

    _bars_html = ""
    for _yr, _pct_val in zip(_anos_folha, _pct_serie):
        _bar_h = int(float(_pct_val) / _max_ref * _chart_h)
        _is_partial = _yr == ANO_ATUAL
        _bar_color = (
            "oklch(0.55 0.11 25)"
            if float(_pct_val) >= float(LRF_PESSOAL_LIMITE_LEGAL)
            else "oklch(0.65 0.13 65)"
            if float(_pct_val) >= float(LRF_PESSOAL_LIMITE_PRUDENCIAL)
            else "oklch(0.62 0.11 235)"
        )
        _bars_html += (
            f'<div style="flex:1;max-width:64px;display:flex;flex-direction:column;align-items:center">'
            f'<div class="serif" style="font-weight:700;font-size:12px;margin-bottom:4px;{"color:#9aa1ab;" if _is_partial else ""}">{float(_pct_val):.1f}%</div>'
            f'<div style="flex:1;display:flex;align-items:flex-end;width:100%">'
            f'<div style="width:100%;height:{_bar_h}px;background:{_bar_color};border-radius:5px 5px 0 0;{"opacity:.55;" if _is_partial else ""}"></div></div>'
            f'<div style="font-size:11px;color:#9aa1ab;margin-top:7px">{_yr}{"*" if _is_partial else ""}</div>'
            f"</div>"
        )

    _reflines_html = ""
    for _pct_ref, _col_ref, _dash_style, _lbl_ref in [
        (float(LRF_PESSOAL_LIMITE_LEGAL), "oklch(0.55 0.14 25)", "solid", f"Legal {LRF_PESSOAL_LIMITE_LEGAL}%"),
        (
            float(LRF_PESSOAL_LIMITE_PRUDENCIAL),
            "oklch(0.65 0.13 65)",
            "dashed",
            f"Prudencial {LRF_PESSOAL_LIMITE_PRUDENCIAL}%",
        ),
        (float(LRF_PESSOAL_LIMITE_ALERTA), "oklch(0.7 0.12 90)", "dotted", f"Alerta {LRF_PESSOAL_LIMITE_ALERTA}%"),
    ]:
        _top = _ref_top(_pct_ref)
        _reflines_html += (
            f'<div style="position:absolute;left:0;right:0;top:{_top}px;border-top:1.5px {_dash_style} {_col_ref};opacity:.7">'
            f'<span style="position:absolute;right:0;font-size:10px;color:{_col_ref};font-weight:600;white-space:nowrap;transform:translateY(-14px)">{_lbl_ref}</span></div>'
        )

    st.html(
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px 26px 20px;margin-bottom:1.5rem">'
        f'<div style="position:relative;padding-left:8px;padding-right:80px">'
        f'<div style="display:flex;align-items:flex-end;gap:6px;height:{_chart_h}px;position:relative">'
        f"{_bars_html}</div>"
        f"{_reflines_html}"
        f"</div></div>"
    )

st.html(section_heading("13º Salário", aside="status de quitação"))
exec_13 = folha_vs_servicos.execucao_decimo_terceiro(conn, year)
if exec_13 is not None and exec_13["empenhado"] > 0:
    _pct_13 = min(max(float(exec_13["pct_pago"]), 0.0), 1.0)
    st.html(
        kpi_grid(
            kpi_card("Total Reservado", fmt_currency(exec_13["empenhado"]), sub="empenho líquido ajustado"),
            kpi_card("Efetivamente Pago", fmt_currency(exec_13["pago"]), accent=True),
            kpi_card(
                "Percentual Quitado",
                f"{exec_13['pct_pago'] * 100:.1f}%",
                sub="da folha de 13º quitada",
                accent=_pct_13 >= 0.99,
            ),
            cols=3,
        )
    )
    st.html(
        f'<div style="background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 22px;margin-bottom:1.5rem">'
        f'<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:9px">'
        f"<strong>Progresso de quitação</strong>"
        f'<strong class="serif" style="font-weight:700">{exec_13["pct_pago"] * 100:.1f}%</strong></div>'
        f'<div style="height:10px;background:#eef0f4;border-radius:6px;overflow:hidden">'
        f'<div style="width:{_pct_13 * 100:.0f}%;height:100%;background:oklch(0.5 0.13 145);border-radius:6px"></div>'
        f"</div></div>"
    )

    df_det_13 = folha_vs_servicos.detalhe_decimo_terceiro(conn, year)
    if not df_det_13.empty:
        with st.expander(":material/search: Ver detalhamento do 13º Salário por Secretaria/Órgão"):
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
st.html(section_heading("Distribuição de Remuneração"))
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
    fig_histograma.update_layout(
        **plotly_card_layout("Distribuição dos Proventos Brutos", height=320),
        yaxis_title="Nº de Servidores",
        xaxis_tickprefix="R$ ",
        xaxis_tickformat=",.0f",
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_histograma, use_container_width=True)
    st.html(plotly_card_end())
else:
    st.info("Dados de proventos não disponíveis para este exercício.")

st.html(section_heading("Perfil de Cargos de Confiança"))
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
        **plotly_card_layout(f"Evolução de Cargos por Tipo de Vínculo ({ANOS[0]}-{ANOS[-1]})", height=340)
    )
    fig_cargos.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
        margin=dict(l=16, r=16, t=36, b=110),
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_cargos, use_container_width=True)
    st.html(plotly_card_end())

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

else:
    st.info("Dados de cargos de confiança não disponíveis.")

st.html(section_heading("Pagamentos via Responsáveis de Secretaria"))
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
    fig_departamentos.update_layout(
        **plotly_card_layout(f"Folha distribuída por responsável ({year})", height=340),
        yaxis={"categoryorder": "total ascending"},
    )
    st.html(plotly_card_start())
    st.plotly_chart(fig_departamentos, use_container_width=True)
    st.html(plotly_card_end())
else:
    st.info("Nenhum pagamento deste tipo registrado para este exercício.")

st.divider()

st.caption(f"[Ver no portal oficial →]({constants.PORTAL_URL})")
