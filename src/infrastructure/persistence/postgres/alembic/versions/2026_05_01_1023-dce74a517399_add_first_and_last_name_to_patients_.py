"""add first and last name to patients table

Revision ID: dce74a517399
Revises: 0ce7fd5161ee
Create Date: 2026-05-01 10:23:41.794600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dce74a517399'
down_revision: Union[str, None] = '0ce7fd5161ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns as nullable first (existing rows have no value)
    op.add_column('patients', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('patients', sa.Column('last_name', sa.String(length=100), nullable=True))

    # 2. Backfill first_name from full_name (split on first space)
    op.execute(
        "UPDATE patients "
        "SET first_name = TRIM(SPLIT_PART(full_name, ' ', 1)), "
        "    last_name  = TRIM(SUBSTRING(full_name FROM POSITION(' ' IN full_name))) "
        "WHERE full_name IS NOT NULL"
    )
    # If there's no space, last_name stays NULL — that's fine.

    # 3. Now make first_name NOT NULL
    op.alter_column('patients', 'first_name', nullable=False)

    # 4. Drop the old column
    op.drop_column('patients', 'full_name')


def downgrade() -> None:
    # 1. Re-add full_name
    op.add_column('patients', sa.Column('full_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True))

    # 2. Reconstitute full_name from first / last
    op.execute(
        "UPDATE patients "
        "SET full_name = TRIM(CONCAT_WS(' ', first_name, last_name)) "
        "WHERE first_name IS NOT NULL"
    )

    # 3. Make full_name NOT NULL
    op.alter_column('patients', 'full_name', nullable=False)

    # 4. Drop new columns
    op.drop_column('patients', 'last_name')
    op.drop_column('patients', 'first_name')
