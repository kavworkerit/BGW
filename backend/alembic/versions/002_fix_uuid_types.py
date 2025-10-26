"""Fix UUID types consistency

Revision ID: 002
Revises: 001
Create Date: 2024-10-26 17:38:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert game.id from String to UUID
    op.execute('ALTER TABLE game ALTER COLUMN id TYPE UUID USING id::uuid')

    # Convert listing_event.game_id from String to UUID
    op.execute('ALTER TABLE listing_event ALTER COLUMN game_id TYPE UUID USING game_id::uuid')

    # Convert price_history.game_id from String to UUID
    op.execute('ALTER TABLE price_history ALTER COLUMN game_id TYPE UUID USING game_id::uuid')

    # Convert notification related tables if they exist
    try:
        op.execute('ALTER TABLE notification ALTER COLUMN rule_id TYPE UUID USING rule_id::uuid')
        op.execute('ALTER TABLE notification ALTER COLUMN event_id TYPE UUID USING event_id::uuid')
    except Exception:
        pass  # Tables might not exist yet

    try:
        op.execute('ALTER TABLE alert_rule ALTER COLUMN id TYPE UUID USING id::uuid')
    except Exception:
        pass  # Table might not exist yet


def downgrade() -> None:
    # Convert back from UUID to String
    op.execute('ALTER TABLE game ALTER COLUMN id TYPE VARCHAR(36) USING id::text')
    op.execute('ALTER TABLE listing_event ALTER COLUMN game_id TYPE VARCHAR(36) USING game_id::text')
    op.execute('ALTER TABLE price_history ALTER COLUMN game_id TYPE VARCHAR(36) USING game_id::text')

    try:
        op.execute('ALTER TABLE notification ALTER COLUMN rule_id TYPE VARCHAR(36) USING rule_id::text')
        op.execute('ALTER TABLE notification ALTER COLUMN event_id TYPE VARCHAR(36) USING event_id::text')
    except Exception:
        pass

    try:
        op.execute('ALTER TABLE alert_rule ALTER COLUMN id TYPE VARCHAR(36) USING id::text')
    except Exception:
        pass