"""Rename items table to products

Revision ID: a621a1d03594
Revises: 9fe176c77da3
Create Date: 2025-09-20 10:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a621a1d03594'
down_revision = '9fe176c77da3'
branch_labels = None
depends_on = None


def upgrade():
    """Rename items table to products"""
    # Rename the table
    op.rename_table('items', 'products')

    # Update foreign key references in outfit_items table
    op.execute('''
        UPDATE outfit_items
        SET item_id = (
            SELECT id FROM products WHERE products.id = outfit_items.item_id
        )
    ''')

    # Recreate indexes with new table name
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)
    op.create_index('idx_products_attributes_category', 'products', ['attributes'], unique=False)
    op.create_index('idx_products_attributes_color', 'products', ['attributes'], unique=False)
    op.create_index('idx_products_created_at', 'products', ['created_at'], unique=False)
    op.create_index('idx_products_in_stock', 'products', ['in_stock'], unique=False)
    op.create_index('idx_products_price', 'products', ['price'], unique=False)


def downgrade():
    """Rename products table back to items"""
    # Drop the new indexes
    op.drop_index('ix_products_id')
    op.drop_index('ix_products_sku')
    op.drop_index('idx_products_attributes_category')
    op.drop_index('idx_products_attributes_color')
    op.drop_index('idx_products_created_at')
    op.drop_index('idx_products_in_stock')
    op.drop_index('idx_products_price')

    # Rename the table back
    op.rename_table('products', 'items')

    # Update foreign key references back
    op.execute('''
        UPDATE outfit_items
        SET item_id = (
            SELECT id FROM items WHERE items.id = outfit_items.item_id
        )
    ''')