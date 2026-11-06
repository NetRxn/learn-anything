import pytest
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites


@pytest.mark.asyncio
async def test_create_reference(db):
    ref = Reference(type="paper", title="Test Paper", credibility="peer_reviewed", url="https://example.com")
    db.add(ref)
    await db.commit()
    await db.refresh(ref)
    assert ref.id is not None
    assert ref.credibility == "peer_reviewed"


@pytest.mark.asyncio
async def test_create_material(db):
    mat = Material(type="lecture", title="Intro Lecture", format="markdown", source="generated", bloom_level="understand")
    db.add(mat)
    await db.commit()
    await db.refresh(mat)
    assert mat.id is not None
    assert mat.effectiveness_score == 0.0


@pytest.mark.asyncio
async def test_material_teaches_junction(db):
    mat = Material(type="flashcard_deck", title="Deck", format="apkg", source="generated")
    db.add(mat)
    await db.commit()
    teaches = MaterialTeaches(material_id=mat.id, node_id="concept-1", node_type="concept", depth="reinforcement", modality="interactive")
    db.add(teaches)
    await db.commit()
    assert teaches.id is not None


@pytest.mark.asyncio
async def test_sourced_from_with_page(db):
    ref = Reference(type="book", title="Textbook", credibility="expert_opinion")
    db.add(ref)
    await db.commit()
    sf = SourcedFrom(node_id="skill-1", node_type="skill_node", reference_id=ref.id, relevance=0.9, excerpt="Chapter 3", page_or_timestamp="p.42")
    db.add(sf)
    await db.commit()
    assert sf.page_or_timestamp == "p.42"


@pytest.mark.asyncio
async def test_material_prerequisite(db):
    m1 = Material(type="lecture", title="Lecture 1", format="markdown", source="generated")
    m2 = Material(type="lecture", title="Lecture 2", format="markdown", source="generated")
    db.add_all([m1, m2])
    await db.commit()
    prereq = MaterialPrerequisite(material_id=m2.id, prerequisite_material_id=m1.id)
    db.add(prereq)
    await db.commit()
    assert prereq.id is not None


@pytest.mark.asyncio
async def test_material_cites(db):
    mat = Material(type="lecture", title="Lecture", format="markdown", source="generated")
    ref = Reference(type="paper", title="Cited Paper", credibility="peer_reviewed")
    db.add_all([mat, ref])
    await db.commit()
    cite = MaterialCites(material_id=mat.id, reference_id=ref.id)
    db.add(cite)
    await db.commit()
    assert cite.id is not None
