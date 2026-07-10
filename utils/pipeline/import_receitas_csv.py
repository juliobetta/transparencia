import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import unicodedata

import pandas as pd
from sqlalchemy import text

import db

# ==============================================================================
# PADRÃO DE ARQUIVOS CSV ESPERADOS:
# Os arquivos devem ser salvos no diretório: data/csv/receitas/
# Seguindo o padrão de nomenclatura: <orgao>_<ano>_<endpoint>.csv
#
# Onde:
#   - <orgao>    : ID da empresa/entidade contábil (ex: 7 para Prefeitura, 2 para Saúde)
#   - <ano>      : Ano correspondente ao exercício fiscal (ex: 2024)
#   - <endpoint> : Nome da listagem oficial correspondente no portal municipal.
#                  Mapeamentos aceitos:
#                    * 'ReceitaOrcamentaria'       -> tabela 'receita_orcamentaria'
#                    * 'ReceitaUniao'             -> tabela 'receita_uniao'
#                    * 'ReceitaEstado'            -> tabela 'receita_estado'
#                    * 'ReceitaExtraOrcamentaria'  -> tabela 'receita_extra_orcamentaria'
#                    * 'DetalhesReceitaOrcamentaria' -> tabela 'receita_detalhes'
# ==============================================================================


def parse_num(val):
    if pd.isna(val):
        return "0.00"
    if isinstance(val, (int, float)):
        return f"{float(val):.2f}"
    val_str = str(val).replace(".", "").replace(",", ".").strip()
    try:
        return f"{float(val_str):.2f}"
    except ValueError:
        return "0.00"


def clean_col_name(c):
    """
    Normaliza os cabeçalhos das colunas removendo acentuação e caracteres especiais.
    """
    if not isinstance(c, str):
        return ""
    # Remove acentuação
    c_clean = "".join(ch for ch in unicodedata.normalize("NFKD", c) if not unicodedata.combining(ch))
    # Remove qualquer caracter não alfanumérico e converte para minúsculas
    c_clean = re.sub(r"[^a-zA-Z0-9]", "", c_clean).lower()
    return c_clean


def run_import():
    engine = db.get_engine()
    csv_dir = Path("data/csv/receitas")

    # Cria o diretório de destino se ele não existir
    if not csv_dir.exists():
        print(f"Diretório '{csv_dir}' não encontrado. Criando diretório...")
        csv_dir.mkdir(parents=True, exist_ok=True)
        print("Certifique-se de salvar os arquivos CSV de receitas nele com o formato:")
        print("  'data/csv/receitas/<orgao>_<ano>_<endpoint>.csv'")
        return

    csv_files = list(csv_dir.glob("*.csv"))

    if not csv_files:
        print(f"Nenhum arquivo CSV encontrado no diretório '{csv_dir}'.")
        print("Certifique-se de salvar seus arquivos no padrão:")
        print("  'data/csv/receitas/<orgao>_<ano>_<endpoint>.csv'")
        print("  (ex: '7_2024_ReceitaOrcamentaria.csv')")
        return

    TABLE_MAPPING = {
        "ReceitaOrcamentaria": "receita_orcamentaria",
        "ReceitaUniao": "receita_uniao",
        "ReceitaEstado": "receita_estado",
        "ReceitaExtraOrcamentaria": "receita_extra_orcamentaria",
        "DetalhesReceitaOrcamentaria": "receita_detalhes",
        "ReceitaDetalhes": "receita_detalhes",
        "ReceitaDetalhe": "receita_detalhes",
    }

    for file_path in csv_files:
        filename = file_path.name
        # Nome esperado: <orgao>_<ano>_<endpoint>.csv
        parts = filename.replace(".csv", "").split("_")
        if len(parts) < 3:
            print(f"\nIgnorando arquivo '{filename}' pois não segue o padrão '<orgao>_<ano>_<endpoint>.csv'")
            continue

        empresa_id = parts[0]
        try:
            year = int(parts[1])
        except ValueError:
            print(f"\nIgnorando arquivo '{filename}': ano '{parts[1]}' inválido.")
            continue

        endpoint_raw = parts[2]
        table_name = TABLE_MAPPING.get(endpoint_raw)

        # Fallback case-insensitive
        if not table_name:
            table_name = next((v for k, v in TABLE_MAPPING.items() if k.lower() == endpoint_raw.lower()), None)

        if not table_name:
            print(f"\nIgnorando arquivo '{filename}': endpoint desconhecido '{endpoint_raw}'.")
            continue

        # Tenta ler o arquivo CSV
        try:
            # Sep=None com engine=python detecta delimitadores automaticamente (como , ou ;)
            df = pd.read_csv(file_path, sep=None, engine="python", encoding="utf-8")
        except Exception as read_exc:
            print(f"\nErro ao ler arquivo '{filename}': {read_exc}")
            continue

        if df.empty:
            print(f"\nArquivo '{filename}' está vazio.")
            continue

        # Mapeia as colunas originais para nomes normalizados e limpos
        original_cols = df.columns.tolist()
        cleaned_to_orig = {clean_col_name(c): c for c in original_cols if clean_col_name(c)}

        # Identifica a coluna de Código (ou Extra se for extra-orçamentária)
        codigo_csv_col = None
        if "codigo" in cleaned_to_orig:
            codigo_csv_col = cleaned_to_orig["codigo"]
        elif "extra" in cleaned_to_orig:
            codigo_csv_col = cleaned_to_orig["extra"]

        if not codigo_csv_col:
            print(f"\nErro no arquivo '{filename}': Coluna de código/extra não identificada.")
            print(f"  Colunas encontradas: {original_cols}")
            continue

        df = df.dropna(subset=[codigo_csv_col])
        df["codigo"] = df[codigo_csv_col].astype(str).str.strip()
        df = df[df["codigo"] != "nan"]

        # Identifica a coluna de Descrição / Especificação
        desc_csv_col = next(
            (cleaned_to_orig[k] for k in ["especificacao", "descricao", "nome", "nomereceita"] if k in cleaned_to_orig),
            None,
        )
        df["descricao"] = df[desc_csv_col].fillna("").astype(str).str.strip() if desc_csv_col else ""

        # Mapeamento de colunas financeiras
        val_mappings = {
            "previsao_inicial": ["previnicial", "previsaoinicial"],
            "previsao_atualizada": ["prevatualizada", "previsaoatualizada"],
            "arrecadado_periodo": ["arrecperiodo", "arrecadadoperiodo"],
            "arrecadado_total": ["arrectotal", "arrecadadototal", "valor"],
        }

        for db_col, clean_keys in val_mappings.items():
            csv_col = next((cleaned_to_orig[k] for k in clean_keys if k in cleaned_to_orig), None)
            if csv_col:
                df[db_col] = df[csv_col].apply(parse_num)
            else:
                df[db_col] = "0.00"

        # Atributos específicos exigidos para extra-orçamentárias
        if table_name == "receita_extra_orcamentaria":
            # Campo 'extra'
            extra_col = cleaned_to_orig.get("extra")
            df["extra"] = df[extra_col].astype(str).str.strip() if extra_col else df["codigo"]

            # Campo 'dtlan' (Data de lançamento)
            data_col = cleaned_to_orig.get("data")
            df["dtlan"] = df[data_col].astype(str).str.strip() if data_col else ""

        # Configura as chaves extras exigidas pelos modelos
        df["previsto"] = df["previsao_atualizada"]
        df["arrecadado"] = df["arrecadado_total"]
        df["ano"] = year
        df["empresa"] = empresa_id

        rows = df.to_dict("records")

        # Exclui registros antigos para evitar duplicidade ou conflitos
        with engine.connect() as conn:
            conn.execute(
                text(f"DELETE FROM {table_name} WHERE ano = :ano AND empresa = :empresa"),
                {"ano": year, "empresa": empresa_id},
            )
            conn.commit()

            if rows:
                count = db.upsert(conn, table_name, rows, ["ano", "empresa", "codigo"])
                conn.commit()
                print(f"✓ {filename} -> Importados {count} registros com sucesso na tabela '{table_name}'!")
            else:
                print(f"⚠ {filename} -> Nenhum registro válido encontrado para importação.")

    print("\n🎉 Processamento e importação de todos os CSVs concluídos!")


if __name__ == "__main__":
    run_import()
