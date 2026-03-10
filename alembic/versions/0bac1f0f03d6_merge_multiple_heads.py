"""merge multiple heads

Revision ID: 0bac1f0f03d6
Revises: 2de220d479fd, 75caedb511e7
Create Date: 2026-03-10 06:48:21.878029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bac1f0f03d6'
down_revision: Union[str, None] = ('2de220d479fd', '75caedb511e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
