import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

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

import glossary
from analysis import adesao_de_ata, historia_saude

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _saude(conn, year, _extracted_at):
    return historia_saude.run(conn, year)


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _adesao_externa(conn, year, _extracted_at):
    return adesao_de_ata.run_external(conn, year, empresa_ids=["2"])


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def _pdf(conn, year, _extracted_at):
    from report.saude_pdf import generate as generate_pdf

    return generate_pdf(conn, year)


conn = get_conn()
year, _ = render_sidebar()
_extracted_at = get_data_extracao(conn)

col_titulo, col_botao = st.columns([8, 2])
with col_titulo:
    st.title(f"Fundo Municipal de Saúde - {year}")
    st.caption(f"Dados do Fundo Municipal de Saúde extraídos do [Portal de Transparência]({glossary.PORTAL_URL}).")
with col_botao:
    st.write("")
    st.write("")
    pdf_bytes = _pdf(conn, year, _extracted_at)
    st.download_button(
        label="⬇ Baixar PDF",
        data=pdf_bytes,
        file_name=f"saude-{year}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

if year == ANO_ATUAL:
    render_aviso_ano_parcial(year, _extracted_at)

dados = _saude(conn, year, _extracted_at)
adesao_externa = _adesao_externa(conn, year, _extracted_at)
# Criar coluna MM/AAAA para exibição
for key, val in dados.items():
    if isinstance(val, pd.DataFrame) and "mes" in val.columns:
        if "ano" in val.columns:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + val["ano"].astype(str)
        else:
            val["periodo"] = val["mes"].astype(str).str.zfill(2) + "/" + str(year)

# ── KPIs resumo ─────────────────────────────────────────────────────────────
orcamento = dados["orcamento"]
tendencia_orcamento = dados["tendencia_orcamento"]
tendencia_ate_ano = tendencia_orcamento[tendencia_orcamento["ano"] <= year]
tendencia_farma = dados["pharma_empenhos"]["trend"]
tendencia_farma_ate_ano = tendencia_farma[tendencia_farma["ano"] <= year]

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Dotação Atualizada",
        fmt_compact(orcamento["dotacao"]),
        delta=pct_delta(tendencia_ate_ano["dotacao"].tolist()),
        delta_color="off",
        help=glossary.tooltip("Dotação Atualizada"),
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["dotacao"].tolist()),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_dotacao",
        )

with k2:
    st.metric(
        "Total Empenhado",
        fmt_compact(orcamento["empenhado"]),
        delta=pct_delta(tendencia_ate_ano["empenhado"].tolist()) if year != ANO_ATUAL else "—",
        delta_color="off",
        help=glossary.tooltip("Empenho"),
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["empenhado"].tolist(), "#4CAF50"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_empenhado",
        )

with k3:
    st.metric(
        "Taxa de Execução",
        f"{orcamento['taxa_execucao']:.1%}",
        delta=pct_delta(tendencia_ate_ano["taxa"].tolist()) if year != ANO_ATUAL else "—",
        delta_color="off" if year == ANO_ATUAL else "normal",
    )
    if len(tendencia_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(tendencia_ate_ano["ano"].tolist(), tendencia_ate_ano["taxa"].tolist(), "#FF9800"),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_taxa",
        )

with k4:
    st.metric(
        "Medicamentos e Insumos",
        fmt_compact(dados["pharma_empenhos"]["total"]),
        delta=pct_delta(tendencia_farma_ate_ano["empenhado"].tolist()),
        delta_color="off",
        help="Total empenhado em Material de Consumo na Subfunção 10.303 (Suporte Profilático e Terapêutico).",
    )
    if len(tendencia_farma_ate_ano) >= 2:
        st.plotly_chart(
            sparkline(
                tendencia_farma_ate_ano["ano"].tolist(), tendencia_farma_ate_ano["empenhado"].tolist(), "#9C27B0"
            ),
            use_container_width=True,
            config=SPARK_CFG,
            key="spark_pharma",
        )

st.divider()

# ── Seção 1: O que entrou ───────────────────────────────────────────────────
st.header("① O que entrou")
st.subheader("Emendas Parlamentares")
if dados["emendas_total"] > 0:
    st.metric("Total de emendas (valor autorizado)", fmt_currency(dados["emendas_total"]))
    if not dados["emendas"].empty and dados["emendas"].notna().any().any():
        st.dataframe(
            dados["emendas"].rename(
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
c1, c2, c3 = st.columns(3)
c1.metric("Dotação Atualizada", fmt_currency(orcamento["dotacao"]), help=glossary.tooltip("Dotação Atualizada"))
c2.metric("Total Empenhado", fmt_currency(orcamento["empenhado"]), help=glossary.tooltip("Empenho"))
c3.metric("Taxa de Execução", f"{orcamento['taxa_execucao']:.1%}")
if orcamento["alerta_sub_execucao"]:
    st.warning(f"Taxa de execução abaixo de 70% ao final do ano {year}.", icon=":material/warning:")

st.subheader("Repasses da Prefeitura")
total_repasses = dados["transferencias_saude_total"]
if total_repasses > 0:
    st.metric(
        "Total de repasses recebidos",
        fmt_currency(total_repasses),
        help="Valores transferidos pela Prefeitura Municipal ao Fundo de Saúde no ano.",
    )
else:
    st.info("Sem repasses registrados para este ano.")

# ── Seção 2: O que foi gasto ────────────────────────────────────────────────
st.header("② O que foi empenhado")
st.subheader("Evolução do Empenhado por Ano")
tendencia_execucao = dados["tendencia_execucao"]
if not tendencia_execucao.empty:
    fig = px.bar(
        tendencia_execucao,
        x="ano",
        y="empenhado",
        title="Fundo de Saúde — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
    )
    fig.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.0f}<extra></extra>")
    fig.update_layout(yaxis=dict(tickprefix="R$ ", tickformat=",.0f"))
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, width="stretch")

    st.dataframe(
        tendencia_execucao.rename(columns={"ano": "Ano", "empenhado": "Empenhado"}),
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
    dados["adesao_de_ata_count"],
    help=glossary.tooltip("Adesão de Ata (Carona)"),
)
adesao_df = dados["adesao_de_ata_list"]
c2.metric(
    "Qtd. de Contratos Vinculados",
    dados["adesao_de_ata_contracts_linked"],
)
c3.metric("Valor Total Contratado via Adesão", fmt_currency(dados["adesao_de_ata_value"]))

if not dados["adesao_de_ata_list"].empty:
    with st.expander("Ver licitações via Adesão de Ata"):
        _ata_df = dados["adesao_de_ata_list"].copy()
        _ata_df["licitacao_valor"] = pd.to_numeric(
            _ata_df["licitacao_valor"].astype(str).str.replace(",", "."), errors="coerce"
        )
        st.dataframe(
            _ata_df.rename(
                columns={
                    "numero": "Nº Licit.",
                    "objeto": "Objeto",
                    "periodo": "Período",
                    "licitacao_valor": "Valor Est. Licitação",
                    "total_c_valor": "Valor Total Contratado",
                    "total_c_empenhado": "Valor Empenhado",
                    "tem_contrato": "Contrato Associado",
                }
            ).drop(columns=["mes", "ano"], errors="ignore"),
            width="stretch",
            column_config={
                "Nº Licit.": None,
                "Valor Est. Licitação": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Total Contratado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Valor Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            hide_index=True,
        )

c1, c2 = st.columns(2)
c1.metric(
    "Empenhos via Ata Externa",
    adesao_externa["quantidade"],
    help="Empenhos cuja justificativa contábil referencia uma Ata de Registro de Preços de outro ente (Termo de Adesão Externa).",
)
c2.metric("Valor Total Pago via Ata Externa", fmt_currency(adesao_externa["total_pago"]))

if not adesao_externa["lista"].empty:
    with st.expander("Ver empenhos via Ata de Registro de Preços Externa"):
        st.caption(
            "Registros extraídos da justificativa contábil dos empenhos do Fundo Municipal de Saúde "
            "que referenciam explicitamente um Termo de Adesão Externa a Ata de Registro de Preços."
        )
        st.dataframe(
            adesao_externa["lista"].rename(
                columns={
                    "data": "Data",
                    "fornecedor": "Fornecedor",
                    "pago": "Valor Pago",
                    "unidade": "Unidade",
                    "justificativa": "Justificativa Contábil",
                    "num_licitacao": "Nº Licitação",
                }
            ),
            column_config={
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Valor Pago": st.column_config.NumberColumn(format="R$ %,.2f"),
            },
            width="stretch",
            hide_index=True,
        )

st.subheader("Distribuição por Modalidade")
df_modalidades = dados["contratos_por_modalidade"]
if not df_modalidades.empty and df_modalidades.notna().all().all():
    st.dataframe(
        df_modalidades.rename(
            columns={
                "modalidade": "Modalidade",
                "quantidade": "Qtd",
                "valor_total": "Valor Total",
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
lacunas_saude = dados["licitacao_gaps"]
if not lacunas_saude.empty and lacunas_saude.notna().all().all():
    st.metric("Total de contratos", len(lacunas_saude))
    st.dataframe(
        lacunas_saude.rename(
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

if not dados["fracionamento"].empty and dados["fracionamento"].notna().all().all():
    st.subheader(":material/warning: Possível fracionamento de contratos")
    st.dataframe(
        dados["fracionamento"].rename(columns={"periodo": "Período"}).drop(columns=["mes", "ano"], errors="ignore"),
        width="stretch",
        hide_index=True,
    )

# ── Seção 4: Quem recebeu ────────────────────────────────────────────────────
st.header("④ Quem recebeu")
st.metric(
    "HHI (concentração de fornecedores)",
    f"{dados['hhi']:,.0f}",
    help="Índice Herfindahl-Hirschman. Acima de 2.500 = concentração alta.",
)
if not dados["principais_fornecedores"].empty and dados["principais_fornecedores"].notna().all().all():
    st.subheader("Top 10 Fornecedores")

    # Exibir tabela principal Top 10
    st.dataframe(
        dados["principais_fornecedores"].rename(
            columns={"descricao": "Fornecedor", "empenhado": "Empenhado", "percentual": "%"}
        ),
        width="stretch",
        column_config={
            "codigo": None,
            "Empenhado": st.column_config.NumberColumn(format="R$ %,.2f"),
            "%": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
    )

    # Tabela de correlação Fornecedor × Serviços Contratados
    st.subheader("Top Fornecedores e seus Objetos de Contrato")
    df_servicos = dados["principais_fornecedores_servicos"]
    nomes_top_fornecedores = dados["principais_fornecedores"]["descricao"].unique()

    top_servicos = historia_saude.get_principais_servicos_por_fornecedor(df_servicos, nomes_top_fornecedores)

    st.dataframe(
        top_servicos.rename(
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

# ── Seção 5: Insumos e Assistência Farmacêutica ────────────────────────────────
st.header("⑤ Insumos e Assistência Farmacêutica")

# Bloco A — Empenhos de Medicamentos e Insumos
st.subheader("Medicamentos e Insumos (Subfunção 10.303 — Material de Consumo)")
pharma = dados["pharma_empenhos"]
st.metric(
    "Total Empenhado em Medicamentos e Insumos",
    fmt_currency(pharma["total"]),
    help="Empenhos da Subfunção 10.303 (Suporte Profilático e Terapêutico) com Natureza de Despesa 3.3.90.30 (Material de Consumo).",
)
st.caption(
    "Os valores acima refletem empenhos diretos classificados na Subfunção 10.303 com Natureza de Despesa 3.3.90.30. "
    "Compras de medicamentos e insumos realizadas via **Adesão a Ata de Registro de Preços Externa** estão "
    "contabilizadas separadamente na seção _Como foi contratado_."
)

pharma_trend = pharma["trend"]
if not pharma_trend.empty:
    fig_pharma = px.bar(
        pharma_trend,
        x="ano",
        y="empenhado",
        title="Medicamentos e Insumos — Empenhado por Ano",
        labels={"ano": "Ano", "empenhado": "Empenhado"},
    )
    fig_pharma.update_traces(hovertemplate="Ano: %{x}<br>Empenhado: R$ %{y:,.2f}<extra></extra>")
    fig_pharma.update_layout(yaxis=dict(tickprefix="R$ ", tickformat=",.0f"))
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig_pharma, width="stretch")

if not pharma["detail"].empty:
    with st.expander("Ver detalhes por fornecedor"):
        st.dataframe(
            pharma["detail"].rename(
                columns={"fornecedor": "Fornecedor", "descricao": "Descrição", "total": "Empenhado"}
            ),
            width="stretch",
            column_config={"Empenhado": st.column_config.NumberColumn(format="R$ %,.2f")},
            hide_index=True,
        )

# Bloco B — Licitações de Medicamentos e Insumos
st.subheader("Licitações de Medicamentos e Insumos")
pharma_licit = dados["pharma_licitacoes"]
if pharma_licit.empty:
    st.info("Sem licitações de medicamentos ou insumos registradas para este ano.")
else:
    st.dataframe(
        pharma_licit.rename(
            columns={
                "numero": "Nº",
                "objeto": "Objeto",
                "modalidade": "Modalidade",
                "situacao": "Situação",
                "data_abertura": "Data Abertura",
            }
        ).drop(columns=["valor", "valor_num"], errors="ignore"),
        width="stretch",
        column_config={
            "Nº": None,
        },
        hide_index=True,
        column_order=["Nº", "Objeto", "Modalidade", "Situação", "Data Abertura"],
    )

# Bloco C — Judicialização da Saúde
st.subheader(":material/gavel: Judicialização da Saúde")
st.caption(
    "Despesas decorrentes de sentenças judiciais (Elemento 3.3.90.91) do Fundo Municipal de Saúde, "
    "separadas das compras programadas de medicamentos e insumos."
)
pharma_jud = dados["pharma_judicial"]
st.metric(
    "Total Empenhado por Determinação Judicial",
    fmt_currency(pharma_jud["total"]),
    help="Empenhos com Elemento de Despesa 3.3.90.91 (Sentenças Judiciais) no Fundo Municipal de Saúde.",
)
if pharma_jud["total"] == 0:
    st.info("Sem registros de judicialização para este ano.")
elif not pharma_jud["detail"].empty:
    with st.expander("Ver detalhes"):
        st.dataframe(
            pharma_jud["detail"].rename(
                columns={
                    "subfuncao": "Subfunção",
                    "fornecedor": "Fornecedor",
                    "descricao": "Descrição",
                    "total": "Empenhado",
                }
            ),
            width="stretch",
            column_config={"Empenhado": st.column_config.NumberColumn(format="R$ %,.2f")},
            hide_index=True,
        )

st.divider()
st.caption(f"Fonte: [Portal de Transparência]({glossary.PORTAL_URL})")
