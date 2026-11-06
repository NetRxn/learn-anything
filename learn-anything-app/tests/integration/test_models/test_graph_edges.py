import pytest
from app.models.graph_nodes import Concept, SkillNode, Domain
from app.models.graph_edges import GraphEdge


@pytest.mark.asyncio
async def test_prerequisite_edge(db):
    c1 = Concept(name="A", description="a", abstraction_level="concrete", bloom_level="remember")
    c2 = Concept(name="B", description="b", abstraction_level="concrete", bloom_level="understand")
    db.add_all([c1, c2])
    await db.commit()
    edge = GraphEdge(
        from_node_id=c1.id,
        from_node_type="concept",
        to_node_id=c2.id,
        to_node_type="concept",
        edge_type="PREREQUISITE",
        strength=0.9,
        prerequisite_type="hard",
        description="A is required before B",
    )
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    assert edge.id is not None
    assert edge.edge_type == "PREREQUISITE"


@pytest.mark.asyncio
async def test_embodies_edge(db):
    d = Domain(name="Test", skill_type="cognitive", environment_type="kind")
    db.add(d)
    await db.commit()
    s = SkillNode(name="S", domain_id=d.id, description="s", component_type="recurrent", bloom_level="apply")
    c = Concept(name="C", description="c", abstraction_level="abstract", bloom_level="understand")
    db.add_all([s, c])
    await db.commit()
    edge = GraphEdge(
        from_node_id=s.id, from_node_type="skill_node",
        to_node_id=c.id, to_node_type="concept",
        edge_type="EMBODIES", strength=0.8,
        description="S implements concept C",
    )
    db.add(edge)
    await db.commit()
    assert edge.edge_type == "EMBODIES"
