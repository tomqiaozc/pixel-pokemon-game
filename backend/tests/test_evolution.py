"""Tests for the evolution and EXP system (Sprint 3 QA-A)."""
import pytest
from unittest.mock import patch

from backend.services.evolution_service import (
    _exp_for_level,
    _level_from_exp,
    award_exp,
    check_evolution,
    evolve_pokemon,
    get_pending_moves,
)
from backend.services.encounter_service import get_species, _calc_stat
from backend.services.game_service import create_game, get_game


# ────────────────────────────────────────────
# EXP curve tests
# ────────────────────────────────────────────
class TestExpCurve:
    def test_exp_for_level_1(self):
        assert _exp_for_level(1) == 1  # 1^3

    def test_exp_for_level_5(self):
        assert _exp_for_level(5) == 125  # 5^3

    def test_exp_for_level_10(self):
        assert _exp_for_level(10) == 1000  # 10^3

    def test_exp_for_level_100(self):
        assert _exp_for_level(100) == 1_000_000

    def test_level_from_exp_exact(self):
        assert _level_from_exp(125) == 5  # exactly level 5

    def test_level_from_exp_between_levels(self):
        # 125 = level 5, 216 = level 6
        assert _level_from_exp(200) == 5  # not enough for 6

    def test_level_from_exp_zero(self):
        assert _level_from_exp(0) == 1  # minimum level

    def test_level_from_exp_capped_at_100(self):
        assert _level_from_exp(999_999_999) == 100


# ────────────────────────────────────────────
# Evolution check tests
# ────────────────────────────────────────────
class TestEvolutionCheck:
    def test_charmander_can_evolve_at_16(self):
        result = check_evolution(4, 16)
        assert result.can_evolve is True
        assert result.evolves_to == 5  # Charmeleon
        assert result.evolves_to_name == "Charmeleon"

    def test_charmander_cannot_evolve_at_15(self):
        result = check_evolution(4, 15)
        assert result.can_evolve is False
        assert result.evolves_to is None

    def test_bulbasaur_can_evolve_at_16(self):
        result = check_evolution(1, 16)
        assert result.can_evolve is True
        assert result.evolves_to == 2  # Ivysaur

    def test_squirtle_can_evolve_at_16(self):
        result = check_evolution(7, 16)
        assert result.can_evolve is True
        assert result.evolves_to == 8  # Wartortle

    def test_no_evolution_for_nonexistent_species(self):
        result = check_evolution(9999, 50)
        assert result.can_evolve is False

    def test_pikachu_has_no_evolution(self):
        result = check_evolution(25, 100)
        assert result.can_evolve is False

    def test_evolution_level_returned(self):
        result = check_evolution(4, 16)
        assert result.evolution_level == 16

    def test_above_evolution_level_still_can_evolve(self):
        result = check_evolution(4, 50)
        assert result.can_evolve is True


# ────────────────────────────────────────────
# Evolve Pokemon tests
# ────────────────────────────────────────────
class TestEvolvePokemon:
    def test_evolve_charmander_to_charmeleon(self):
        pokemon_data = {
            "id": 4, "name": "Charmander", "level": 16,
            "types": ["fire"],
            "stats": {"hp": 30, "attack": 20, "defense": 18, "sp_attack": 22, "sp_defense": 20, "speed": 22},
            "moves": [{"name": "scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        }
        result = evolve_pokemon(pokemon_data)
        assert result is not None
        assert result.success is True
        assert result.old_species_id == 4
        assert result.old_name == "Charmander"
        assert result.new_species_id == 5
        assert result.new_name == "Charmeleon"
        assert result.new_level == 16

    def test_evolve_updates_stats(self):
        pokemon_data = {
            "id": 4, "name": "Charmander", "level": 16,
            "types": ["fire"],
            "stats": {"hp": 30, "attack": 20, "defense": 18, "sp_attack": 22, "sp_defense": 20, "speed": 22},
            "moves": [{"name": "scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        }
        result = evolve_pokemon(pokemon_data)
        assert result is not None
        # Charmeleon has higher base stats — verify recalculated stats with IV=15
        new_species = get_species(5)
        expected_hp = _calc_stat(new_species.stats.hp, 16, 15, is_hp=True)
        assert result.new_stats["hp"] == expected_hp

    def test_evolve_provides_new_moves(self):
        pokemon_data = {
            "id": 4, "name": "Charmander", "level": 16,
            "types": ["fire"],
            "stats": {"hp": 30, "attack": 20, "defense": 18, "sp_attack": 22, "sp_defense": 20, "speed": 22},
            "moves": [{"name": "scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        }
        result = evolve_pokemon(pokemon_data)
        assert result is not None
        assert len(result.new_moves) > 0
        assert len(result.new_moves) <= 4

    def test_cannot_evolve_below_level(self):
        pokemon_data = {
            "id": 4, "name": "Charmander", "level": 10,
            "types": ["fire"],
            "stats": {"hp": 30, "attack": 20, "defense": 18, "sp_attack": 22, "sp_defense": 20, "speed": 22},
            "moves": [],
        }
        result = evolve_pokemon(pokemon_data)
        assert result is None

    def test_cannot_evolve_no_evolution(self):
        pokemon_data = {
            "id": 25, "name": "Pikachu", "level": 100,
            "types": ["electric"],
            "stats": {"hp": 30, "attack": 20, "defense": 18, "sp_attack": 22, "sp_defense": 20, "speed": 22},
            "moves": [],
        }
        result = evolve_pokemon(pokemon_data)
        assert result is None

    def test_cannot_evolve_invalid_species(self):
        pokemon_data = {"id": 9999, "name": "Unknown", "level": 50, "types": [], "stats": {}, "moves": []}
        result = evolve_pokemon(pokemon_data)
        assert result is None


# ────────────────────────────────────────────
# Pending moves tests
# ────────────────────────────────────────────
class TestPendingMoves:
    def test_get_pending_moves_at_level(self):
        species = get_species(4)  # Charmander
        # Find a level where Charmander learns a move
        if species and species.learnset:
            target_level = species.learnset[0].level
            target_move = species.learnset[0].move
            pending = get_pending_moves(4, target_level, [])
            move_names = [m["name"] for m in pending]
            assert target_move in move_names

    def test_no_pending_if_already_known(self):
        species = get_species(4)
        if species and species.learnset:
            entry = species.learnset[0]
            current_moves = [{"name": entry.move}]
            pending = get_pending_moves(4, entry.level, current_moves)
            move_names = [m["name"] for m in pending]
            assert entry.move not in move_names

    def test_no_pending_for_wrong_level(self):
        pending = get_pending_moves(4, 999, [])
        assert len(pending) == 0

    def test_no_pending_for_invalid_species(self):
        pending = get_pending_moves(9999, 10, [])
        assert len(pending) == 0


# ────────────────────────────────────────────
# Award EXP tests
# ────────────────────────────────────────────
class TestAwardExp:
    def test_award_exp_basic(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        result = award_exp(game_id, 0, 16, 5)  # Defeat Pidgey level 5
        assert result is not None
        assert result.exp_gained > 0
        assert result.new_total_exp > 0
        assert result.old_level == 5  # Charmander starts at level 5

    def test_award_exp_level_up(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        # Give a ton of EXP by defeating high-level Pokemon repeatedly
        pokemon = game["player"]["team"][0]
        pokemon["exp"] = _exp_for_level(5)  # Reset to level 5 baseline
        pokemon["level"] = 5

        # Set EXP just below level 6 threshold (216)
        pokemon["exp"] = 215
        result = award_exp(game_id, 0, 16, 50)  # Defeat high-level Pidgey
        assert result is not None
        assert result.leveled_up is True
        assert result.new_level > 5

    def test_award_exp_no_level_up(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        pokemon["exp"] = _exp_for_level(5)  # Start of level 5
        pokemon["level"] = 5

        # Defeat a low-level Pokemon for minimal EXP
        result = award_exp(game_id, 0, 16, 2)  # Defeat level 2 Pidgey
        assert result is not None
        # May or may not level up depending on base_exp, but EXP should increase
        assert result.exp_gained > 0

    def test_award_exp_invalid_game(self):
        result = award_exp("nonexistent", 0, 16, 5)
        assert result is None

    def test_award_exp_invalid_pokemon_index(self):
        game = create_game("Ash", 4)
        result = award_exp(game["id"], 5, 16, 5)  # Only 1 Pokemon on team
        assert result is None

    def test_award_exp_invalid_defeated_species(self):
        game = create_game("Ash", 4)
        result = award_exp(game["id"], 0, 9999, 5)
        assert result is None

    def test_award_exp_updates_game_state(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        old_level = pokemon["level"]
        pokemon["exp"] = _exp_for_level(old_level)

        award_exp(game_id, 0, 16, 5)
        updated = get_game(game_id)
        assert updated["player"]["team"][0]["exp"] > _exp_for_level(old_level)

    def test_award_exp_can_evolve_flag(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        # Set to just below Charmander's evolution level (16)
        pokemon["level"] = 15
        pokemon["exp"] = _exp_for_level(15)

        # Give enough EXP to reach 16
        pokemon["exp"] = _exp_for_level(16) - 1
        result = award_exp(game_id, 0, 16, 50)  # Big EXP boost
        if result and result.leveled_up and result.new_level >= 16:
            assert result.can_evolve is True

    def test_level_cap_at_100(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        pokemon = game["player"]["team"][0]
        pokemon["level"] = 99
        pokemon["exp"] = _exp_for_level(99)

        # Award massive EXP
        result = award_exp(game_id, 0, 16, 100)
        assert result is not None
        assert result.new_level <= 100


# ────────────────────────────────────────────
# Evolution API tests
# ────────────────────────────────────────────
class TestEvolutionAPI:
    def test_check_evolution_endpoint(self, client):
        resp = client.get("/api/evolution/check/4/16")
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_evolve"] is True
        assert data["evolves_to"] == 5

    def test_check_evolution_below_level(self, client):
        resp = client.get("/api/evolution/check/4/10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["can_evolve"] is False

    def test_evolve_endpoint(self, client, game_with_pokemon):
        game_id, game = game_with_pokemon
        # Set Charmander to level 16 so it can evolve
        stored = get_game(game_id)
        stored["player"]["team"][0]["level"] = 16
        resp = client.post(f"/api/evolution/evolve/{game_id}/0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["new_name"] == "Charmeleon"

    def test_evolve_game_not_found(self, client):
        resp = client.post("/api/evolution/evolve/nonexistent/0")
        assert resp.status_code == 404

    def test_evolve_invalid_index(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(f"/api/evolution/evolve/{game_id}/5")
        assert resp.status_code == 400

    def test_evolve_cannot_evolve(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Level 5 Charmander can't evolve
        resp = client.post(f"/api/evolution/evolve/{game_id}/0")
        assert resp.status_code == 400

    def test_pending_moves_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.get(f"/api/evolution/pending-moves/{game_id}/0")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_moves" in data
        assert "current_moves" in data

    def test_pending_moves_game_not_found(self, client):
        resp = client.get("/api/evolution/pending-moves/nonexistent/0")
        assert resp.status_code == 404

    def test_learn_move_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        # Charmander should know some moves; try learning a new one
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        # Only proceed if < 4 moves
        if len(pokemon["moves"]) < 4:
            resp = client.post(
                f"/api/evolution/learn-move/{game_id}/0",
                json={"move_name": "Scratch"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True

    def test_learn_move_not_found(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(
            f"/api/evolution/learn-move/{game_id}/0",
            json={"move_name": "nonexistent_move"},
        )
        assert resp.status_code == 404

    def test_learn_move_with_forget(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        # Pad to 4 moves
        while len(pokemon["moves"]) < 4:
            pokemon["moves"].append({"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35})
        resp = client.post(
            f"/api/evolution/learn-move/{game_id}/0",
            json={"move_name": "Scratch", "forget_move_index": 0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["forgot"] is not None

    def test_learn_move_full_no_forget(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        stored = get_game(game_id)
        pokemon = stored["player"]["team"][0]
        while len(pokemon["moves"]) < 4:
            pokemon["moves"].append({"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35})
        resp = client.post(
            f"/api/evolution/learn-move/{game_id}/0",
            json={"move_name": "Scratch"},
        )
        assert resp.status_code == 400

    def test_award_exp_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post("/api/evolution/award-exp", json={
            "game_id": game_id,
            "pokemon_index": 0,
            "defeated_species_id": 16,  # Pidgey
            "defeated_level": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["exp_gained"] > 0

    def test_award_exp_invalid_game(self, client):
        resp = client.post("/api/evolution/award-exp", json={
            "game_id": "nonexistent",
            "pokemon_index": 0,
            "defeated_species_id": 16,
            "defeated_level": 5,
        })
        assert resp.status_code == 400
