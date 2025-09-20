"""Fix product schema and remove JSON format attributes

Revision ID: fix_product_schema
Revises: add_product_attributes_columns
Create Date: 2025-09-20 13:06:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_product_schema'
down_revision = 'add_product_attributes_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, let's create a new table with the correct schema
    op.create_table('products_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('size_range', sa.JSON(), nullable=True, default=[]),
        sa.Column('image_key', sa.String(length=255), nullable=False),
        sa.Column('attributes', sa.JSON(), nullable=True, default={}),  # Keep for backward compatibility
        sa.Column('in_stock', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        # All individual attribute columns
        sa.Column('season', sa.String(length=50), nullable=True),
        sa.Column('url_key', sa.String(length=255), nullable=True, unique=True),
        sa.Column('product_created_at', sa.DateTime(), nullable=True),
        sa.Column('stock_qty', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=100), nullable=True),
        sa.Column('material', sa.String(length=100), nullable=True),
        sa.Column('pattern', sa.String(length=100), nullable=True),
        sa.Column('occasion', sa.String(length=100), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku')
    )

    # Add indexes for performance
    op.create_index('idx_products_new_price', 'products_new', ['price'])
    op.create_index('idx_products_new_in_stock', 'products_new', ['in_stock'])
    op.create_index('idx_products_new_created_at', 'products_new', ['created_at'])
    op.create_index('idx_products_new_url_key', 'products_new', ['url_key'])
    op.create_index('idx_products_new_category', 'products_new', ['category'])
    op.create_index('idx_products_new_color', 'products_new', ['color'])
    op.create_index('idx_products_new_material', 'products_new', ['material'])
    op.create_index('idx_products_new_season', 'products_new', ['season'])
    op.create_index('idx_products_new_occasion', 'products_new', ['occasion'])

    # Migrate data from old table to new table
    op.execute("""
        INSERT INTO products_new (
            id, sku, title, price, size_range, image_key, attributes, in_stock,
            created_at, updated_at, season, url_key, product_created_at, stock_qty,
            category, color, material, pattern, occasion
        )
        SELECT
            id, sku, title, price,
            CASE
                WHEN typeof(size_range) = 'text' THEN json(size_range)
                ELSE size_range
            END,
            image_key,
            CASE
                WHEN typeof(attributes) = 'text' THEN json(attributes)
                ELSE attributes
            END,
            in_stock, created_at, updated_at, season, url_key, product_created_at,
            stock_qty, category, color, material, pattern, occasion
        FROM products
    """)

    # Drop old table and rename new table
    op.drop_table('products')
    op.rename_table('products_new', 'products')

    # Recreate indexes
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_sku', 'products', ['sku'])
    op.create_index('idx_products_price', 'products', ['price'])
    op.create_index('idx_products_in_stock', 'products', ['in_stock'])
    op.create_index('idx_products_created_at', 'products', ['created_at'])
    op.create_index('ix_products_url_key', 'products', ['url_key'])
    op.create_index('uq_products_url_key', 'products', ['url_key'], unique=True)
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_color', 'products', ['color'])
    op.create_index('idx_products_material', 'products', ['material'])
    op.create_index('idx_products_season', 'products', ['season'])
    op.create_index('idx_products_occasion', 'products', ['occasion'])


def downgrade() -> None:
    # This is a complex downgrade, so we'll just recreate the old structure
    op.create_table('products_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('size_range', sa.Text(), nullable=True),
        sa.Column('image_key', sa.String(length=255), nullable=False),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('in_stock', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('season', sa.String(length=50), nullable=True),
        sa.Column('url_key', sa.String(length=255), nullable=True),
        sa.Column('product_created_at', sa.DateTime(), nullable=True),
        sa.Column('stock_qty', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=100), nullable=True),
        sa.Column('material', sa.String(length=100), nullable=True),
        sa.Column('pattern', sa.String(length=100), nullable=True),
        sa.Column('occasion', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Migrate back
    op.execute("""
        INSERT INTO products_old (
            id, sku, title, price, size_range, image_key, attributes, in_stock,
            created_at, updated_at, season, url_key, product_created_at, stock_qty,
            category, color, material, pattern, occasion
        )
        SELECT
            id, sku, title, price,
            CASE
                WHEN typeof(size_range) = 'json' THEN json_extract(size_range, '$')
                ELSE size_range
            END,
            image_key,
            CASE
                WHEN typeof(attributes) = 'json' THEN json_extract(attributes, '$')
                ELSE attributes
            END,
            CASE WHEN in_stock = 1 THEN 1 ELSE 0 END,
            created_at, updated_at, season, url_key, product_created_at,
            stock_qty, category, color, material, pattern, occasion
        FROM products
    """)

    op.drop_table('products')
    op.rename_table('products_old', 'products')

    # Recreate old indexes
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_sku', 'products', ['sku'])
    op.create_index('ix_products_attributes_category', 'products', ['attributes'])
    op.create_index('ix_products_attributes_color', 'products', ['attributes'])
    op.create_index('ix_products_created_at', 'products', ['created_at'])
    op.create_index('ix_products_in_stock', 'products', ['in_stock'])
    op.create_index('ix_products_price', 'products', ['price'])
    op.create_index('ix_products_url_key', 'products', ['url_key'])
    op.create_unique_index('uq_products_url_key', 'products', ['url_key'])