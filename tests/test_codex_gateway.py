"""Structural integration checks; these do not run a Codex teaching session."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / ".agents/skills/learn-anything/SKILL.md"
PLUGIN = ROOT / "learn-anything-plugin"


class GatewayPackaging(unittest.TestCase):
    def test_repository_discovery_entrypoint_exists(self):
        self.assertTrue(GATEWAY.is_file(), "Codex repository discovery needs .agents/skills/learn-anything/SKILL.md")

    def test_canonical_skill_command_and_schema_targets_resolve(self):
        self.assertTrue(GATEWAY.is_file(), "Gateway is missing")
        body = GATEWAY.read_text()
        targets = {(GATEWAY.parent / link.split("#")[0]).resolve() for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body)}
        required = set((PLUGIN / "skills").glob("*/SKILL.md")) | set((PLUGIN / "commands").glob("*.md")) | {PLUGIN / "schemas"}
        self.assertTrue({p.resolve() for p in required} <= targets, "Gateway must reference the canonical instruction surfaces")
        for target in targets:
            self.assertTrue(target.is_relative_to(ROOT))
            self.assertTrue(target.exists(), target)
        for skill in (PLUGIN / "skills").glob("*/SKILL.md"):
            for reference in re.findall(r"`(references/[^`]+)`", skill.read_text()):
                self.assertTrue((skill.parent / reference).is_file(), f"Missing canonical reference {reference}")
        for schema in (PLUGIN / "schemas").glob("*.schema.json"):
            payload = json.loads(schema.read_text())
            self.assertIsInstance(payload, dict)
            self.assertIn("$schema", payload)


if __name__ == "__main__":
    unittest.main()
