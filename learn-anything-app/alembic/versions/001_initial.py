"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(20), nullable=False, server_default="local"),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- app_config ---
    op.create_table(
        "app_config",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False, server_default=""),
        sa.Column("encrypted", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    # --- domains ---
    op.create_table(
        "domains",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("skill_type", sa.String(50), nullable=False),
        sa.Column("environment_type", sa.String(50), nullable=False),
    )

    # --- concepts ---
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("abstraction_level", sa.String(20), nullable=False),
        sa.Column("bloom_level", sa.String(20), nullable=False),
        sa.Column("field_freshness", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- skill_nodes ---
    op.create_table(
        "skill_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("domain_id", sa.String(36), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("component_type", sa.String(20), nullable=False),
        sa.Column("bloom_level", sa.String(20), nullable=False),
        sa.Column("frequency_score", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("impact_score", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("field_freshness", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- graph_edges ---
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("from_node_id", sa.String(36), index=True, nullable=False),
        sa.Column("from_node_type", sa.String(20), nullable=False),
        sa.Column("to_node_id", sa.String(36), index=True, nullable=False),
        sa.Column("to_node_type", sa.String(20), nullable=False),
        sa.Column("edge_type", sa.String(30), index=True, nullable=False),
        sa.Column("strength", sa.Float, nullable=False, server_default=sa.text("1.0")),
        sa.Column("prerequisite_type", sa.String(10), nullable=True),
        sa.Column("cosine_similarity", sa.Float, nullable=True),
        sa.Column("transfer_type", sa.String(20), nullable=True),
        sa.Column("risk", sa.Text, nullable=True),
        sa.Column("mitigation", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- learner_states ---
    op.create_table(
        "learner_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), index=True, nullable=False),
        sa.Column("node_id", sa.String(36), index=True, nullable=False),
        sa.Column("node_type", sa.String(20), nullable=False),
        sa.Column("mastery_probability", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("mastery_category", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("confidence", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("evidence_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("evidence_summary", sa.Text, nullable=False, server_default=""),
        sa.Column("last_assessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fsrs_difficulty", sa.Float, nullable=False, server_default=sa.text("5.0")),
        sa.Column("fsrs_stability", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("bkt_p_transit", sa.Float, nullable=False, server_default=sa.text("0.15")),
        sa.Column("bkt_p_slip", sa.Float, nullable=False, server_default=sa.text("0.08")),
        sa.Column("bkt_p_guess", sa.Float, nullable=False, server_default=sa.text("0.12")),
        sa.Column("transfer_boost", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("source", sa.String(30), nullable=False, server_default="calibration"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "node_id", name="uq_user_node"),
    )

    # --- mastery_transitions ---
    op.create_table(
        "mastery_transitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), index=True, nullable=False),
        sa.Column("node_id", sa.String(36), index=True, nullable=False),
        sa.Column("from_state", sa.String(20), nullable=False),
        sa.Column("to_state", sa.String(20), nullable=False),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text, nullable=False, server_default=""),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- references ---
    op.create_table(
        "references",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("date_published", sa.String(20), nullable=True),
        sa.Column("date_accessed", sa.String(20), nullable=True),
        sa.Column("credibility", sa.String(20), nullable=False, server_default="community"),
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # --- materials ---
    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("url_or_path", sa.String(2000), nullable=True),
        sa.Column("bloom_level", sa.String(20), nullable=True),
        sa.Column("effectiveness_score", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("updated_by", sa.String(255), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- material_teaches ---
    op.create_table(
        "material_teaches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id"), index=True, nullable=False),
        sa.Column("node_id", sa.String(36), index=True, nullable=False),
        sa.Column("node_type", sa.String(20), nullable=False),
        sa.Column("depth", sa.String(20), nullable=False, server_default="introduction"),
        sa.Column("modality", sa.String(20), nullable=False, server_default="reading"),
    )

    # --- sourced_from ---
    op.create_table(
        "sourced_from",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("node_id", sa.String(36), index=True, nullable=False),
        sa.Column("node_type", sa.String(20), nullable=False),
        sa.Column("reference_id", sa.String(36), sa.ForeignKey("references.id"), index=True, nullable=False),
        sa.Column("relevance", sa.Float, nullable=False, server_default=sa.text("1.0")),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("page_or_timestamp", sa.String(100), nullable=True),
    )

    # --- material_prerequisites ---
    op.create_table(
        "material_prerequisites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id"), index=True, nullable=False),
        sa.Column("prerequisite_material_id", sa.String(36), sa.ForeignKey("materials.id"), index=True, nullable=False),
    )

    # --- material_cites ---
    op.create_table(
        "material_cites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("material_id", sa.String(36), sa.ForeignKey("materials.id"), index=True, nullable=False),
        sa.Column("reference_id", sa.String(36), sa.ForeignKey("references.id"), index=True, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("material_cites")
    op.drop_table("material_prerequisites")
    op.drop_table("sourced_from")
    op.drop_table("material_teaches")
    op.drop_table("materials")
    op.drop_table("references")
    op.drop_table("mastery_transitions")
    op.drop_table("learner_states")
    op.drop_table("graph_edges")
    op.drop_table("skill_nodes")
    op.drop_table("concepts")
    op.drop_table("domains")
    op.drop_table("app_config")
    op.drop_table("users")
