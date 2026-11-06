# app/models/material.py
import uuid
from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, VersionedMixin


class Reference(Base):
    __tablename__ = "references"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(30))  # book, paper, video, website, course, podcast
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date_published: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_accessed: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credibility: Mapped[str] = mapped_column(String(20), default="community")  # peer_reviewed, expert_opinion, community, anecdotal
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Material(Base, VersionedMixin):
    __tablename__ = "materials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(30))  # lecture, flashcard_deck, worked_example, video, etc.
    title: Mapped[str] = mapped_column(String(500))
    format: Mapped[str] = mapped_column(String(20))  # markdown, apkg, svg, mp4, youtube_embed
    source: Mapped[str] = mapped_column(String(20), default="generated")  # generated, curated, external
    url_or_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    bloom_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)


class MaterialTeaches(Base):
    """Junction: Material -[:TEACHES]-> Concept|SkillNode"""
    __tablename__ = "material_teaches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)  # Polymorphic: concept or skill_node
    node_type: Mapped[str] = mapped_column(String(20))  # "concept" or "skill_node"
    depth: Mapped[str] = mapped_column(String(20), default="introduction")
    modality: Mapped[str] = mapped_column(String(20), default="reading")


class SourcedFrom(Base):
    """Junction: Concept|SkillNode -[:SOURCED_FROM]-> Reference"""
    __tablename__ = "sourced_from"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id: Mapped[str] = mapped_column(String(36), index=True)  # Polymorphic: concept or skill_node
    node_type: Mapped[str] = mapped_column(String(20))
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id"), index=True)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_or_timestamp: Mapped[str | None] = mapped_column(String(100), nullable=True)


class MaterialPrerequisite(Base):
    """Junction: Material -[:PREREQUISITE_MATERIAL]-> Material"""
    __tablename__ = "material_prerequisites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    prerequisite_material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)


class MaterialCites(Base):
    """Junction: Material -[:CITES]-> Reference"""
    __tablename__ = "material_cites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id"), index=True)
