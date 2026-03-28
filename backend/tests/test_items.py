"""Tests for the items, inventory, shop, and catch system (Sprint 3 QA-A)."""
import pytest
from unittest.mock import patch

from backend.services.item_service import (
    attempt_catch,
    buy_item,
    get_all_items,
    get_inventory,
    get_item,
    get_shop,
    sell_item,
    toss_item,
    use_item,
    STARTING_MONEY,
)
from backend.services.game_service import create_game, get_game
from backend.services.battle_service import start_battle


# ────────────────────────────────────────────
# Item data tests
# ────────────────────────────────────────────
class TestItemData:
    def test_items_loaded(self):
        items = get_all_items()
        assert len(items) >= 9

    def test_potion_exists(self):
        item = get_item(1)
        assert item is not None
        assert item.name == "Potion"
        assert item.price == 300
        assert item.effect.type == "heal_hp"
        assert item.effect.amount == 20

    def test_super_potion(self):
        item = get_item(2)
        assert item is not None
        assert item.name == "Super Potion"
        assert item.effect.amount == 50

    def test_pokeball(self):
        item = get_item(7)
        assert item is not None
        assert item.name == "Pokeball"
        assert item.category == "pokeball"
        assert item.effect.type == "catch"
        assert item.effect.modifier == 1.0

    def test_great_ball_modifier(self):
        item = get_item(8)
        assert item.effect.modifier == 1.5

    def test_ultra_ball_modifier(self):
        item = get_item(9)
        assert item.effect.modifier == 2.0

    def test_revive(self):
        item = get_item(6)
        assert item.name == "Revive"
        assert item.effect.type == "revive"
        assert item.effect.amount == 0.5

    def test_full_heal(self):
        item = get_item(5)
        assert item.name == "Full Heal"
        assert item.effect.type == "cure_status"
        assert item.effect.status == "all"

    def test_sell_price_half_of_buy(self):
        items = get_all_items()
        for item in items:
            assert item.sell_price == item.price // 2

    def test_invalid_item(self):
        assert get_item(9999) is None


# ────────────────────────────────────────────
# Shop tests
# ────────────────────────────────────────────
class TestShops:
    def test_pallet_shop(self):
        shop = get_shop("pallet_shop")
        assert shop is not None
        assert shop.name == "Pallet Town Shop"
        assert len(shop.items) == 2

    def test_viridian_shop(self):
        shop = get_shop("viridian_shop")
        assert shop is not None
        assert shop.name == "Viridian City Pokemart"
        assert len(shop.items) == 8

    def test_invalid_shop(self):
        assert get_shop("nonexistent") is None

    def test_shop_items_have_prices(self):
        shop = get_shop("viridian_shop")
        for item in shop.items:
            assert item.price > 0
            assert item.name != ""


# ────────────────────────────────────────────
# Inventory management tests
# ────────────────────────────────────────────
class TestInventory:
    def test_empty_inventory(self):
        game = create_game("Ash", 4)
        inv = get_inventory(game["id"])
        assert inv is not None
        assert len(inv) == 0

    def test_inventory_invalid_game(self):
        assert get_inventory("nonexistent") is None


# ────────────────────────────────────────────
# Buy item tests
# ────────────────────────────────────────────
class TestBuyItem:
    def test_buy_item_success(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        result = buy_item(game_id, "pallet_shop", 1, 1)  # Buy 1 Potion
        assert result is not None
        assert result.success is True
        assert result.money == STARTING_MONEY - 300
        assert any(e.item_id == 1 for e in result.inventory)

    def test_buy_multiple(self):
        game = create_game("Ash", 4)
        result = buy_item(game["id"], "pallet_shop", 1, 3)
        assert result.success is True
        assert result.money == STARTING_MONEY - 900
        entry = next(e for e in result.inventory if e.item_id == 1)
        assert entry.quantity == 3

    def test_buy_not_enough_money(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        # Try to buy too many
        result = buy_item(game_id, "pallet_shop", 1, 100)  # 100 * 300 = 30000 > 3000
        assert result.success is False
        assert "money" in result.message.lower()

    def test_buy_invalid_item(self):
        game = create_game("Ash", 4)
        result = buy_item(game["id"], "pallet_shop", 9999, 1)
        assert result.success is False

    def test_buy_invalid_game(self):
        result = buy_item("nonexistent", "pallet_shop", 1, 1)
        assert result is None

    def test_buy_stacks_quantities(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 2)
        buy_item(game_id, "pallet_shop", 1, 3)
        inv = get_inventory(game_id)
        entry = next(e for e in inv if e.item_id == 1)
        assert entry.quantity == 5


# ────────────────────────────────────────────
# Sell item tests
# ────────────────────────────────────────────
class TestSellItem:
    def test_sell_item_success(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 2)  # Buy 2 Potions (cost 600)
        result = sell_item(game_id, 1, 1)  # Sell 1 Potion
        assert result.success is True
        assert result.money == STARTING_MONEY - 600 + 150  # sell_price = 150
        entry = next(e for e in result.inventory if e.item_id == 1)
        assert entry.quantity == 1

    def test_sell_not_enough_items(self):
        game = create_game("Ash", 4)
        result = sell_item(game["id"], 1, 1)  # No potions to sell
        assert result.success is False

    def test_sell_invalid_game(self):
        result = sell_item("nonexistent", 1, 1)
        assert result is None


# ────────────────────────────────────────────
# Use item tests
# ────────────────────────────────────────────
class TestUseItem:
    def _setup_game_with_potion(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 5)  # Buy 5 Potions
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        max_hp = pokemon["stats"]["hp"]
        pokemon["current_hp"] = max_hp - 30  # Damage the Pokemon
        return game_id, stored

    def test_use_potion(self):
        game_id, game = self._setup_game_with_potion()
        pokemon = game["player"]["team"][0]
        old_hp = pokemon["current_hp"]
        result = use_item(game_id, 1, 0)
        assert result is not None
        assert result.success is True
        assert result.healed_amount == 20
        assert result.new_hp == old_hp + 20

    def test_use_potion_full_hp(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 1)
        result = use_item(game_id, 1, 0)
        assert result.success is False
        assert "full" in result.message.lower()

    def test_use_potion_no_target(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 1)
        stored = get_game(game_id)
        stored["player"]["team"][0]["current_hp"] = 1
        result = use_item(game_id, 1, None)
        assert result.success is False

    def test_use_potion_not_in_inventory(self):
        game = create_game("Ash", 4)
        stored = get_game(game["id"])
        stored["player"]["team"][0]["current_hp"] = 1
        result = use_item(game["id"], 1, 0)
        assert result.success is False
        assert "inventory" in result.message.lower()

    def test_use_potion_decrements_quantity(self):
        game_id, _ = self._setup_game_with_potion()
        use_item(game_id, 1, 0)
        inv = get_inventory(game_id)
        entry = next(e for e in inv if e.item_id == 1)
        assert entry.quantity == 4  # Started with 5, used 1

    def test_use_revive_on_fainted(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        # Buy revive from viridian shop
        buy_item(game_id, "viridian_shop", 6, 1)
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        max_hp = pokemon["stats"]["hp"]
        pokemon["current_hp"] = 0  # Fainted
        result = use_item(game_id, 6, 0)
        assert result.success is True
        assert result.new_hp == max(1, int(max_hp * 0.5))

    def test_use_revive_on_alive_pokemon(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "viridian_shop", 6, 1)
        result = use_item(game_id, 6, 0)
        assert result.success is False
        assert "not fainted" in result.message.lower()

    def test_use_potion_on_fainted(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 1)
        stored = get_game(game_id)
        stored["player"]["team"][0]["current_hp"] = 0
        result = use_item(game_id, 1, 0)
        assert result.success is False
        assert "fainted" in result.message.lower()

    def test_use_status_heal(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "viridian_shop", 3, 1)  # Antidote
        stored = get_game(game_id)
        stored["player"]["team"][0]["status"] = "poison"
        result = use_item(game_id, 3, 0)
        assert result.success is True
        assert result.status_removed == "poison"

    def test_use_status_heal_wrong_status(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "viridian_shop", 3, 1)  # Antidote (poison only)
        stored = get_game(game_id)
        stored["player"]["team"][0]["status"] = "paralysis"
        result = use_item(game_id, 3, 0)
        assert result.success is False

    def test_use_full_heal_any_status(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "viridian_shop", 5, 1)  # Full Heal
        stored = get_game(game_id)
        stored["player"]["team"][0]["status"] = "paralysis"
        result = use_item(game_id, 5, 0)
        assert result.success is True
        assert result.status_removed == "paralysis"

    def test_use_status_heal_no_status(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "viridian_shop", 3, 1)
        result = use_item(game_id, 3, 0)
        assert result.success is False

    def test_use_invalid_game(self):
        result = use_item("nonexistent", 1, 0)
        assert result is None

    def test_use_potion_caps_at_max_hp(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 1)
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        max_hp = pokemon["stats"]["hp"]
        pokemon["current_hp"] = max_hp - 5  # Only 5 HP missing
        result = use_item(game_id, 1, 0)
        assert result.success is True
        assert result.new_hp == max_hp  # Capped at max
        assert result.healed_amount == 5  # Only healed 5


# ────────────────────────────────────────────
# Toss item tests
# ────────────────────────────────────────────
class TestTossItem:
    def test_toss_item(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 5)
        result = toss_item(game_id, 1, 3)
        assert result is not None
        entry = next(e for e in result if e.item_id == 1)
        assert entry.quantity == 2

    def test_toss_all(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        buy_item(game_id, "pallet_shop", 1, 5)
        result = toss_item(game_id, 1, 5)
        entry = next(e for e in result if e.item_id == 1)
        assert entry.quantity == 0

    def test_toss_invalid_game(self):
        result = toss_item("nonexistent", 1, 1)
        assert result is None


# ────────────────────────────────────────────
# Catch system tests
# ────────────────────────────────────────────
class TestCatchSystem:
    def test_catch_always_succeeds(self):
        enemy = {
            "stats": {"hp": 45},
            "current_hp": 1,
            "catch_rate": 255,  # Max catch rate
        }
        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 0  # Always below catch_value
            result = attempt_catch(enemy, 2.0)  # Ultra ball
            assert result.caught is True
            assert result.shakes == 3

    def test_catch_fails(self):
        enemy = {
            "stats": {"hp": 45},
            "current_hp": 45,  # Full HP
            "catch_rate": 3,  # Very low
        }
        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 255  # Always above catch_value
            result = attempt_catch(enemy, 1.0)
            assert result.caught is False
            assert result.shakes == 0

    def test_catch_partial_shakes(self):
        enemy = {
            "stats": {"hp": 100},
            "current_hp": 50,
            "catch_rate": 100,
        }
        with patch("backend.services.item_service.random") as mock_random:
            # First shake succeeds, second fails
            mock_random.randint.side_effect = [0, 255, 255]
            result = attempt_catch(enemy, 1.0)
            assert result.caught is False
            assert result.shakes == 1

    def test_catch_message_on_success(self):
        enemy = {"stats": {"hp": 45}, "current_hp": 1, "catch_rate": 255}
        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 0
            result = attempt_catch(enemy, 2.0)
            assert "caught" in result.message.lower()

    def test_catch_message_on_fail(self):
        enemy = {"stats": {"hp": 45}, "current_hp": 45, "catch_rate": 3}
        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 255
            result = attempt_catch(enemy, 1.0)
            assert "broke free" in result.message.lower()

    def test_ball_modifier_affects_catch(self):
        enemy = {"stats": {"hp": 100}, "current_hp": 50, "catch_rate": 100}
        # With higher modifier, catch_value is higher, making catch easier
        # catch_value = ((3*100 - 2*50) * 100 * modifier) / (3*100) = 100*modifier/3
        # With modifier=1: cv ~ 33.3
        # With modifier=2: cv ~ 66.7
        # This is a formula test, not a random test
        from backend.services.item_service import attempt_catch as ac
        # Just verify the formula works by checking different modifiers produce different results
        # deterministically
        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 50  # Between 33 and 67
            r1 = attempt_catch(enemy, 1.0)
            mock_random.randint.return_value = 50
            mock_random.randint.side_effect = None
            mock_random.randint.return_value = 50
            r2 = attempt_catch(enemy, 3.0)
            # With modifier 3.0, catch_value ~100 > 50, so should get more shakes
            assert r2.shakes >= r1.shakes


# ────────────────────────────────────────────
# Items API tests
# ────────────────────────────────────────────
class TestItemsAPI:
    def test_list_items(self, client):
        resp = client.get("/api/items")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 9

    def test_item_detail(self, client):
        resp = client.get("/api/items/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Potion"

    def test_item_not_found(self, client):
        resp = client.get("/api/items/9999")
        assert resp.status_code == 404

    def test_inventory_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.get(f"/api/inventory/{game_id}")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_inventory_not_found(self, client):
        resp = client.get("/api/inventory/nonexistent")
        assert resp.status_code == 404

    def test_use_item_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Buy a potion first
        client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 1, "quantity": 1,
        })
        stored = get_game(game_id)
        stored["player"]["team"][0]["current_hp"] = 1
        resp = client.post("/api/inventory/use", json={
            "game_id": game_id, "item_id": 1, "target_pokemon_index": 0,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_toss_item_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 1, "quantity": 5,
        })
        resp = client.post("/api/inventory/toss", json={
            "game_id": game_id, "item_id": 1, "quantity": 2,
        })
        assert resp.status_code == 200

    def test_shop_endpoint(self, client):
        resp = client.get("/api/shop/pallet_shop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Pallet Town Shop"

    def test_shop_not_found(self, client):
        resp = client.get("/api/shop/nonexistent")
        assert resp.status_code == 404

    def test_buy_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 1, "quantity": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_sell_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Buy first, then sell
        client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 1, "quantity": 2,
        })
        resp = client.post("/api/shop/sell", json={
            "game_id": game_id, "item_id": 1, "quantity": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_catch_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Buy pokeballs
        client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 7, "quantity": 5,
        })
        # Start a wild battle (endpoint uses game_id + optional wild_pokemon)
        wild_pokemon = {
            "species_id": 16, "name": "Pidgey", "types": ["normal", "flying"],
            "level": 3,
            "stats": {"hp": 20, "attack": 12, "defense": 10, "sp_attack": 10, "sp_defense": 10, "speed": 14},
            "current_hp": 1, "max_hp": 20,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "pidgey.png", "catch_rate": 255,
        }
        resp = client.post("/api/battle/start", json={
            "game_id": game_id, "wild_pokemon": wild_pokemon,
        })
        assert resp.status_code == 200
        battle_id = resp.json()["battle"]["id"]

        with patch("backend.services.item_service.random") as mock_random:
            mock_random.randint.return_value = 0
            resp = client.post("/api/battle/catch", json={
                "battle_id": battle_id, "item_id": 7, "game_id": game_id,
            })
            assert resp.status_code == 200

    def test_catch_not_wild_battle(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Start a wild battle but then change its type to trainer for testing
        resp = client.post("/api/battle/start", json={"game_id": game_id})
        assert resp.status_code == 200
        battle_id = resp.json()["battle"]["id"]
        # Modify battle type to trainer
        from backend.services.battle_service import get_battle
        battle = get_battle(battle_id)
        battle.battle_type = "trainer"
        client.post("/api/shop/buy", json={
            "game_id": game_id, "shop_id": "pallet_shop", "item_id": 7, "quantity": 1,
        })
        resp = client.post("/api/battle/catch", json={
            "battle_id": battle_id, "item_id": 7, "game_id": game_id,
        })
        assert resp.status_code == 400
        assert "trainer" in resp.json()["detail"].lower()
