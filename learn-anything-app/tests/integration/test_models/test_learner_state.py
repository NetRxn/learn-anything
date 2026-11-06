import pytest
from app.models.graph_nodes import Concept
from app.models.user import User
from app.models.learner_state import LearnerState, MasteryTransition
from app.security.passwords import hash_password


@pytest.mark.asyncio
async def test_learner_state(db):
    user = User(email="l@t.com", display_name="L", password_hash=hash_password("x"), provider="local")
    concept = Concept(name="X", description="x", abstraction_level="concrete", bloom_level="remember")
    db.add_all([user, concept])
    await db.commit()
    state = LearnerState(
        user_id=user.id,
        node_id=concept.id,
        node_type="concept",
        mastery_probability=0.72,
        mastery_category="proficient",
        confidence=0.85,
        evidence_count=8,
        source="calibration",
    )
    db.add(state)
    await db.commit()
    await db.refresh(state)
    assert state.mastery_probability == 0.72


@pytest.mark.asyncio
async def test_mastery_transition(db):
    t = MasteryTransition(
        user_id="user-1",
        node_id="node-1",
        from_state="familiar",
        to_state="proficient",
        trigger_type="assessment",
        reason="Passed mastery gate TC1",
    )
    db.add(t)
    await db.commit()
    assert t.id is not None
