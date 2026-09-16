"""Validate documentation-only contracts and synthetic examples; no network access."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent


def semantic_pack(pack: dict[str, Any]) -> None:
    """Check relationships that JSON Schema cannot check by itself."""
    nodes = pack["nodes"]
    ids = [node["id"] for node in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate node id")
    index = {node["id"]: node for node in nodes}
    if pack["entry_node"] not in index:
        raise ValueError("unknown entry node")
    asset_ids = [asset["id"] for asset in pack["assets"]]
    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("duplicate asset id")
    paths = [asset["path"] for asset in pack["assets"]]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate asset path")
    edges: dict[str, set[str]] = {}
    ends: set[str] = set()
    for node in nodes:
        if not set(node["asset_ids"]).issubset(asset_ids):
            raise ValueError("unknown asset reference")
        if node["kind"] == "choice":
            options = [option["id"] for option in node["options"]]
            if len(options) != len(set(options)) or node["answer_id"] not in options:
                raise ValueError("invalid choice option identity or answer")
            targets = {node[k] for k in ("next_correct", "next_incorrect", "next_unscored")}
        elif node["kind"] == "instruction":
            targets = {node["next"]}
        else:
            ends.add(node["id"])
            targets = set()
        if not targets.issubset(index):
            raise ValueError("unknown branch target")
        edges[node["id"]] = targets
    reached: set[str] = set()
    pending = [pack["entry_node"]]
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(edges[current] - reached)
    if reached != set(ids):
        raise ValueError("unreachable nodes")
    # Cycles are permitted for bounded retries, but each node needs an exit.
    can_finish = set(ends)
    while True:
        expanded = can_finish | {n for n, targets in edges.items() if targets & can_finish}
        if expanded == can_finish:
            break
        can_finish = expanded
    if can_finish != set(ids):
        raise ValueError("node has no terminal path")


def main() -> None:
    bundle = json.loads((HERE / "contracts.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(bundle)
    registry = Registry().with_resource(bundle["$id"], Resource.from_contents(bundle))
    validators: dict[str, Draft202012Validator] = {}
    for path in sorted(HERE.glob("*.schema.json")):
        if path.name == "contracts.schema.json":
            continue
        wrapper = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(wrapper)
        validators[wrapper["title"]] = Draft202012Validator(
            wrapper, registry=registry, format_checker=FormatChecker()
        )
    fixtures = json.loads((HERE / "examples.json").read_text(encoding="utf-8"))
    if set(fixtures) != set(validators):
        raise ValueError("fixture/schema coverage mismatch")

    def validate(name: str, data: dict[str, Any]) -> None:
        validators[name].validate(data)
        if name == "SessionPack":
            semantic_pack(data)

    for name, fixture in fixtures.items():
        validate(name, fixture)
    negatives = 0

    def reject(name: str, mutate: Any) -> None:
        nonlocal negatives
        bad = copy.deepcopy(fixtures[name])
        mutate(bad)
        try:
            validate(name, bad)
        except (ValueError, ValidationError):
            negatives += 1
        else:
            raise AssertionError(f"negative case unexpectedly accepted for {name}")

    for name in fixtures:
        reject(name, lambda d: d.update(schema_version="unsupported"))
        reject(name, lambda d: d.update(unrecognized_field=True))
    reject("CanonicalCompetency", lambda d: d.update(success_criteria=[]))
    reject("CanonicalCompetency", lambda d: d.update(source_refs=[]))
    reject("EvidenceEvent", lambda d: d.update(device_sequence=-1))
    reject("EvidenceEvent", lambda d: d.update(observed_at="not-a-timestamp"))
    reject("EvidenceEvent", lambda d: d.update(outcome={"status": "scored", "score": 2}))
    reject("EvidenceEvent", lambda d: d.update(outcome={"status": "unscored", "reason": "skipped", "score": 0}))
    reject("MotivationState", lambda d: d["affinities"][0].update(confidence=2))
    reject("MotivationState", lambda d: d["affinities"][0].update(evidence_ids=[]))
    reject("AuthoringIntent", lambda d: d.update(count=11))
    reject("AuthoringIntent", lambda d: d.update(approval_required=False))
    reject("AuthoringIntent", lambda d: d.update(stage="published"))
    reject("StoryBrief", lambda d: d.update(character_pack_ids=[]))
    reject("StoryBrief", lambda d: d.update(selection_status="automatic"))
    reject("SessionPack", lambda d: d.update(entry_node="missing"))
    reject("SessionPack", lambda d: d.update(max_transitions=0))
    reject("SessionPack", lambda d: d["nodes"][1].update(next_correct="missing"))
    reject("SessionPack", lambda d: d["nodes"][1].update(answer_id="missing"))
    reject("SessionPack", lambda d: d["nodes"][1]["options"][1].update(id="a"))
    reject("SessionPack", lambda d: d["nodes"][0].update(asset_ids=["missing"]))
    reject("SessionPack", lambda d: d["nodes"].append(copy.deepcopy(d["nodes"][0])))
    reject("SessionPack", lambda d: d["nodes"].append({"id":"unreachable", "kind":"end", "competency_ids":[], "asset_ids":[], "message":"End"}))
    reject("SessionPack", lambda d: d["nodes"][0].update(next="intro"))
    reject("SessionPack", lambda d: d["nodes"][1].update(kind="javascript"))
    reject("SessionPack", lambda d: d["assets"].append({"id":"bad","path":"../secret","media_type":"image/png","sha256":"0" * 64,"byte_length":1,"required_offline":True}))
    print(json.dumps({"scope":"documentation prototypes; not runtime or pedagogical validation", "schemas_checked":len(validators)+1,"positive_examples":len(fixtures),"negative_cases_rejected":negatives}, indent=2))


if __name__ == "__main__":
    main()
