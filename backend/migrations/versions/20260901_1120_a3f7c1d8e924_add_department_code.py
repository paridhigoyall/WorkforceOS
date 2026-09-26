"""add_department_code

Revision ID: a3f7c1d8e924
Revises: e8c1b3f99012
Create Date: 2026-09-01 11:20:00.000000+00:00
"""
from __future__ import annotations

from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa


revision: str = 'a3f7c1d8e924'
down_revision: Union[str, Sequence[str], None] = 'e8c1b3f99012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        dept_cols = []
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        dept_cols = [c['name'] for c in inspector.get_columns('departments')]

    if 'code' not in dept_cols:
        # Add column as nullable first so existing rows don't violate NOT NULL
        op.add_column(
            'departments',
            sa.Column(
                'code',
                sa.String(length=10),
                nullable=True,
                comment='Short uppercase department code, e.g. ENG, HR, FIN'
            )
        )
        # Back-fill existing rows with a guaranteed-unique code derived from
        # the first 6 chars of name + last 4 hex chars of UUID primary key.
        op.execute(
            """
            UPDATE departments
            SET code = UPPER(LEFT(REGEXP_REPLACE(name, '[^A-Za-z0-9]', '', 'g'), 6))
                       || UPPER(SUBSTRING(CAST(id AS TEXT), 33, 4))
            WHERE code IS NULL
            """
        )
        # Enforce NOT NULL, then add unique index
        op.alter_column('departments', 'code', nullable=False)
        op.create_unique_constraint('uq_departments_code', 'departments', ['code'])
        op.create_index(op.f('ix_departments_code'), 'departments', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_departments_code'), table_name='departments')
    op.drop_constraint('uq_departments_code', 'departments', type_='unique')
    op.drop_column('departments', 'code')
