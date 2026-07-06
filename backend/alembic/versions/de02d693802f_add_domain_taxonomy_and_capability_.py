"""add domain taxonomy and capability domain_id

Revision ID: de02d693802f
Revises: 0ba39f226686
Create Date: 2026-07-06 18:05:19.447675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'de02d693802f'
down_revision: Union[str, None] = '0ba39f226686'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'domain',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_domain_name'), 'domain', ['name'], unique=True)

    # Add domain_id as nullable first so existing rows can be backfilled from
    # the legacy free-text `domain` column before the NOT NULL constraint and
    # the column drop.
    op.add_column('capability', sa.Column('domain_id', sa.Integer(), nullable=True))

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO domain (name, created_at, updated_at)
            SELECT DISTINCT domain, now(), now()
            FROM capability
            WHERE domain IS NOT NULL
            """
        )
    )
    connection.execute(
        sa.text(
            """
            UPDATE capability
            SET domain_id = domain.id
            FROM domain
            WHERE capability.domain = domain.name
            """
        )
    )

    op.alter_column('capability', 'domain_id', nullable=False)
    op.create_index(op.f('ix_capability_domain_id'), 'capability', ['domain_id'], unique=False)
    op.create_foreign_key(None, 'capability', 'domain', ['domain_id'], ['id'])
    op.drop_column('capability', 'domain')


def downgrade() -> None:
    op.add_column('capability', sa.Column('domain', sa.VARCHAR(length=255), autoincrement=False, nullable=True))

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE capability
            SET domain = domain_table.name
            FROM domain AS domain_table
            WHERE capability.domain_id = domain_table.id
            """
        )
    )

    op.drop_constraint(None, 'capability', type_='foreignkey')
    op.drop_index(op.f('ix_capability_domain_id'), table_name='capability')
    op.drop_column('capability', 'domain_id')
    op.drop_index(op.f('ix_domain_name'), table_name='domain')
    op.drop_table('domain')
