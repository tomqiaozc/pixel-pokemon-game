"""Tests for Sprint 58: Phone system, debug tools, notification system.

These tests verify phone/contact system, debug tools configuration,
and in-game notification system.
"""
import json
import os
import re
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


HEX_PAT = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ──── Phone System ───────────────────────────────────────────

class TestPhoneSystem:
    def test_contact_count(self):
        ps = _load_json("phone_system.json")
        assert len(ps["contacts"]) == 10

    def test_contacts_have_fields(self):
        ps = _load_json("phone_system.json")
        for c in ps["contacts"]:
            assert "id" in c
            assert "name" in c
            assert "type" in c
            assert "location" in c
            assert "rematch" in c

    def test_rematchable_contacts(self):
        ps = _load_json("phone_system.json")
        rematch = [c for c in ps["contacts"] if c["rematch"]]
        assert len(rematch) == 7

    def test_rematch_contacts_have_location(self):
        ps = _load_json("phone_system.json")
        for c in ps["contacts"]:
            if c["rematch"]:
                assert "rematch_location" in c, f"{c['id']} missing rematch_location"

    def test_unique_contact_ids(self):
        ps = _load_json("phone_system.json")
        ids = [c["id"] for c in ps["contacts"]]
        assert len(ids) == len(set(ids))

    def test_oak_is_story_contact(self):
        ps = _load_json("phone_system.json")
        oak = next(c for c in ps["contacts"] if c["id"] == "professor_oak")
        assert oak["type"] == "story"
        assert oak["rematch"] is False

    def test_joey_exists(self):
        ps = _load_json("phone_system.json")
        joey = next(c for c in ps["contacts"] if c["id"] == "youngster_joey")
        assert joey["rematch"] is True

    def test_call_dialogues(self):
        ps = _load_json("phone_system.json")
        cd = ps["call_dialogues"]
        assert len(cd["greeting"]) >= 2
        assert len(cd["rematch_request"]) >= 2
        assert len(cd["farewell"]) >= 2

    def test_phone_ui(self):
        ps = _load_json("phone_system.json")
        assert "ring_sound" in ps["phone_ui"]
        assert ps["phone_ui"]["scroll_enabled"] is True


# ──── Debug Tools ────────────────────────────────────────────

class TestDebugTools:
    def test_debug_disabled_by_default(self):
        dt = _load_json("debug_tools.json")
        assert dt["debug_mode"]["enabled"] is False

    def test_command_count(self):
        dt = _load_json("debug_tools.json")
        assert len(dt["debug_commands"]) == 20

    def test_category_count(self):
        dt = _load_json("debug_tools.json")
        assert len(dt["debug_categories"]) == 7

    def test_commands_have_fields(self):
        dt = _load_json("debug_tools.json")
        for cmd in dt["debug_commands"]:
            assert "command" in cmd
            assert "description" in cmd
            assert "category" in cmd

    def test_commands_valid_categories(self):
        dt = _load_json("debug_tools.json")
        valid = set(dt["debug_categories"])
        for cmd in dt["debug_commands"]:
            assert cmd["category"] in valid, \
                f"{cmd['command']} invalid category: {cmd['category']}"

    def test_console_config(self):
        dt = _load_json("debug_tools.json")
        console = dt["console"]
        assert console["enabled"] is False
        assert console["max_history"] > 0

    def test_performance_overlay(self):
        dt = _load_json("debug_tools.json")
        po = dt["performance_overlay"]
        assert po["show_fps"] is False
        assert po["update_interval_ms"] > 0

    def test_activation_code(self):
        dt = _load_json("debug_tools.json")
        assert len(dt["debug_mode"]["activation_code"]) > 0

    def test_heal_command_exists(self):
        dt = _load_json("debug_tools.json")
        cmds = {c["command"] for c in dt["debug_commands"]}
        assert "heal" in cmds
        assert "teleport" in cmds
        assert "noclip" in cmds


# ──── Notification System ────────────────────────────────────

class TestNotificationSystem:
    def test_notification_type_count(self):
        ns = _load_json("notification_system.json")
        assert len(ns["notification_types"]) == 10

    def test_animation_count(self):
        ns = _load_json("notification_system.json")
        assert len(ns["animations"]) == 7

    def test_types_have_fields(self):
        ns = _load_json("notification_system.json")
        required = ["priority", "duration_ms", "position", "background_color",
                     "text_color", "animation"]
        for name, nt in ns["notification_types"].items():
            for field in required:
                assert field in nt, f"{name} missing {field}"

    def test_priorities_valid(self):
        ns = _load_json("notification_system.json")
        for name, nt in ns["notification_types"].items():
            assert 1 <= nt["priority"] <= 5, f"{name} priority out of range"

    def test_durations_positive(self):
        ns = _load_json("notification_system.json")
        for name, nt in ns["notification_types"].items():
            assert nt["duration_ms"] > 0, f"{name} non-positive duration"

    def test_colors_valid(self):
        ns = _load_json("notification_system.json")
        for name, nt in ns["notification_types"].items():
            assert HEX_PAT.match(nt["background_color"]), f"{name} bad bg color"
            assert HEX_PAT.match(nt["text_color"]), f"{name} bad text color"

    def test_animations_reference_valid(self):
        ns = _load_json("notification_system.json")
        valid = set(ns["animations"].keys())
        for name, nt in ns["notification_types"].items():
            assert nt["animation"] in valid, \
                f"{name} references unknown animation: {nt['animation']}"

    def test_queue_settings(self):
        ns = _load_json("notification_system.json")
        qs = ns["queue_settings"]
        assert qs["max_queued"] >= 1
        assert qs["display_simultaneously"] >= 1
        assert qs["priority_preempt"] is True

    def test_global_settings(self):
        ns = _load_json("notification_system.json")
        gs = ns["global_settings"]
        assert gs["notifications_enabled"] is True
        assert gs["font_size"] > 0

    def test_achievement_high_priority(self):
        ns = _load_json("notification_system.json")
        assert ns["notification_types"]["achievement"]["priority"] >= 3


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
