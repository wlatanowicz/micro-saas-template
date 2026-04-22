"""users.id to UUID (when an older revision created it as integer)

Revision ID: g5b2c9e3a1d2
Revises: f4a1c8e2b0d1
Create Date: 2026-04-22 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "g5b2c9e3a1d2"
down_revision: str | Sequence[str] | None = "f4a1c8e2b0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return
    row = conn.execute(
        sa.text(
            "SELECT data_type, udt_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'id'",
        )
    ).one_or_none()
    if row is None:
        return
    data_type, udt_name = row[0], row[1]
    if udt_name == "uuid" or data_type == "uuid":
        return
    if data_type not in ("integer", "smallint", "bigint"):
        msg = f"expected users.id to be integer types or uuid, got data_type={data_type!r} udt_name={udt_name!r}"
        raise NotImplementedError(msg)
    # PostgreSQL: replace integer PK with a new uuid column
    op.add_column("users", sa.Column("id_new", UUID(as_uuid=True), nullable=True))
    op.execute(sa.text("UPDATE users SET id_new = gen_random_uuid()"))
    op.drop_constraint("users_pkey", "users", type_="primary")
    op.execute(sa.text("ALTER TABLE users DROP COLUMN id"))
    op.execute(sa.text("ALTER TABLE users RENAME COLUMN id_new TO id"))
    op.create_primary_key("users_pkey", "users", ["id"])


def downgrade() -> None:
    # Lossy: cannot map uuid back to original integers. No-op to avoid data loss.
    return
