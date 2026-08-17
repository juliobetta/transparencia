#!/usr/bin/env python3
"""
codegen-taxonomy.py
Sincroniza automaticamente os esquemas dos dbt marts (.yml) com o arquivo JSON de taxonomia em apps/web/lib/mcp/fiscal-taxonomy.json.
Lê dinamicamente nomes de tabelas, descrições, colunas e domínios fiscais.
"""

import json
from pathlib import Path
import yaml

MARTS_DIR = Path("elt/transform/models/marts")
TARGET_FILE = Path("apps/web/lib/mcp/fiscal-taxonomy.json")


def infer_domain(
    model_name: str, meta_domain: str | None, tags: list[str] | None, description: str
) -> str:
    """Classifica o domínio do modelo dbt de forma 100% dinâmica."""
    name = model_name.lower()
    desc = description.lower()

    # Tabelas de dimensão (dim_*) ganham domínio próprio de destaque
    if name.startswith("dim_"):
        return "Dimensões Fiscais e Cadastros (STN/MCASP)"

    if meta_domain:
        return meta_domain

    if tags:
        tags_lower = [t.lower() for t in tags]
        if "saude" in tags_lower or "caprem" in tags_lower:
            return "Saúde e CAPREM"
        if "licitacoes" in tags_lower or "contratos" in tags_lower:
            return "Licitações e Contratos"
        if "posicao_fiscal" in tags_lower:
            return "Posição Fiscal"
        if "receitas" in tags_lower:
            return "Receitas e Emendas"
        if "despesas" in tags_lower:
            return "Despesas e Credores"

    if "posicao_fiscal" in name or "posicao fiscal" in desc:
        return "Posição Fiscal"
    if any(k in name for k in ["saude", "caprem"]):
        return "Saúde e CAPREM"
    if any(
        k in name
        for k in [
            "licitacao",
            "licitacoes",
            "contrato",
            "contratos",
            "diaria",
            "diarias",
        ]
    ):
        return "Licitações e Contratos"
    if any(
        k in name
        for k in [
            "receita",
            "receitas",
            "emenda",
            "emendas",
            "fonte",
            "fontes",
            "transferencia",
        ]
    ):
        return "Receitas e Emendas"
    if any(
        k in name
        for k in [
            "despesa",
            "despesas",
            "credor",
            "credores",
            "fornecedor",
            "fornecedores",
        ]
    ):
        return "Despesas e Credores"
    if any(
        k in name
        for k in [
            "orcamento",
            "pessoal",
            "folha",
            "departamento",
            "funcao",
            "orgao",
            "natureza",
            "elemento",
        ]
    ):
        return "Orçamento e Pessoal"

    return "Outros Marts"


def main():
    if not MARTS_DIR.exists():
        print(f"❌ Diretório {MARTS_DIR} não encontrado.")
        return

    marts_by_domain: dict[str, list[dict]] = {}
    total_models = 0

    for yml_path in sorted(MARTS_DIR.rglob("*.yml")):
        with open(yml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data or "models" not in data:
                continue

            for m in data["models"]:
                name = m["name"]
                desc = m.get("description", "").strip()
                cols = [c["name"] for c in m.get("columns", [])]

                # Suporte a meta.domain no YAML dbt
                meta_domain = m.get("meta", {}).get("domain") or m.get(
                    "config", {}
                ).get("meta", {}).get("domain")
                tags = m.get("tags") or m.get("config", {}).get("tags")

                domain = infer_domain(name, meta_domain, tags, desc)

                mart_info = {
                    "table": name,
                    "description": desc or f"Mart {name}",
                    "columns": cols,
                }

                if domain not in marts_by_domain:
                    marts_by_domain[domain] = []
                marts_by_domain[domain].append(mart_info)
                total_models += 1

    print(
        f"🔍 Extraídos dinamicamente {total_models} modelos de marts distribuídos em {len(marts_by_domain)} domínios."
    )

    # Ordem fixa e amigável dos domínios principais
    preferred_order = [
        "Posição Fiscal",
        "Despesas e Credores",
        "Receitas e Emendas",
        "Saúde e CAPREM",
        "Licitações e Contratos",
        "Orçamento e Pessoal",
        "Dimensões Fiscais e Cadastros (STN/MCASP)",
        "Outros Marts",
    ]

    taxonomy = []
    for dom in preferred_order:
        if dom in marts_by_domain:
            marts_list = marts_by_domain.pop(dom)
            marts_list.sort(
                key=lambda m: ("00_" + m["table"])
                if m["table"] == "fct_posicao_fiscal_metricas"
                else m["table"]
            )
            taxonomy.append({"domain": dom, "marts": marts_list})

    # Quaisquer outros domínios customizados
    for dom, marts in marts_by_domain.items():
        marts.sort(key=lambda m: m["table"])
        taxonomy.append({"domain": dom, "marts": marts})

    json_str = json.dumps(taxonomy, indent=2, ensure_ascii=False)
    TARGET_FILE.write_text(json_str + "\n", encoding="utf-8")

    print(
        f"✅ Sincronização dinâmica concluída! Taxonomia JSON gerada em {TARGET_FILE}."
    )


if __name__ == "__main__":
    main()
