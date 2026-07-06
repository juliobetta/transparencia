"""update pk despesas por exigibilidade

Revision ID: 123456789abc
Revises: 6a2e943b674e
Create Date: 2026-07-06 15:10:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "123456789abc"
down_revision: Union[str, Sequence[str], None] = "6a2e943b674e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("despesas_por_exigibilidade_pkey", "despesas_por_exigibilidade", type_="primary")
    op.create_primary_key(
        "despesas_por_exigibilidade_pkey",
        "despesas_por_exigibilidade",
        ["ano", "empresa", "tipo", "empenho"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("despesas_por_exigibilidade_pkey", "despesas_por_exigibilidade", type_="primary")
    op.create_primary_key(
        "despesas_por_exigibilidade_pkey",
        "despesas_por_exigibilidade",
        ["ano", "empresa", "tipo"],
    )
