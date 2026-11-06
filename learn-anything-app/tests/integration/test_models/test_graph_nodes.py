import pytest
from app.models.graph_nodes import Concept, SkillNode, Domain


@pytest.mark.asyncio
async def test_create_concept(db):
    c = Concept(
        name="Harmonic Intervals",
        description="Frequency ratios between musical notes",
        abstraction_level="abstract",
        bloom_level="understand",
        field_freshness="stable",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    assert c.id is not None
    assert c.version == 1


@pytest.mark.asyncio
async def test_create_skill_node(db):
    d = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add(d)
    await db.commit()
    s = SkillNode(
        name="Voicings",
        domain_id=d.id,
        description="Chord voicing techniques for jazz piano",
        component_type="recurrent",
        bloom_level="apply",
        frequency_score=0.8,
        impact_score=0.9,
        field_freshness="stable",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    assert s.id is not None
    assert s.domain_id == d.id
