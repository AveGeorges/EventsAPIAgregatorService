"""fix outbox enum values

Revision ID: f4a8c2d1e567
Revises: ceac11bd0752
Create Date: 2026-07-05 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a8c2d1e567"
down_revision: Union[str, Sequence[str], None] = "ceac11bd0752"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE outbox SET status = 'pending' WHERE status = 'PENDING'")
    op.execute("UPDATE outbox SET status = 'sent' WHERE status = 'SENT'")
    op.execute(
        "UPDATE outbox SET event_type = 'ticket_purchased' "
        "WHERE event_type = 'TICKET_PURCHASED'"
    )

    op.alter_column(
        "outbox",
        "status",
        existing_type=sa.Enum("PENDING", "SENT", name="outbox_event_status", native_enum=False),
        type_=sa.Enum("pending", "sent", name="outbox_event_status", native_enum=False),
        existing_nullable=False,
    )
    op.alter_column(
        "outbox",
        "event_type",
        existing_type=sa.Enum(
            "TICKET_PURCHASED", name="outbox_event_type", native_enum=False
        ),
        type_=sa.Enum("ticket_purchased", name="outbox_event_type", native_enum=False),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "outbox",
        "event_type",
        existing_type=sa.Enum("ticket_purchased", name="outbox_event_type", native_enum=False),
        type_=sa.Enum("TICKET_PURCHASED", name="outbox_event_type", native_enum=False),
        existing_nullable=False,
    )
    op.alter_column(
        "outbox",
        "status",
        existing_type=sa.Enum("pending", "sent", name="outbox_event_status", native_enum=False),
        type_=sa.Enum("PENDING", "SENT", name="outbox_event_status", native_enum=False),
        existing_nullable=False,
    )

    op.execute("UPDATE outbox SET event_type = 'TICKET_PURCHASED' WHERE event_type = 'ticket_purchased'")
    op.execute("UPDATE outbox SET status = 'PENDING' WHERE status = 'pending'")
    op.execute("UPDATE outbox SET status = 'SENT' WHERE status = 'sent'")
