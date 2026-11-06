# app/models/graph_nodes.py
import uuid
from sqlalchemy import String, Float, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, VersionedMixin
import enum


class BloomLevel(str, enum.Enum):
    remember = "remember"
    understand = "understand"
    apply = "apply"
    analyze = "analyze"
    evaluate = "evaluate"
    create = "create"


class Freshness(str, enum.Enum):
    stable = "stable"
    evolving = "evolving"
    volatile = "volatile"


class Domain(Base):
    __tablename__ = "domains"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True)
    skill_type: Mapped[str] = mapped_column(String(50))
    environment_type: Mapped[str] = mapped_column(String(50))


class Concept(Base, VersionedMixin):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    abstraction_level: Mapped[str] = mapped_column(String(20))  # concrete, abstract
    bloom_level: Mapped[str] = mapped_column(String(20))
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    # PGVector embedding added via Alembic migration (PG-only)


class SkillNode(Base, VersionedMixin):
    __tablename__ = "skill_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    domain_id: Mapped[str] = mapped_column(ForeignKey("domains.id"))
    description: Mapped[str] = mapped_column(Text)
    component_type: Mapped[str] = mapped_column(String(20))  # recurrent, non_recurrent
    bloom_level: Mapped[str] = mapped_column(String(20))
    frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    # PGVector embedding added via Alembic migration (PG-only)
