"""
Database migration: Add creators table with vector support
Revision ID: add_creators_table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create creators table
    op.create_table(
        'creators',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('handle', sa.String()),
        sa.Column('bio', sa.Text()),
        sa.Column('subscriber_count', sa.Integer(), default=0),
        sa.Column('language', sa.String(), default='en'),
        sa.Column('niche', sa.String()),
        sa.Column('embedding', postgresql.ARRAY(sa.Float(), dimensions=1)),  # 384-dim vector
        sa.Column('content_samples', postgresql.JSONB()),
        sa.Column('tags', postgresql.JSONB()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_creators_platform', 'creators', ['platform'])
    op.create_index('idx_creators_niche', 'creators', ['niche'])
    op.create_index('idx_creators_subscriber_count', 'creators', ['subscriber_count'])
    
    # Note: Vector index will be created after data is loaded
    # op.execute('CREATE INDEX idx_creators_embedding ON creators USING ivfflat (embedding vector_cosine_ops)')


def downgrade():
    op.drop_index('idx_creators_subscriber_count')
    op.drop_index('idx_creators_niche')
    op.drop_index('idx_creators_platform')
    op.drop_table('creators')
    op.execute('DROP EXTENSION IF EXISTS vector')
