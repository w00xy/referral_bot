"""Unique channel

Revision ID: 3ef49ac9a69d
Revises: 043b0f1fcd53
Create Date: 2024-11-13 22:33:20.625076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ef49ac9a69d'
down_revision: Union[str, None] = '043b0f1fcd53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'channels', ['channel_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'channels', type_='unique')
    # ### end Alembic commands ###
