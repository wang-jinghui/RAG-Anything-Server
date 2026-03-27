"""create kb_user_access table

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create kb_user_access table
    op.create_table('kb_user_access',
        sa.Column('kb_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('access_level', sa.String(50), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('granted_by', UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['kb_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('kb_id', 'user_id')
    )
    
    # Create indexes
    op.create_index('ix_kb_user_access_user', 'kb_user_access', ['user_id'])
    op.create_index('ix_kb_user_access_kb', 'kb_user_access', ['kb_id'])


def downgrade() -> None:
    op.drop_index('ix_kb_user_access_kb', table_name='kb_user_access')
    op.drop_index('ix_kb_user_access_user', table_name='kb_user_access')
    op.drop_table('kb_user_access')
