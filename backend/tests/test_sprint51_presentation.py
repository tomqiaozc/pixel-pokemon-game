"""Tests for Sprint 51: Tutorial system, particle effects, sprite data.

These tests verify tutorial sequence definitions, particle effect properties,
and Pokemon sprite sheet configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Tutorial System ────────────────────────────────────────

class TestTutorialSystem:
    def test_tutorial_count(self):
        ts = _load_json("tutorial_system.json")
        assert len(ts) == 10

    def test_all_have_required_fields(self):
        ts = _load_json("tutorial_system.json")
        for t in ts:
            assert "id" in t, f"Missing id"
            assert "name" in t, f"Missing name"
            assert "trigger" in t, f"Missing trigger"
            assert "steps" in t, f"Missing steps in {t['id']}"
            assert "completed_flag" in t, f"Missing completed_flag in {t['id']}"

    def test_unique_ids(self):
        ts = _load_json("tutorial_system.json")
        ids = [t["id"] for t in ts]
        assert len(ids) == len(set(ids))

    def test_unique_completed_flags(self):
        ts = _load_json("tutorial_system.json")
        flags = [t["completed_flag"] for t in ts]
        assert len(flags) == len(set(flags))

    def test_steps_have_text(self):
        ts = _load_json("tutorial_system.json")
        for t in ts:
            for step in t["steps"]:
                assert "text" in step, f"Step missing text in {t['id']}"
                assert len(step["text"]) > 0

    def test_movement_tutorial_first(self):
        ts = _load_json("tutorial_system.json")
        assert ts[0]["id"] == "tutorial_movement"
        assert ts[0]["trigger"] == "game_start"

    def test_battle_tutorial_exists(self):
        ts = _load_json("tutorial_system.json")
        battle = [t for t in ts if t["id"] == "tutorial_battle"]
        assert len(battle) == 1
        assert battle[0]["trigger"] == "first_wild_encounter"

    def test_catching_tutorial_exists(self):
        ts = _load_json("tutorial_system.json")
        catch = [t for t in ts if t["id"] == "tutorial_catching"]
        assert len(catch) == 1

    def test_starter_not_skippable(self):
        ts = _load_json("tutorial_system.json")
        starter = next(t for t in ts if t["id"] == "tutorial_first_pokemon")
        assert starter["skippable"] is False

    def test_skippable_field_present(self):
        ts = _load_json("tutorial_system.json")
        for t in ts:
            assert "skippable" in t, f"Missing skippable in {t['id']}"


# ──── Particle Effects ───────────────────────────────────────

class TestParticleEffects:
    def test_particle_count(self):
        pe = _load_json("particle_effects.json")
        assert len(pe["particles"]) == 18

    def test_all_have_required_fields(self):
        pe = _load_json("particle_effects.json")
        required = ["color_start", "color_end", "size_min", "size_max",
                     "lifetime_ms", "count", "velocity_x", "velocity_y",
                     "gravity", "fade_out"]
        for name, data in pe["particles"].items():
            for field in required:
                assert field in data, f"{name} missing {field}"

    def test_colors_are_hex(self):
        pe = _load_json("particle_effects.json")
        import re
        hex_pat = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for name, data in pe["particles"].items():
            assert hex_pat.match(data["color_start"]), f"{name} bad color_start"
            assert hex_pat.match(data["color_end"]), f"{name} bad color_end"

    def test_size_min_less_than_max(self):
        pe = _load_json("particle_effects.json")
        for name, data in pe["particles"].items():
            assert data["size_min"] <= data["size_max"], f"{name} size_min > size_max"

    def test_lifetime_positive(self):
        pe = _load_json("particle_effects.json")
        for name, data in pe["particles"].items():
            assert data["lifetime_ms"] > 0, f"{name} non-positive lifetime"

    def test_count_positive(self):
        pe = _load_json("particle_effects.json")
        for name, data in pe["particles"].items():
            assert data["count"] > 0, f"{name} non-positive count"

    def test_velocity_has_min_max(self):
        pe = _load_json("particle_effects.json")
        for name, data in pe["particles"].items():
            assert "min" in data["velocity_x"] and "max" in data["velocity_x"]
            assert "min" in data["velocity_y"] and "max" in data["velocity_y"]

    def test_weather_particles_mapping(self):
        pe = _load_json("particle_effects.json")
        wp = pe["weather_particles"]
        assert "rain" in wp
        assert "sandstorm" in wp
        assert "hail" in wp
        assert "sun" in wp
        assert wp["clear"] is None

    def test_weather_particles_reference_valid(self):
        pe = _load_json("particle_effects.json")
        particles = pe["particles"]
        for weather, particle_name in pe["weather_particles"].items():
            if particle_name is not None:
                assert particle_name in particles, \
                    f"Weather {weather} references missing particle {particle_name}"

    def test_fire_particle_exists(self):
        pe = _load_json("particle_effects.json")
        assert "fire" in pe["particles"]
        assert pe["particles"]["fire"]["fade_out"] is True

    def test_explosion_high_count(self):
        pe = _load_json("particle_effects.json")
        assert pe["particles"]["explosion"]["count"] >= 30


# ──── Pokemon Sprite Data ────────────────────────────────────

class TestPokemonSpriteData:
    def test_sprite_count(self):
        sd = _load_json("pokemon_sprite_data.json")
        assert len(sd["sprites"]) == 146  # 151 species, 5 duplicate names

    def test_sprite_sheets_defined(self):
        sd = _load_json("pokemon_sprite_data.json")
        assert len(sd["sprite_sheets"]) == 5

    def test_animation_states(self):
        sd = _load_json("pokemon_sprite_data.json")
        states = sd["animation_states"]
        assert "idle" in states
        assert "attack" in states
        assert "hurt" in states
        assert "faint" in states

    def test_all_sprites_have_fields(self):
        sd = _load_json("pokemon_sprite_data.json")
        required = ["species_id", "sprite_sheet", "sheet_position", "size",
                     "pixel_width", "pixel_height", "animation_frames",
                     "frame_duration_ms", "palette", "has_shiny", "shadow_offset_y"]
        for name, data in sd["sprites"].items():
            for field in required:
                assert field in data, f"{name} missing {field}"

    def test_valid_sizes(self):
        sd = _load_json("pokemon_sprite_data.json")
        valid = {"small", "medium", "large"}
        for name, data in sd["sprites"].items():
            assert data["size"] in valid, f"{name} invalid size: {data['size']}"

    def test_pixel_dimensions_match_size(self):
        sd = _load_json("pokemon_sprite_data.json")
        size_dims = {"small": (16, 16), "medium": (24, 24), "large": (32, 32)}
        for name, data in sd["sprites"].items():
            expected = size_dims[data["size"]]
            assert data["pixel_width"] == expected[0], f"{name} width mismatch"
            assert data["pixel_height"] == expected[1], f"{name} height mismatch"

    def test_animation_frames_have_states(self):
        sd = _load_json("pokemon_sprite_data.json")
        for name, data in sd["sprites"].items():
            frames = data["animation_frames"]
            assert "idle" in frames, f"{name} missing idle frames"
            assert "attack" in frames, f"{name} missing attack frames"

    def test_species_names_match(self):
        sd = _load_json("pokemon_sprite_data.json")
        species = _load_json("pokemon_species.json")
        species_names = {s["name"] for s in species}
        sprite_names = set(sd["sprites"].keys())
        # All sprite names should be valid species
        for name in sprite_names:
            assert name in species_names, f"{name} not in species"

    def test_bulbasaur_sprite(self):
        sd = _load_json("pokemon_sprite_data.json")
        assert "Bulbasaur" in sd["sprites"]
        b = sd["sprites"]["Bulbasaur"]
        assert b["species_id"] == 1
        assert b["palette"] == "palette_grass"

    def test_charizard_large(self):
        sd = _load_json("pokemon_sprite_data.json")
        assert sd["sprites"]["Charizard"]["size"] == "large"
        assert sd["sprites"]["Charizard"]["pixel_width"] == 32

    def test_all_have_shiny(self):
        sd = _load_json("pokemon_sprite_data.json")
        for name, data in sd["sprites"].items():
            assert data["has_shiny"] is True


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
