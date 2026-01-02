"""add niche_id to users table

Revision ID: add_niche_id_to_users
Revises: cd81216830e7
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_niche_id_to_users'
down_revision = 'cd81216830e7'
branch_labels = None
depends_on = None


def upgrade():
    """Add niche_id column to users table and create foreign key"""
    # Add niche_id column
    op.add_column('users', 
        sa.Column('niche_id', sa.String(length=64), nullable=True)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_users_niche_id',
        'users', 'dynamic_niches',
        ['niche_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for faster lookups
    op.create_index(
        'ix_users_niche_id',
        'users',
        ['niche_id']
    )


def downgrade():
    """Remove niche_id column and foreign key"""
    # Drop index
    op.drop_index('ix_users_niche_id', table_name='users')
    
    # Drop foreign key
    op.drop_constraint('fk_users_niche_id', 'users', type_='foreignkey')
    
    # Drop column
    op.drop_column('users', 'niche_id')
