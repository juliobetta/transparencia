import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st
from shared import fmt_currency, get_conn, render_sidebar

import glossary
from analysis import revenue_sources

conn = get_conn()
year = render_sidebar()

st.header("Fontes de Receita")

# Informative historical limitations notice
if year < 2026:
    st.info(
        "ℹ️ O portal de transparência municipal disponibiliza previsões orçamentárias detalhadas para todos os anos, "
        "mas os dados de arrecadação efetiva estão disponíveis na API apenas a partir do exercício de 2026."
    )
else:
    st.success("✅ Dados de Arrecadação Realizados disponíveis para o exercício corrente (2026).")

with st.expander("ℹ️ Glossário de Termos"):
    st.write(f"**Receita Própria:** {glossary.tooltip('Receita Própria')}")
    st.write(f"**FPM:** {glossary.tooltip('FPM (Fundo de Participação dos Municípios)')}")

df = revenue_sources.run(conn, [year])
if not df.empty:
    row = df.iloc[0]

    # Double metric column layout
    c1, c2 = st.columns(2)
    c1.metric("Previsão Orçamentária", fmt_currency(row["total_previsto"]))

    if year == 2026:
        c2.metric("Total Arrecadado Real", fmt_currency(row["total_arrecadado"]))

        # Progress Bar
        progress_pct = (row["total_arrecadado"] / row["total_previsto"]) if row["total_previsto"] > 0 else 0
        st.markdown(f"**Progresso de Arrecadação Anual: {progress_pct * 100:.2f}%**")
        st.progress(min(max(progress_pct, 0.0), 1.0))
    else:
        c2.metric("Total Arrecadado Real", "N/D (Não Disp. na API)")

    # Detailed Summary Table
    st.subheader("Previsto vs. Arrecadado por Origem")

    resumo_data = [
        {
            "Fonte": "Receita Própria (Municipal)",
            "Previsto": row["receita_propria_previsto"],
            "Arrecadado": row["receita_propria_arrecadado"] if year == 2026 else None,
        },
        {
            "Fonte": "Transferências da União (Federal)",
            "Previsto": row["transferencias_uniao_previsto"],
            "Arrecadado": row["transferencias_uniao_arrecadado"] if year == 2026 else None,
        },
        {
            "Fonte": "Transferências do Estado",
            "Previsto": row["transferencias_estado_previsto"],
            "Arrecadado": row["transferencias_estado_arrecadado"] if year == 2026 else None,
        },
    ]
    resumo_df = pd.DataFrame(resumo_data)

    if year == 2026:
        resumo_df["Desvio/Falta"] = resumo_df["Previsto"] - resumo_df["Arrecadado"]
        resumo_df["Realização (%)"] = (resumo_df["Arrecadado"] / resumo_df["Previsto"]) * 100

        # Bar chart comparing predicted vs collected
        melt_df = resumo_df.melt(
            id_vars=["Fonte"], value_vars=["Previsto", "Arrecadado"], var_name="Métrica", value_name="Valor"
        )
        fig = px.bar(
            melt_df,
            x="Fonte",
            y="Valor",
            color="Métrica",
            barmode="group",
            title="Comparação: Planejado (Previsão) vs. Arrecadado Real",
            labels={"Valor": "R$ (Reais)", "Fonte": "Fonte de Receita"},
        )
        fig.update_layout(yaxis_tickformat=",.2f")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            resumo_df,
            column_config={
                "Previsto": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Arrecadado": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Desvio/Falta": st.column_config.NumberColumn(format="R$ %,.2f"),
                "Realização (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        fig = px.pie(resumo_df, values="Previsto", names="Fonte", title="Distribuição da Previsão Orçamentária")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            resumo_df[["Fonte", "Previsto"]],
            column_config={"Previsto": st.column_config.NumberColumn(format="R$ %,.2f")},
            use_container_width=True,
            hide_index=True,
        )

    if row["alerta_dependencia"]:
        st.warning(
            "⚠️ Alerta: Receita própria municipal está abaixo de 10% do total. Alta dependência fiscal de repasses federais e estaduais."
        )

st.caption(f"[Ver portal oficial de transparência →]({glossary.PORTAL_URL})")
