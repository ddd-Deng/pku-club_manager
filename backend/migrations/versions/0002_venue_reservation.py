"""Venue and venue reservation tables."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "venues",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("time_slots", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_table(
        "venue_reservations",
        sa.Column("venue_id", sa.String(length=36), nullable=False),
        sa.Column("club_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("reserve_date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.String(length=20), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('pending','approved','rejected')"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index(
        op.f("ix_venue_reservations_venue_id"), "venue_reservations", ["venue_id"], unique=False
    )
    op.create_index(
        op.f("ix_venue_reservations_club_id"), "venue_reservations", ["club_id"], unique=False
    )
    op.create_index(
        op.f("ix_venue_reservations_user_id"), "venue_reservations", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_venue_reservations_status"), "venue_reservations", ["status"], unique=False
    )
    op.create_index(
        "ix_reservation_venue_date_slot",
        "venue_reservations",
        ["venue_id", "reserve_date", "time_slot"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_reservation_venue_date_slot", table_name="venue_reservations")
    op.drop_index(op.f("ix_venue_reservations_status"), table_name="venue_reservations")
    op.drop_index(op.f("ix_venue_reservations_user_id"), table_name="venue_reservations")
    op.drop_index(op.f("ix_venue_reservations_club_id"), table_name="venue_reservations")
    op.drop_index(op.f("ix_venue_reservations_venue_id"), table_name="venue_reservations")
    op.drop_table("venue_reservations")
    op.drop_table("venues")
