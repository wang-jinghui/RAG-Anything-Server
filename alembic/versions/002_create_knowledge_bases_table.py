"""create knowledge_bases table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum for KB status if not exists
    op.execute("CREATE TYPE IF NOT EXISTS kb_status AS ENUM ('active', 'archived', 'deleted')")
    
    # Create knowledge_bases table
    op.create_table('knowledge_bases',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('lightrag_namespace_prefix', sa.String(100), nullable=False),
        sa.Column('vector_storage_config', JSONB(), nullable=False, server_default='{"type": "pgvector"}'),
        sa.Column('graph_storage_config', JSONB(), nullable=False, server_default='{"type": "neo4j"}'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('document_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.String(20), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'name', name='uq_owner_kb_name'),
        sa.UniqueConstraint('lightrag_namespace_prefix', name='uq_kb_namespace')
    )
    
    # Create indexes
    op.create_index('ix_kb_owner', 'knowledge_bases', ['owner_id'])
    op.create_index('ix_kb_namespace', 'knowledge_bases', ['lightrag_namespace_prefix'])


def downgrade() -> None:
    op.drop_index('ix_kb_namespace', table_name='knowledge_bases')
    op.drop_index('ix_kb_owner', table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
    op.execute("DROP TYPE IF EXISTS kb_status")
