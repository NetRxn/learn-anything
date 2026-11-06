# app/models/learner_state.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Text, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class LearnerState(Base):
    __tablename__ = "learner_states"
    __table_args__ = (UniqueConstraint("user_id", "node_id", name="uq_user_node"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)
    node_type: Mapped[str] = mapped_column(String(20))  # concept, skill_node
    mastery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    mastery_category: Mapped[str] = mapped_column(String(20), default="not_started")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_summary: Mapped[str] = mapped_column(Text, default="")
    last_assessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fsrs_difficulty: Mapped[float] = mapped_column(Float, default=5.0)
    fsrs_stability: Mapped[float] = mapped_column(Float, default=0.0)
    bkt_p_transit: Mapped[float] = mapped_column(Float, default=0.15)
    bkt_p_slip: Mapped[float] = mapped_column(Float, default=0.08)
    bkt_p_guess: Mapped[float] = mapped_column(Float, default=0.12)
    transfer_boost: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(30), default="calibration")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MasteryTransition(Base):
    __tablename__ = "mastery_transitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)
    from_state: Mapped[str] = mapped_column(String(20))
    to_state: Mapped[str] = mapped_column(String(20))
    trigger_type: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
