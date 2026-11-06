"""Persist revocable sessions and identity-scoped documents."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "002"
down_revision = "001"
branch_labels = depends_on = None


def upgrade():
    op.create_table("login_sessions", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_login_sessions_user_id", "login_sessions", ["user_id"])
    op.create_table("workspace_documents", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("skill_slug", sa.String(100), primary_key=True), sa.Column("document", sa.String(20), primary_key=True), sa.Column("revision", sa.Integer, nullable=False), sa.Column("data", postgresql.JSONB, nullable=False), sa.CheckConstraint("revision > 0", name="positive_document_revision"))


def downgrade():
    op.drop_table("workspace_documents")
    op.drop_table("login_sessions")
