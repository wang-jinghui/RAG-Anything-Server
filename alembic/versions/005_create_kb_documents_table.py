"""create kb_documents table

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 00:00:04.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum for upload status if not exists
    op.execute("CREATE TYPE IF NOT EXISTS upload_status AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # Create kb_documents table
    op.create_table('kb_documents',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_base_id', UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=True),
        sa.Column('lightrag_doc_id', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('upload_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('uploaded_by', UUID(as_uuid=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_kb_documents_kb', 'kb_documents', ['knowledge_base_id'])
    op.create_index('ix_kb_documents_lightrag', 'kb_documents', ['lightrag_doc_id'])


def downgrade() -> None:
    op.drop_index('ix_kb_documents_lightrag', table_name='kb_documents')
    op.drop_index('ix_kb_documents_kb', table_name='kb_documents')
    op.drop_table('kb_documents')
    op.execute("DROP TYPE IF EXISTS upload_status")
