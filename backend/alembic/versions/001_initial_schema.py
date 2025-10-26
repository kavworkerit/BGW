"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum for event_kind
    op.execute("CREATE TYPE event_kind AS ENUM ('announce', 'preorder', 'release', 'discount', 'price')")

    # Create game table
    op.create_table('game',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('synonyms', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('bgg_id', sa.String(length=50), nullable=True),
        sa.Column('publisher', sa.String(length=200), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_title'), 'game', ['title'], unique=False)

    # Create store table
    op.create_table('store',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('site_url', sa.String(length=500), nullable=True),
        sa.Column('region', sa.String(length=10), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create source_agent table
    op.create_table('source_agent',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('schedule', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rate_limit', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create raw_item table
    op.create_table('raw_item',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('content_ref', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['source_agent.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hash')
    )
    op.create_index('ix_raw_item_source_id_fetched_at', 'raw_item', ['source_id', 'fetched_at'], unique=False)

    # Create listing_event table
    op.create_table('listing_event',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('game_id', sa.String(length=36), nullable=True),
        sa.Column('store_id', sa.String(length=100), nullable=True),
        sa.Column('kind', sa.Enum('announce', 'preorder', 'release', 'discount', 'price', name='event_kind'), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('edition', sa.String(length=200), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('in_stock', sa.Boolean(), nullable=True),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('signature_hash', sa.String(length=64), nullable=False),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['source_agent.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('signature_hash')
    )
    op.create_index('ix_listing_event_game_id_created_at', 'listing_event', ['game_id', 'created_at'], unique=False)
    op.create_index('ix_listing_event_kind', 'listing_event', ['kind'], unique=False)

    # Create price_history table
    op.create_table('price_history',
        sa.Column('game_id', sa.String(length=36), nullable=False),
        sa.Column('store_id', sa.String(length=100), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
        sa.PrimaryKeyConstraint('game_id', 'store_id', 'observed_at')
    )

    # Create alert_rule table
    op.create_table('alert_rule',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('logic', sa.String(length=10), nullable=False),
        sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('channels', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('cooldown_hours', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create notification table
    op.create_table('notification',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rule_id', sa.String(length=36), nullable=True),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['listing_event.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['alert_rule.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем hypertable для price_history
    op.execute("SELECT create_hypertable('price_history', 'observed_at');")


def downgrade() -> None:
    op.drop_table('notification')
    op.drop_table('alert_rule')
    op.execute("DROP TABLE IF EXISTS price_history;")
    op.drop_index('ix_listing_event_kind', table_name='listing_event')
    op.drop_index('ix_listing_event_game_id_created_at', table_name='listing_event')
    op.drop_table('listing_event')
    op.drop_index('ix_raw_item_source_id_fetched_at', table_name='raw_item')
    op.drop_table('raw_item')
    op.drop_table('source_agent')
    op.drop_table('store')
    op.drop_index(op.f('ix_game_title'), table_name='game')
    op.drop_table('game')
    op.execute("DROP TYPE IF EXISTS event_kind;")