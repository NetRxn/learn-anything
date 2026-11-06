# app/models/graph_edges.py
import uuid
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, VersionedMixin


class GraphEdge(Base, VersionedMixin):
    __tablename__ = "graph_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_node_id: Mapped[str] = mapped_column(String(36), index=True)
    from_node_type: Mapped[str] = mapped_column(String(20))  # concept, skill_node
    to_node_id: Mapped[str] = mapped_column(String(36), index=True)
    to_node_type: Mapped[str] = mapped_column(String(20))
    edge_type: Mapped[str] = mapped_column(String(30), index=True)
    # PREREQUISITE, EMBODIES, SIMILAR_TO, GENERALIZES, REINFORCES, NEGATIVE_TRANSFER
    strength: Mapped[float] = mapped_column(Float, default=1.0)
    prerequisite_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # hard, soft
    cosine_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    transfer_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
