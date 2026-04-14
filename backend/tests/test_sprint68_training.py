"""Tests for Sprint 68: Fossil revival, move reminder, EV training spots.

These tests verify fossil revival at Cinnabar Lab, Move Reminder/Deleter NPCs,
and EV training location recommendations.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Fossil Revival ──────────────────────────────────────

class TestFossilRevival:
    def test_lab_location(self):
        fr = _load_json("fossil_revival.json")
        assert fr["lab"]["location"] == "cinnabar_island"

    def test_fossil_count(self):
        fr = _load_json("fossil_revival.json")
        assert len(fr["fossils"]) == 3

    def test_fossils_have_fields(self):
        fr = _load_json("fossil_revival.json")
        for f in fr["fossils"]:
            assert "id" in f
            assert "item_name" in f
            assert "pokemon" in f
            assert "level" in f

    def test_helix_dome_choice(self):
        fr = _load_json("fossil_revival.json")
        helix = next(f for f in fr["fossils"] if f["id"] == "helix_fossil")
        dome = next(f for f in fr["fossils"] if f["id"] == "dome_fossil")
        assert helix["choice_with"] == "dome_fossil"
        assert dome["choice_with"] == "helix_fossil"

    def test_old_amber_standalone(self):
        fr = _load_json("fossil_revival.json")
        amber = next(f for f in fr["fossils"] if f["id"] == "old_amber")
        assert amber["pokemon"] == "Aerodactyl"
        assert amber["choice_with"] is None

    def test_all_level_30(self):
        fr = _load_json("fossil_revival.json")
        for f in fr["fossils"]:
            assert f["level"] == 30

    def test_revival_instant(self):
        fr = _load_json("fossil_revival.json")
        assert fr["revival_process"]["instant"] is True
        assert fr["revival_process"]["cost"] == 0

    def test_requires_party_space(self):
        fr = _load_json("fossil_revival.json")
        assert fr["revival_process"]["requires_party_space"] is True

    def test_dialogue(self):
        fr = _load_json("fossil_revival.json")
        assert len(fr["dialogue"]) == 7
        assert "{pokemon}" in fr["dialogue"]["success"]


# ──── Move Reminder ────────────────────────────────────────

class TestMoveReminder:
    def test_reminder_location(self):
        mr = _load_json("move_reminder.json")
        assert mr["move_reminder"]["location"] == "fuchsia_city"

    def test_reminder_cost(self):
        mr = _load_json("move_reminder.json")
        assert mr["move_reminder"]["cost_type"] == "heart_scale"
        assert mr["move_reminder"]["cost_amount"] == 1

    def test_deleter_free(self):
        mr = _load_json("move_reminder.json")
        assert mr["move_deleter"]["cost_type"] == "free"

    def test_deleter_can_delete_hm(self):
        mr = _load_json("move_reminder.json")
        assert mr["move_deleter"]["can_delete_hm"] is True

    def test_reminder_rules(self):
        mr = _load_json("move_reminder.json")
        rules = mr["reminder_rules"]
        assert rules["teaches_level_up_moves"] is True
        assert rules["teaches_future_moves"] is False
        assert rules["max_moves"] == 4

    def test_heart_scale_sources(self):
        mr = _load_json("move_reminder.json")
        sources = mr["heart_scale_sources"]
        assert len(sources) == 5

    def test_dialogue_count(self):
        mr = _load_json("move_reminder.json")
        assert len(mr["dialogue"]) == 10


# ──── EV Training Spots ───────────────────────────────────

class TestEVTrainingSpots:
    def test_ev_cap_total(self):
        ev = _load_json("ev_training_spots.json")
        assert ev["ev_cap"]["total_max"] == 510

    def test_ev_cap_per_stat(self):
        ev = _load_json("ev_training_spots.json")
        assert ev["ev_cap"]["per_stat_max"] == 252

    def test_six_stats(self):
        ev = _load_json("ev_training_spots.json")
        assert len(ev["ev_cap"]["stats"]) == 6

    def test_training_spot_count(self):
        ev = _load_json("ev_training_spots.json")
        assert len(ev["training_spots"]) == 12

    def test_spots_have_fields(self):
        ev = _load_json("ev_training_spots.json")
        for spot in ev["training_spots"]:
            assert "stat" in spot
            assert "location" in spot
            assert "pokemon" in spot
            assert "ev_yield" in spot

    def test_all_stats_covered(self):
        ev = _load_json("ev_training_spots.json")
        stats = {s["stat"] for s in ev["training_spots"]}
        assert stats == set(ev["ev_cap"]["stats"])

    def test_ev_yield_positive(self):
        ev = _load_json("ev_training_spots.json")
        for spot in ev["training_spots"]:
            assert spot["ev_yield"] >= 1

    def test_boosting_items(self):
        ev = _load_json("ev_training_spots.json")
        items = ev["ev_boosting_items"]
        assert len(items) == 6
        for item in items:
            assert item["ev_gain"] == 10

    def test_item_rules(self):
        ev = _load_json("ev_training_spots.json")
        rules = ev["ev_item_rules"]
        assert rules["max_from_items"] == 100
        assert rules["cannot_exceed_stat_cap"] is True


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
