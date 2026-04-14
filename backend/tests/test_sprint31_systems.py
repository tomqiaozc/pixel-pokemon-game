"""Tests for Sprint 31: Held items/berries, weather system, learnset quality.

These tests verify berry items, held items, weather conditions data,
and overall learnset coverage quality.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── Berries ──────────────────────────────────────────────────

class TestBerries:
    def test_berry_count(self):
        items = _load_json("items.json")
        berries = [i for i in items if i["category"] == "berry"]
        assert len(berries) == 10

    EXPECTED_BERRIES = [
        "Oran Berry", "Sitrus Berry", "Lum Berry",
        "Rawst Berry", "Chesto Berry", "Pecha Berry",
        "Aspear Berry", "Cheri Berry", "Leppa Berry", "Persim Berry",
    ]

    @pytest.mark.parametrize("berry_name", EXPECTED_BERRIES)
    def test_berry_exists(self, berry_name):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == berry_name), None)
        assert found is not None, f"Berry {berry_name} not found"
        assert found["category"] == "berry"
        assert "effect" in found
        assert found["effect"].get("trigger") == "held"

    def test_healing_berries_have_amount(self):
        items = _load_json("items.json")
        healing_berries = ["Oran Berry", "Sitrus Berry"]
        for name in healing_berries:
            berry = next(i for i in items if i["name"] == name)
            assert berry["effect"]["type"] == "heal_hp"
            assert berry["effect"]["amount"] > 0

    def test_status_berries_have_status(self):
        items = _load_json("items.json")
        status_berries = [
            ("Rawst Berry", "burn"), ("Chesto Berry", "sleep"),
            ("Pecha Berry", "poison"), ("Aspear Berry", "freeze"),
            ("Cheri Berry", "paralysis"), ("Persim Berry", "confusion"),
        ]
        for name, status in status_berries:
            berry = next(i for i in items if i["name"] == name)
            assert berry["effect"]["type"] == "cure_status"
            assert berry["effect"]["status"] == status


# ──── Held Items ───────────────────────────────────────────────

class TestHeldItems:
    def test_held_item_count(self):
        items = _load_json("items.json")
        held = [i for i in items if i["category"] == "held_item"]
        assert len(held) == 8

    EXPECTED_HELD_ITEMS = [
        "Leftovers", "Choice Band", "Choice Specs",
        "Focus Sash", "Life Orb", "Shell Bell",
        "Quick Claw", "Kings Rock",
    ]

    @pytest.mark.parametrize("item_name", EXPECTED_HELD_ITEMS)
    def test_held_item_exists(self, item_name):
        items = _load_json("items.json")
        found = next((i for i in items if i["name"] == item_name), None)
        assert found is not None, f"Held item {item_name} not found"
        assert found["category"] == "held_item"
        assert "effect" in found

    def test_choice_items_lock_moves(self):
        items = _load_json("items.json")
        for name in ["Choice Band", "Choice Specs"]:
            item = next(i for i in items if i["name"] == name)
            assert item["effect"].get("lock_move") is True

    def test_focus_sash_single_use(self):
        items = _load_json("items.json")
        sash = next(i for i in items if i["name"] == "Focus Sash")
        assert sash["effect"].get("single_use") is True


# ──── Weather System ───────────────────────────────────────────

class TestWeatherSystem:
    def test_weather_file_exists(self):
        weather = _load_json("weather.json")
        assert len(weather) == 5

    EXPECTED_CONDITIONS = ["clear", "sun", "rain", "sandstorm", "hail"]

    @pytest.mark.parametrize("condition", EXPECTED_CONDITIONS)
    def test_condition_exists(self, condition):
        weather = _load_json("weather.json")
        assert condition in weather, f"Weather {condition} not found"
        w = weather[condition]
        assert "name" in w
        assert "description" in w
        assert "effects" in w

    def test_sun_boosts_fire(self):
        weather = _load_json("weather.json")
        assert weather["sun"]["effects"]["fire_multiplier"] == 1.5

    def test_sun_weakens_water(self):
        weather = _load_json("weather.json")
        assert weather["sun"]["effects"]["water_multiplier"] == 0.5

    def test_rain_boosts_water(self):
        weather = _load_json("weather.json")
        assert weather["rain"]["effects"]["water_multiplier"] == 1.5

    def test_rain_weakens_fire(self):
        weather = _load_json("weather.json")
        assert weather["rain"]["effects"]["fire_multiplier"] == 0.5

    def test_sandstorm_damages_non_immune(self):
        weather = _load_json("weather.json")
        ss = weather["sandstorm"]
        assert ss["effects"]["damage_per_turn_percent"] == 6.25
        assert "rock" in ss["effects"]["immune_types"]
        assert "ground" in ss["effects"]["immune_types"]
        assert "steel" in ss["effects"]["immune_types"]

    def test_hail_damages_non_ice(self):
        weather = _load_json("weather.json")
        hail = weather["hail"]
        assert hail["effects"]["damage_per_turn_percent"] == 6.25
        assert "ice" in hail["effects"]["immune_types"]

    def test_weather_durations(self):
        weather = _load_json("weather.json")
        assert weather["clear"]["duration"] is None
        for cond in ["sun", "rain", "sandstorm", "hail"]:
            assert weather[cond]["duration"] == 5

    def test_weather_ability_triggers(self):
        weather = _load_json("weather.json")
        assert "drought" in weather["sun"]["ability_triggers"]
        assert "drizzle" in weather["rain"]["ability_triggers"]
        assert "sand_stream" in weather["sandstorm"]["ability_triggers"]
        assert "snow_warning" in weather["hail"]["ability_triggers"]

    def test_rain_thunder_accuracy(self):
        weather = _load_json("weather.json")
        assert weather["rain"]["effects"]["thunder_accuracy"] == 100

    def test_sun_solar_beam_no_charge(self):
        weather = _load_json("weather.json")
        assert weather["sun"]["effects"]["solar_beam_charge"] is False


# ──── Learnset Quality ─────────────────────────────────────────

class TestLearnsetQuality:
    def test_all_species_have_learnsets(self):
        species = _load_json("pokemon_species.json")
        for s in species:
            assert len(s.get("learnset", [])) >= 1, (
                f"{s['name']} has no learnset"
            )

    def test_average_learnset_size(self):
        species = _load_json("pokemon_species.json")
        avg = sum(len(s["learnset"]) for s in species) / len(species)
        assert avg >= 5.0, f"Average learnset too small: {avg}"

    def test_starters_have_good_learnsets(self):
        species = _load_json("pokemon_species.json")
        starters = [s for s in species if s["name"] in [
            "Bulbasaur", "Charmander", "Squirtle"
        ]]
        for s in starters:
            assert len(s["learnset"]) >= 5, (
                f"{s['name']} learnset too small: {len(s['learnset'])}"
            )

    def test_fully_evolved_have_learnsets(self):
        species = _load_json("pokemon_species.json")
        fully_evolved = [s for s in species if s["name"] in [
            "Venusaur", "Charizard", "Blastoise",
            "Alakazam", "Gengar", "Dragonite"
        ]]
        for s in fully_evolved:
            assert len(s["learnset"]) >= 5, (
                f"{s['name']} should have 5+ moves: {len(s['learnset'])}"
            )

    def test_learnset_moves_have_level(self):
        species = _load_json("pokemon_species.json")
        for s in species:
            for entry in s["learnset"]:
                assert "level" in entry, f"{s['name']} learnset entry missing level"
                assert "move" in entry, f"{s['name']} learnset entry missing move"


# ──── Counts ───────────────────────────────────────────────────

class TestCounts:
    def test_total_items(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_total_moves(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_maps_unchanged(self):
        maps = _load_json("maps.json")
        assert len(maps) == 132

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151

    def test_npcs_unchanged(self):
        npcs = _load_json("npcs.json")
        assert len(npcs) == 103

    def test_dialogues_unchanged(self):
        dialogues = _load_json("dialogues.json")
        assert len(dialogues) == 90

    def test_trainers_unchanged(self):
        trainers = _load_json("trainers.json")
        assert len(trainers) == 116
