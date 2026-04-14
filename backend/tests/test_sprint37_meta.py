"""Tests for Sprint 37: Music tracks, achievements, game configuration.

These tests verify the music/SFX catalog, achievement definitions,
and game configuration settings.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Music Tracks ─────────────────────────────────────────────

class TestMusicTracks:
    def test_track_count(self):
        music = _load_json("music_tracks.json")
        assert len(music["tracks"]) == 30

    def test_sfx_count(self):
        music = _load_json("music_tracks.json")
        assert len(music["sfx"]) == 16

    EXPECTED_TRACKS = [
        "title_screen", "pallet_town", "battle_wild", "battle_trainer",
        "battle_gym_leader", "battle_champion", "pokemon_center",
        "evolution", "hall_of_fame", "lavender_town",
    ]

    @pytest.mark.parametrize("track_id", EXPECTED_TRACKS)
    def test_track_exists(self, track_id):
        music = _load_json("music_tracks.json")
        assert track_id in music["tracks"]
        track = music["tracks"][track_id]
        assert "name" in track
        assert "file" in track
        assert "loop" in track

    def test_battle_tracks_loop(self):
        music = _load_json("music_tracks.json")
        for tid in ["battle_wild", "battle_trainer", "battle_gym_leader"]:
            assert music["tracks"][tid]["loop"] is True

    def test_victory_tracks_no_loop(self):
        music = _load_json("music_tracks.json")
        for tid in ["victory_wild", "victory_trainer", "victory_gym"]:
            assert music["tracks"][tid]["loop"] is False

    EXPECTED_SFX = [
        "menu_select", "damage_normal", "critical_hit",
        "level_up", "pokemon_caught", "healing", "badge_obtained",
    ]

    @pytest.mark.parametrize("sfx_id", EXPECTED_SFX)
    def test_sfx_exists(self, sfx_id):
        music = _load_json("music_tracks.json")
        assert sfx_id in music["sfx"]


# ──── Achievements ─────────────────────────────────────────────

class TestAchievements:
    def test_achievement_count(self):
        achievements = _load_json("achievements.json")
        assert len(achievements) == 32

    def test_all_have_required_fields(self):
        achievements = _load_json("achievements.json")
        for ach in achievements:
            assert "id" in ach
            assert "name" in ach
            assert "description" in ach
            assert "category" in ach
            assert "reward_type" in ach

    def test_unique_ids(self):
        achievements = _load_json("achievements.json")
        ids = [a["id"] for a in achievements]
        assert len(ids) == len(set(ids))

    EXPECTED_CATEGORIES = {"story", "catching", "badges", "training", "battling", "exploration", "misc"}

    def test_valid_categories(self):
        achievements = _load_json("achievements.json")
        for ach in achievements:
            assert ach["category"] in self.EXPECTED_CATEGORIES, (
                f"Achievement {ach['id']} has invalid category: {ach['category']}"
            )

    def test_catching_achievements(self):
        achievements = _load_json("achievements.json")
        catching = [a for a in achievements if a["category"] == "catching"]
        assert len(catching) >= 8

    def test_champion_achievement(self):
        achievements = _load_json("achievements.json")
        champ = next(a for a in achievements if a["id"] == "become_champion")
        assert champ["reward_type"] == "certificate"

    def test_pokedex_completion(self):
        achievements = _load_json("achievements.json")
        dex = next(a for a in achievements if a["id"] == "catch_151")
        assert "151" in dex["description"]

    def test_reward_items_valid(self):
        achievements = _load_json("achievements.json")
        items = _load_json("items.json")
        item_names = {i["name"] for i in items}
        for ach in achievements:
            if ach["reward_type"] == "item":
                assert "reward" in ach
                assert ach["reward"] in item_names, (
                    f"Achievement {ach['id']} reward {ach['reward']} not in items"
                )


# ──── Game Config ──────────────────────────────────────────────

class TestGameConfig:
    def test_file_exists(self):
        config = _load_json("game_config.json")
        assert "version" in config

    def test_canvas_settings(self):
        config = _load_json("game_config.json")
        canvas = config["canvas"]
        assert canvas["width"] == 800
        assert canvas["height"] == 600
        assert canvas["tile_size"] == 16

    def test_player_defaults(self):
        config = _load_json("game_config.json")
        player = config["player"]
        assert player["max_party_size"] == 6
        assert player["starting_money"] == 3000
        assert player["max_money"] == 999999

    def test_speed_settings(self):
        config = _load_json("game_config.json")
        player = config["player"]
        assert player["walk_speed"] < player["run_speed"] < player["bike_speed"]

    def test_difficulty_options(self):
        config = _load_json("game_config.json")
        diff = config["difficulty"]
        assert diff["default"] == "normal"
        assert len(diff["options"]) == 3
        assert "easy" in diff["options"]
        assert "normal" in diff["options"]
        assert "hard" in diff["options"]

    def test_normal_difficulty_neutral(self):
        config = _load_json("game_config.json")
        normal = config["difficulty"]["options"]["normal"]
        assert normal["exp_multiplier"] == 1.0
        assert normal["catch_rate_modifier"] == 1.0

    def test_easy_gives_more_exp(self):
        config = _load_json("game_config.json")
        easy = config["difficulty"]["options"]["easy"]
        assert easy["exp_multiplier"] > 1.0

    def test_hard_gives_less_exp(self):
        config = _load_json("game_config.json")
        hard = config["difficulty"]["options"]["hard"]
        assert hard["exp_multiplier"] < 1.0

    def test_battle_style_options(self):
        config = _load_json("game_config.json")
        assert "shift" in config["battle"]["battle_style_options"]
        assert "set" in config["battle"]["battle_style_options"]

    def test_text_speed_options(self):
        config = _load_json("game_config.json")
        speeds = config["battle"]["text_speed_options"]
        assert speeds["slow"] > speeds["normal"] > speeds["fast"] > speeds["instant"]

    def test_save_settings(self):
        config = _load_json("game_config.json")
        save = config["save"]
        assert save["max_save_slots"] == 3
        assert save["auto_save"] is True

    def test_audio_settings(self):
        config = _load_json("game_config.json")
        audio = config["audio"]
        assert 0 <= audio["master_volume"] <= 100
        assert 0 <= audio["music_volume"] <= 100
        assert 0 <= audio["sfx_volume"] <= 100


# ──── Counts ───────────────────────────────────────────────────

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

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132
