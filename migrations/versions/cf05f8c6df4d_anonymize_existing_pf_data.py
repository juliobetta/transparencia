"""anonymize_existing_pf_data

Revision ID: cf05f8c6df4d
Revises: 5329f4288940
Create Date: 2026-07-04 18:06:54.584368

"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cf05f8c6df4d"
down_revision: Union[str, Sequence[str], None] = "5329f4288940"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Importando a lógica do utilitário
def mask_cpf_logic(cpf: str) -> str:
    clean = re.sub(r"\D", "", cpf)
    if len(clean) != 11:
        return cpf
    return f"***.{clean[3:6]}.{clean[6:9]}-**"


def mask_name_logic(nome: str) -> str:
    parts = nome.split()
    initials = "".join([p[0] for p in parts if p])
    return initials


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # 1. Mascarar `despesas_por_fornecedor`
    # Usando ano, empresa, codigo como chave primária composta
    result = conn.execute(sa.text("SELECT ano, empresa, codigo, insmf, descricao FROM despesas_por_fornecedor"))
    for row in result:
        ano, empresa, codigo, insmf, descricao = row
        if insmf and len(re.sub(r"\D", "", insmf)) == 11:
            conn.execute(
                sa.text(
                    "UPDATE despesas_por_fornecedor SET insmf = :new_insmf, descricao = :new_desc WHERE ano = :ano AND empresa = :empresa AND codigo = :codigo"
                ),
                {
                    "new_insmf": mask_cpf_logic(insmf),
                    "new_desc": mask_name_logic(descricao) if descricao else "",
                    "ano": ano,
                    "empresa": empresa,
                    "codigo": codigo,
                },
            )

    # 2. Adicionar lógica similar para outras tabelas que tenham PII (DespesasGerais, etc.) se necessário
    # ...


def downgrade() -> None:
    """Downgrade schema."""
    # A anonimização é destrutiva (não reversível sem backup).
    # O downgrade apenas deixa a estrutura do banco como está.
    pass
