import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, get_extraction_date, render_sidebar
from sqlalchemy.engine import Engine

import glossary
from analysis import adesao_de_ata, health_story

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _health(conn, year, _extracted_at):
    return health_story.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, _extracted_at):
    return adesao_de_ata.run_external(conn, year, empresa_id="2")


conn = get_conn()
year = render_sidebar()
_extracted_at = get_extraction_date(conn)

st.title("Fundo Municipal de Saúde")
st.caption(f"Dados do Fundo Municipal de Saúde extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")

data = _health(conn, year, _extracted_at)
adesao_externa = _adesao_externa(conn, year, _extracted_at)
# Create MM/YYYY column for display
for key, val in data.items():
    if isinstance(val, pd.DataFrame) and "mes" in val.columns:
        if "ano" in val.columns:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + val["ano"].astype(str)
        else:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + str(year)


# ── Seção 1: O que entrou ───────────────────────────────────────────────────
st.header("① O que entrou")
st.subheader("Emendas Parlamentares")
if data["emendas_total"] > 0:
    st.metric("Total de emendas (valor autorizado)", fmt_currency(data["emendas_total"]))
    if not data["emendas"].empty and data["emendas"].notna().any().any():
        st.dataframe(
            data["emendas"].rename(
                columns={
                    "numero": "Nº",
                    "descricao": "Objeto",
                    "Período": "Período",
                    "valor": "Valor Autorizado",
                    "empenhado": "Empenhado",
                    "autor": "Autor",
                    "Tipo da Emenda": "Tipo da Emenda",
                    "Esfera de Origem": "Esfera de Origem",
                    "ato_normativo": "Ato Normativo",
                    "Destinação": "Destinação",
                }
            ),
            width="stretch",
            column_config={
                "Valor Autorizado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Nº": None,
                "Tipo da Emenda": None,
                "Esfera de Origem": None,
                "Destinação": None,
            },
            hide_index=True,
        )
    with st.expander(":material/info: O que é uma emenda parlamentar?"):
        st.write(glossary.tooltip("Emenda Impositiva"))
else:
    st.info("Sem emendas parlamentares registradas para este ano.")

st.subheader("Orçamento")
budget = data["budget"]
c1, c2, c3 = st.columns(3)
c1.metric("Dotação Atualizada", fmt_currency(budget["dotacao"]), help=glossary.tooltip("Dotação Atualizada"))
c2.metric("Total Empenhado", fmt_currency(budget["empenhado"]), help=glossary.tooltip("Empenho"))
c3.metric("Taxa de Execução", f"{budget['taxa_execucao']:.1%}")
if budget["flag_under_execution"]:
    st.warning(f"Taxa de execução abaixo de 70% ao final do ano {year}.", icon=":material/warning:")

st.subheader("Repasses da Prefeitura")
transfers_total = data["transfers_to_health_total"]
if transfers_total > 0:
    st.metric(
        "Total de repasses recebidos",
        fmt_currency(transfers_total),
        help="Valores transferidos pela Prefeitura Municipal ao Fundo de Saúde no ano.",
    )
else:
    st.info("Sem repasses registrados para este ano.")

# ── Seção 2: O que foi gasto ────────────────────────────────────────────────
st.header("② O que foi gasto")
st.subheader("Evolução do Gasto (Empenhado por Ano)")
trend = data["execution_trend"]
if not trend.empty:
    fig = px.bar(
        trend,
        x="ano",
        y="empenhado",
        title="Fundo de Saúde — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        trend.rename(columns={"ano": "Ano", "empenhado": "Empenhado"}),
        width="stretch",
        hide_index=True,
        column_config={
            "Ano": st.column_config.NumberColumn(format="%d"),
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.0f"),
        },
    )


# ── Seção 3: Como foi contratado ────────────────────────────────────────────
st.header("③ Como foi contratado")

c1, c2, c3 = st.columns(3)
c1.metric(
    "Licitações via Adesão de Ata (Carona)",
    data["adesao_de_ata_count"],
    help=glossary.tooltip("Adesão de Ata (Carona)"),
)
adesao_df = data["adesao_de_ata_list"]
c2.metric(
    "Qtd. de Contratos Vinculados",
    data["adesao_de_ata_contracts_linked"],
)
c3.metric("Valor Total Contratado via Adesão", fmt_currency(data["adesao_de_ata_value"]))

if not data["adesao_de_ata_list"].empty:
    with st.expander("Ver licitações via Adesão de Ata"):
        st.dataframe(
            data["adesao_de_ata_list"]
            .rename(
                columns={
                    "numero": "Nº Licit.",
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "has_contract": "Contrato Associado",
                }
            )
            .drop(columns=["mes", "ano"], errors="ignore"),
            width="stretch",
            hide_index=True,
        )

c1, c2 = st.columns(2)
c1.metric(
    "Empenhos via Ata Externa",
    adesao_externa["count"],
    help="Empenhos cuja justificativa contábil referencia uma Ata de Registro de Preços de outro ente (Termo de Adesão Externa).",
)
c2.metric("Valor Total Pago via Ata Externa", fmt_currency(adesao_externa["total_pago"]))

if not adesao_externa["list"].empty:
    with st.expander("Ver empenhos via Ata de Registro de Preços Externa"):
        st.caption(
            "Registros extraídos da justificativa contábil dos empenhos do Fundo Municipal de Saúde "
            "que referenciam explicitamente um Termo de Adesão Externa a Ata de Registro de Preços."
        )
        st.dataframe(
            adesao_externa["list"].rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "pago": "Valor Pago",
                    "unidade": "Unidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={"Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f")},
            width="stretch",
            hide_index=True,
        )

st.subheader("Distribuição por Modalidade")
modality_df = data["contracts_by_modality"]
if not modality_df.empty and modality_df.notna().all().all():
    st.dataframe(
        modality_df.rename(
            columns={
                "modality": "Modalidade",
                "count": "Qtd",
                "total_value": "Valor Total",
                "periodo": "Período",
            }
        )
        .sort_values(by=["Modalidade", "Período"], ascending=True)
        .drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        column_config={"Valor Total": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
        column_order=["Período", "Modalidade", "Qtd", "Valor Total"],
    )
    with st.expander(":material/info: O que são essas modalidades?"):
        st.write(f"**Licitação:** {glossary.tooltip('Licitação')}")
        st.write(f"**Pregão Eletrônico:** {glossary.tooltip('Pregão Eletrônico')}")
        st.write(f"**Pregão Presencial:** {glossary.tooltip('Pregão Presencial')}")
        st.write(f"**Dispensa:** {glossary.tooltip('Dispensa de Licitação')}")
        st.write(f"**Inexigibilidade:** {glossary.tooltip('Inexigibilidade')}")
        st.write(f"**Adesão de Ata:** {glossary.tooltip('Adesão de Ata (Carona)')}")

st.subheader("Contratos sem Licitação acima de R$ 62.725,59")
st.caption(
    "[Lei 14.133/21, Art. 75, I](https://licitacoesecontratos.tcu.gov.br/5-10-2-1-dispensa-em-razao-do-valor-incisos-i-e-ii-2/)"
)
gaps = data["bidding_gaps"]
if not gaps.empty and gaps.notna().all().all():
    st.metric("Total de contratos", len(gaps))
    st.dataframe(
        gaps.rename(
            columns={
                "periodo": "Período",
                "numero": "Nº",
                "fornecedor": "Fornecedor",
                "objeto": "Objeto",
                "valcon": "Valor",
                "modali": "Modalidade",
            }
        )
        .sort_values(by="Valor", ascending=False)
        .drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        column_config={"Nº": None, "Valor": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
        column_order=["Período", "Nº", "Fornecedor", "Objeto", "Valor", "Modalidade"],
    )
else:
    st.success("Nenhum contrato acima do limite legal sem processo licitatório.")

if not data["splitting"].empty and data["splitting"].notna().all().all():
    st.subheader(":material/warning: Possível fracionamento de contratos")
    st.dataframe(
        data["splitting"].rename(columns={"periodo": "Período"}).drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        hide_index=True,
    )

# ── Seção 4: Quem recebeu ────────────────────────────────────────────────────
st.header("④ Quem recebeu")
st.metric(
    "HHI (concentração de fornecedores)",
    f"{data['hhi']:,.0f}",
    help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
)
if not data["top_suppliers"].empty and data["top_suppliers"].notna().all().all():
    st.subheader("Top 10 Fornecedores")

    # Display main Top 10 table
    st.dataframe(
        data["top_suppliers"].rename(columns={"descricao": "Fornecedor", "empenhado": "Empenhado", "percentual": "%"}),
        width="stretch",
        column_config={
            "codigo": None,
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "%": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
    )

    # New: Supplier-to-Services Correlation Table
    st.subheader("Top Fornecedores e seus Objetos de Contrato")
    services_df = data["top_suppliers_services"]
    top_suppliers_names = data["top_suppliers"]["descricao"].unique()

    top_services = health_story.top_services_per_supplier(services_df, top_suppliers_names)

    st.dataframe(
        top_services.rename(
            columns={
                "fornecedor": "Fornecedor",
                "objeto": "Objeto / Serviço",
                "total": "Valor Contratado",
            }
        ),
        width="stretch",
        column_config={"Valor Contratado": st.column_config.NumberColumn(format="R$ %,.2f")},
        hide_index=True,
    )

st.divider()
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")

# ── Exportar relatório ───────────────────────────────────────────────────────
st.subheader("Exportar")

if "saude_report_year" not in st.session_state:
    st.session_state["saude_report_year"] = None

if st.button("Gerar Relatório HTML"):
    from report.saude import generate

    path = generate(conn, year)
    st.session_state["saude_report_year"] = (year, str(path))

if st.session_state["saude_report_year"] is not None:
    _year, _path = st.session_state["saude_report_year"]
    with open(_path, "rb") as f:
        st.download_button(
            label=f"Baixar relatório {_year} (HTML)",
            data=f,
            file_name=f"saude-{_year}.html",
            mime="text/html",
            key="download_saude_report",
        )
