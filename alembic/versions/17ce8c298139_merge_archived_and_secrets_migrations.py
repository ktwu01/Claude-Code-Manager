"""merge archived and secrets migrations

Revision ID: 17ce8c298139
Revises: 492f4274adbb, 72bb07679317
Create Date: 2026-03-18 04:16:53.444234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17ce8c298139'
down_revision: Union[str, None] = ('492f4274adbb', '72bb07679317')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
