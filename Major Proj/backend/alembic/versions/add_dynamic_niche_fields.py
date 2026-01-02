"""add new fields to dynamic_niches

Revision ID: add_dynamic_niche_fields
Revises: add_niche_id_to_users
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_dynamic_niche_fields'
down_revision = 'add_niche_id_to_users'
branch_labels = None
depends_on = None


def upgrade():
    """Add new fields to dynamic_niches table"""
    
    # Add name column (alias for label)
    op.add_column('dynamic_niches', 
        sa.Column('name', sa.String(), nullable=True)
    )
    
    # Add embedding_centroid column (new naming)
    op.add_column('dynamic_niches',
        sa.Column('embedding_centroid', sa.JSON(), nullable=True)
    )
    
    # Add descriptors column (alias for keywords)
    op.add_column('dynamic_niches',
        sa.Column('descriptors', sa.JSON(), nullable=True)
    )
    
    # Add is_micro column
    op.add_column('dynamic_niches',
        sa.Column('is_micro', sa.Integer(), server_default='0', nullable=False)
    )
    
    # Add member_count column (alias for creator_count)
    op.add_column('dynamic_niches',
        sa.Column('member_count', sa.Integer(), server_default='0', nullable=False)
    )
    
    # Copy data from old columns to new columns
    op.execute("""
        UPDATE dynamic_niches 
        SET name = label,
            embedding_centroid = centroid_vector,
            descriptors = keywords,
            member_count = creator_count
        WHERE name IS NULL
    """)


def downgrade():
    """Remove new fields from dynamic_niches table"""
    op.drop_column('dynamic_niches', 'member_count')
    op.drop_column('dynamic_niches', 'is_micro')
    op.drop_column('dynamic_niches', 'descriptors')
    op.drop_column('dynamic_niches', 'embedding_centroid')
    op.drop_column('dynamic_niches', 'name')
