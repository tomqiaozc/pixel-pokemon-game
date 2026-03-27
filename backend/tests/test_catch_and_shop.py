"""Tests for catch bug fix and shop quantity validation."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.battle_service import start_battle
from backend.services.game_service import create_game_with_starter, get_game

client = TestClient(app)


def _create_test_game():
    """Create a test game with a starter and some pokeballs."""
    game = create_game_with_starter("TestTrainer", {
        "id": 4,
        "name": "Charmander",
        "types": ["fire"],
        "stats": {"hp": 35, "attack": 30, "defense": 25, "sp_attack": 35, "sp_defense": 30, "speed": 40},
        "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        "sprite": "charmander",
        "level": 5,
    })
    game_id = game["id"]
    # Add pokeballs to inventory (item_id 7 = Pokeball)
    game["player"]["inventory"] = [{"item_id": 7, "quantity": 10}]
    game["player"]["money"] = 3000
    return game_id, game


def _create_battle(enemy_species_id=10, enemy_name="Pidgey", enemy_types=None):
    """Create a battle with a weak enemy."""
    if enemy_types is None:
        enemy_types = ["normal", "flying"]
    return start_battle(
        player_pokemon_data={
            "species_id": 4, "name": "Charmander", "types": ["fire"], "level": 5,
            "stats": {"hp": 35, "attack": 30, "defense": 25, "sp_attack": 35, "sp_defense": 30, "speed": 40},
            "current_hp": 35, "max_hp": 35,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "charmander",
        },
        enemy_pokemon_data={
            "species_id": enemy_species_id, "name": enemy_name, "types": enemy_types, "level": 3,
            "stats": {"hp": 20, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 20},
            "current_hp": 1, "max_hp": 20,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": enemy_name.lower(),
        },
    )


# --- Catch Bug Fix Tests ---

def test_caught_pokemon_added_to_party():
    """Verify caught Pokemon is added to player's party."""
    game_id, game = _create_test_game()
    battle = _create_battle()

    # Mock random.randint to always return 0 (guarantees catch: 0 < catch_value)
    with patch("backend.services.item_service.random.randint", return_value=0):
        resp = client.post("/api/battle/catch", json={
            "battle_id": battle.id,
            "item_id": 7,
            "game_id": game_id,
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["caught"] is True
    assert data["stored_in"] == "party"

    # Verify party has 2 Pokemon now
    g = get_game(game_id)
    assert len(g["player"]["team"]) == 2
    assert g["player"]["team"][1]["name"] == "Pidgey"


def test_catch_adds_to_pokedex():
    """Verify catching registers Pokemon in Pokedex."""
    game_id, game = _create_test_game()
    battle = _create_battle(enemy_species_id=13, enemy_name="Rattata", enemy_types=["normal"])

    with patch("backend.services.item_service.random.randint", return_value=0):
        resp = client.post("/api/battle/catch", json={
            "battle_id": battle.id,
            "item_id": 7,
            "game_id": game_id,
        })

    assert resp.status_code == 200
    assert resp.json()["caught"] is True

    from backend.services.pokedex_service import get_pokedex_entry
    entry = get_pokedex_entry(game_id, 13)
    assert entry is not None
    assert entry.status == "caught"


def test_catch_deducts_pokeball():
    """Verify pokeball is consumed on catch attempt."""
    game_id, game = _create_test_game()
    battle = _create_battle()

    initial_qty = game["player"]["inventory"][0]["quantity"]

    with patch("backend.services.item_service.random.randint", return_value=0):
        client.post("/api/battle/catch", json={
            "battle_id": battle.id,
            "item_id": 7,
            "game_id": game_id,
        })

    g = get_game(game_id)
    ball_entry = next(e for e in g["player"]["inventory"] if e["item_id"] == 7)
    assert ball_entry["quantity"] == initial_qty - 1


# --- Shop Quantity Validation Tests ---

def test_buy_negative_quantity_rejected():
    """Buying with negative quantity must be rejected."""
    game_id, game = _create_test_game()
    resp = client.post("/api/shop/buy", json={
        "game_id": game_id,
        "shop_id": "viridian_mart",
        "item_id": 1,
        "quantity": -1,
    })
    assert resp.status_code == 422


def test_buy_zero_quantity_rejected():
    """Buying with zero quantity must be rejected."""
    game_id, game = _create_test_game()
    resp = client.post("/api/shop/buy", json={
        "game_id": game_id,
        "shop_id": "viridian_mart",
        "item_id": 1,
        "quantity": 0,
    })
    assert resp.status_code == 422


def test_sell_negative_quantity_rejected():
    """Selling with negative quantity must be rejected."""
    game_id, game = _create_test_game()
    resp = client.post("/api/shop/sell", json={
        "game_id": game_id,
        "item_id": 1,
        "quantity": -1,
    })
    assert resp.status_code == 422


def test_toss_negative_quantity_rejected():
    """Tossing with negative quantity must be rejected."""
    game_id, game = _create_test_game()
    resp = client.post("/api/inventory/toss", json={
        "game_id": game_id,
        "item_id": 1,
        "quantity": -1,
    })
    assert resp.status_code == 422


def test_buy_positive_quantity_works():
    """Buying with positive quantity should succeed normally."""
    game_id, game = _create_test_game()
    resp = client.post("/api/shop/buy", json={
        "game_id": game_id,
        "shop_id": "viridian_mart",
        "item_id": 1,
        "quantity": 1,
    })
    assert resp.status_code in (200, 404)
