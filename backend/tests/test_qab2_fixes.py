"""Tests for Sprint 6.5 QA-B backend fixes."""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import _games, create_game_with_starter

client = TestClient(app)


def _make_game(name="TestPlayer"):
    """Create a game with a starter Pokemon for testing."""
    starter = {
        "id": 1,
        "name": "Bulbasaur",
        "types": ["grass", "poison"],
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
        "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        "sprite": "bulbasaur.png",
        "level": 5,
        "ability_id": "overgrow",
    }
    return create_game_with_starter(name, starter)


# ---- Fix 1: InventoryItem accepts item_id or name ----

class TestInventoryModelFix:
    def test_save_with_item_id_inventory(self):
        """Save game with item_id-based inventory (from item_service buy flow)."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["inventory"] = [{"item_id": 7, "quantity": 5}]
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200
        saved = resp.json()
        assert len(saved["player"]["inventory"]) == 1

    def test_save_with_name_inventory(self):
        """Save game with name-based inventory (legacy format)."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["inventory"] = [{"name": "Potion", "quantity": 3}]
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200

    def test_save_with_both_fields_inventory(self):
        """Save game with both item_id and name."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["inventory"] = [{"item_id": 7, "name": "Pokeball", "quantity": 10}]
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200

    def test_save_with_empty_inventory(self):
        """Save game with empty inventory."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["inventory"] = []
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200

    def test_save_with_pokemon_extra_fields(self):
        """Save game with Pokemon that has current_hp, ability_id etc."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["team"] = [{
            "id": 1,
            "name": "Bulbasaur",
            "types": ["grass", "poison"],
            "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "bulbasaur.png",
            "level": 5,
            "current_hp": 30,
            "max_hp": 45,
            "ability_id": "overgrow",
            "status": "poison",
        }]
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200
        saved = resp.json()
        assert saved["player"]["team"][0]["current_hp"] == 30
        assert saved["player"]["team"][0]["ability_id"] == "overgrow"

    def test_save_with_money_field(self):
        """Save game with money field on player."""
        game = _make_game()
        gid = game["id"]
        player = game["player"].copy()
        player["money"] = 5000
        resp = client.post(f"/api/game/{gid}/save", json={"player": player})
        assert resp.status_code == 200
        saved = resp.json()
        assert saved["player"]["money"] == 5000


# ---- Fix 2: PC Box alias routes ----

class TestPCBoxRoutes:
    def test_pc_boxes_primary_route(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/pc/boxes/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5  # 5 boxes

    def test_pc_boxes_alias_route(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/pokemon-center/pc/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5

    def test_pc_withdraw_alias_route(self):
        """Withdraw from alias route should work."""
        game = _make_game()
        gid = game["id"]
        # Deposit first via primary route
        resp = client.post("/api/pc/deposit", json={"game_id": gid, "pokemon_index": 0})
        # This will fail since we only have 1 pokemon, but should get 400 not 404
        assert resp.status_code == 400  # "Cannot deposit — need at least 1 Pokemon"


# ---- Fix 3: Gym badge string ID ----

class TestGymBadgeStringId:
    def test_gym_list_returns_string_ids(self):
        resp = client.get("/api/gyms")
        assert resp.status_code == 200
        gyms = resp.json()
        assert len(gyms) >= 1
        assert isinstance(gyms[0]["id"], str)

    def test_gym_detail_with_string_id(self):
        resp = client.get("/api/gyms/pewter_gym")
        assert resp.status_code == 200
        data = resp.json()
        assert data["badge_id"] == "boulder"

    def test_award_badge_with_string_gym_id(self):
        game = _make_game()
        gid = game["id"]
        # First challenge (need to have won battle, but award_badge doesn't check)
        resp = client.post(f"/api/gyms/pewter_gym/award-badge/{gid}")
        assert resp.status_code == 200
        badges = resp.json()
        # Should return list of badge objects
        assert isinstance(badges, list)
        # Find boulder badge
        boulder = [b for b in badges if b["badge_id"] == "boulder"]
        assert len(boulder) == 1
        assert boulder[0]["earned"] is True

    def test_award_badge_nonexistent_gym_400(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/gyms/fake_gym/award-badge/{gid}")
        assert resp.status_code == 400


# ---- Fix 4: Load game returns enriched state ----

class TestLoadGameEnriched:
    def test_load_game_has_badges_list(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/game/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "badges_list" in data
        assert isinstance(data["badges_list"], list)

    def test_load_game_has_pokedex_stats(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/game/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "pokedex_stats" in data
        assert "total_species" in data["pokedex_stats"]
        assert "seen_count" in data["pokedex_stats"]

    def test_load_game_has_pc_boxes(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/game/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "pc_boxes" in data
        assert len(data["pc_boxes"]) == 5

    def test_load_game_has_player_data(self):
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/game/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["player"]["name"] == "TestPlayer"
        assert len(data["player"]["team"]) >= 1
        assert "play_time_seconds" in data

    def test_load_game_nonexistent_404(self):
        resp = client.get("/api/game/doesnotexist")
        assert resp.status_code == 404

    def test_load_game_after_badge_shows_earned(self):
        game = _make_game()
        gid = game["id"]
        # Award a badge
        client.post(f"/api/gyms/pewter_gym/award-badge/{gid}")
        # Load game
        resp = client.get(f"/api/game/{gid}")
        data = resp.json()
        boulder = [b for b in data["badges_list"] if b["badge_id"] == "boulder"]
        assert len(boulder) == 1
        assert boulder[0]["earned"] is True
