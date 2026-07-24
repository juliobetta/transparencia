import sys
from pathlib import Path

import constants

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

import streamlit as st
from shared import (
    ANO_ATUAL,
    ANO_INICIAL,
    COLOR_POSITIVE,
    SPARK_CFG,
    alert_box,
    fmt_compact,
    funnel_waterfall,
    get_conn,
    get_data_extracao,
    kpi_card,
    kpi_grid,
    page_header,
    partial_year_month,
    pct_delta,
    render_aviso_ano_parcial,
    render_metodologia_receita,
    render_sidebar,
    section_heading,
    sparkline,
)
from sqlalchemy.engine import Engine

from app.analytics import (
    adesao_de_ata,
    analise_despesas,
    anomalias_contratuais,
    execucao_orcamentaria,
    folha_vs_servicos,
    fontes_receita,
    licitacao_gaps,
    posicao_fiscal,
)

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _orcamento(conn, year, empresa_ids, _extracted_at):
    return execucao_orcamentaria.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _licitacoes_gaps(conn, year, empresa_ids, _extracted_at):
    return licitacao_gaps.run(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_licitacoes(conn, years, empresa_ids, _extracted_at):
    return licitacao_gaps.counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _receita(conn, years, empresa_ids, _extracted_at):
    return fontes_receita.run(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_counts(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.formal_counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa_counts(conn, years, empresa_ids, _extracted_at):
    return adesao_de_ata.external_counts_by_year(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _contagens_fracionamento(conn, years, empresa_ids, _extracted_at):
    return anomalias_contratuais.contagens_fracionamento_por_ano(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at):
    return posicao_fiscal.get_fornecedores_pendentes(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _tendencia_pendentes(conn, years, empresa_ids, _extracted_at):
    return posicao_fiscal.get_tendencia_fornecedores_pendentes(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _composicao(conn, year, empresa_ids, _extracted_at):
    return analise_despesas.get_composicao_despesa(conn, year, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _folha(conn, years, empresa_ids, _extracted_at):
    return folha_vs_servicos.run(conn, years, empresa_ids=empresa_ids)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _cargos_confianca(conn, years, _extracted_at):
    return analise_despesas.get_perfil_cargos_confianca(conn, list(years))


conn = get_conn()
year, empresa_ids = render_sidebar()
_extracted_at = get_data_extracao(conn)

_all_years = list(range(ANO_INICIAL, year + 1))
anos = _all_years

with st.spinner("Carregando..."):
    orcamento = _orcamento(conn, year, empresa_ids, _extracted_at)
    licitacoes = _licitacoes_gaps(conn, year, empresa_ids, _extracted_at)
    receita = _receita(conn, _all_years, empresa_ids, _extracted_at)
    df_composicao = _composicao(conn, year, empresa_ids, _extracted_at)
    _adesao_map = _adesao_counts(conn, _all_years, empresa_ids, _extracted_at)
    _adesao_ext_map = _adesao_externa_counts(conn, _all_years, empresa_ids, _extracted_at)
    _mapa_fracionamento = _contagens_fracionamento(conn, _all_years, empresa_ids, _extracted_at)
    df_pendentes = _fornecedores_pendentes(conn, year, empresa_ids, _extracted_at)
    tendencia_pendentes = _tendencia_pendentes(conn, tuple(_all_years), empresa_ids, _extracted_at)
    df_folha_resumo = _folha(conn, _all_years, empresa_ids, _extracted_at)
    df_cargos = _cargos_confianca(conn, tuple(_all_years), _extracted_at)

_mapa_contagens = _contagens_licitacoes(conn, anos, empresa_ids, _extracted_at)
_contagens_contratos = [_mapa_contagens[y] for y in anos]

# ── Receita data ──────────────────────────────────────────────────────────────
_receita_row = (
    receita[receita["ano"] == year].iloc[0]
    if (not receita.empty and year in receita["ano"].values)
    else (receita.iloc[-1] if not receita.empty else None)
)
_tem_arrecadado = _receita_row is not None and float(_receita_row["total_arrecadado"]) > 0

# ── Orçamento data ────────────────────────────────────────────────────────────
_dot = float(orcamento["dotacao_atualizada"].sum()) if not orcamento.empty else 0.0
_emp = float(orcamento["empenhado"].sum()) if not orcamento.empty else 0.0
_liq = float(orcamento["liquidado"].sum()) if not orcamento.empty else 0.0
_pago = float(orcamento["pago"].sum()) if not orcamento.empty else 0.0
_pct_emp = _emp / _dot if _dot > 0 else 0.0

# ── Hero section ──────────────────────────────────────────────────────────────
_partial_suffix = f"parcial, Jan–{partial_year_month(_extracted_at)}" if year == ANO_ATUAL else ""
_eyebrow = f"Visão geral · Exercício {year}" + (f" ({_partial_suffix})" if _partial_suffix else "")

if _receita_row is not None:
    _total_rec = float(_receita_row["total_arrecadado"]) if _tem_arrecadado else float(_receita_row["total_previsto"])
    _prev_rec = float(_receita_row["total_previsto"])
    _pct_rec_val = float(_receita_row["pct_arrecadado"]) if _tem_arrecadado else 1.0
    _propria_val = float(_receita_row["receita_propria"])
    _uniao_val = float(_receita_row["transferencias_uniao"])
    _estado_val = float(_receita_row["transferencias_estado"])
    _pct_propria_int = round(_propria_val / _total_rec * 100) if _total_rec > 0 else 0
    _pct_uniao_int = round(_uniao_val / _total_rec * 100) if _total_rec > 0 else 0
    _pct_estado_int = round(_estado_val / _total_rec * 100) if _total_rec > 0 else 0

    _hero_title = (
        f'De cada R$ 100 que entram no caixa, <span style="color:oklch(0.5 0.13 250)">'
        f"apenas R$ {_pct_propria_int}</span> a cidade arrecada sozinha."
    )
    _hero_desc = (
        f"O município já recebeu <strong style='color:#1a1d21'>{fmt_compact(_total_rec)}</strong> em {year}"
        + (f" — {_pct_rec_val:.0%} do previsto para o ano" if _tem_arrecadado else "")
        + ". Quase todo esse dinheiro vem de repasses da União e do Estado, "
        "o que torna as contas sensíveis a decisões tomadas longe daqui."
    )

    _prog_pct = min(int(_pct_rec_val * 100), 100) if _tem_arrecadado else 100
    _prog_label = (
        "no ritmo" if _tem_arrecadado and _pct_rec_val >= 0.5 else ("acima" if _pct_rec_val > 1.0 else "abaixo")
    )
    _prog_color = (
        "oklch(0.5 0.13 145)"
        if _prog_label == "no ritmo"
        else ("oklch(0.5 0.13 250)" if _prog_label == "acima" else "oklch(0.55 0.11 25)")
    )

    def _source_bar(label: str, pct: int, color: str) -> str:
        return (
            f'<div><div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:5px">'
            f'<span>{label}</span><strong style="font-weight:600">{pct}%</strong></div>'
            f'<div style="height:7px;background:#eef0f4;border-radius:4px;overflow:hidden">'
            f'<div style="width:{pct}%;height:100%;background:{color}"></div></div></div>'
        )

    _hero_right = (
        f'<div style="background:#ffffff;border:1px solid #e7e9ee;border-radius:14px;padding:24px 26px;'
        f'display:flex;flex-direction:column">'
        f'<div style="font-size:12px;color:#6b7280;margin-bottom:3px">{"Arrecadado no ano até agora" if _tem_arrecadado else "Previsão orçamentária"}</div>'
        f"<div style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:44px;line-height:1;margin-bottom:6px\">"
        f"{fmt_compact(_total_rec)}</div>"
        + (
            f'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:#6b7280;margin-bottom:6px">'
            f"<span>{_prog_pct}% da previsão de {fmt_compact(_prev_rec)}</span>"
            f'<span style="color:{_prog_color};font-weight:600">{_prog_label}</span></div>'
            f'<div style="height:8px;background:#eef0f4;border-radius:6px;overflow:hidden;margin-bottom:20px">'
            f'<div style="width:{_prog_pct}%;height:100%;background:oklch(0.55 0.11 250);border-radius:6px"></div></div>'
            if _tem_arrecadado
            else '<div style="margin-bottom:26px"></div>'
        )
        + '<div style="font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#8a919c;margin-bottom:12px">De onde vem cada R$ 1,00</div>'
        '<div style="display:flex;flex-direction:column;gap:11px">'
        + _source_bar("Transferências da União", _pct_uniao_int, "oklch(0.55 0.11 250)")
        + _source_bar("Transferências do Estado", _pct_estado_int, "oklch(0.62 0.11 215)")
        + _source_bar("Receita própria", _pct_propria_int, "oklch(0.72 0.13 145)")
        + "</div></div>"
    )

    col_left, col_right = st.columns([1.3, 1])
    with col_left:
        st.html(page_header(_eyebrow, _hero_title, _hero_desc))
    with col_right:
        st.html(_hero_right)
else:
    st.html(page_header(_eyebrow, "Visão Geral", "Dados de receita não disponíveis para o período selecionado."))

st.html(
    alert_box(
        "<strong>Iniciativa livre e apartidária</strong>, sem vínculo com a administração municipal. "
        f'Dados extraídos do <a href="{constants.PORTAL_URL}" target="_blank">Portal da Transparência</a> oficial.',
        kind="info",
    )
)

# ── Receitas ─────────────────────────────────────────────────────────────────
st.html(section_heading("Receitas", aside="Ver detalhes →"))
render_metodologia_receita()

if year == ANO_ATUAL and _tem_arrecadado:
    render_aviso_ano_parcial(year, _extracted_at)

if _receita_row is not None:
    _anos_rec = receita["ano"].tolist()
    _prev_serie = receita["total_previsto"].tolist()
    _total_serie = receita["total"].tolist()

    c1, c2 = st.columns(2)
    with c1:
        st.html(
            kpi_card(
                "Previsão Orçamentária (LOA)",
                fmt_compact(float(_receita_row["total_previsto"])),
                sub=pct_delta(_prev_serie) or "",
            )
        )
        st.plotly_chart(
            sparkline(_anos_rec, _prev_serie), use_container_width=True, config=SPARK_CFG, key="spark_rec_prev"
        )
    with c2:
        if _tem_arrecadado:
            st.html(
                kpi_card(
                    "Total Arrecadado Real",
                    fmt_compact(float(_receita_row["total_arrecadado"])),
                    sub="ano parcial" if year == ANO_ATUAL else (pct_delta(_total_serie) or ""),
                    accent=True,
                )
            )
            st.plotly_chart(
                sparkline(_anos_rec, _total_serie, COLOR_POSITIVE),
                use_container_width=True,
                config=SPARK_CFG,
                key="spark_rec_total",
            )
        else:
            st.html(kpi_card("Total Arrecadado Real", "N/D"))

# ── Execução Orçamentária ─────────────────────────────────────────────────────
st.html(section_heading("Do orçamento autorizado ao pagamento", aside="Ver detalhes →"))

if _dot > 0:
    _pct_liq = _liq / _dot
    _pct_pago = _pago / _dot
    st.html(
        kpi_grid(
            kpi_card("Dotação Atualizada", fmt_compact(_dot), sub="100% autorizado", accent=False),
            kpi_card("Empenhado", fmt_compact(_emp), sub=f"{_pct_emp:.1%} da dotação", accent=True),
            kpi_card("Liquidado", fmt_compact(_liq), sub=f"{_pct_liq:.1%} da dotação", accent=True),
            kpi_card("Pago", fmt_compact(_pago), sub=f"{_pct_pago:.1%} da dotação", accent=True),
            cols=4,
        )
    )
    st.html(
        funnel_waterfall(
            [
                ("Dotação", _dot, fmt_compact(_dot)),
                ("Empenhado", _emp, fmt_compact(_emp)),
                ("Liquidado", _liq, fmt_compact(_liq)),
                ("Pago", _pago, fmt_compact(_pago)),
            ],
            _dot,
        )
    )
    st.html(
        alert_box(
            "A cadeia <strong>Dotação → Empenhado → Liquidado → Pago</strong> mostra o ciclo completo da despesa pública. "
            "Cada etapa é um estágio legal: reservar, confirmar entrega e pagar.",
            kind="info",
        )
    )

# ── Secondary grid: Despesas | Licitações | Pessoal ───────────────────────────
# Despesas card
_total_pendente = float(df_pendentes["pendente"].sum()) if not df_pendentes.empty else 0.0
_num_fornecedores = len(df_pendentes) if not df_pendentes.empty else 0
_ano_mais_antigo = int(df_pendentes["aguardando_desde"].min()) if not df_pendentes.empty else year

_valores_tendencia = tendencia_pendentes["total_pendente"].tolist() if not tendencia_pendentes.empty else []
_anos_tendencia = tendencia_pendentes["ano"].tolist() if not tendencia_pendentes.empty else []
_n_bars = len(_valores_tendencia)
_max_tend = max(_valores_tendencia) if _valores_tendencia else 1
_max_tend = _max_tend if _max_tend > 0 else 1
_mini_bars = (
    "".join(
        f'<div style="flex:1;background:{"oklch(0.55 0.11 25)" if i == _n_bars - 1 else "#f0dadd"};'
        f'border-radius:2px;height:{int(v / _max_tend * 100)}%"></div>'
        for i, v in enumerate(_valores_tendencia[-5:])
    )
    if _valores_tendencia
    else ""
)

_card_despesas = (
    f'<div style="background:#fff;border:1px solid #e7e9ee;border-radius:14px;padding:20px 22px;display:flex;flex-direction:column;gap:13px">'
    f'<div style="display:flex;align-items:center;justify-content:space-between">'
    f"<span style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:15px\">Despesas</span>"
    f'<span style="font-size:11px;color:#9aa1ab">Restos a pagar →</span></div>'
    f"<div><div style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:30px;line-height:1;color:oklch(0.55 0.11 25)\">"
    f"{fmt_compact(_total_pendente)}</div>"
    f'<div style="font-size:11.5px;color:#6b7280;margin-top:4px">pendentes a {_num_fornecedores} fornecedores</div></div>'
    + (f'<div style="display:flex;gap:6px;align-items:flex-end;height:32px">{_mini_bars}</div>' if _mini_bars else "")
    + f'<div style="font-size:11px;color:#9aa1ab;border-top:1px solid #f0f1f4;padding-top:9px">'
    f'Dívida mais antiga desde <strong style="color:#6b7280">{_ano_mais_antigo}</strong></div></div>'
)

# Licitações card
_lista_licitacoes = [_mapa_contagens[y] for y in anos]
_adesao_counts_list = [_adesao_map[y] for y in anos]
_adesao_ext_counts_list = [_adesao_ext_map[y] for y in anos]
_contagens_fracionamento_list = [_mapa_fracionamento[y] for y in anos]
_contratos_sem_lic = int(licitacoes["acima_limite"].sum()) if not licitacoes.empty else 0
_fracionamento_ano = _mapa_fracionamento[year]

_risk_color = "" if _fracionamento_ano == 0 else ";color:oklch(0.55 0.11 25)"


def _lic_line(num: int, label: str, risk: bool = False) -> str:
    color = ";color:oklch(0.55 0.11 25)" if risk else ""
    return (
        f'<div style="display:flex;align-items:center;gap:8px;font-size:12.5px">'
        f"<strong style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:18px;width:26px{color}\">{num}</strong>"
        f'<span style="flex:1;color:#4b5563">{label}</span></div>'
    )


_card_licitacoes = (
    '<div style="background:#fff;border:1px solid #e7e9ee;border-radius:14px;padding:20px 22px;display:flex;flex-direction:column;gap:13px">'
    '<div style="display:flex;align-items:center;justify-content:space-between">'
    "<span style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:15px\">Licitações</span>"
    '<span style="font-size:11px;color:#9aa1ab">Contratos →</span></div>'
    '<div style="display:flex;flex-direction:column;gap:9px">'
    + _lic_line(_contratos_sem_lic, "Acima do limite s/ licitação")
    + _lic_line(_adesao_map[year], "Adesões de ata (carona)")
    + _lic_line(_adesao_ext_map[year], "Empenhos via ata externa")
    + _lic_line(_fracionamento_ano, "Possível fracionamento", risk=_fracionamento_ano > 0)
    + "</div></div>"
)

# Pessoal card
_pct_folha_val = 0.0
_pct_efetivos_val = 0.0
_lrf_pct = 54

if not df_folha_resumo.empty:
    _folha_ano = df_folha_resumo[df_folha_resumo["ano"] == year]
    _row_folha = _folha_ano.iloc[0] if not _folha_ano.empty else df_folha_resumo.iloc[-1]
    _pct_folha_val = float(_row_folha["percentual_folha"])

if not df_cargos.empty:
    _series_pct_efetivos = []
    for _y in sorted(df_cargos["ano"].unique()):
        if _y > year:
            continue
        _qty = df_cargos[df_cargos["ano"] == _y].set_index("tipo_vinculo_detalhado")["quantidade"].to_dict()
        _efetivos = _qty.get("Servidor Efetivo com Função de Confiança (DAI/FG)", 0) + _qty.get(
            "Servidor Efetivo com Cargo Comissionado (DAS/CC)", 0
        )
        _total_conf = _efetivos + _qty.get("Comissionado Externo (DAS/CC - Sem Vínculo)", 0)
        _series_pct_efetivos.append((_efetivos / _total_conf * 100) if _total_conf > 0 else 0.0)
    if _series_pct_efetivos:
        _pct_efetivos_val = _series_pct_efetivos[-1]

_folha_bar_pct = min(int(_pct_folha_val), 100)
_lrf_marker_left = min(_lrf_pct, 100)

_card_pessoal = (
    f'<div style="background:#fff;border:1px solid #e7e9ee;border-radius:14px;padding:20px 22px;display:flex;flex-direction:column;gap:13px">'
    f'<div style="display:flex;align-items:center;justify-content:space-between">'
    f"<span style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:15px\">Pessoal</span>"
    f'<span style="font-size:11px;color:#9aa1ab">Folha →</span></div>'
    f"<div><div style=\"font-family:'Source Serif 4',serif;font-weight:700;font-size:30px;line-height:1\">"
    f'{_pct_folha_val:.1f}<span style="font-size:16px;color:#9aa1ab">%</span></div>'
    f'<div style="font-size:11.5px;color:#6b7280;margin-top:4px">da receita vai para a folha</div></div>'
    f'<div><div style="height:8px;background:#eef0f4;border-radius:5px;overflow:hidden;position:relative">'
    f'<div style="width:{_folha_bar_pct}%;height:100%;background:oklch(0.62 0.11 215);border-radius:5px"></div>'
    f'<div style="position:absolute;left:{_lrf_marker_left}%;top:-3px;width:2px;height:14px;background:#c0392b"></div></div>'
    f'<div style="font-size:10.5px;color:#9aa1ab;margin-top:5px">limite LRF: {_lrf_pct}% da RCL</div></div>'
    f'<div style="font-size:11px;color:#9aa1ab;border-top:1px solid #f0f1f4;padding-top:9px">'
    f'<strong style="color:#6b7280">{_pct_efetivos_val:.0f}%</strong> das chefias com servidores efetivos</div></div>'
)

st.html(
    f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:2rem">'
    f"{_card_despesas}{_card_licitacoes}{_card_pessoal}</div>"
)
