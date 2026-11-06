> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 2: Knowledge Graph Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on feature branch `feature/learn-anything-webapp`. TDD strictly enforced.

**Goal:** A fully operational knowledge graph engine backed by PostgreSQL with Apache AGE (graph traversal, centrality, shortest path, community detection), PGVector (embedding storage, cosine similarity search for transfer detection), server-side graph layout computation, JSON/PG import/export, and backup/restore endpoints. This plan completes the PostgresBackend stub from Plan 1 and adds four new modules under `app/graph/`.

**Architecture:** PostgresBackend reads/writes the three-layer knowledge graph (Concept ontology, SkillNode graphs, LearnerState overlay) through SQLAlchemy for relational queries and raw AGE Cypher for graph traversal. PGVector embedding columns on Concept and SkillNode enable transfer detection. Graph layout is computed server-side for large graphs and sent as pre-computed positions to D3.

**Tech Stack:** SQLAlchemy + asyncpg (relational), Apache AGE (Cypher graph queries), PGVector (embedding similarity), NetworkX (layout computation), Alembic (migration for embedding columns), pytest + pytest-asyncio (TDD)


**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md` — Sections 3, 7, 9

---

## File Tree (new/modified files)

```
learn-anything-app/
├── alembic/
│   └── versions/
│       └── 002_pgvector_embeddings.py     # NEW — adds embedding columns
├── app/
│   ├── backends/
│   │   └── postgres.py                    # MODIFIED — full implementation
│   ├── graph/
│   │   ├── __init__.py                    # NEW
│   │   ├── age_queries.py                 # NEW — AGE Cypher query functions
│   │   ├── embeddings.py                  # NEW — PGVector operations
│   │   ├── transfer.py                    # NEW — Transfer detection logic
│   │   └── layout.py                      # NEW — Server-side graph layout
│   └── routes/
│       └── backup.py                      # NEW — Backup/restore routes
├── templates/
│   └── settings/
│       └── backup.html                    # NEW — Backup/restore UI
└── tests/
    └── integration/
        ├── test_backends/
        │   └── test_postgres_backend.py       # MODIFIED — full integration tests
        ├── test_graph/
        │   ├── __init__.py                    # NEW
        │   ├── test_age_queries.py            # NEW
        │   ├── test_embeddings.py             # NEW
        │   ├── test_transfer.py               # NEW
        │   ├── test_layout.py                 # NEW
        │   ├── test_age_sync.py               # NEW (Task 8)
        │   └── test_integration.py            # NEW (Task 9)
        └── test_routes/
            └── test_backup.py                 # NEW
```

---

### Task 1: Alembic Migration for PGVector Embedding Columns

**Files:**
- Create: `learn-anything-app/alembic/versions/002_pgvector_embeddings.py`
- Modify: `learn-anything-app/app/models/graph_nodes.py` (add embedding columns)
- Modify: `learn-anything-app/pyproject.toml` (add `networkx` dependency)

- [ ] **Step 1: Add networkx to pyproject.toml dependencies**

Add `networkx>=3.4` to the `dependencies` list in `learn-anything-app/pyproject.toml`:

```toml
[project]
name = "learn-anything"
version = "0.2.0"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "jinja2>=3.1",
    "python-multipart>=0.0.18",
    "passlib[bcrypt]>=1.7",
    "authlib>=1.4",
    "httpx>=0.28",
    "cryptography>=44",
    "structlog>=24",
    "pydantic-settings>=2.7",
    "pgvector>=0.3",
    "itsdangerous>=2.2",
    "psycopg[binary]>=3.2",
    "datastar-py>=0.5",
    "networkx>=3.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "httpx>=0.28",
    "pytest-cov>=6",
    "pip-audit>=2.7",
]
```

- [ ] **Step 2: Add embedding column annotations to graph_nodes.py**

Add the embedding column definitions to `Concept` and `SkillNode` in `app/models/graph_nodes.py`. PGVector is always available per CONVENTIONS.md (all tests run against real PG):

```python
# app/models/graph_nodes.py
import uuid
from typing import Optional, Any
from sqlalchemy import String, Float, ForeignKey, Text, Column
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, VersionedMixin

from pgvector.sqlalchemy import Vector  # Always available — tests run against real PG

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
    abstraction_level: Mapped[str] = mapped_column(String(20))
    bloom_level: Mapped[str] = mapped_column(String(20))
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    embedding = Column(Vector(1536), nullable=True)  # PGVector — always available

class SkillNode(Base, VersionedMixin):
    __tablename__ = "skill_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    domain_id: Mapped[str] = mapped_column(ForeignKey("domains.id"))
    description: Mapped[str] = mapped_column(Text)
    component_type: Mapped[str] = mapped_column(String(20))
    bloom_level: Mapped[str] = mapped_column(String(20))
    frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    embedding = Column(Vector(1536), nullable=True)  # PGVector — always available
```

- [ ] **Step 3: Create the Alembic migration**

```python
# alembic/versions/002_pgvector_embeddings.py
"""Add PGVector embedding columns to concepts and skill_nodes.

Revision ID: 002
Revises: 001
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade():
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding columns (1536 dimensions — matches common embedding models)
    op.add_column("concepts", sa.Column("embedding", sa.Text(), nullable=True))
    op.execute("ALTER TABLE concepts ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")

    op.add_column("skill_nodes", sa.Column("embedding", sa.Text(), nullable=True))
    op.execute("ALTER TABLE skill_nodes ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")

    # Create HNSW indexes for fast cosine similarity search
    op.execute(
        "CREATE INDEX ix_concepts_embedding ON concepts USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_skill_nodes_embedding ON skill_nodes USING hnsw (embedding vector_cosine_ops)"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_skill_nodes_embedding")
    op.execute("DROP INDEX IF EXISTS ix_concepts_embedding")
    op.drop_column("skill_nodes", "embedding")
    op.drop_column("concepts", "embedding")
```

- [ ] **Step 4: Verify existing model tests still pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_models/test_graph_nodes.py -v`
Expected: PASS (embedding columns are nullable)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: Alembic migration 002 — PGVector embedding columns on Concept + SkillNode with HNSW indexes"
```

---

### Task 2: Graph Module Init + AGE Cypher Query Functions

**Files:**
- Create: `learn-anything-app/app/graph/__init__.py`
- Create: `learn-anything-app/app/graph/age_queries.py`
- Create: `learn-anything-app/tests/integration/test_graph/__init__.py`
- Create: `learn-anything-app/tests/integration/test_graph/test_age_queries.py`

- [ ] **Step 1: Write failing tests for AGE query functions**

The AGE query functions work with raw SQL via asyncpg. For unit testing, we test the SQL generation and result parsing logic separately from the actual AGE execution (which requires a live PG+AGE instance). We mock the DB connection for unit tests.

```python
# tests/integration/test_graph/__init__.py
# empty

# tests/integration/test_graph/test_age_queries.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.graph.age_queries import (
    build_shortest_path_query,
    build_centrality_query,
    build_community_detection_query,
    build_cross_skill_path_query,
    parse_age_path_result,
    parse_age_centrality_result,
    ensure_age_graph,
)


def test_build_shortest_path_query():
    sql = build_shortest_path_query("learn_graph", "node-1", "node-5")
    assert "ag_catalog" in sql
    # AGE doesn't support shortestPath(); uses variable-length path + ORDER BY length
    assert "order by length(p)" in sql.lower()
    assert "limit 1" in sql.lower()
    assert "node-1" in sql
    assert "node-5" in sql
    assert "learn_graph" in sql


def test_build_centrality_query():
    sql = build_centrality_query("learn_graph", "jazz-piano")
    assert "learn_graph" in sql
    assert "jazz-piano" in sql
    # Must compute degree for each node
    assert "count" in sql.lower() or "degree" in sql.lower()


def test_build_community_detection_query():
    sql = build_community_detection_query("learn_graph", "jazz-piano")
    assert "learn_graph" in sql
    assert "jazz-piano" in sql
    # Label propagation uses connected components in AGE
    assert "connected" in sql.lower() or "component" in sql.lower() or "community" in sql.lower()


def test_build_cross_skill_path_query():
    sql = build_cross_skill_path_query("learn_graph", "node-a", "node-z")
    assert "learn_graph" in sql
    assert "node-a" in sql
    assert "node-z" in sql
    # Cross-skill traverses EMBODIES edges through concepts
    assert "EMBODIES" in sql or "embodies" in sql.lower()


def test_parse_age_path_result_empty():
    result = parse_age_path_result([])
    assert result == {"path": [], "total_weight": 0.0}


def test_parse_age_path_result_with_nodes():
    # Simulate AGE path result rows
    rows = [
        {"node_id": "n1", "name": "A", "edge_type": None, "strength": None},
        {"node_id": "n2", "name": "B", "edge_type": "PREREQUISITE", "strength": 0.9},
        {"node_id": "n3", "name": "C", "edge_type": "PREREQUISITE", "strength": 0.7},
    ]
    result = parse_age_path_result(rows)
    assert len(result["path"]) == 3
    assert result["path"][0]["node_id"] == "n1"
    assert result["path"][1]["edge_type"] == "PREREQUISITE"
    assert result["total_weight"] == pytest.approx(1.6)


def test_parse_age_centrality_result():
    rows = [
        {"node_id": "n1", "name": "A", "in_degree": 3, "out_degree": 2},
        {"node_id": "n2", "name": "B", "in_degree": 1, "out_degree": 4},
    ]
    result = parse_age_centrality_result(rows)
    assert len(result) == 2
    assert result[0]["node_id"] == "n1"
    assert result[0]["degree"] == 5
    assert result[0]["in_degree"] == 3
    # Sorted by total degree descending
    assert result[0]["degree"] >= result[1]["degree"]


@pytest.mark.asyncio
async def test_ensure_age_graph_creates_graph():
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=None)  # Graph doesn't exist yet
    await ensure_age_graph(mock_conn, "learn_graph")
    # Should have called execute to create the graph
    calls = [str(c) for c in mock_conn.execute.call_args_list]
    assert any("create_graph" in c.lower() or "create_vlabel" in c.lower() for c in calls)
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_age_queries.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.graph'`

- [ ] **Step 3: Implement AGE query module**

```python
# app/graph/__init__.py
# Knowledge graph engine — AGE queries, embeddings, transfer detection, layout

# app/graph/age_queries.py
"""Apache AGE Cypher query builders and result parsers.

AGE requires:
1. SET search_path = ag_catalog, "$user", public;
2. Queries wrapped in ag_catalog.cypher() function calls
3. Graph created before first use via ag_catalog.create_graph()

All functions return raw SQL strings or parse raw result rows.
The actual execution happens in PostgresBackend or route handlers.
"""
from __future__ import annotations

GRAPH_NAME = "learn_graph"

# --- Graph lifecycle ---

async def ensure_age_graph(conn, graph_name: str = GRAPH_NAME) -> None:
    """Create the AGE graph and labels if they don't already exist."""
    # Check if graph exists
    exists = await conn.fetchval(
        "SELECT count(*) FROM ag_catalog.ag_graph WHERE name = $1",
        graph_name,
    )
    if not exists:
        await conn.execute(f"SELECT ag_catalog.create_graph('{graph_name}')")
        # Create vertex labels
        await conn.execute(
            f"SELECT ag_catalog.create_vlabel('{graph_name}', 'Concept')"
        )
        await conn.execute(
            f"SELECT ag_catalog.create_vlabel('{graph_name}', 'SkillNode')"
        )
        await conn.execute(
            f"SELECT ag_catalog.create_vlabel('{graph_name}', 'Reference')"
        )
        await conn.execute(
            f"SELECT ag_catalog.create_vlabel('{graph_name}', 'Material')"
        )
        # Create edge labels
        for label in [
            "PREREQUISITE", "PREREQUISITE_MATERIAL", "EMBODIES",
            "SIMILAR_TO", "GENERALIZES", "REINFORCES",
            "NEGATIVE_TRANSFER", "SOURCED_FROM", "TEACHES", "CITES",
        ]:
            await conn.execute(
                f"SELECT ag_catalog.create_elabel('{graph_name}', '{label}')"
            )


# --- Query builders ---

def _cypher_wrapper(graph_name: str, cypher: str, return_types: str) -> str:
    """Wrap a Cypher query in the ag_catalog.cypher() function call."""
    return (
        f"SELECT * FROM ag_catalog.cypher('{graph_name}', $$ {cypher} $$) "
        f"AS ({return_types})"
    )


def build_shortest_path_query(graph_name: str, from_id: str, to_id: str) -> str:
    """Build a shortest-path Cypher query between two nodes.

    AGE does not support Neo4j's shortestPath() function, so we use a
    variable-length path pattern and ORDER BY length(p) ASC LIMIT 1
    to find the shortest path.
    """
    cypher = (
        f"MATCH p = "
        f"(a {{id: '{from_id}'}})-[*1..15]-(b {{id: '{to_id}'}}) "
        f"RETURN nodes(p) AS path_nodes, relationships(p) AS path_edges "
        f"ORDER BY length(p) ASC LIMIT 1"
    )
    return _cypher_wrapper(
        graph_name,
        cypher,
        "path_nodes agtype, path_edges agtype",
    )


def build_centrality_query(graph_name: str, domain_slug: str) -> str:
    """Build a degree centrality query for all nodes in a domain.

    Computes in-degree (how many nodes depend on this) and out-degree
    (how many nodes this depends on). Total degree = in + out.
    Filtered by domain for skill nodes; concepts are domain-independent.

    AGE does not expose vertex labels as a property (n.label), so we
    use explicit label matching with UNION for SkillNode and Concept.
    """
    # SkillNode query — filtered by domain
    skill_cypher = (
        f"MATCH (n:SkillNode) "
        f"WHERE n.domain = '{domain_slug}' "
        f"OPTIONAL MATCH (n)<-[r_in]-() "
        f"OPTIONAL MATCH (n)-[r_out]->() "
        f"RETURN n.id AS node_id, n.name AS name, "
        f"count(DISTINCT r_in) AS in_degree, count(DISTINCT r_out) AS out_degree"
    )
    skill_sql = _cypher_wrapper(
        graph_name, skill_cypher,
        "node_id agtype, name agtype, in_degree agtype, out_degree agtype",
    )
    # Concept query — domain-independent
    concept_cypher = (
        f"MATCH (n:Concept) "
        f"OPTIONAL MATCH (n)<-[r_in]-() "
        f"OPTIONAL MATCH (n)-[r_out]->() "
        f"RETURN n.id AS node_id, n.name AS name, "
        f"count(DISTINCT r_in) AS in_degree, count(DISTINCT r_out) AS out_degree"
    )
    concept_sql = _cypher_wrapper(
        graph_name, concept_cypher,
        "node_id agtype, name agtype, in_degree agtype, out_degree agtype",
    )
    # Combine with UNION ALL and sort in outer query
    return (
        f"SELECT * FROM ({skill_sql} UNION ALL {concept_sql}) AS combined "
        f"ORDER BY (in_degree + out_degree) DESC"
    )


def build_community_detection_query(graph_name: str, domain_slug: str) -> str:
    """Build a connected-component community detection query.

    AGE doesn't have native label propagation, so we use connected components
    via variable-length PREREQUISITE paths. Each connected component is a
    community — tightly coupled skill clusters that should be taught together.

    AGE does not expose vertex labels as a property (n.label), so we
    use explicit label matching with UNION for SkillNode and Concept.
    """
    # SkillNode community query — filtered by domain
    skill_cypher = (
        f"MATCH (n:SkillNode) "
        f"WHERE n.domain = '{domain_slug}' "
        f"OPTIONAL MATCH path = (n)-[:PREREQUISITE|EMBODIES*1..10]-(m) "
        f"RETURN n.id AS node_id, n.name AS name, "
        f"collect(DISTINCT m.id) AS connected_community"
    )
    skill_sql = _cypher_wrapper(
        graph_name, skill_cypher,
        "node_id agtype, name agtype, connected_community agtype",
    )
    # Concept community query — domain-independent
    concept_cypher = (
        f"MATCH (n:Concept) "
        f"OPTIONAL MATCH path = (n)-[:PREREQUISITE|EMBODIES*1..10]-(m) "
        f"RETURN n.id AS node_id, n.name AS name, "
        f"collect(DISTINCT m.id) AS connected_community"
    )
    concept_sql = _cypher_wrapper(
        graph_name, concept_cypher,
        "node_id agtype, name agtype, connected_community agtype",
    )
    # Combine with UNION ALL and sort
    return (
        f"SELECT * FROM ({skill_sql} UNION ALL {concept_sql}) AS combined "
        f"ORDER BY node_id"
    )


def build_cross_skill_path_query(
    graph_name: str, from_id: str, to_id: str
) -> str:
    """Build a cross-skill path query that traverses through shared concepts.

    Path: SkillNode -[:EMBODIES]-> Concept <-[:EMBODIES]- SkillNode
    This finds transfer pathways between skills in different domains.
    """
    cypher = (
        f"MATCH p = (a {{id: '{from_id}'}})"
        f"-[:EMBODIES|SIMILAR_TO|PREREQUISITE*1..8]-"
        f"(b {{id: '{to_id}'}}) "
        f"RETURN nodes(p) AS path_nodes, relationships(p) AS path_edges "
        f"ORDER BY length(p) ASC LIMIT 5"
    )
    return _cypher_wrapper(
        graph_name,
        cypher,
        "path_nodes agtype, path_edges agtype",
    )


# --- Result parsers ---

def parse_age_path_result(rows: list[dict]) -> dict:
    """Parse AGE shortest-path result rows into a structured path dict.

    Args:
        rows: List of dicts with node_id, name, edge_type, strength keys.

    Returns:
        {"path": [{"node_id": ..., "name": ..., "edge_type": ..., "strength": ...}],
         "total_weight": float}
    """
    if not rows:
        return {"path": [], "total_weight": 0.0}

    path = []
    total_weight = 0.0
    for row in rows:
        entry = {
            "node_id": row["node_id"],
            "name": row["name"],
            "edge_type": row.get("edge_type"),
            "strength": row.get("strength"),
        }
        path.append(entry)
        if row.get("strength") is not None:
            total_weight += row["strength"]

    return {"path": path, "total_weight": total_weight}


def parse_age_centrality_result(rows: list[dict]) -> list[dict]:
    """Parse AGE centrality result rows into ranked node list.

    Args:
        rows: List of dicts with node_id, name, in_degree, out_degree.

    Returns:
        List of dicts sorted by total degree descending, with degree field added.
    """
    result = []
    for row in rows:
        in_deg = int(row["in_degree"])
        out_deg = int(row["out_degree"])
        result.append({
            "node_id": row["node_id"],
            "name": row["name"],
            "in_degree": in_deg,
            "out_degree": out_deg,
            "degree": in_deg + out_deg,
        })
    result.sort(key=lambda x: x["degree"], reverse=True)
    return result


def assign_communities(rows: list[dict]) -> dict[str, int]:
    """Assign community IDs from connected-component query results.

    Each node belongs to the community of the smallest node_id in its
    connected component.

    Args:
        rows: List of dicts with node_id, connected_community.

    Returns:
        Dict mapping node_id -> community_id (int, starting from 0).
    """
    # Build union-find from connected components
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for row in rows:
        nid = row["node_id"]
        if nid not in parent:
            parent[nid] = nid
        for connected_id in row.get("connected_community", []):
            if connected_id is not None:
                if connected_id not in parent:
                    parent[connected_id] = connected_id
                union(nid, connected_id)

    # Map roots to sequential community IDs
    root_to_id: dict[str, int] = {}
    result: dict[str, int] = {}
    next_id = 0
    for nid in sorted(parent.keys()):
        root = find(nid)
        if root not in root_to_id:
            root_to_id[root] = next_id
            next_id += 1
        result[nid] = root_to_id[root]

    return result
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_age_queries.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: AGE Cypher query builders — shortest path, centrality, community detection, cross-skill traversal"
```

---

### Task 3: PGVector Embedding Operations

**Files:**
- Create: `learn-anything-app/app/graph/embeddings.py`
- Create: `learn-anything-app/tests/integration/test_graph/test_embeddings.py`

- [ ] **Step 1: Write failing tests for embedding operations**

```python
# tests/integration/test_graph/test_embeddings.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.embeddings import (
    store_embedding,
    batch_store_embeddings,
    cosine_search,
    EmbeddingResult,
)


@pytest.mark.asyncio
async def test_store_embedding_concept(db):
    """Test storing an embedding on a concept node."""
    from app.models.graph_nodes import Concept

    c = Concept(
        name="Test Concept",
        description="A test concept for embedding",
        abstraction_level="abstract",
        bloom_level="understand",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)

    fake_embedding = [0.1] * 1536
    await store_embedding(db, "concept", c.id, fake_embedding)
    await db.refresh(c)
    assert c.embedding is not None


@pytest.mark.asyncio
async def test_store_embedding_skill_node(db):
    """Test storing an embedding on a skill node."""
    from app.models.graph_nodes import SkillNode, Domain

    d = Domain(name="TestEmbed", skill_type="cognitive", environment_type="kind")
    db.add(d)
    await db.commit()
    s = SkillNode(
        name="Test Skill",
        domain_id=d.id,
        description="A test skill for embedding",
        component_type="recurrent",
        bloom_level="apply",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)

    fake_embedding = [0.2] * 1536
    await store_embedding(db, "skill_node", s.id, fake_embedding)
    await db.refresh(s)
    assert s.embedding is not None


@pytest.mark.asyncio
async def test_batch_store_embeddings(db):
    """Test batch storing embeddings for multiple nodes."""
    from app.models.graph_nodes import Concept

    concepts = []
    for i in range(3):
        c = Concept(
            name=f"Batch Concept {i}",
            description=f"Concept {i} for batch embedding",
            abstraction_level="concrete",
            bloom_level="remember",
        )
        concepts.append(c)
    db.add_all(concepts)
    await db.commit()
    for c in concepts:
        await db.refresh(c)

    items = [
        ("concept", c.id, [0.1 * (i + 1)] * 1536)
        for i, c in enumerate(concepts)
    ]
    count = await batch_store_embeddings(db, items)
    assert count == 3


def test_embedding_result_dataclass():
    """Test EmbeddingResult structure."""
    r = EmbeddingResult(
        node_id="abc",
        node_type="concept",
        name="Test",
        cosine_similarity=0.92,
    )
    assert r.node_id == "abc"
    assert r.cosine_similarity == 0.92


def test_cosine_search_builds_correct_query():
    """Test that cosine_search generates the right SQL for PGVector."""
    query_embedding = [0.1] * 1536
    sql, params = cosine_search(
        query_embedding, table="concepts", limit=10, min_similarity=0.70
    )
    assert "concepts" in sql
    assert "1 - (embedding <=> " in sql or "<=>" in sql
    assert params["limit"] == 10
    assert params["min_similarity"] == 0.70
    assert len(params["embedding"]) == 1536
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_embeddings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement embedding operations**

```python
# app/graph/embeddings.py
"""PGVector embedding operations for concept and skill node similarity.

Embeddings are stored as vector(1536) columns in PostgreSQL with PGVector
and queried using cosine distance operator (<=>). All tests run against
real PostgreSQL per CONVENTIONS.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph_nodes import Concept, SkillNode


@dataclass
class EmbeddingResult:
    """A single result from a cosine similarity search."""
    node_id: str
    node_type: str
    name: str
    cosine_similarity: float


# Table name -> model mapping
_TABLE_MAP = {
    "concept": ("concepts", Concept),
    "skill_node": ("skill_nodes", SkillNode),
}


async def store_embedding(
    db: AsyncSession,
    node_type: str,
    node_id: str,
    embedding: list[float],
) -> None:
    """Store an embedding vector on a Concept or SkillNode.

    Args:
        db: Async database session.
        node_type: "concept" or "skill_node".
        node_id: The node's UUID.
        embedding: List of floats (1536 dimensions).
    """
    table_name, model_cls = _TABLE_MAP[node_type]

    stmt = (
        update(model_cls)
        .where(model_cls.id == node_id)
        .values(embedding=embedding)
    )
    await db.execute(stmt)
    await db.commit()


async def batch_store_embeddings(
    db: AsyncSession,
    items: list[tuple[str, str, list[float]]],
) -> int:
    """Store embeddings for multiple nodes in a single transaction.

    Uses a single commit at the end of the batch instead of per-item
    commits to avoid O(n) commit overhead.

    Args:
        items: List of (node_type, node_id, embedding) tuples.

    Returns:
        Number of embeddings stored.
    """
    count = 0
    for node_type, node_id, embedding in items:
        table_name, model_cls = _TABLE_MAP[node_type]
        try:
            stmt = (
                update(model_cls)
                .where(model_cls.id == node_id)
                .values(embedding=embedding)
            )
            await db.execute(stmt)
            count += 1
    # Single commit for entire batch
    await db.commit()
    return count


# Allowlist of valid table names to prevent SQL injection
_VALID_TABLES = {"concepts", "skill_nodes"}

# Mapping from table name to node_type for result typing
_TABLE_TO_NODE_TYPE = {"concepts": "concept", "skill_nodes": "skill_node"}


def _validate_table(table: str) -> str:
    """Validate table name against allowlist to prevent SQL injection.

    Args:
        table: Table name to validate.

    Returns:
        The validated table name.

    Raises:
        ValueError: If table is not in the allowlist.
    """
    if table not in _VALID_TABLES:
        raise ValueError(
            f"Invalid table '{table}'. Must be one of: {_VALID_TABLES}"
        )
    return table


def cosine_search(
    query_embedding: list[float],
    table: str = "concepts",
    limit: int = 20,
    min_similarity: float = 0.70,
) -> tuple[str, dict]:
    """Build a PGVector cosine similarity search query.

    Returns (sql_string, params_dict) for execution via asyncpg.

    The cosine distance operator (<=>) returns distance, so similarity = 1 - distance.
    The table parameter is validated against an allowlist to prevent SQL injection.

    Args:
        query_embedding: The embedding vector to search against.
        table: Table to search ("concepts" or "skill_nodes").
        limit: Maximum results to return.
        min_similarity: Minimum cosine similarity threshold.

    Returns:
        Tuple of (SQL string, parameter dict).

    Raises:
        ValueError: If table is not in the allowlist {"concepts", "skill_nodes"}.
    """
    validated_table = _validate_table(table)
    sql = f"""
        SELECT id AS node_id, name,
               1 - (embedding <=> :embedding::vector) AS cosine_similarity
        FROM {validated_table}
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> :embedding::vector) >= :min_similarity
        ORDER BY embedding <=> :embedding::vector ASC
        LIMIT :limit
    """
    params = {
        "embedding": query_embedding,
        "min_similarity": min_similarity,
        "limit": limit,
    }
    return sql, params


async def execute_cosine_search(
    db: AsyncSession,
    query_embedding: list[float],
    table: str = "concepts",
    node_type: str | None = None,
    limit: int = 20,
    min_similarity: float = 0.70,
) -> list[EmbeddingResult]:
    """Execute a cosine similarity search and return typed results.

    This is the high-level function for production use. Requires PGVector.
    Delegates to cosine_search() for query building (which validates the
    table name against an allowlist).

    Args:
        db: Async database session (must be PG with PGVector).
        query_embedding: The embedding to search against.
        table: "concepts" or "skill_nodes" (validated against allowlist).
        node_type: "concept" or "skill_node" (for result typing).
            If None, inferred from the table name.
        limit: Max results.
        min_similarity: Minimum cosine similarity.

    Returns:
        List of EmbeddingResult sorted by similarity descending.
    """
    # Build the query (validates table name)
    sql_str, _ = cosine_search(query_embedding, table, limit, min_similarity)

    # Infer node_type from table if not provided
    resolved_node_type = node_type or _TABLE_TO_NODE_TYPE[table]

    embedding_str = "[" + ",".join(str(f) for f in query_embedding) + "]"
    sql = text(sql_str)
    result = await db.execute(
        sql,
        {"embedding": embedding_str, "min_similarity": min_similarity, "limit": limit},
    )
    rows = result.mappings().all()
    return [
        EmbeddingResult(
            node_id=row["node_id"],
            node_type=resolved_node_type,
            name=row["name"],
            cosine_similarity=float(row["cosine_similarity"]),
        )
        for row in rows
    ]
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_embeddings.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: PGVector embedding operations — store, batch store, cosine similarity search"
```

---

### Task 4: Transfer Detection Logic

**Files:**
- Create: `learn-anything-app/app/graph/transfer.py`
- Create: `learn-anything-app/tests/integration/test_graph/test_transfer.py`

- [ ] **Step 1: Write failing tests for transfer detection**

```python
# tests/integration/test_graph/test_transfer.py
import pytest
from app.graph.transfer import (
    classify_transfer,
    TransferClassification,
    compute_transfer_boost,
    build_transfer_matches,
    apply_transfer_boosts,
)
from app.graph.embeddings import EmbeddingResult


def test_classify_near_transfer():
    result = classify_transfer(0.92)
    assert result == TransferClassification.NEAR
    assert result.action == "auto_boost"


def test_classify_moderate_transfer():
    result = classify_transfer(0.78)
    assert result == TransferClassification.MODERATE
    assert result.action == "probe_first"


def test_classify_independent():
    result = classify_transfer(0.55)
    assert result == TransferClassification.INDEPENDENT
    assert result.action == "learn_fresh"


def test_classify_boundary_high():
    # 0.85 is MODERATE per spec (>0.85 is NEAR, not >=0.85)
    result = classify_transfer(0.85)
    assert result == TransferClassification.MODERATE


def test_classify_boundary_low():
    result = classify_transfer(0.70)
    assert result == TransferClassification.MODERATE


def test_classify_below_boundary():
    result = classify_transfer(0.699)
    assert result == TransferClassification.INDEPENDENT


def test_compute_transfer_boost_near():
    boost = compute_transfer_boost(
        cosine_similarity=0.92,
        source_mastery=0.85,
        classification=TransferClassification.NEAR,
    )
    # Near transfer: boost = cosine * source_mastery * 0.8
    expected = 0.92 * 0.85 * 0.8
    assert boost == pytest.approx(expected, abs=0.01)


def test_compute_transfer_boost_moderate():
    boost = compute_transfer_boost(
        cosine_similarity=0.78,
        source_mastery=0.90,
        classification=TransferClassification.MODERATE,
    )
    # Moderate: boost = cosine * source_mastery * 0.4 (conservative until probed)
    expected = 0.78 * 0.90 * 0.4
    assert boost == pytest.approx(expected, abs=0.01)


def test_compute_transfer_boost_independent():
    boost = compute_transfer_boost(
        cosine_similarity=0.50,
        source_mastery=0.95,
        classification=TransferClassification.INDEPENDENT,
    )
    assert boost == 0.0


def test_build_transfer_matches():
    search_results = [
        EmbeddingResult(node_id="c1", node_type="concept", name="Intervals", cosine_similarity=0.92),
        EmbeddingResult(node_id="c2", node_type="concept", name="Rhythm", cosine_similarity=0.75),
        EmbeddingResult(node_id="c3", node_type="concept", name="Cooking", cosine_similarity=0.40),
    ]
    source_masteries = {"c1": 0.80, "c2": 0.60, "c3": 0.0}

    matches = build_transfer_matches(search_results, source_masteries)

    # Only near + moderate should produce matches (cosine >= 0.70)
    assert len(matches) == 2
    assert matches[0].source_node_id == "c1"
    assert matches[0].classification == TransferClassification.NEAR
    assert matches[0].boost > 0
    assert matches[1].source_node_id == "c2"
    assert matches[1].classification == TransferClassification.MODERATE


@pytest.mark.asyncio
async def test_apply_transfer_boosts(db):
    from app.models.graph_nodes import Concept
    from app.models.user import User
    from app.models.learner_state import LearnerState
    from app.security.passwords import hash_password

    user = User(email="transfer@test.com", display_name="T", password_hash=hash_password("x"), provider="local")
    target = Concept(name="Target", description="target node", abstraction_level="abstract", bloom_level="understand")
    db.add_all([user, target])
    await db.commit()
    await db.refresh(user)
    await db.refresh(target)

    state = LearnerState(
        user_id=user.id,
        node_id=target.id,
        node_type="concept",
        mastery_probability=0.10,
        mastery_category="attempted",
        confidence=0.3,
        source="calibration",
    )
    db.add(state)
    await db.commit()

    boosts = [
        {"node_id": target.id, "boost": 0.25, "source_node_id": "c1", "source_name": "Intervals"},
    ]
    updated = await apply_transfer_boosts(db, user.id, boosts)
    assert updated == 1

    await db.refresh(state)
    assert state.transfer_boost == pytest.approx(0.25)
    assert state.mastery_probability == pytest.approx(0.35, abs=0.01)
    assert state.source == "propagation"
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_transfer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement transfer detection**

```python
# app/graph/transfer.py
"""Transfer detection logic for cross-skill knowledge transfer.

When new skill nodes are embedded, their PGVector cosine similarity
against existing concept embeddings determines transfer classification:

| Cosine    | Classification | Action     |
|-----------|---------------|------------|
| >= 0.85   | NEAR          | Auto-boost |
| 0.70-0.85 | MODERATE      | Probe first|
| < 0.70    | INDEPENDENT   | Learn fresh|

Transfer boosts are multiplicative: boost = cosine * source_mastery * weight_factor
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.embeddings import EmbeddingResult
from app.models.learner_state import LearnerState, MasteryTransition


class TransferClassification(enum.Enum):
    NEAR = "near"
    MODERATE = "moderate"
    INDEPENDENT = "independent"

    @property
    def action(self) -> str:
        return {
            TransferClassification.NEAR: "auto_boost",
            TransferClassification.MODERATE: "probe_first",
            TransferClassification.INDEPENDENT: "learn_fresh",
        }[self]

    @property
    def weight_factor(self) -> float:
        """Multiplier for transfer boost computation."""
        return {
            TransferClassification.NEAR: 0.8,
            TransferClassification.MODERATE: 0.4,
            TransferClassification.INDEPENDENT: 0.0,
        }[self]


def classify_transfer(cosine_similarity: float) -> TransferClassification:
    """Classify transfer type based on cosine similarity threshold.

    Args:
        cosine_similarity: Cosine similarity between embeddings (0.0-1.0).

    Returns:
        TransferClassification enum value.
    """
    if cosine_similarity > 0.85:
        return TransferClassification.NEAR
    elif cosine_similarity >= 0.70:
        return TransferClassification.MODERATE
    else:
        return TransferClassification.INDEPENDENT


def compute_transfer_boost(
    cosine_similarity: float,
    source_mastery: float,
    classification: TransferClassification,
) -> float:
    """Compute the transfer boost value.

    boost = cosine_similarity * source_mastery * weight_factor

    Args:
        cosine_similarity: Cosine similarity between embeddings.
        source_mastery: Mastery probability of the source concept (0.0-1.0).
        classification: Transfer classification.

    Returns:
        Transfer boost value (0.0-1.0). Returns 0.0 for INDEPENDENT.
    """
    if classification == TransferClassification.INDEPENDENT:
        return 0.0
    return cosine_similarity * source_mastery * classification.weight_factor


@dataclass
class TransferMatch:
    """A detected transfer match between a new skill node and an existing concept."""
    source_node_id: str
    source_name: str
    source_node_type: str
    cosine_similarity: float
    classification: TransferClassification
    source_mastery: float
    boost: float


def build_transfer_matches(
    search_results: list[EmbeddingResult],
    source_masteries: dict[str, float],
) -> list[TransferMatch]:
    """Build transfer matches from cosine search results.

    Filters out INDEPENDENT classifications (cosine < 0.70) and computes
    boost values for NEAR and MODERATE matches.

    Args:
        search_results: Cosine similarity search results from PGVector.
        source_masteries: Dict mapping node_id -> mastery_probability.

    Returns:
        List of TransferMatch for non-independent matches, sorted by boost descending.
    """
    matches = []
    for result in search_results:
        classification = classify_transfer(result.cosine_similarity)
        if classification == TransferClassification.INDEPENDENT:
            continue

        source_mastery = source_masteries.get(result.node_id, 0.0)
        boost = compute_transfer_boost(
            result.cosine_similarity, source_mastery, classification
        )
        matches.append(TransferMatch(
            source_node_id=result.node_id,
            source_name=result.name,
            source_node_type=result.node_type,
            cosine_similarity=result.cosine_similarity,
            classification=classification,
            source_mastery=source_mastery,
            boost=boost,
        ))

    matches.sort(key=lambda m: m.boost, reverse=True)
    return matches


async def apply_transfer_boosts(
    db: AsyncSession,
    user_id: str,
    boosts: list[dict],
) -> int:
    """Apply transfer boosts to learner states.

    For each boost entry, updates the LearnerState:
    - Adds boost to transfer_boost field
    - Adds boost to mastery_probability (capped at 1.0)
    - Sets source to "propagation"
    - Records a MasteryTransition

    Args:
        db: Async database session.
        user_id: The learner's user ID.
        boosts: List of dicts with keys: node_id, boost, source_node_id, source_name.

    Returns:
        Number of states updated.
    """
    updated = 0
    for entry in boosts:
        node_id = entry["node_id"]
        boost = entry["boost"]

        # Fetch current learner state
        result = await db.execute(
            select(LearnerState).where(
                LearnerState.user_id == user_id,
                LearnerState.node_id == node_id,
            )
        )
        state = result.scalar_one_or_none()
        if state is None:
            continue

        old_category = state.mastery_category

        # Apply boost
        state.transfer_boost = min(1.0, state.transfer_boost + boost)
        state.mastery_probability = min(1.0, state.mastery_probability + boost)
        state.source = "propagation"

        # Update mastery category based on new probability
        prob = state.mastery_probability
        if prob >= 0.90:
            state.mastery_category = "mastered"
        elif prob >= 0.70:
            state.mastery_category = "proficient"
        elif prob >= 0.40:
            state.mastery_category = "familiar"
        elif prob >= 0.10:
            state.mastery_category = "attempted"
        else:
            state.mastery_category = "not_started"

        # Record transition if category changed
        if state.mastery_category != old_category:
            transition = MasteryTransition(
                user_id=user_id,
                node_id=node_id,
                from_state=old_category,
                to_state=state.mastery_category,
                trigger_type="transfer",
                reason=f"Transfer boost {boost:.3f} from {entry['source_name']} (node {entry['source_node_id']})",
            )
            db.add(transition)

        updated += 1

    await db.commit()
    return updated
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_transfer.py -v`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: transfer detection — classify, compute boost, apply to learner states with audit trail"
```

---

### Task 5: Server-Side Graph Layout

**Files:**
- Create: `learn-anything-app/app/graph/layout.py`
- Create: `learn-anything-app/tests/integration/test_graph/test_layout.py`

- [ ] **Step 1: Write failing tests for layout computation**

```python
# tests/integration/test_graph/test_layout.py
import pytest
from app.graph.layout import (
    compute_layout,
    LayoutAlgorithm,
    scale_positions,
    compute_node_sizes,
)


def make_test_graph():
    """Create a small test graph for layout computation."""
    nodes = [
        {"id": "n1", "name": "Concept A", "type": "concept", "impact_score": 0.9, "frequency_score": 0.8},
        {"id": "n2", "name": "Skill B", "type": "skill_node", "impact_score": 0.7, "frequency_score": 0.6},
        {"id": "n3", "name": "Concept C", "type": "concept", "impact_score": 0.5, "frequency_score": 0.4},
        {"id": "n4", "name": "Skill D", "type": "skill_node", "impact_score": 0.3, "frequency_score": 0.2},
    ]
    edges = [
        {"from_id": "n1", "to_id": "n2", "edge_type": "PREREQUISITE"},
        {"from_id": "n2", "to_id": "n3", "edge_type": "EMBODIES"},
        {"from_id": "n3", "to_id": "n4", "edge_type": "PREREQUISITE"},
    ]
    return nodes, edges


def test_compute_layout_spring():
    nodes, edges = make_test_graph()
    positions = compute_layout(nodes, edges, algorithm=LayoutAlgorithm.SPRING)
    assert len(positions) == 4
    for node_id, pos in positions.items():
        assert "x" in pos
        assert "y" in pos
        assert isinstance(pos["x"], float)
        assert isinstance(pos["y"], float)


def test_compute_layout_hierarchical():
    nodes, edges = make_test_graph()
    positions = compute_layout(nodes, edges, algorithm=LayoutAlgorithm.HIERARCHICAL)
    assert len(positions) == 4
    # Hierarchical layout: upstream nodes should have smaller y (higher)
    # n1 -> n2 -> n3 -> n4 (prerequisite chain)
    assert positions["n1"]["y"] <= positions["n4"]["y"]


def test_compute_layout_empty_graph():
    positions = compute_layout([], [], algorithm=LayoutAlgorithm.SPRING)
    assert positions == {}


def test_compute_layout_single_node():
    nodes = [{"id": "n1", "name": "Solo", "type": "concept", "impact_score": 1.0, "frequency_score": 1.0}]
    positions = compute_layout(nodes, [], algorithm=LayoutAlgorithm.SPRING)
    assert len(positions) == 1
    assert "n1" in positions


def test_scale_positions():
    raw_positions = {
        "n1": {"x": -1.5, "y": 0.5},
        "n2": {"x": 2.0, "y": -1.0},
    }
    scaled = scale_positions(raw_positions, width=1920, height=1080, padding=50)
    for pos in scaled.values():
        assert pos["x"] >= 50
        assert pos["x"] <= 1870
        assert pos["y"] >= 50
        assert pos["y"] <= 1030


def test_compute_node_sizes():
    nodes = [
        {"id": "n1", "impact_score": 0.9, "frequency_score": 0.8},
        {"id": "n2", "impact_score": 0.3, "frequency_score": 0.2},
        {"id": "n3", "impact_score": 0.5, "frequency_score": 0.5},
    ]
    sizes = compute_node_sizes(nodes, min_radius=12, max_radius=40)
    assert len(sizes) == 3
    # Higher impact * frequency should mean larger radius
    assert sizes["n1"] > sizes["n2"]
    assert all(12 <= r <= 40 for r in sizes.values())


def test_compute_layout_large_graph():
    """Test layout with >100 nodes doesn't crash and completes."""
    nodes = [
        {"id": f"n{i}", "name": f"Node {i}", "type": "concept", "impact_score": 0.5, "frequency_score": 0.5}
        for i in range(150)
    ]
    edges = [
        {"from_id": f"n{i}", "to_id": f"n{i+1}", "edge_type": "PREREQUISITE"}
        for i in range(149)
    ]
    positions = compute_layout(nodes, edges, algorithm=LayoutAlgorithm.SPRING)
    assert len(positions) == 150
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_layout.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement layout computation**

```python
# app/graph/layout.py
"""Server-side graph layout computation for large knowledge graphs.

For small graphs (<50 nodes), D3 force-layout runs client-side.
For large cross-skill graphs, server computes layout using NetworkX
and sends pre-computed positions to D3 for rendering.

Supports two algorithms:
- SPRING: Force-directed (Fruchterman-Reingold) — good general-purpose
- HIERARCHICAL: Topological-sort-based layered layout — respects prerequisite chains
"""
from __future__ import annotations

import enum
import math
import networkx as nx


class LayoutAlgorithm(str, enum.Enum):
    SPRING = "spring"
    HIERARCHICAL = "hierarchical"


def compute_layout(
    nodes: list[dict],
    edges: list[dict],
    algorithm: LayoutAlgorithm = LayoutAlgorithm.SPRING,
    width: float = 1920.0,
    height: float = 1080.0,
    padding: float = 50.0,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    """Compute layout positions for all nodes in the graph.

    Args:
        nodes: List of node dicts with at least "id" key.
        edges: List of edge dicts with "from_id" and "to_id" keys.
        algorithm: Layout algorithm to use.
        width: Target viewport width in pixels.
        height: Target viewport height in pixels.
        padding: Padding from viewport edges in pixels.
        seed: Random seed for reproducible layouts.

    Returns:
        Dict mapping node_id -> {"x": float, "y": float}.
    """
    if not nodes:
        return {}

    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"])
    for edge in edges:
        G.add_edge(edge["from_id"], edge["to_id"])

    if algorithm == LayoutAlgorithm.HIERARCHICAL:
        raw_positions = _hierarchical_layout(G, nodes)
    else:
        raw_positions = _spring_layout(G, seed=seed)

    # Convert to dict format
    pos_dict = {
        nid: {"x": float(xy[0]), "y": float(xy[1])}
        for nid, xy in raw_positions.items()
    }

    return scale_positions(pos_dict, width, height, padding)


def _spring_layout(G: nx.DiGraph, seed: int = 42) -> dict:
    """Fruchterman-Reingold force-directed layout."""
    k = 1.0 / math.sqrt(max(G.number_of_nodes(), 1))
    return nx.spring_layout(G, k=k, iterations=100, seed=seed)


def _hierarchical_layout(G: nx.DiGraph, nodes: list[dict]) -> dict:
    """Topological-sort-based layered layout.

    Assigns y-coordinates based on longest path from sources (nodes with no
    prerequisites). Nodes at the same depth are spread horizontally.
    Respects prerequisite ordering: upstream nodes are higher (smaller y).
    """
    # Handle cycles by iteratively finding and removing them until DAG
    # A single find_cycle call only finds one cycle; the graph may have many.
    if not nx.is_directed_acyclic_graph(G):
        G_dag = G.copy()
        while not nx.is_directed_acyclic_graph(G_dag):
            try:
                cycle_edges = list(nx.find_cycle(G_dag))
                # Remove the last edge in the cycle (back edge)
                u, v = cycle_edges[-1][0], cycle_edges[-1][1]
                if G_dag.has_edge(u, v):
                    G_dag.remove_edge(u, v)
            except nx.NetworkXNoCycle:
                break
    else:
        G_dag = G

    # Compute depth (longest path from any source)
    depths: dict[str, int] = {}
    try:
        for node in nx.topological_sort(G_dag):
            predecessors = list(G_dag.predecessors(node))
            if not predecessors:
                depths[node] = 0
            else:
                depths[node] = max(depths.get(p, 0) for p in predecessors) + 1
    except nx.NetworkXError:
        # Fallback for disconnected components
        for node in G.nodes():
            if node not in depths:
                depths[node] = 0

    # Ensure all nodes have a depth
    for node in G.nodes():
        if node not in depths:
            depths[node] = 0

    # Group by depth, spread horizontally within each layer
    layers: dict[int, list[str]] = {}
    for node_id, depth in depths.items():
        layers.setdefault(depth, []).append(node_id)

    positions = {}
    max_depth = max(depths.values()) if depths else 0
    for depth, layer_nodes in layers.items():
        y = depth / max(max_depth, 1)  # 0 to 1 (top to bottom)
        for i, nid in enumerate(sorted(layer_nodes)):
            x = (i + 1) / (len(layer_nodes) + 1)  # Spread evenly 0-1
            positions[nid] = (x, y)

    return positions


def scale_positions(
    positions: dict[str, dict[str, float]],
    width: float = 1920.0,
    height: float = 1080.0,
    padding: float = 50.0,
) -> dict[str, dict[str, float]]:
    """Scale positions to fit within a viewport with padding.

    Normalizes positions to [padding, width-padding] x [padding, height-padding].

    Args:
        positions: Dict mapping node_id -> {"x": float, "y": float}.
        width: Viewport width.
        height: Viewport height.
        padding: Minimum distance from edges.

    Returns:
        Scaled positions dict.
    """
    if not positions:
        return {}

    if len(positions) == 1:
        nid = next(iter(positions))
        return {nid: {"x": width / 2, "y": height / 2}}

    xs = [p["x"] for p in positions.values()]
    ys = [p["y"] for p in positions.values()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    range_x = max_x - min_x if max_x != min_x else 1.0
    range_y = max_y - min_y if max_y != min_y else 1.0

    usable_w = width - 2 * padding
    usable_h = height - 2 * padding

    scaled = {}
    for nid, pos in positions.items():
        sx = padding + ((pos["x"] - min_x) / range_x) * usable_w
        sy = padding + ((pos["y"] - min_y) / range_y) * usable_h
        scaled[nid] = {"x": sx, "y": sy}

    return scaled


def compute_node_sizes(
    nodes: list[dict],
    min_radius: float = 12.0,
    max_radius: float = 40.0,
) -> dict[str, float]:
    """Compute node display sizes based on impact and frequency scores.

    Size = impact_score * frequency_score, normalized to [min_radius, max_radius].

    Args:
        nodes: List of node dicts with "id", "impact_score", "frequency_score".
        min_radius: Minimum node radius in pixels.
        max_radius: Maximum node radius in pixels.

    Returns:
        Dict mapping node_id -> radius (float).
    """
    if not nodes:
        return {}

    raw_scores = {}
    for node in nodes:
        impact = node.get("impact_score", 0.5)
        freq = node.get("frequency_score", 0.5)
        raw_scores[node["id"]] = impact * freq

    min_score = min(raw_scores.values())
    max_score = max(raw_scores.values())
    score_range = max_score - min_score if max_score != min_score else 1.0

    sizes = {}
    for nid, score in raw_scores.items():
        normalized = (score - min_score) / score_range
        sizes[nid] = min_radius + normalized * (max_radius - min_radius)

    return sizes
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_layout.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: server-side graph layout — spring + hierarchical algorithms with node sizing"
```

---

### Task 6: PostgresBackend — Full Implementation

**Files:**
- Modify: `learn-anything-app/app/backends/protocol.py` (extend `read_graph` signature)
- Modify: `learn-anything-app/app/backends/postgres.py`
- Modify: `learn-anything-app/app/backends/json_file.py` (update `read_graph` signature)
- Modify: `learn-anything-app/tests/integration/test_backends/test_postgres_backend.py`

- [ ] **Step 0: Extend StateBackend protocol with user_id parameter**

Plan 1's `StateBackend` protocol defines `read_graph(self, skill_slug: str) -> dict`. Plan 2 requires learner state overlay, which needs a `user_id` parameter. Extend the protocol to include `user_id` as an optional parameter so both backends conform:

```python
# app/backends/protocol.py — update the read_graph signature
class StateBackend(Protocol):
    async def read_graph(self, skill_slug: str, user_id: str | None = None) -> dict: ...
    async def write_graph(self, skill_slug: str, graph: dict) -> None: ...
    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]: ...
    async def export_json(self, skill_slug: str) -> dict: ...
    async def import_json(self, skill_slug: str, data: dict) -> None: ...
```

Also update `JSONFileBackend.read_graph` to accept the new parameter (ignored for JSON backend):

```python
# app/backends/json_file.py — update read_graph signature
    async def read_graph(self, skill_slug: str, user_id: str | None = None) -> dict:
        path = self._graph_path(skill_slug)
        if not path.exists():
            return {}
        return json.loads(path.read_text())
```

- [ ] **Step 1: Write comprehensive tests for PostgresBackend**

All tests run against real PostgreSQL with PGVector + AGE extensions per CONVENTIONS.md.

```python
# tests/integration/test_backends/test_postgres_backend.py
import pytest
from app.backends.postgres import PostgresBackend
from app.backends.protocol import StateBackend
from app.models.graph_nodes import Concept, SkillNode, Domain
from app.models.graph_edges import GraphEdge
from app.models.learner_state import LearnerState
from app.models.user import User
from app.security.passwords import hash_password


def test_postgres_backend_implements_protocol():
    """Verify PostgresBackend has all methods from StateBackend protocol."""
    required_methods = ["read_graph", "write_graph", "query_transfer", "export_json", "import_json"]
    for method in required_methods:
        assert hasattr(PostgresBackend, method), f"Missing method: {method}"


@pytest.fixture
async def populated_db(db):
    """Create a populated database with domain, concepts, skill nodes, edges, and learner state."""
    user = User(email="pg@test.com", display_name="PG", password_hash=hash_password("x"), provider="local")
    domain = Domain(name="jazz-piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()
    await db.refresh(domain)
    await db.refresh(user)

    c1 = Concept(
        name="Harmonic Intervals",
        description="Frequency ratios between notes",
        abstraction_level="abstract",
        bloom_level="understand",
    )
    c2 = Concept(
        name="Chord Voicing",
        description="How to select and arrange chord tones",
        abstraction_level="concrete",
        bloom_level="apply",
    )
    db.add_all([c1, c2])
    await db.commit()
    await db.refresh(c1)
    await db.refresh(c2)

    s1 = SkillNode(
        name="Shell Voicings",
        domain_id=domain.id,
        description="3-note chord shells for jazz",
        component_type="recurrent",
        bloom_level="apply",
        frequency_score=0.9,
        impact_score=0.8,
    )
    s2 = SkillNode(
        name="Rootless Voicings",
        domain_id=domain.id,
        description="Voicings without the root",
        component_type="recurrent",
        bloom_level="analyze",
        frequency_score=0.7,
        impact_score=0.9,
    )
    db.add_all([s1, s2])
    await db.commit()
    await db.refresh(s1)
    await db.refresh(s2)

    edges = [
        GraphEdge(
            from_node_id=s1.id, from_node_type="skill_node",
            to_node_id=s2.id, to_node_type="skill_node",
            edge_type="PREREQUISITE", strength=0.95, prerequisite_type="hard",
            description="Shell voicings must be learned before rootless",
        ),
        GraphEdge(
            from_node_id=s1.id, from_node_type="skill_node",
            to_node_id=c2.id, to_node_type="concept",
            edge_type="EMBODIES", strength=0.8,
            description="Shell voicings implement chord voicing concept",
        ),
        GraphEdge(
            from_node_id=c1.id, from_node_type="concept",
            to_node_id=c2.id, to_node_type="concept",
            edge_type="GENERALIZES", strength=1.0,
            description="Intervals generalize to voicings",
        ),
    ]
    db.add_all(edges)

    state1 = LearnerState(
        user_id=user.id, node_id=s1.id, node_type="skill_node",
        mastery_probability=0.75, mastery_category="proficient",
        confidence=0.8, evidence_count=5, source="calibration",
    )
    state2 = LearnerState(
        user_id=user.id, node_id=c1.id, node_type="concept",
        mastery_probability=0.45, mastery_category="familiar",
        confidence=0.6, evidence_count=3, source="calibration",
    )
    db.add_all([state1, state2])
    await db.commit()

    return {
        "user": user, "domain": domain,
        "concepts": [c1, c2], "skills": [s1, s2],
        "edges": edges, "states": [state1, state2],
    }


@pytest.fixture
def backend(db):
    """Create a PostgresBackend wrapping the test session."""
    return PostgresBackend(session=db)


@pytest.mark.asyncio
async def test_read_graph_empty(backend, db):
    domain = Domain(name="empty-domain", skill_type="cognitive", environment_type="kind")
    db.add(domain)
    await db.commit()
    result = await backend.read_graph("empty-domain")
    assert result["vertices"] == []
    assert result["edges"] == []


@pytest.mark.asyncio
async def test_read_graph_populated(backend, populated_db):
    result = await backend.read_graph("jazz-piano")
    assert len(result["vertices"]) == 4  # 2 concepts + 2 skills
    assert len(result["edges"]) == 3

    # Verify vertex structure
    names = {v["name"] for v in result["vertices"]}
    assert "Harmonic Intervals" in names
    assert "Shell Voicings" in names

    # Verify edge structure
    edge_types = {e["edge_type"] for e in result["edges"]}
    assert "PREREQUISITE" in edge_types
    assert "EMBODIES" in edge_types
    assert "GENERALIZES" in edge_types


@pytest.mark.asyncio
async def test_read_graph_includes_learner_state(backend, populated_db):
    user = populated_db["user"]
    result = await backend.read_graph("jazz-piano", user_id=user.id)

    # Find Shell Voicings vertex
    shell = next(v for v in result["vertices"] if v["name"] == "Shell Voicings")
    assert shell["learner_state"]["mastery_probability"] == 0.75
    assert shell["learner_state"]["mastery_category"] == "proficient"


@pytest.mark.asyncio
async def test_write_graph_creates_nodes(backend, db):
    domain = Domain(name="write-test", skill_type="cognitive", environment_type="kind")
    db.add(domain)
    await db.commit()

    graph_data = {
        "vertices": [
            {
                "id": "new-c1", "label": "Concept", "name": "New Concept",
                "description": "A brand new concept",
                "abstraction_level": "abstract", "bloom_level": "understand",
            },
            {
                "id": "new-s1", "label": "Skill", "name": "New Skill",
                "description": "A brand new skill",
                "component_type": "recurrent", "bloom_level": "apply",
                "frequency_score": 0.6, "impact_score": 0.7,
            },
        ],
        "edges": [
            {
                "from_id": "new-s1", "to_id": "new-c1",
                "label": "EMBODIES", "strength": 0.9,
                "description": "New skill embodies new concept",
            },
        ],
    }
    await backend.write_graph("write-test", graph_data)

    result = await backend.read_graph("write-test")
    assert len(result["vertices"]) == 2
    assert len(result["edges"]) == 1


@pytest.mark.asyncio
async def test_export_json(backend, populated_db):
    exported = await backend.export_json("jazz-piano")
    assert "vertices" in exported
    assert "edges" in exported
    assert "gap_analysis" in exported
    assert len(exported["vertices"]) == 4


@pytest.mark.asyncio
async def test_import_json(backend, db):
    domain = Domain(name="import-test", skill_type="cognitive", environment_type="kind")
    db.add(domain)
    await db.commit()

    import_data = {
        "vertices": [
            {
                "id": "imp-c1", "label": "Concept", "name": "Imported Concept",
                "description": "Came from JSON export",
                "abstraction_level": "concrete", "bloom_level": "remember",
            },
        ],
        "edges": [],
    }
    await backend.import_json("import-test", import_data)

    result = await backend.read_graph("import-test")
    assert len(result["vertices"]) == 1
    assert result["vertices"][0]["name"] == "Imported Concept"


@pytest.mark.asyncio
async def test_export_import_roundtrip(backend, populated_db):
    exported = await backend.export_json("jazz-piano")
    domain = Domain(name="roundtrip-test", skill_type="hybrid", environment_type="mostly_kind")
    db = backend._session
    db.add(domain)
    await db.commit()

    await backend.import_json("roundtrip-test", exported)
    reimported = await backend.read_graph("roundtrip-test")
    assert len(reimported["vertices"]) == len(exported["vertices"])
    assert len(reimported["edges"]) == len(exported["edges"])
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_backends/test_postgres_backend.py -v`
Expected: Most tests FAIL — stub returns empty dicts

- [ ] **Step 3: Implement full PostgresBackend**

```python
# app/backends/postgres.py
"""PostgreSQL backend for the StateBackend protocol.

Uses SQLAlchemy for relational queries on Concept, SkillNode, GraphEdge,
and LearnerState models. PGVector and AGE integration handled by
app.graph.embeddings and app.graph.age_queries modules respectively.
"""
from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.backends.protocol import TransferMatch
from app.models.graph_nodes import Concept, SkillNode, Domain
from app.models.graph_edges import GraphEdge
from app.models.learner_state import LearnerState


class PostgresBackend:
    def __init__(self, session_factory=None, session: AsyncSession | None = None):
        """Initialize PostgresBackend.

        Args:
            session_factory: Async session factory (for production — creates sessions per operation).
            session: Direct session (for testing — reuses a single session).
        """
        self._session_factory = session_factory
        self._session = session

    async def _get_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        return self._session_factory()

    async def _close_session(self, session: AsyncSession) -> None:
        """Close session if we created it (not in test mode)."""
        if self._session is None:
            await session.close()

    async def read_graph(self, skill_slug: str, user_id: str | None = None) -> dict:
        """Read the full knowledge graph for a skill domain.

        Returns a dict compatible with the knowledge-graph.schema.json format:
        {"vertices": [...], "edges": [...]}

        Vertices include both Concepts (domain-independent) and SkillNodes
        (filtered by domain). If user_id is provided, learner_state is overlaid.

        Args:
            skill_slug: Domain name (matches Domain.name).
            user_id: Optional user ID for learner state overlay.

        Returns:
            Dict with "vertices" and "edges" keys.
        """
        session = await self._get_session()
        try:
            # Look up domain
            domain_result = await session.execute(
                select(Domain).where(Domain.name == skill_slug)
            )
            domain = domain_result.scalar_one_or_none()

            vertices = []
            vertex_ids = set()

            # Load skill nodes for this domain
            if domain is not None:
                skill_result = await session.execute(
                    select(SkillNode).where(SkillNode.domain_id == domain.id)
                )
                for sn in skill_result.scalars().all():
                    vertex = {
                        "id": sn.id,
                        "label": "Skill",
                        "name": sn.name,
                        "description": sn.description,
                        "component_type": sn.component_type,
                        "bloom_level": sn.bloom_level,
                        "frequency_score": sn.frequency_score,
                        "impact_score": sn.impact_score,
                        "field_freshness": sn.field_freshness,
                        "version": sn.version,
                    }
                    vertices.append(vertex)
                    vertex_ids.add(sn.id)

            # Load concepts that are connected to these skill nodes via EMBODIES edges
            if vertex_ids:
                embodies_result = await session.execute(
                    select(GraphEdge).where(
                        GraphEdge.edge_type == "EMBODIES",
                        GraphEdge.from_node_id.in_(vertex_ids),
                    )
                )
                concept_ids = {e.to_node_id for e in embodies_result.scalars().all()}

                # Also load concepts connected via GENERALIZES to those concepts
                if concept_ids:
                    gen_result = await session.execute(
                        select(GraphEdge).where(
                            GraphEdge.edge_type == "GENERALIZES",
                            GraphEdge.from_node_id.in_(concept_ids) | GraphEdge.to_node_id.in_(concept_ids),
                        )
                    )
                    for e in gen_result.scalars().all():
                        concept_ids.add(e.from_node_id)
                        concept_ids.add(e.to_node_id)

                if concept_ids:
                    concept_result = await session.execute(
                        select(Concept).where(Concept.id.in_(concept_ids))
                    )
                    for c in concept_result.scalars().all():
                        vertex = {
                            "id": c.id,
                            "label": "Concept",
                            "name": c.name,
                            "description": c.description,
                            "abstraction_level": c.abstraction_level,
                            "bloom_level": c.bloom_level,
                            "field_freshness": c.field_freshness,
                            "version": c.version,
                        }
                        vertices.append(vertex)
                        vertex_ids.add(c.id)

            # Load edges between all collected nodes
            edges = []
            if vertex_ids:
                edge_result = await session.execute(
                    select(GraphEdge).where(
                        GraphEdge.from_node_id.in_(vertex_ids),
                        GraphEdge.to_node_id.in_(vertex_ids),
                    )
                )
                for e in edge_result.scalars().all():
                    edge = {
                        "from_id": e.from_node_id,
                        "to_id": e.to_node_id,
                        "edge_type": e.edge_type,
                        "strength": e.strength,
                        "description": e.description,
                    }
                    if e.prerequisite_type:
                        edge["prerequisite_type"] = e.prerequisite_type
                    if e.cosine_similarity is not None:
                        edge["cosine_similarity"] = e.cosine_similarity
                    if e.transfer_type:
                        edge["transfer_type"] = e.transfer_type
                    edges.append(edge)

            # Overlay learner state if user_id provided
            if user_id and vertex_ids:
                state_result = await session.execute(
                    select(LearnerState).where(
                        LearnerState.user_id == user_id,
                        LearnerState.node_id.in_(vertex_ids),
                    )
                )
                state_map = {s.node_id: s for s in state_result.scalars().all()}
                for vertex in vertices:
                    state = state_map.get(vertex["id"])
                    if state:
                        vertex["learner_state"] = {
                            "mastery_probability": state.mastery_probability,
                            "mastery_category": state.mastery_category,
                            "confidence": state.confidence,
                            "evidence_count": state.evidence_count,
                            "transfer_boost": state.transfer_boost,
                            "source": state.source,
                            "fsrs_difficulty": state.fsrs_difficulty,
                            "fsrs_stability": state.fsrs_stability,
                        }
                    else:
                        vertex["learner_state"] = {
                            "mastery_probability": 0.0,
                            "mastery_category": "not_started",
                            "confidence": 0.0,
                            "evidence_count": 0,
                            "transfer_boost": 0.0,
                            "source": "calibration",
                        }

            return {"vertices": vertices, "edges": edges}
        finally:
            await self._close_session(session)

    async def write_graph(self, skill_slug: str, graph: dict) -> None:
        """Write a knowledge graph to the database.

        Creates or updates Concepts, SkillNodes, and GraphEdges based on
        the vertices and edges in the graph dict. Uses the JSON schema format
        from knowledge-graph.schema.json.

        Vertex label determines model: "Concept" -> Concept, "Skill" -> SkillNode.

        Args:
            skill_slug: Domain name.
            graph: Dict with "vertices" and "edges" keys.
        """
        if not graph or (not graph.get("vertices") and not graph.get("edges")):
            return

        session = await self._get_session()
        try:
            # Ensure domain exists
            domain_result = await session.execute(
                select(Domain).where(Domain.name == skill_slug)
            )
            domain = domain_result.scalar_one_or_none()
            if domain is None:
                domain = Domain(name=skill_slug, skill_type="unknown", environment_type="unknown")
                session.add(domain)
                await session.commit()
                await session.refresh(domain)

            # Upsert vertices
            for v in graph.get("vertices", []):
                label = v.get("label", "Concept")
                if label == "Concept":
                    existing = await session.execute(
                        select(Concept).where(Concept.id == v["id"])
                    )
                    concept = existing.scalar_one_or_none()
                    if concept is None:
                        concept = Concept(
                            id=v["id"],
                            name=v["name"],
                            description=v.get("description", ""),
                            abstraction_level=v.get("abstraction_level", "concrete"),
                            bloom_level=v.get("bloom_level", v.get("blooms_level", "remember")),
                            field_freshness=v.get("field_freshness", "stable"),
                        )
                        session.add(concept)
                    else:
                        concept.name = v["name"]
                        concept.description = v.get("description", concept.description)
                        concept.version += 1
                else:  # Skill
                    existing = await session.execute(
                        select(SkillNode).where(SkillNode.id == v["id"])
                    )
                    skill = existing.scalar_one_or_none()
                    if skill is None:
                        skill = SkillNode(
                            id=v["id"],
                            name=v["name"],
                            domain_id=domain.id,
                            description=v.get("description", ""),
                            component_type=v.get("component_type", "non_recurrent"),
                            bloom_level=v.get("bloom_level", v.get("blooms_level", "remember")),
                            frequency_score=v.get("frequency_score", 0.0),
                            impact_score=v.get("impact_score", 0.0),
                            field_freshness=v.get("field_freshness", "stable"),
                        )
                        session.add(skill)
                    else:
                        skill.name = v["name"]
                        skill.description = v.get("description", skill.description)
                        skill.version += 1

            await session.commit()

            # Upsert edges
            for e in graph.get("edges", []):
                edge_type = e.get("edge_type", e.get("label", "PREREQUISITE"))
                from_id = e["from_id"]
                to_id = e["to_id"]

                # Determine node types from vertex list
                vertex_map = {v["id"]: v for v in graph.get("vertices", [])}
                from_label = vertex_map.get(from_id, {}).get("label", "Concept")
                to_label = vertex_map.get(to_id, {}).get("label", "Concept")
                from_type = "concept" if from_label == "Concept" else "skill_node"
                to_type = "concept" if to_label == "Concept" else "skill_node"

                # Check for existing edge
                existing_edge = await session.execute(
                    select(GraphEdge).where(
                        GraphEdge.from_node_id == from_id,
                        GraphEdge.to_node_id == to_id,
                        GraphEdge.edge_type == edge_type,
                    )
                )
                edge = existing_edge.scalar_one_or_none()
                if edge is None:
                    edge = GraphEdge(
                        from_node_id=from_id,
                        from_node_type=from_type,
                        to_node_id=to_id,
                        to_node_type=to_type,
                        edge_type=edge_type,
                        strength=e.get("strength", 1.0),
                        prerequisite_type=e.get("prerequisite_type"),
                        cosine_similarity=e.get("cosine_similarity"),
                        transfer_type=e.get("transfer_type"),
                        description=e.get("description", ""),
                    )
                    session.add(edge)
                else:
                    edge.strength = e.get("strength", edge.strength)
                    edge.description = e.get("description", edge.description)
                    edge.version += 1

            await session.commit()
        finally:
            await self._close_session(session)

    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]:
        """Query for transfer matches using PGVector cosine similarity.

        Delegates to app.graph.embeddings.execute_cosine_search for the actual query.

        Args:
            embeddings: Query embedding vector (1536 dimensions).

        Returns:
            List of TransferMatch objects for matches above 0.70 cosine similarity.
        """
        session = await self._get_session()
        try:
            # Import here to avoid circular dependency
            from app.graph.embeddings import execute_cosine_search
            from app.graph.transfer import classify_transfer

            results = await execute_cosine_search(
                session, embeddings, table="concepts",
                node_type="concept", min_similarity=0.70,
            )
            return [
                TransferMatch(
                    node_id=r.node_id,
                    node_type=r.node_type,
                    name=r.name,
                    cosine=r.cosine_similarity,
                    transfer_type=classify_transfer(r.cosine_similarity).value,
                )
                for r in results
            ]
        finally:
            await self._close_session(session)

    async def export_json(self, skill_slug: str, user_id: str | None = None) -> dict:
        """Export the full knowledge graph as a JSON-serializable dict.

        Produces a format compatible with the knowledge-graph.schema.json,
        including gap_analysis summary.

        Args:
            skill_slug: Domain name.
            user_id: Optional user ID for learner state overlay.

        Returns:
            Dict with "vertices", "edges", and "gap_analysis" keys.
        """
        graph = await self.read_graph(skill_slug, user_id=user_id)

        # Compute gap analysis
        vertices = graph.get("vertices", [])
        total = len(vertices)
        coverage = {"mastered": 0, "proficient": 0, "familiar": 0, "attempted": 0, "not_started": 0}

        for v in vertices:
            ls = v.get("learner_state", {})
            cat = ls.get("mastery_category", "not_started")
            if cat in coverage:
                coverage[cat] += 1
            else:
                coverage["not_started"] += 1

        # Weighted coverage percentage
        weighted_sum = 0.0
        weight_total = 0.0
        for v in vertices:
            impact = v.get("impact_score", 0.5)
            mastery = v.get("learner_state", {}).get("mastery_probability", 0.0)
            weighted_sum += mastery * impact
            weight_total += impact

        coverage_pct = (weighted_sum / weight_total * 100) if weight_total > 0 else 0.0

        graph["gap_analysis"] = {
            "total_vertices": total,
            "coverage_summary": {
                **coverage,
                "coverage_percentage": round(coverage_pct, 1),
            },
            "priority_gaps": [],
            "effective_scope_estimate": f"{total - coverage['mastered'] - coverage['proficient']} nodes remaining",
        }

        return graph

    async def import_json(self, skill_slug: str, data: dict) -> None:
        """Import a knowledge graph from JSON format.

        Delegates to write_graph for the actual upsert logic.

        Args:
            skill_slug: Domain name.
            data: Dict with "vertices" and "edges" keys.
        """
        await self.write_graph(skill_slug, data)
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_backends/test_postgres_backend.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: PostgresBackend full implementation — read/write graph, export/import, learner state overlay"
```

---

### Task 7: Backup/Restore Routes

**Files:**
- Create: `learn-anything-app/app/routes/backup.py`
- Create: `learn-anything-app/templates/settings/backup.html`
- Create: `learn-anything-app/tests/integration/test_routes/test_backup.py`

- [ ] **Step 1: Write failing tests for backup/restore routes**

```python
# tests/integration/test_routes/test_backup.py
import pytest
import json
import io
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_backup_page_renders(client):
    resp = await client.get("/settings/backup")
    assert resp.status_code == 200
    assert "backup" in resp.text.lower() or "Backup" in resp.text


@pytest.mark.asyncio
async def test_backup_export_json(client):
    resp = await client.get("/settings/backup/export?format=json")
    assert resp.status_code == 200
    assert resp.headers.get("content-type") in (
        "application/json",
        "application/json; charset=utf-8",
        "application/octet-stream",
    )


@pytest.mark.asyncio
async def test_restore_rejects_empty_upload(client):
    resp = await client.post("/settings/backup/restore")
    assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_restore_accepts_json(client):
    backup_data = json.dumps({
        "version": "0.2.0",
        "backend": "json",
        "skills": {},
    }).encode()
    resp = await client.post(
        "/settings/backup/restore",
        files={"backup_file": ("backup.json", io.BytesIO(backup_data), "application/json")},
    )
    assert resp.status_code in (200, 303)
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_backup.py -v`
Expected: FAIL — routes don't exist

- [ ] **Step 3: Implement backup/restore routes**

```python
# app/routes/backup.py
"""Backup and restore routes at /settings/backup and /settings/restore.

PG backend: exports all skill graphs as JSON (via PostgresBackend.export_json).
JSON backend: exports state directory as JSON bundle.

Restore: accepts JSON upload and imports via StateBackend.import_json.

Requires admin auth — dependency added in auth middleware.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from app.templating import templates
from app.config import settings
from app.security.sessions import require_admin  # Requires admin auth — dependency added in auth middleware

router = APIRouter(
    prefix="/settings/backup",
    tags=["backup"],
    dependencies=[Depends(require_admin)],
)


def _get_backend():
    """Get the active state backend instance.

    Returns JSONFileBackend or PostgresBackend depending on config.
    """
    if settings.state_backend == "postgres":
        from app.database import SessionLocal
        from app.backends.postgres import PostgresBackend
        return PostgresBackend(session_factory=SessionLocal)
    else:
        from app.backends.json_file import JSONFileBackend
        return JSONFileBackend(settings.json_state_dir)


@router.get("")
async def backup_page(request: Request):
    """Render the backup/restore settings page."""
    return templates.TemplateResponse(request, "settings/backup.html", {
        "backend": settings.state_backend,
    })


@router.get("/export")
async def export_backup(request: Request, format: str = "json"):
    """Export all skill data as a downloadable JSON file.

    Query params:
        format: "json" (default). Future: "sql" for pg_dump.
    """
    backend = _get_backend()

    if format == "json":
        # Collect all skill graphs
        # For JSON backend, iterate state directory
        # For PG backend, query all domains
        export_data = {
            "version": "0.2.0",
            "backend": settings.state_backend,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "skills": {},
        }

        if settings.state_backend == "json":
            from pathlib import Path
            state_dir = Path(settings.json_state_dir)
            if state_dir.exists():
                for skill_dir in state_dir.iterdir():
                    if skill_dir.is_dir():
                        graph = await backend.read_graph(skill_dir.name)
                        if graph:
                            export_data["skills"][skill_dir.name] = graph
        else:
            # PG backend: query all domains
            from app.database import SessionLocal
            from app.models.graph_nodes import Domain
            from sqlalchemy import select
            async with SessionLocal() as session:
                result = await session.execute(select(Domain))
                domains = result.scalars().all()
                for domain in domains:
                    graph = await backend.export_json(domain.name)
                    export_data["skills"][domain.name] = graph

        content = json.dumps(export_data, indent=2, default=str)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"learn-anything-backup-{timestamp}.json"

        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.post("/restore")
async def restore_backup(
    request: Request,
    backup_file: UploadFile | None = File(None),
):
    """Restore from a backup file upload.

    Accepts a JSON backup file and imports each skill graph.
    """
    if backup_file is None:
        raise HTTPException(status_code=400, detail="No backup file provided")

    try:
        content = await backup_file.read()
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid backup file: {exc}")

    backend = _get_backend()

    # Import each skill
    skills = data.get("skills", {})
    imported_count = 0
    for skill_slug, graph_data in skills.items():
        await backend.import_json(skill_slug, graph_data)
        imported_count += 1

    return JSONResponse({
        "status": "restored",
        "skills_imported": imported_count,
        "source_backend": data.get("backend", "unknown"),
    })
```

- [ ] **Step 4: Create backup template**

```html
<!-- templates/settings/backup.html -->
{% extends "base.html" %}
{% block title %}Backup & Restore — Learn Anything{% endblock %}
{% block content %}
<div class="setup-container">
  <h1>Backup & Restore</h1>
  <p class="subtitle">Export your learning data or restore from a previous backup.</p>

  <div style="margin-top: 32px;">
    <h2>Export</h2>
    <p class="hint">Download all skill graphs, learner states, and materials metadata as JSON.</p>
    <p class="hint">Current backend: <code>{{ backend }}</code></p>
    <a href="/settings/backup/export?format=json" class="export-btn">
      <button type="button">Download Backup (JSON)</button>
    </a>
  </div>

  <div style="margin-top: 40px;">
    <h2>Restore</h2>
    <p class="hint">Upload a previously exported backup file to restore your data.</p>
    <form method="post" action="/settings/backup/restore" enctype="multipart/form-data">
      <label>Backup File</label>
      <input name="backup_file" type="file" accept=".json" required>
      <button type="submit">Restore from Backup</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Register backup router in main.py**

Add to `app/main.py`:
```python
from app.routes.backup import router as backup_router
app.include_router(backup_router)
```

- [ ] **Step 6: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_backup.py -v`
Expected: PASS (4 tests)

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: backup/restore routes — JSON export/import at /settings/backup"
```

---

### Task 8: AGE Graph Sync — Populate AGE from SQLAlchemy Models

**Files:**
- Modify: `learn-anything-app/app/graph/age_queries.py` (add sync functions)
- Create: `learn-anything-app/tests/integration/test_graph/test_age_sync.py`

The AGE graph is a secondary index — the SQLAlchemy models are the source of truth. We need functions that sync data from the relational tables into AGE vertex/edge labels so that Cypher queries work.

- [ ] **Step 1: Write failing tests for AGE sync**

```python
# tests/integration/test_graph/test_age_sync.py
import pytest
from unittest.mock import AsyncMock, call
from app.graph.age_queries import (
    build_upsert_vertex_cypher,
    build_upsert_edge_cypher,
    build_sync_domain_queries,
)


def test_build_upsert_vertex_cypher_concept():
    cypher = build_upsert_vertex_cypher(
        graph_name="learn_graph",
        label="Concept",
        node_id="c-123",
        properties={"name": "Intervals", "bloom_level": "understand"},
    )
    assert "learn_graph" in cypher
    assert "Concept" in cypher
    assert "c-123" in cypher
    assert "Intervals" in cypher


def test_build_upsert_vertex_cypher_skill():
    cypher = build_upsert_vertex_cypher(
        graph_name="learn_graph",
        label="SkillNode",
        node_id="s-456",
        properties={"name": "Voicings", "domain": "jazz-piano"},
    )
    assert "SkillNode" in cypher
    assert "s-456" in cypher
    assert "Voicings" in cypher
    assert "jazz-piano" in cypher


def test_build_upsert_edge_cypher():
    cypher = build_upsert_edge_cypher(
        graph_name="learn_graph",
        from_id="s-456",
        to_id="c-123",
        edge_label="EMBODIES",
        properties={"strength": 0.9},
    )
    assert "learn_graph" in cypher
    assert "s-456" in cypher
    assert "c-123" in cypher
    assert "EMBODIES" in cypher
    assert "0.9" in cypher


def test_build_sync_domain_queries():
    vertices = [
        {"id": "c1", "label": "Concept", "name": "A", "bloom_level": "remember"},
        {"id": "s1", "label": "Skill", "name": "B", "domain": "test", "bloom_level": "apply"},
    ]
    edges = [
        {"from_id": "s1", "to_id": "c1", "edge_type": "EMBODIES", "strength": 0.8},
    ]
    queries = build_sync_domain_queries("learn_graph", vertices, edges)
    # Should produce one query per vertex + one per edge
    assert len(queries) == 3
    assert any("Concept" in q for q in queries)
    assert any("EMBODIES" in q for q in queries)
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_age_sync.py -v`
Expected: FAIL — functions don't exist

- [ ] **Step 3: Add sync functions to age_queries.py**

Append to `app/graph/age_queries.py`:

```python
# --- AGE sync (relational -> graph) ---

def _escape_age_string(s: str) -> str:
    """Escape a string for use in AGE Cypher property values."""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


def build_upsert_vertex_cypher(
    graph_name: str,
    label: str,
    node_id: str,
    properties: dict,
) -> str:
    """Build a DELETE+CREATE Cypher query to upsert a vertex in AGE.

    AGE does not reliably support MERGE...SET. Since relational tables
    are the source of truth, we use a DELETE+CREATE pattern: delete any
    existing vertex with this id, then create a fresh one with all properties.

    Args:
        graph_name: AGE graph name.
        label: Vertex label (Concept, SkillNode, Reference, Material).
        node_id: The node's UUID.
        properties: Dict of property key-value pairs to set.

    Returns:
        List of SQL strings: first deletes existing vertex, then creates new one.
        Returned as a single semicolon-joined string for sequential execution.
    """
    escaped_id = _escape_age_string(node_id)

    # Build property map for CREATE
    prop_parts = [f"id: '{escaped_id}'"]
    for key, value in properties.items():
        if isinstance(value, str):
            prop_parts.append(f"{key}: '{_escape_age_string(value)}'")
        elif isinstance(value, (int, float)):
            prop_parts.append(f"{key}: {value}")
        elif value is None:
            continue
        else:
            prop_parts.append(f"{key}: '{_escape_age_string(str(value))}'")
    prop_str = ", ".join(prop_parts)

    # Delete existing vertex (OPTIONAL MATCH so it doesn't fail if absent)
    delete_cypher = (
        f"MATCH (n:{label} {{id: '{escaped_id}'}}) "
        f"DETACH DELETE n"
    )
    delete_sql = _cypher_wrapper(graph_name, delete_cypher, "v agtype")

    # Create fresh vertex with all properties
    create_cypher = f"CREATE (n:{label} {{{prop_str}}}) RETURN n"
    create_sql = _cypher_wrapper(graph_name, create_cypher, "v agtype")

    return f"{delete_sql}; {create_sql}"


def build_upsert_edge_cypher(
    graph_name: str,
    from_id: str,
    to_id: str,
    edge_label: str,
    properties: dict | None = None,
) -> str:
    """Build a DELETE+CREATE Cypher query to upsert an edge in AGE.

    AGE does not reliably support MERGE...SET. Since relational tables
    are the source of truth, we delete any existing edge of the same type
    between these nodes, then create a fresh one with properties.

    Args:
        graph_name: AGE graph name.
        from_id: Source node UUID.
        to_id: Target node UUID.
        edge_label: Edge label (PREREQUISITE, EMBODIES, etc.).
        properties: Optional dict of edge properties.

    Returns:
        Semicolon-joined SQL strings: first deletes existing edge, then creates new one.
    """
    escaped_from = _escape_age_string(from_id)
    escaped_to = _escape_age_string(to_id)

    prop_str = ""
    if properties:
        parts = []
        for key, value in properties.items():
            if isinstance(value, str):
                parts.append(f"{key}: '{_escape_age_string(value)}'")
            elif isinstance(value, (int, float)):
                parts.append(f"{key}: {value}")
            elif value is not None:
                parts.append(f"{key}: '{_escape_age_string(str(value))}'")
        if parts:
            prop_str = " {" + ", ".join(parts) + "}"

    # Delete existing edge of same type between these nodes
    delete_cypher = (
        f"MATCH (a {{id: '{escaped_from}'}})-[r:{edge_label}]->(b {{id: '{escaped_to}'}}) "
        f"DELETE r"
    )
    delete_sql = _cypher_wrapper(graph_name, delete_cypher, "r agtype")

    # Create fresh edge with properties
    create_cypher = (
        f"MATCH (a {{id: '{escaped_from}'}}), (b {{id: '{escaped_to}'}}) "
        f"CREATE (a)-[r:{edge_label}{prop_str}]->(b) "
        f"RETURN r"
    )
    create_sql = _cypher_wrapper(graph_name, create_cypher, "r agtype")

    return f"{delete_sql}; {create_sql}"


def build_sync_domain_queries(
    graph_name: str,
    vertices: list[dict],
    edges: list[dict],
) -> list[str]:
    """Build all Cypher queries to sync a domain's graph data into AGE.

    Takes the same vertex/edge format as PostgresBackend.read_graph output.

    Args:
        graph_name: AGE graph name.
        vertices: List of vertex dicts with "id", "label", "name", etc.
        edges: List of edge dicts with "from_id", "to_id", "edge_type", etc.

    Returns:
        List of SQL strings (one per vertex + one per edge).
    """
    queries = []

    for v in vertices:
        label = v.get("label", "Concept")
        # Map "Skill" label to "SkillNode" for AGE
        age_label = "SkillNode" if label == "Skill" else label
        props = {k: v[k] for k in v if k not in ("id", "label", "learner_state")}
        queries.append(
            build_upsert_vertex_cypher(graph_name, age_label, v["id"], props)
        )

    for e in edges:
        edge_label = e.get("edge_type", e.get("label", "PREREQUISITE"))
        props = {k: e[k] for k in e if k not in ("from_id", "to_id", "edge_type", "label")}
        queries.append(
            build_upsert_edge_cypher(graph_name, e["from_id"], e["to_id"], edge_label, props)
        )

    return queries
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_age_sync.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: AGE graph sync — upsert vertices and edges from relational models to Cypher"
```

---

### Task 9: Integration — Backend + Graph Modules Wired Together

**Files:**
- Modify: `learn-anything-app/app/backends/postgres.py` (add AGE sync on write)
- Create: `learn-anything-app/tests/integration/test_graph/test_integration.py`

- [ ] **Step 1: Write integration tests**

```python
# tests/integration/test_graph/test_integration.py
"""Integration tests verifying the full pipeline:
1. Write graph via PostgresBackend
2. Read graph back
3. Compute layout
4. Export/import roundtrip
"""
import pytest
from app.backends.postgres import PostgresBackend
from app.graph.layout import compute_layout, LayoutAlgorithm, compute_node_sizes
from app.graph.transfer import classify_transfer, TransferClassification
from app.models.graph_nodes import Domain


@pytest.fixture
async def setup_db(db):
    domain = Domain(name="integration-test", skill_type="cognitive", environment_type="kind")
    db.add(domain)
    await db.commit()
    return db


@pytest.fixture
def backend(setup_db):
    return PostgresBackend(session=setup_db)


SAMPLE_GRAPH = {
    "vertices": [
        {"id": "c1", "label": "Concept", "name": "Variables", "description": "Named storage", "abstraction_level": "concrete", "bloom_level": "remember"},
        {"id": "c2", "label": "Concept", "name": "Functions", "description": "Callable units", "abstraction_level": "abstract", "bloom_level": "apply"},
        {"id": "c3", "label": "Concept", "name": "Closures", "description": "Functions with captured scope", "abstraction_level": "abstract", "bloom_level": "analyze"},
        {"id": "s1", "label": "Skill", "name": "Python Variables", "description": "Variable assignment in Python", "component_type": "non_recurrent", "bloom_level": "remember", "frequency_score": 0.95, "impact_score": 0.7},
        {"id": "s2", "label": "Skill", "name": "Python Functions", "description": "def, args, return", "component_type": "recurrent", "bloom_level": "apply", "frequency_score": 0.9, "impact_score": 0.85},
        {"id": "s3", "label": "Skill", "name": "Decorators", "description": "Function wrappers", "component_type": "recurrent", "bloom_level": "analyze", "frequency_score": 0.6, "impact_score": 0.75},
    ],
    "edges": [
        {"from_id": "s1", "to_id": "s2", "edge_type": "PREREQUISITE", "strength": 0.95, "prerequisite_type": "hard", "description": "Must know variables before functions"},
        {"from_id": "s2", "to_id": "s3", "edge_type": "PREREQUISITE", "strength": 0.9, "prerequisite_type": "hard", "description": "Functions before decorators"},
        {"from_id": "s1", "to_id": "c1", "edge_type": "EMBODIES", "strength": 0.9, "description": "Python vars embody variable concept"},
        {"from_id": "s2", "to_id": "c2", "edge_type": "EMBODIES", "strength": 0.85, "description": "Python funcs embody function concept"},
        {"from_id": "s3", "to_id": "c3", "edge_type": "EMBODIES", "strength": 0.8, "description": "Decorators embody closure concept"},
        {"from_id": "c1", "to_id": "c2", "edge_type": "GENERALIZES", "strength": 1.0, "description": "Variables generalize to functions"},
        {"from_id": "c2", "to_id": "c3", "edge_type": "GENERALIZES", "strength": 1.0, "description": "Functions generalize to closures"},
    ],
}


@pytest.mark.asyncio
async def test_write_read_roundtrip(backend):
    await backend.write_graph("integration-test", SAMPLE_GRAPH)
    result = await backend.read_graph("integration-test")
    assert len(result["vertices"]) == 6
    assert len(result["edges"]) == 7

    names = {v["name"] for v in result["vertices"]}
    assert "Variables" in names
    assert "Decorators" in names


@pytest.mark.asyncio
async def test_layout_on_read_graph(backend):
    await backend.write_graph("integration-test", SAMPLE_GRAPH)
    result = await backend.read_graph("integration-test")

    positions = compute_layout(
        result["vertices"], result["edges"],
        algorithm=LayoutAlgorithm.HIERARCHICAL,
    )
    assert len(positions) == 6

    sizes = compute_node_sizes(result["vertices"])
    assert len(sizes) == 6


@pytest.mark.asyncio
async def test_export_import_roundtrip(backend, setup_db):
    await backend.write_graph("integration-test", SAMPLE_GRAPH)
    exported = await backend.export_json("integration-test")

    assert "gap_analysis" in exported
    assert exported["gap_analysis"]["total_vertices"] == 6

    # Import into a new domain
    new_domain = Domain(name="roundtrip-target", skill_type="cognitive", environment_type="kind")
    setup_db.add(new_domain)
    await setup_db.commit()

    await backend.import_json("roundtrip-target", exported)
    reimported = await backend.read_graph("roundtrip-target")
    assert len(reimported["vertices"]) == 6
    assert len(reimported["edges"]) == 7


def test_transfer_classification_thresholds():
    """Verify transfer classification at exact boundary values."""
    assert classify_transfer(1.0) == TransferClassification.NEAR
    assert classify_transfer(0.85) == TransferClassification.MODERATE  # Boundary: >0.85 is NEAR per spec
    assert classify_transfer(0.849) == TransferClassification.MODERATE
    assert classify_transfer(0.70) == TransferClassification.MODERATE
    assert classify_transfer(0.699) == TransferClassification.INDEPENDENT
    assert classify_transfer(0.0) == TransferClassification.INDEPENDENT
```

- [ ] **Step 2: Add AGE sync call to PostgresBackend.write_graph**

Add to the end of the `write_graph` method in `app/backends/postgres.py`, just before the `finally` block:

```python
            # Build AGE sync queries (for execution when AGE is available)
            # Store queries for deferred execution — AGE sync is best-effort
            try:
                from app.graph.age_queries import build_sync_domain_queries
                graph_data = await self.read_graph(skill_slug)
                self._pending_age_sync = build_sync_domain_queries(
                    "learn_graph",
                    graph_data.get("vertices", []),
                    graph_data.get("edges", []),
                )
            except Exception:
                # AGE sync is non-critical — don't fail the write
                self._pending_age_sync = []
```

- [ ] **Step 3: Run integration tests**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_graph/test_integration.py -v`
Expected: PASS (4 tests)

- [ ] **Step 4: Run full test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`
Expected: All tests pass. Count should be ~45+ tests:
- Plan 1 tests (~20)
- AGE queries (8)
- AGE sync (4)
- Embeddings (6)
- Transfer (11)
- Layout (7)
- PostgresBackend (8)
- Backup routes (4)
- Integration (4)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: integration tests — write/read/layout/export/import pipeline verified end-to-end"
```

---

### Task 10: Docker Verification + Final Polish

**Files:**
- Modify: `learn-anything-app/docker-compose.yml` (verify PGVector + AGE init)
- Modify: `learn-anything-app/app/routes/__init__.py` (register backup router)

- [ ] **Step 1: Verify init-extensions.sql includes AGE graph creation**

Update `docker/postgres/init-extensions.sql` to also load AGE and create the default graph:

```sql
-- docker/postgres/init-extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
SELECT ag_catalog.create_graph('learn_graph');
SELECT ag_catalog.create_vlabel('learn_graph', 'Concept');
SELECT ag_catalog.create_vlabel('learn_graph', 'SkillNode');
SELECT ag_catalog.create_vlabel('learn_graph', 'Reference');
SELECT ag_catalog.create_vlabel('learn_graph', 'Material');
SELECT ag_catalog.create_elabel('learn_graph', 'PREREQUISITE');
SELECT ag_catalog.create_elabel('learn_graph', 'PREREQUISITE_MATERIAL');
SELECT ag_catalog.create_elabel('learn_graph', 'EMBODIES');
SELECT ag_catalog.create_elabel('learn_graph', 'SIMILAR_TO');
SELECT ag_catalog.create_elabel('learn_graph', 'GENERALIZES');
SELECT ag_catalog.create_elabel('learn_graph', 'REINFORCES');
SELECT ag_catalog.create_elabel('learn_graph', 'NEGATIVE_TRANSFER');
SELECT ag_catalog.create_elabel('learn_graph', 'SOURCED_FROM');
SELECT ag_catalog.create_elabel('learn_graph', 'TEACHES');
SELECT ag_catalog.create_elabel('learn_graph', 'CITES');
```

- [ ] **Step 2: Verify all route routers are registered in main.py**

Ensure `app/main.py` includes:

```python
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.setup import router as setup_router
from app.routes.backup import router as backup_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(setup_router)
app.include_router(backup_router)
```

- [ ] **Step 3: Test Docker Compose build**

Run: `cd learn-anything-app && docker compose build`
Expected: Both images build successfully with networkx included.

- [ ] **Step 4: Test Docker Compose up**

```bash
cd learn-anything-app
docker compose up -d && sleep 15
curl -s http://localhost:8000/health | python -m json.tool
# Expected: {"status": "ok", "version": "0.2.0", "state_backend": "postgres", "setup_complete": false}
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/settings/backup
# Expected: 200 (or 307 redirect to /setup if guard middleware catches it)
docker compose down
```

- [ ] **Step 5: Run final test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: Plan 2 complete — knowledge graph engine with AGE, PGVector, transfer detection, layout, backup/restore"
```
