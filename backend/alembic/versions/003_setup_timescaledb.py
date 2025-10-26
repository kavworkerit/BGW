"""Setup TimescaleDB hypertable for price history

Revision ID: 003
Revises: 002
Create Date: 2024-10-26 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create TimescaleDB extension
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE')

    # Convert price_history to hypertable
    op.execute('SELECT create_hypertable(\'price_history\', \'observed_at\', if_not_exists => TRUE)')

    # Create indexes for better performance
    op.execute('CREATE INDEX IF NOT EXISTS idx_price_history_game_observed ON price_history (game_id, observed_at DESC)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_price_history_store_observed ON price_history (store_id, observed_at DESC)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_price_history_price ON price_history (price)')

    # Create retention policy (2 years)
    op.execute('''
        SELECT add_retention_policy('price_history', INTERVAL '2 years', if_not_exists => TRUE)
    ''')


def downgrade() -> None:
    # Remove retention policy
    op.execute('SELECT remove_retention_policy(\'price_history\', if_exists => TRUE)')

    # Remove indexes
    op.execute('DROP INDEX IF EXISTS idx_price_history_game_observed')
    op.execute('DROP INDEX IF EXISTS idx_price_history_store_observed')
    op.execute('DROP INDEX IF EXISTS idx_price_history_price')

    # Convert back to regular table (TimescaleDB doesn't support dropping hypertable)
    # Note: This is a simplified approach - in production you might need different strategy
    op.execute('DROP TABLE IF EXISTS price_history')