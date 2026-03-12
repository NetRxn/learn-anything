#!/usr/bin/env python3
"""
generate_anki.py — Export SRS cards to Anki-compatible .apkg file.

Reads an srs-cards.json file (conforming to srs-cards.schema.json) and produces
an .apkg package importable by Anki. Supports basic, cloze, reversed, and
comparison card types, with optional inline SVG diagrams.

Key design decisions:
- Model and Deck IDs are hardcoded per the schema's anki_config. Changing them
  creates duplicates on re-import. If anki_config is absent, IDs are generated
  deterministically from the plan_id.
- Each note includes a hidden KnowledgeNodeID field linking back to the AGE
  graph vertex, enabling round-trip data flow (export -> Anki review -> import).
- GUIDs are deterministic via genanki.guid_for(card_id), so re-exporting the
  same card updates it in Anki rather than creating a duplicate.
- Cards with image_svg fields embed inline SVG directly in the HTML. No external
  media files needed — SVGs are self-contained in the card content.

Usage:
  python generate_anki.py srs-cards.json output.apkg
  python generate_anki.py srs-cards.json  # defaults to <plan_id>.apkg
"""

import json
import re
import sys
import hashlib
import genanki


def stable_id(seed: str) -> int:
    """Generate a stable integer ID from a string seed, in genanki's valid range."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:8], 16) % (1 << 30) + (1 << 30)


# --- Card Styling ---

CARD_CSS = """\
/* ── Theme-agnostic styling ──
   No color or background-color on .card — Anki provides theme-appropriate
   defaults. Semi-transparent overlays and currentColor adapt to any theme
   without needing .nightMode/.night_mode overrides. */
.card {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  max-width: 600px;
  margin: 0 auto;
  padding: 12px;
}
.card code {
  background: rgba(128, 128, 128, 0.15);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 14px;
}
.card pre {
  background: rgba(128, 128, 128, 0.15);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
}
/* ── Diagram "light box" ──
   SVGs contain hardcoded colors designed for a light background, so the
   diagram container forces a white background. This is intentional — the
   diagram is a self-contained visual element, not themed text. */
.card-diagram {
  text-align: center;
  margin: 14px 0;
  background: #ffffff;
  border-radius: 8px;
  padding: 8px;
}
.card-diagram svg {
  max-width: 100%;
  height: auto;
}
.card-meta {
  font-size: 10px;
  opacity: 0.5;
  margin-top: 14px;
  border-top: 1px solid rgba(128, 128, 128, 0.3);
  padding-top: 6px;
}
hr#answer {
  border: none;
  border-top: 1px solid rgba(128, 128, 128, 0.3);
  margin: 16px 0;
}
"""


# --- Anki Note Models ---


def make_basic_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Basic",
        css=CARD_CSS,
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "FrontDiagram"},
            {"name": "BackDiagram"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": (
                    '<div class="card">'
                    "{{Front}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    "</div>"
                ),
                "afmt": (
                    '<div class="card">'
                    "{{Front}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    '<hr id="answer">'
                    "{{Back}}"
                    '{{#BackDiagram}}<div class="card-diagram">{{BackDiagram}}</div>{{/BackDiagram}}'
                    '<div class="card-meta">{{BloomLevel}} &middot; {{KnowledgeType}}</div>'
                    "</div>"
                ),
            }
        ],
    )


def make_cloze_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Cloze",
        model_type=genanki.Model.CLOZE,
        css=CARD_CSS,
        fields=[
            {"name": "Text"},
            {"name": "Extra"},
            {"name": "FrontDiagram"},
            {"name": "BackDiagram"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[
            {
                "name": "Cloze",
                "qfmt": (
                    '<div class="card">'
                    "{{cloze:Text}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    "</div>"
                ),
                "afmt": (
                    '<div class="card">'
                    "{{cloze:Text}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    "<br>{{Extra}}"
                    '{{#BackDiagram}}<div class="card-diagram">{{BackDiagram}}</div>{{/BackDiagram}}'
                    '<div class="card-meta">{{BloomLevel}} &middot; {{KnowledgeType}}</div>'
                    "</div>"
                ),
            }
        ],
    )


def make_reversed_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Reversed",
        css=CARD_CSS,
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "FrontDiagram"},
            {"name": "BackDiagram"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[
            {
                "name": "Forward",
                "qfmt": (
                    '<div class="card">'
                    "{{Front}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    "</div>"
                ),
                "afmt": (
                    '<div class="card">'
                    "{{Front}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    '<hr id="answer">'
                    "{{Back}}"
                    '{{#BackDiagram}}<div class="card-diagram">{{BackDiagram}}</div>{{/BackDiagram}}'
                    "</div>"
                ),
            },
            {
                "name": "Reverse",
                "qfmt": (
                    '<div class="card">'
                    "{{Back}}"
                    '{{#BackDiagram}}<div class="card-diagram">{{BackDiagram}}</div>{{/BackDiagram}}'
                    "</div>"
                ),
                "afmt": (
                    '<div class="card">'
                    "{{Back}}"
                    '{{#BackDiagram}}<div class="card-diagram">{{BackDiagram}}</div>{{/BackDiagram}}'
                    '<hr id="answer">'
                    "{{Front}}"
                    '{{#FrontDiagram}}<div class="card-diagram">{{FrontDiagram}}</div>{{/FrontDiagram}}'
                    "</div>"
                ),
            },
        ],
    )


class MetaLearningNote(genanki.Note):
    """Note subclass that generates deterministic GUIDs from card_id."""

    def __init__(self, card_id: str, **kwargs):
        self._card_id = card_id
        super().__init__(**kwargs)

    @property
    def guid(self):
        return genanki.guid_for(self._card_id)


def sanitize_svg(svg: str, card_id: str = "") -> str:
    """Sanitize SVG content to prevent XSS via embedded scripts or event handlers.

    Removes <script> elements, on* event handler attributes, href/xlink:href
    attributes pointing to javascript: URIs, and <foreignObject> elements (which
    can embed arbitrary HTML). Logs a warning if anything is stripped.

    The SVG content is generated by the Forge itself, not user-supplied, so this
    is defense-in-depth against malicious edits to srs-cards.json.
    """
    original = svg

    # Remove <script>...</script> elements (including self-closing)
    svg = re.sub(
        r"<script[\s>].*?</script\s*>", "", svg, flags=re.DOTALL | re.IGNORECASE
    )
    svg = re.sub(r"<script\s*/>", "", svg, flags=re.IGNORECASE)

    # Remove on* event handler attributes (onload, onclick, onerror, etc.)
    svg = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', "", svg, flags=re.IGNORECASE)
    svg = re.sub(r"\s+on\w+\s*=\s*\S+", "", svg, flags=re.IGNORECASE)

    # Remove javascript: URIs in href and xlink:href
    svg = re.sub(
        r'((?:xlink:)?href\s*=\s*["\'])\s*javascript:[^"\']*(["\'])',
        r"\1#\2",
        svg,
        flags=re.IGNORECASE,
    )

    # Remove <foreignObject> elements (can embed arbitrary HTML/JS)
    svg = re.sub(
        r"<foreignObject[\s>].*?</foreignObject\s*>",
        "",
        svg,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if svg != original:
        label = f" in card {card_id}" if card_id else ""
        print(
            f"WARNING: Stripped potentially unsafe content from SVG{label}",
            file=sys.stderr,
        )

    return svg


def resolve_diagram_fields(card: dict) -> tuple[str, str]:
    """Extract SVG content into front/back diagram fields based on image_placement.

    SVG is sanitized to remove script injection vectors before embedding.
    Returns (front_diagram, back_diagram) tuple. Each is either a sanitized SVG
    string or empty string.
    """
    svg = card.get("image_svg", "")
    if not svg:
        return ("", "")

    svg = sanitize_svg(svg, card.get("card_id", ""))
    placement = card.get("image_placement", "back")

    if placement == "front":
        return (svg, "")
    elif placement == "both":
        return (svg, svg)
    else:  # "back" (default)
        return ("", svg)


def build_deck(deck_data: dict, models: dict) -> genanki.Deck:
    """Build a genanki Deck from a deck entry in srs-cards.json."""
    deck_name = deck_data["deck_name"]
    deck_id = stable_id(f"deck:{deck_name}")
    deck = genanki.Deck(deck_id, deck_name)

    for card in deck_data["cards"]:
        card_type = card["card_type"]
        card_id = card["card_id"]
        component_id = card["component_id"]
        bloom = card.get("bloom_level", "")
        ktype = card.get("knowledge_type", "")
        tags_str = ", ".join(card.get("topic_tags", []))
        anki_tags = [t.replace("::", "_") for t in card.get("topic_tags", [])]

        front_diagram, back_diagram = resolve_diagram_fields(card)

        if card_type == "cloze":
            model = models["cloze"]
            note = MetaLearningNote(
                card_id=card_id,
                model=model,
                fields=[
                    card["front"],  # Text (with {{c1::...}} syntax)
                    card.get("back", ""),  # Extra
                    front_diagram,  # FrontDiagram
                    back_diagram,  # BackDiagram
                    component_id,
                    card_id,
                    bloom,
                    ktype,
                    tags_str,
                ],
                tags=anki_tags,
            )
        elif card_type == "reversed":
            model = models["reversed"]
            note = MetaLearningNote(
                card_id=card_id,
                model=model,
                fields=[
                    card["front"],
                    card["back"],
                    front_diagram,
                    back_diagram,
                    component_id,
                    card_id,
                    bloom,
                    ktype,
                    tags_str,
                ],
                tags=anki_tags,
            )
        else:
            # basic, open_ended, comparison all use the basic model
            model = models["basic"]
            note = MetaLearningNote(
                card_id=card_id,
                model=model,
                fields=[
                    card["front"],
                    card["back"],
                    front_diagram,
                    back_diagram,
                    component_id,
                    card_id,
                    bloom,
                    ktype,
                    tags_str,
                ],
                tags=anki_tags,
            )

        deck.add_note(note)

    return deck


def generate_apkg(srs_cards_path: str, output_path: str = None):
    """Main export function. Reads srs-cards.json, writes .apkg."""
    with open(srs_cards_path, "r") as f:
        data = json.load(f)

    plan_id = data.get("plan_id", "default")

    # Resolve model IDs — use anki_config if present, otherwise generate deterministically
    anki_config = data.get("anki_config", {})
    basic_model_id = anki_config.get(
        "model_id_basic", stable_id(f"model:basic:{plan_id}")
    )
    cloze_model_id = anki_config.get(
        "model_id_cloze", stable_id(f"model:cloze:{plan_id}")
    )
    reversed_model_id = anki_config.get(
        "model_id_reversed", stable_id(f"model:reversed:{plan_id}")
    )

    models = {
        "basic": make_basic_model(basic_model_id),
        "cloze": make_cloze_model(cloze_model_id),
        "reversed": make_reversed_model(reversed_model_id),
    }

    # Build all decks
    decks = []
    visual_count = 0
    for deck_data in data.get("decks", []):
        deck = build_deck(deck_data, models)
        decks.append(deck)
        # Count visual cards for summary
        for card in deck_data.get("cards", []):
            if card.get("image_svg"):
                visual_count += 1

    if not decks:
        print("No decks found in input file.")
        sys.exit(1)

    # Determine output path
    if output_path is None:
        output_path = f"{plan_id}.apkg"

    # Write package
    package = genanki.Package(decks)
    package.write_to_file(output_path)

    # Summary
    total_cards = sum(len(d.get("cards", [])) for d in data.get("decks", []))
    visual_note = f" ({visual_count} with diagrams)" if visual_count else ""
    print(
        f"Exported {total_cards} cards{visual_note} across {len(decks)} deck(s) to {output_path}"
    )

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_anki.py <srs-cards.json> [output.apkg]")
        sys.exit(1)

    srs_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    generate_apkg(srs_path, out_path)
