"""Account status and one-president-per-club invariants; preserve existing records."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    checks = [
        "SELECT id FROM users WHERE NOT ((role='clubAdmin' AND club_id IS NOT NULL) "
        "OR (role IN ('student','admin') AND club_id IS NULL)) LIMIT 1",
        "SELECT club_id FROM users WHERE club_id IS NOT NULL GROUP BY club_id "
        "HAVING COUNT(*) > 1 LIMIT 1",
        "SELECT u.id FROM users u LEFT JOIN members m ON m.user_id=u.id "
        "AND m.club_id=u.club_id AND m.role='owner' WHERE u.role='clubAdmin' "
        "GROUP BY u.id HAVING COUNT(m.id) <> 1 LIMIT 1",
        "SELECT m.id FROM members m JOIN users u ON u.id=m.user_id "
        "WHERE m.role='owner' AND (u.role<>'clubAdmin' OR u.club_id IS NULL "
        "OR u.club_id<>m.club_id) LIMIT 1",
    ]
    connection = op.get_bind()
    for query in checks:
        if connection.execute(sa.text(query)).first():
            raise RuntimeError("社长与成员数据不一致，迁移已停止；请维护者检查，不自动重置数据")
    # MySQL DDL commits independently. Resume this revision after partial DDL,
    # and preserve the FK-supporting index retained by a previous downgrade.
    inspector = sa.inspect(connection)
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    if "is_active" not in columns:
        op.add_column(
            "users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1")
        )
    elif columns["is_active"]["nullable"]:
        raise RuntimeError("已有 is_active 列结构不符，请维护者检查")
    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_club_id" not in indexes:
        op.create_index("ix_users_club_id", "users", ["club_id"])
    if "uq_users_managed_club" not in indexes:
        op.create_unique_constraint("uq_users_managed_club", "users", ["club_id"])
    if "ck_users_role_club" not in {
        item["name"] for item in inspector.get_check_constraints("users")
    }:
        op.create_check_constraint(
            "ck_users_role_club",
            "users",
            "(role = 'clubAdmin' AND club_id IS NOT NULL) OR "
            "(role IN ('student','admin') AND club_id IS NULL)",
        )


def downgrade():
    op.drop_constraint("ck_users_role_club", "users", type_="check")
    op.drop_constraint("uq_users_managed_club", "users", type_="unique")
    # Retain the nonunique index needed by the existing club foreign key.
    op.drop_column("users", "is_active")
