"""expand events status column

Revision ID: b2c4e8f1a903
Revises: 91faa9cf42a0
Create Date: 2026-06-06 15:10:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c4e8f1a903"
down_revision: Union[str, Sequence[str], None] = "91faa9cf42a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE events ALTER COLUMN status TYPE VARCHAR(32)")


def downgrade() -> None:
    op.execute("ALTER TABLE events ALTER COLUMN status TYPE VARCHAR(9)")
