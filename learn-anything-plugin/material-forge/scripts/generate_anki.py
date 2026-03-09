#!/usr/bin/env python3
"""
generate_anki.py — Export SRS cards to Anki-compatible .apkg file.

Reads an srs-cards.json file (conforming to srs-cards.schema.json) and produces
an .apkg package importable by Anki. Supports basic, cloze, reversed, and
comparison card types.

Key design decisions:
- Model and Deck IDs are hardcoded per the schema's anki_config. Changing them
  creates duplicates on re-import. If anki_config is absent, IDs are generated
  deterministically from the plan_id.
- Each note includes a hidden KnowledgeNodeID field linking back to the AGE
  graph vertex, enabling round-trip data flow (export -> Anki review -> import).
- GUIDs are deterministic via genanki.guid_for(card_id), so re-exporting the
  same card updates it in Anki rather than creating a duplicate.

Usage:
  python generate_anki.py srs-cards.json output.apkg
  python generate_anki.py srs-cards.json  # defaults to <plan_id>.apkg
"""

import json
import sys
import hashlib
import genanki


def stable_id(seed: str) -> int:
    """Generate a stable integer ID from a string seed, in genanki's valid range."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:8], 16) % (1 << 30) + (1 << 30)


# --- Anki Note Models ---

def make_basic_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Basic",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[{
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}'
                    '<div style="font-size:10px;color:#999;margin-top:12px;">'
                    '{{BloomLevel}} &middot; {{KnowledgeType}}</div>',
        }],
    )


def make_cloze_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Cloze",
        model_type=genanki.Model.CLOZE,
        fields=[
            {"name": "Text"},
            {"name": "Extra"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[{
            "name": "Cloze",
            "qfmt": "{{cloze:Text}}",
            "afmt": "{{cloze:Text}}<br>{{Extra}}"
                    '<div style="font-size:10px;color:#999;margin-top:12px;">'
                    "{{BloomLevel}} &middot; {{KnowledgeType}}</div>",
        }],
    )


def make_reversed_model(model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        "MetaLearning Reversed",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
            {"name": "KnowledgeNodeID"},
            {"name": "CardID"},
            {"name": "BloomLevel"},
            {"name": "KnowledgeType"},
            {"name": "Tags"},
        ],
        templates=[
            {
                "name": "Forward",
                "qfmt": "{{Front}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
            },
            {
                "name": "Reverse",
                "qfmt": "{{Back}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Front}}',
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

        if card_type == "cloze":
            model = models["cloze"]
            note = MetaLearningNote(
                card_id=card_id,
                model=model,
                fields=[
                    card["front"],         # Text (with {{c1::...}} syntax)
                    card.get("back", ""),   # Extra
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
    basic_model_id = anki_config.get("model_id_basic", stable_id(f"model:basic:{plan_id}"))
    cloze_model_id = anki_config.get("model_id_cloze", stable_id(f"model:cloze:{plan_id}"))
    reversed_model_id = anki_config.get("model_id_reversed", stable_id(f"model:reversed:{plan_id}"))

    models = {
        "basic": make_basic_model(basic_model_id),
        "cloze": make_cloze_model(cloze_model_id),
        "reversed": make_reversed_model(reversed_model_id),
    }

    # Build all decks
    decks = []
    for deck_data in data.get("decks", []):
        deck = build_deck(deck_data, models)
        decks.append(deck)

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
    print(f"Exported {total_cards} cards across {len(decks)} deck(s) to {output_path}")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_anki.py <srs-cards.json> [output.apkg]")
        sys.exit(1)

    srs_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    generate_apkg(srs_path, out_path)
