"""Tests for Sprint 9: Expanded Held Items & Evolution Stones.

Covers:
- Held item data definitions and lookup
- Type-boosting items (Charcoal, Mystic Water, etc.)
- Stat-boosting items (Choice Band, Choice Specs, Leftovers, Life Orb)
- Battle items (Focus Sash)
- EXP items (Lucky Egg)
- Equip/unequip held items on Pokemon
- Battle damage modifiers from held items
- End-of-turn held item effects (Leftovers, Life Orb recoil)
- Focus Sash OHKO prevention
- Evolution stones (Fire/Water/Thunder/Moon/Leaf Stone)
- Stone evolution compatibility and execution
- API endpoints for hold-item, remove-item, held-effects, stone usage
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game, _games

client = TestClient(app)


@pytest.fixture
def game():
    """Create a fresh game with Bulbasaur starter."""
    g = create_game("Tester", 1)
    return g


# ============================================================
# Held Item Definitions
# ============================================================

class TestHeldItemDefinitions:
    def test_get_all_held_items(self):
        """GET /api/items/held-effects returns held item definitions."""
        resp = client.get("/api/items/held-effects")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_charcoal_exists(self):
        """Charcoal held item definition exists with correct properties."""
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "charcoal" in items
        charcoal = items["charcoal"]
        assert charcoal["effect_type"] == "type_boost"
        assert charcoal["boost_type"] == "fire"
        assert charcoal["modifier"] == 1.2

    def test_mystic_water_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "mystic_water" in items
        assert items["mystic_water"]["boost_type"] == "water"

    def test_choice_band_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "choice_band" in items
        cb = items["choice_band"]
        assert cb["effect_type"] == "stat_boost"
        assert cb["modifier"] == 1.5

    def test_leftovers_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "leftovers" in items
        assert items["leftovers"]["effect_type"] == "end_of_turn_heal"

    def test_life_orb_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "life_orb" in items
        lo = items["life_orb"]
        assert lo["effect_type"] == "damage_boost_recoil"

    def test_focus_sash_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "focus_sash" in items
        assert items["focus_sash"]["effect_type"] == "survive_ohko"

    def test_lucky_egg_exists(self):
        resp = client.get("/api/items/held-effects")
        items = {i["id"]: i for i in resp.json()}
        assert "lucky_egg" in items
        assert items["lucky_egg"]["effect_type"] == "exp_boost"
        assert items["lucky_egg"]["modifier"] == 1.5


# ============================================================
# Equip/Unequip Held Items
# ============================================================

class TestEquipUnequip:
    def test_equip_held_item(self, game):
        """POST /api/pokemon/hold-item equips an item on a Pokemon."""
        gid = game["id"]
        resp = client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "charcoal"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["held_item"] == "charcoal"

    def test_equip_updates_pokemon(self, game):
        """After equip, the Pokemon's held_item is set in game state."""
        gid = game["id"]
        client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "leftovers"
        })
        pokemon = _games[gid]["player"]["team"][0]
        assert pokemon.get("held_item") == "leftovers"

    def test_equip_replaces_existing(self, game):
        """Equipping a new item replaces the old one."""
        gid = game["id"]
        client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "charcoal"
        })
        resp = client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "leftovers"
        })
        assert resp.status_code == 200
        assert resp.json()["held_item"] == "leftovers"
        assert resp.json().get("previous_item") == "charcoal"

    def test_equip_invalid_item(self, game):
        """Equipping unknown item returns 400."""
        gid = game["id"]
        resp = client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "nonexistent"
        })
        assert resp.status_code == 400

    def test_equip_invalid_pokemon_index(self, game):
        """Equipping on invalid index returns 400."""
        gid = game["id"]
        resp = client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 99, "item_id": "charcoal"
        })
        assert resp.status_code == 400

    def test_equip_invalid_game(self):
        """Equipping on invalid game returns 404."""
        resp = client.post("/api/pokemon/hold-item", json={
            "game_id": "bad", "pokemon_index": 0, "item_id": "charcoal"
        })
        assert resp.status_code == 404

    def test_remove_held_item(self, game):
        """POST /api/pokemon/remove-item removes held item."""
        gid = game["id"]
        client.post("/api/pokemon/hold-item", json={
            "game_id": gid, "pokemon_index": 0, "item_id": "charcoal"
        })
        resp = client.post("/api/pokemon/remove-item", json={
            "game_id": gid, "pokemon_index": 0
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["removed_item"] == "charcoal"

    def test_remove_no_item(self, game):
        """Removing when no item held returns success with removed_item=None."""
        gid = game["id"]
        resp = client.post("/api/pokemon/remove-item", json={
            "game_id": gid, "pokemon_index": 0
        })
        assert resp.status_code == 200
        assert resp.json()["removed_item"] is None


# ============================================================
# Held Item Battle Damage Modifiers
# ============================================================

class TestHeldItemDamageModifiers:
    def test_type_boost_charcoal(self):
        """Charcoal boosts fire-type move damage by 1.2x."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("charcoal", "fire", "physical")
        assert modifier == 1.2

    def test_type_boost_no_match(self):
        """Charcoal does not boost water-type moves."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("charcoal", "water", "physical")
        assert modifier == 1.0

    def test_mystic_water_boosts_water(self):
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("mystic_water", "water", "special")
        assert modifier == 1.2

    def test_miracle_seed_boosts_grass(self):
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("miracle_seed", "grass", "physical")
        assert modifier == 1.2

    def test_choice_band_boosts_physical(self):
        """Choice Band boosts physical attack damage by 1.5x regardless of type."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("choice_band", "fire", "physical")
        assert modifier == 1.5

    def test_choice_band_no_special(self):
        """Choice Band does not boost special moves."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("choice_band", "fire", "special")
        assert modifier == 1.0

    def test_choice_specs_boosts_special(self):
        """Choice Specs boosts special attack damage by 1.5x."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("choice_specs", "fire", "special")
        assert modifier == 1.5

    def test_choice_specs_no_physical(self):
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("choice_specs", "fire", "physical")
        assert modifier == 1.0

    def test_life_orb_boosts_all(self):
        """Life Orb boosts all attacking moves by 1.3x."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("life_orb", "water", "special")
        assert modifier == 1.3

    def test_no_held_item(self):
        """No held item returns 1.0 modifier."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier(None, "fire", "physical")
        assert modifier == 1.0

    def test_unknown_held_item(self):
        """Unknown held item returns 1.0 modifier."""
        from backend.services.held_item_service import get_held_item_damage_modifier
        modifier = get_held_item_damage_modifier("unknown_thing", "fire", "physical")
        assert modifier == 1.0


# ============================================================
# End-of-Turn Held Item Effects
# ============================================================

class TestEndOfTurnEffects:
    def test_leftovers_heals(self):
        """Leftovers heals 1/16 max HP at end of turn."""
        from backend.services.held_item_service import process_held_item_end_of_turn
        pokemon = {
            "name": "Bulbasaur", "current_hp": 80, "max_hp": 100,
            "held_item": "leftovers", "types": ["grass"],
        }
        events = process_held_item_end_of_turn(pokemon, "player")
        assert len(events) == 1
        assert events[0]["type"] == "heal"
        assert events[0]["amount"] == 6  # floor(100/16) = 6
        assert pokemon["current_hp"] == 86

    def test_leftovers_no_overheal(self):
        """Leftovers does not heal above max HP."""
        from backend.services.held_item_service import process_held_item_end_of_turn
        pokemon = {
            "name": "Bulbasaur", "current_hp": 99, "max_hp": 100,
            "held_item": "leftovers", "types": ["grass"],
        }
        events = process_held_item_end_of_turn(pokemon, "player")
        assert pokemon["current_hp"] == 100

    def test_leftovers_at_full_hp(self):
        """Leftovers does nothing at full HP."""
        from backend.services.held_item_service import process_held_item_end_of_turn
        pokemon = {
            "name": "Bulbasaur", "current_hp": 100, "max_hp": 100,
            "held_item": "leftovers", "types": ["grass"],
        }
        events = process_held_item_end_of_turn(pokemon, "player")
        assert len(events) == 0

    def test_life_orb_recoil(self):
        """Life Orb deals 10% max HP recoil after attacking."""
        from backend.services.held_item_service import process_held_item_after_attack
        pokemon = {
            "name": "Bulbasaur", "current_hp": 100, "max_hp": 100,
            "held_item": "life_orb", "types": ["grass"],
        }
        events = process_held_item_after_attack(pokemon, "player", did_damage=True)
        assert len(events) == 1
        assert events[0]["type"] == "recoil"
        assert events[0]["damage"] == 10  # 10% of 100
        assert pokemon["current_hp"] == 90

    def test_life_orb_no_recoil_on_miss(self):
        """Life Orb does not cause recoil if no damage was dealt."""
        from backend.services.held_item_service import process_held_item_after_attack
        pokemon = {
            "name": "Bulbasaur", "current_hp": 100, "max_hp": 100,
            "held_item": "life_orb", "types": ["grass"],
        }
        events = process_held_item_after_attack(pokemon, "player", did_damage=False)
        assert len(events) == 0

    def test_no_held_item_no_effect(self):
        """No held item produces no end-of-turn effects."""
        from backend.services.held_item_service import process_held_item_end_of_turn
        pokemon = {
            "name": "Bulbasaur", "current_hp": 80, "max_hp": 100,
            "held_item": None, "types": ["grass"],
        }
        events = process_held_item_end_of_turn(pokemon, "player")
        assert len(events) == 0


# ============================================================
# Focus Sash
# ============================================================

class TestFocusSash:
    def test_focus_sash_survives_ohko(self):
        """Focus Sash lets Pokemon survive OHKO at 1 HP when at full HP."""
        from backend.services.held_item_service import apply_focus_sash
        pokemon = {
            "name": "Pikachu", "current_hp": 100, "max_hp": 100,
            "held_item": "focus_sash", "types": ["electric"],
        }
        result = apply_focus_sash(pokemon, incoming_damage=200)
        assert result["survived"] is True
        assert result["new_hp"] == 1
        assert result["consumed"] is True

    def test_focus_sash_not_at_full_hp(self):
        """Focus Sash does not activate if not at full HP."""
        from backend.services.held_item_service import apply_focus_sash
        pokemon = {
            "name": "Pikachu", "current_hp": 99, "max_hp": 100,
            "held_item": "focus_sash", "types": ["electric"],
        }
        result = apply_focus_sash(pokemon, incoming_damage=200)
        assert result["survived"] is False

    def test_focus_sash_not_ohko(self):
        """Focus Sash doesn't activate if damage doesn't KO."""
        from backend.services.held_item_service import apply_focus_sash
        pokemon = {
            "name": "Pikachu", "current_hp": 100, "max_hp": 100,
            "held_item": "focus_sash", "types": ["electric"],
        }
        result = apply_focus_sash(pokemon, incoming_damage=50)
        assert result["survived"] is False

    def test_focus_sash_consumed_after_use(self):
        """Focus Sash is consumed after activation."""
        from backend.services.held_item_service import apply_focus_sash
        pokemon = {
            "name": "Pikachu", "current_hp": 100, "max_hp": 100,
            "held_item": "focus_sash", "types": ["electric"],
        }
        apply_focus_sash(pokemon, incoming_damage=200)
        assert pokemon["held_item"] is None

    def test_no_focus_sash(self):
        """Without Focus Sash, no survival effect."""
        from backend.services.held_item_service import apply_focus_sash
        pokemon = {
            "name": "Pikachu", "current_hp": 100, "max_hp": 100,
            "held_item": None, "types": ["electric"],
        }
        result = apply_focus_sash(pokemon, incoming_damage=200)
        assert result["survived"] is False


# ============================================================
# Lucky Egg (EXP Boost)
# ============================================================

class TestLuckyEgg:
    def test_lucky_egg_multiplier(self):
        """Lucky Egg returns 1.5x EXP multiplier."""
        from backend.services.held_item_service import get_exp_multiplier
        assert get_exp_multiplier("lucky_egg") == 1.5

    def test_no_item_exp_multiplier(self):
        """No held item returns 1.0x EXP multiplier."""
        from backend.services.held_item_service import get_exp_multiplier
        assert get_exp_multiplier(None) == 1.0

    def test_other_item_exp_multiplier(self):
        """Non-EXP items return 1.0x."""
        from backend.services.held_item_service import get_exp_multiplier
        assert get_exp_multiplier("charcoal") == 1.0


# ============================================================
# Evolution Stones
# ============================================================

class TestEvolutionStones:
    def test_stone_definitions_exist(self):
        """Evolution stone definitions are available."""
        from backend.services.held_item_service import get_evolution_stones
        stones = get_evolution_stones()
        assert "fire_stone" in stones
        assert "water_stone" in stones
        assert "thunder_stone" in stones
        assert "moon_stone" in stones
        assert "leaf_stone" in stones

    def test_fire_stone_evolves_eevee_to_flareon(self):
        """Fire Stone can evolve Eevee into Flareon."""
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(133, "fire_stone")  # Eevee
        assert result is not None
        assert result["to_name"] == "Flareon"

    def test_water_stone_evolves_eevee_to_vaporeon(self):
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(133, "water_stone")
        assert result is not None
        assert result["to_name"] == "Vaporeon"

    def test_thunder_stone_evolves_eevee_to_jolteon(self):
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(133, "thunder_stone")
        assert result is not None
        assert result["to_name"] == "Jolteon"

    def test_thunder_stone_evolves_pikachu(self):
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(15, "thunder_stone")  # Pikachu
        assert result is not None
        assert result["to_name"] == "Raichu"

    def test_wrong_stone_returns_none(self):
        """Using wrong stone on a Pokemon returns None."""
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(133, "moon_stone")  # Eevee + Moon Stone
        assert result is None

    def test_no_stone_evolution_returns_none(self):
        """Pokemon with no stone evolution returns None."""
        from backend.services.held_item_service import check_stone_evolution
        result = check_stone_evolution(1, "fire_stone")  # Bulbasaur
        assert result is None


class TestStoneEvolutionAPI:
    def test_use_stone_on_pokemon(self, game):
        """POST /api/evolution/stone uses a stone to evolve a Pokemon."""
        gid = game["id"]
        # Replace team member with Eevee
        _games[gid]["player"]["team"][0] = {
            "id": 133, "name": "Eevee", "types": ["normal"], "level": 25,
            "stats": {"hp": 65, "attack": 55, "defense": 50, "sp_attack": 45, "sp_defense": 65, "speed": 55},
            "current_hp": 65, "max_hp": 65,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "eevee.png",
        }
        resp = client.post("/api/evolution/stone", json={
            "game_id": gid, "pokemon_index": 0, "stone_id": "fire_stone"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["new_name"] == "Flareon"

    def test_use_stone_updates_game_state(self, game):
        """After stone evolution, game state reflects new species."""
        gid = game["id"]
        _games[gid]["player"]["team"][0] = {
            "id": 133, "name": "Eevee", "types": ["normal"], "level": 25,
            "stats": {"hp": 65, "attack": 55, "defense": 50, "sp_attack": 45, "sp_defense": 65, "speed": 55},
            "current_hp": 65, "max_hp": 65,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "eevee.png",
        }
        client.post("/api/evolution/stone", json={
            "game_id": gid, "pokemon_index": 0, "stone_id": "fire_stone"
        })
        pokemon = _games[gid]["player"]["team"][0]
        assert pokemon["name"] == "Flareon"

    def test_use_wrong_stone(self, game):
        """Using incompatible stone returns 400."""
        gid = game["id"]
        # Bulbasaur can't use fire stone
        resp = client.post("/api/evolution/stone", json={
            "game_id": gid, "pokemon_index": 0, "stone_id": "fire_stone"
        })
        assert resp.status_code == 400

    def test_use_invalid_stone(self, game):
        """Using unknown stone returns 400."""
        gid = game["id"]
        resp = client.post("/api/evolution/stone", json={
            "game_id": gid, "pokemon_index": 0, "stone_id": "chaos_stone"
        })
        assert resp.status_code == 400

    def test_use_stone_invalid_game(self):
        """Using stone on invalid game returns 404."""
        resp = client.post("/api/evolution/stone", json={
            "game_id": "bad", "pokemon_index": 0, "stone_id": "fire_stone"
        })
        assert resp.status_code == 404

    def test_stone_evolution_records_achievement(self, game):
        """BUG #171: Stone evolution must call record_evolution + check_achievements."""
        from backend.services.leaderboard_service import _player_stats
        gid = game["id"]
        # Clear any existing stats
        _player_stats.pop(gid, None)
        # Set up Eevee for evolution
        _games[gid]["player"]["team"][0] = {
            "id": 133, "name": "Eevee", "types": ["normal"], "level": 25,
            "stats": {"hp": 65, "attack": 55, "defense": 50, "sp_attack": 45, "sp_defense": 65, "speed": 55},
            "current_hp": 65, "max_hp": 65,
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "sprite": "eevee.png",
        }
        resp = client.post("/api/evolution/stone", json={
            "game_id": gid, "pokemon_index": 0, "stone_id": "fire_stone"
        })
        assert resp.status_code == 200
        # After stone evolution, evolution count should be incremented
        stats = _player_stats.get(gid, {})
        assert stats.get("evolutions", 0) >= 1, (
            "Stone evolution did not call record_evolution() — evolutions stat is 0"
        )
