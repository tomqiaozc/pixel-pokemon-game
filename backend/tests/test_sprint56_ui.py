"""Tests for Sprint 56: Map transitions, Pokedex UI, trainer card.

These tests verify map transition animations, Pokedex interface config,
and trainer card display data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Map Transitions ────────────────────────────────────────

class TestMapTransitions:
    def test_transition_type_count(self):
        mt = _load_json("map_transitions.json")
        assert len(mt["transition_types"]) == 10

    def test_animation_count(self):
        mt = _load_json("map_transitions.json")
        assert len(mt["animations"]) == 8

    def test_transitions_have_fields(self):
        mt = _load_json("map_transitions.json")
        for name, t in mt["transition_types"].items():
            assert "animation" in t, f"{name} missing animation"
            assert "duration_ms" in t, f"{name} missing duration_ms"
            assert "show_location_name" in t, f"{name} missing show_location_name"

    def test_durations_positive(self):
        mt = _load_json("map_transitions.json")
        for name, t in mt["transition_types"].items():
            assert t["duration_ms"] > 0, f"{name} non-positive duration"

    def test_animations_reference_valid(self):
        mt = _load_json("map_transitions.json")
        valid_anims = set(mt["animations"].keys())
        for name, t in mt["transition_types"].items():
            assert t["animation"] in valid_anims, \
                f"{name} references unknown animation: {t['animation']}"

    def test_animations_have_type(self):
        mt = _load_json("map_transitions.json")
        for name, anim in mt["animations"].items():
            assert "type" in anim, f"{name} missing type"
            assert "stages" in anim, f"{name} missing stages"

    def test_location_name_display(self):
        mt = _load_json("map_transitions.json")
        lnd = mt["location_name_display"]
        assert lnd["show_duration_ms"] > 0
        assert lnd["fade_in_ms"] > 0

    def test_loading_tips_count(self):
        mt = _load_json("map_transitions.json")
        assert len(mt["loading_screen"]["tips"]) == 10

    def test_tips_non_empty(self):
        mt = _load_json("map_transitions.json")
        for tip in mt["loading_screen"]["tips"]:
            assert len(tip) > 0


# ──── Pokedex UI ─────────────────────────────────────────────

class TestPokedexUI:
    def test_mode_count(self):
        pu = _load_json("pokedex_ui.json")
        assert len(pu["modes"]) == 4

    def test_entry_state_count(self):
        pu = _load_json("pokedex_ui.json")
        assert len(pu["entry_states"]) == 3

    def test_entry_states(self):
        pu = _load_json("pokedex_ui.json")
        assert "unseen" in pu["entry_states"]
        assert "seen" in pu["entry_states"]
        assert "caught" in pu["entry_states"]

    def test_unseen_hides_info(self):
        pu = _load_json("pokedex_ui.json")
        unseen = pu["entry_states"]["unseen"]
        assert unseen["show_sprite"] is False
        assert unseen["show_name"] is False

    def test_layout_dimensions(self):
        pu = _load_json("pokedex_ui.json")
        layout = pu["layout"]
        assert layout["screen_width"] > 0
        assert layout["screen_height"] > 0

    def test_list_mode_has_sort(self):
        pu = _load_json("pokedex_ui.json")
        assert len(pu["modes"]["list"]["sort_options"]) >= 3

    def test_detail_mode_sections(self):
        pu = _load_json("pokedex_ui.json")
        sections = pu["modes"]["detail"]["sections"]
        assert "info" in sections
        assert "stats" in sections
        assert "evolution" in sections

    def test_completion_display(self):
        pu = _load_json("pokedex_ui.json")
        cd = pu["completion_display"]
        assert cd["total_species"] == 151
        assert cd["show_percentage"] is True

    def test_colors_valid(self):
        pu = _load_json("pokedex_ui.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, color in pu["colors"].items():
            assert hex_pat.match(color), f"Pokedex color {name}: {color} invalid"

    def test_navigation(self):
        pu = _load_json("pokedex_ui.json")
        nav = pu["navigation"]
        assert "a_button" in nav
        assert "b_button" in nav


# ──── Trainer Card ───────────────────────────────────────────

class TestTrainerCard:
    def test_displayed_field_count(self):
        tc = _load_json("trainer_card.json")
        assert len(tc["displayed_fields"]) == 6

    def test_badge_count(self):
        tc = _load_json("trainer_card.json")
        assert len(tc["badge_display"]["badges"]) == 8

    def test_card_background_count(self):
        tc = _load_json("trainer_card.json")
        assert len(tc["card_backgrounds"]) == 5

    def test_badges_have_fields(self):
        tc = _load_json("trainer_card.json")
        for badge in tc["badge_display"]["badges"]:
            assert "id" in badge
            assert "gym" in badge
            assert "color" in badge
            assert "leader" in badge

    def test_badge_colors_valid(self):
        tc = _load_json("trainer_card.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for badge in tc["badge_display"]["badges"]:
            assert hex_pat.match(badge["color"]), f"{badge['id']} bad color"

    def test_card_layout(self):
        tc = _load_json("trainer_card.json")
        cl = tc["card_layout"]
        assert cl["width"] > 0
        assert cl["height"] > 0
        assert cl["border_width"] > 0

    def test_star_rating(self):
        tc = _load_json("trainer_card.json")
        sr = tc["star_rating"]
        assert sr["max_stars"] == 4
        assert len(sr["criteria"]) == 4

    def test_star_criteria_have_requirement(self):
        tc = _load_json("trainer_card.json")
        for criterion in tc["star_rating"]["criteria"]:
            assert "star" in criterion
            assert "requirement" in criterion
            assert "description" in criterion

    def test_default_background(self):
        tc = _load_json("trainer_card.json")
        assert "default" in tc["card_backgrounds"]
        assert tc["card_backgrounds"]["default"]["pattern"] is None

    def test_flip_animation(self):
        tc = _load_json("trainer_card.json")
        fa = tc["flip_animation"]
        assert fa["enabled"] is True
        assert fa["duration_ms"] > 0

    def test_first_badge_boulder(self):
        tc = _load_json("trainer_card.json")
        first = tc["badge_display"]["badges"][0]
        assert first["id"] == "boulder_badge"
        assert first["leader"] == "Brock"


# ──── Counts ──────────────────────────────────────────────────

class TestCounts:
    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_moves_unchanged(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151
