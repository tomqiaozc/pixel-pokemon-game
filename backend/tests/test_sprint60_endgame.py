"""Tests for Sprint 60: Stats tracker, postgame events, multiplayer config.

These tests verify player statistics tracking, postgame content events,
and multiplayer configuration data.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Stats Tracker ──────────────────────────────────────────

class TestStatsTracker:
    def test_stat_count(self):
        st = _load_json("stats_tracker.json")
        assert len(st["tracked_stats"]) == 25

    def test_category_count(self):
        st = _load_json("stats_tracker.json")
        assert len(st["categories"]) == 6

    def test_stats_have_fields(self):
        st = _load_json("stats_tracker.json")
        for stat in st["tracked_stats"]:
            assert "id" in stat
            assert "name" in stat
            assert "category" in stat
            assert "default" in stat

    def test_stats_default_zero(self):
        st = _load_json("stats_tracker.json")
        for stat in st["tracked_stats"]:
            assert stat["default"] == 0, f"{stat['id']} default not 0"

    def test_unique_stat_ids(self):
        st = _load_json("stats_tracker.json")
        ids = [s["id"] for s in st["tracked_stats"]]
        assert len(ids) == len(set(ids))

    def test_valid_categories(self):
        st = _load_json("stats_tracker.json")
        valid = set(st["categories"])
        for stat in st["tracked_stats"]:
            assert stat["category"] in valid, \
                f"{stat['id']} invalid category: {stat['category']}"

    def test_milestone_count(self):
        st = _load_json("stats_tracker.json")
        assert len(st["milestones"]) == 5

    def test_milestones_reference_valid_stats(self):
        st = _load_json("stats_tracker.json")
        stat_ids = {s["id"] for s in st["tracked_stats"]}
        for ms in st["milestones"]:
            assert ms["stat_id"] in stat_ids, \
                f"Milestone references unknown stat: {ms['stat_id']}"

    def test_display_settings(self):
        st = _load_json("stats_tracker.json")
        ds = st["display_settings"]
        assert ds["accessible_from_menu"] is True
        assert ds["stats_per_page"] > 0

    def test_play_time_stat(self):
        st = _load_json("stats_tracker.json")
        pt = next(s for s in st["tracked_stats"] if s["id"] == "play_time_seconds")
        assert pt["category"] == "system"


# ──── Postgame Events ────────────────────────────────────────

class TestPostgameEvents:
    def test_event_count(self):
        pe = _load_json("postgame_events.json")
        assert len(pe["events"]) == 10

    def test_unlock_trigger(self):
        pe = _load_json("postgame_events.json")
        assert pe["unlock_trigger"] == "champion_defeated"

    def test_events_have_fields(self):
        pe = _load_json("postgame_events.json")
        for evt in pe["events"]:
            assert "id" in evt
            assert "name" in evt
            assert "trigger" in evt
            assert "type" in evt

    def test_mewtwo_encounter(self):
        pe = _load_json("postgame_events.json")
        mewtwo = next(e for e in pe["events"] if e["id"] == "mewtwo_encounter")
        assert mewtwo["pokemon"] == "Mewtwo"
        assert mewtwo["level"] == 70
        assert mewtwo["one_time"] is True

    def test_gym_rematches_not_one_time(self):
        pe = _load_json("postgame_events.json")
        rematches = next(e for e in pe["events"] if e["id"] == "gym_leader_rematches")
        assert rematches["one_time"] is False

    def test_legendary_birds(self):
        pe = _load_json("postgame_events.json")
        birds = next(e for e in pe["events"] if e["id"] == "legendary_birds_roam")
        assert len(birds["encounters"]) == 3
        names = {b["pokemon"] for b in birds["encounters"]}
        assert "Articuno" in names
        assert "Zapdos" in names
        assert "Moltres" in names

    def test_battle_tower(self):
        pe = _load_json("postgame_events.json")
        bt = next(e for e in pe["events"] if e["id"] == "battle_tower_open")
        assert bt["type"] == "facility"

    def test_postgame_difficulty(self):
        pe = _load_json("postgame_events.json")
        pd = pe["postgame_difficulty"]
        assert pd["wild_level_boost"] > 0
        assert pd["trainer_level_boost"] > 0

    def test_unique_event_ids(self):
        pe = _load_json("postgame_events.json")
        ids = [e["id"] for e in pe["events"]]
        assert len(ids) == len(set(ids))


# ──── Multiplayer Config ─────────────────────────────────────

class TestMultiplayerConfig:
    def test_trading_enabled(self):
        mc = _load_json("multiplayer_config.json")
        assert mc["trading"]["enabled"] is True

    def test_trade_restrictions(self):
        mc = _load_json("multiplayer_config.json")
        tr = mc["trading"]["trade_restrictions"]
        assert tr["min_party_after_trade"] >= 1
        assert tr["allow_hm_pokemon"] is False

    def test_battle_format_count(self):
        mc = _load_json("multiplayer_config.json")
        assert len(mc["link_battle"]["battle_formats"]) == 3

    def test_battle_formats_have_fields(self):
        mc = _load_json("multiplayer_config.json")
        for fmt in mc["link_battle"]["battle_formats"]:
            assert "id" in fmt
            assert "name" in fmt
            assert "team_size" in fmt
            assert "active_pokemon" in fmt

    def test_flat_battle_has_level_cap(self):
        mc = _load_json("multiplayer_config.json")
        flat = next(f for f in mc["link_battle"]["battle_formats"]
                    if f["id"] == "singles_flat")
        assert flat["level_cap"] == 50
        assert flat["species_clause"] is True

    def test_connection_config(self):
        mc = _load_json("multiplayer_config.json")
        conn = mc["connection"]
        assert conn["max_players"] == 2
        assert conn["timeout_ms"] > 0
        assert conn["heartbeat_interval_ms"] > 0

    def test_battle_rules(self):
        mc = _load_json("multiplayer_config.json")
        rules = mc["link_battle"]["battle_rules"]
        assert rules["sleep_clause"] is True

    def test_colosseum(self):
        mc = _load_json("multiplayer_config.json")
        col = mc["colosseum"]
        assert col["enabled"] is True
        assert col["unlock_requirement"] == "four_badges"

    def test_trade_screen_confirm(self):
        mc = _load_json("multiplayer_config.json")
        ts = mc["trading"]["trade_screen"]
        assert ts["confirm_required"] is True
        assert ts["show_stats"] is True


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
