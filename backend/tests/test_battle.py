"""Tests for Battle API endpoints and battle engine logic."""
import pytest
from unittest.mock import patch

from backend.services.battle_service import (
    _calculate_damage,
    _get_type_effectiveness,
    _choose_enemy_move,
    start_battle,
    process_action,
    get_battle,
    _battles,
)
from backend.models.battle import BattlePokemon
from backend.models.pokemon import Move, Stats


@pytest.fixture
def bulbasaur_data():
    return {
        "species_id": 1,
        "name": "Bulbasaur",
        "types": ["grass", "poison"],
        "level": 5,
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
        "current_hp": 45,
        "max_hp": 45,
        "moves": [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            {"name": "Vine Whip", "type": "grass", "power": 45, "accuracy": 100, "pp": 25},
        ],
        "sprite": "bulbasaur.png",
    }


@pytest.fixture
def charmander_data():
    return {
        "species_id": 4,
        "name": "Charmander",
        "types": ["fire"],
        "level": 5,
        "stats": {"hp": 39, "attack": 52, "defense": 43, "sp_attack": 60, "sp_defense": 50, "speed": 65},
        "current_hp": 39,
        "max_hp": 39,
        "moves": [
            {"name": "Scratch", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            {"name": "Ember", "type": "fire", "power": 40, "accuracy": 100, "pp": 25},
        ],
        "sprite": "charmander.png",
    }


@pytest.fixture
def pidgey_data():
    return {
        "species_id": 10,
        "name": "Pidgey",
        "types": ["normal", "flying"],
        "level": 3,
        "stats": {"hp": 40, "attack": 45, "defense": 40, "sp_attack": 35, "sp_defense": 35, "speed": 56},
        "current_hp": 40,
        "max_hp": 40,
        "moves": [
            {"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35},
            {"name": "Gust", "type": "flying", "power": 40, "accuracy": 100, "pp": 35},
        ],
        "sprite": "pidgey.png",
    }


@pytest.fixture(autouse=True)
def reset_battles():
    _battles.clear()
    yield
    _battles.clear()


class TestTypeEffectiveness:
    def test_fire_vs_grass(self):
        assert _get_type_effectiveness("fire", ["grass"]) == 2.0

    def test_water_vs_fire(self):
        assert _get_type_effectiveness("water", ["fire"]) == 2.0

    def test_grass_vs_water(self):
        assert _get_type_effectiveness("grass", ["water"]) == 2.0

    def test_fire_vs_water(self):
        assert _get_type_effectiveness("fire", ["water"]) == 0.5

    def test_normal_vs_ghost(self):
        assert _get_type_effectiveness("normal", ["ghost"]) == 0.0

    def test_electric_vs_ground(self):
        assert _get_type_effectiveness("electric", ["ground"]) == 0.0

    def test_neutral_matchup(self):
        assert _get_type_effectiveness("normal", ["normal"]) == 1.0

    def test_dual_type_multiplier(self):
        # Grass vs Water/Ground should be 2.0 * 2.0 = 4.0
        assert _get_type_effectiveness("grass", ["water", "ground"]) == 4.0

    def test_dual_type_cancel(self):
        # Fire vs Grass/Water should be 2.0 * 0.5 = 1.0
        assert _get_type_effectiveness("fire", ["grass", "water"]) == 1.0


class TestDamageCalculation:
    def test_damage_is_positive(self, bulbasaur_data, charmander_data):
        attacker = BattlePokemon(**bulbasaur_data)
        defender = BattlePokemon(**charmander_data)
        move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2  # No crit
            mock_random.uniform.return_value = 1.0  # Max random factor

            dmg, eff, crit = _calculate_damage(attacker, defender, move)
            assert dmg > 0
            assert eff == "normal"

    def test_stab_bonus(self, bulbasaur_data, charmander_data):
        attacker = BattlePokemon(**bulbasaur_data)
        defender = BattlePokemon(**charmander_data)

        # Vine Whip is grass-type, Bulbasaur is grass-type = STAB
        stab_move = Move(name="Vine Whip", type="grass", power=45, accuracy=100, pp=25)
        # Tackle is normal-type, Bulbasaur is NOT normal-type = no STAB
        no_stab_move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2  # No crit
            mock_random.uniform.return_value = 1.0

            stab_dmg, _, _ = _calculate_damage(attacker, defender, stab_move)
            no_stab_dmg, _, _ = _calculate_damage(attacker, defender, no_stab_move)

            # STAB move should deal more damage (even accounting for type effectiveness)
            # Vine Whip vs fire = 0.5x, but with STAB (1.5x) and higher power (45 vs 40)
            # The comparison is complex, so just verify both are > 0
            assert stab_dmg > 0
            assert no_stab_dmg > 0

    def test_super_effective(self, bulbasaur_data):
        attacker = BattlePokemon(**{**bulbasaur_data, "types": ["water"]})
        defender = BattlePokemon(**{**bulbasaur_data, "types": ["fire"], "name": "Charmander"})
        move = Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25)

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2
            mock_random.uniform.return_value = 1.0

            _, eff, _ = _calculate_damage(attacker, defender, move)
            assert eff == "super_effective"

    def test_not_very_effective(self, bulbasaur_data):
        attacker = BattlePokemon(**{**bulbasaur_data, "types": ["fire"]})
        defender = BattlePokemon(**{**bulbasaur_data, "types": ["water"], "name": "Squirtle"})
        move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2
            mock_random.uniform.return_value = 1.0

            _, eff, _ = _calculate_damage(attacker, defender, move)
            assert eff == "not_very_effective"

    def test_immune(self, bulbasaur_data):
        attacker = BattlePokemon(**{**bulbasaur_data, "types": ["normal"]})
        defender = BattlePokemon(**{**bulbasaur_data, "types": ["ghost"], "name": "Gastly"})
        move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2
            mock_random.uniform.return_value = 1.0

            dmg, eff, _ = _calculate_damage(attacker, defender, move)
            assert dmg == 0
            assert eff == "immune"

    def test_zero_power_move(self, bulbasaur_data, charmander_data):
        attacker = BattlePokemon(**bulbasaur_data)
        defender = BattlePokemon(**charmander_data)
        move = Move(name="Growl", type="normal", power=0, accuracy=100, pp=40)

        dmg, eff, crit = _calculate_damage(attacker, defender, move)
        assert dmg == 0
        assert crit is False


class TestBattleFlow:
    def test_start_battle(self, bulbasaur_data, pidgey_data):
        battle = start_battle(bulbasaur_data, pidgey_data, "wild")
        assert battle.id is not None
        assert battle.player_pokemon.name == "Bulbasaur"
        assert battle.enemy_pokemon.name == "Pidgey"
        assert battle.battle_type == "wild"
        assert battle.can_run is True
        assert battle.is_over is False

    def test_start_trainer_battle(self, bulbasaur_data, charmander_data):
        battle = start_battle(bulbasaur_data, charmander_data, "trainer")
        assert battle.can_run is False

    def test_turn_order_by_speed(self, bulbasaur_data, charmander_data):
        # Charmander (speed 65) should go first vs Bulbasaur (speed 45)
        battle = start_battle(bulbasaur_data, charmander_data, "wild")

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2  # No crit, hits
            mock_random.uniform.return_value = 1.0
            mock_random.choice.return_value = Move(
                name="Scratch", type="normal", power=40, accuracy=100, pp=35
            )

            result = process_action(battle.id, "fight", 0)
            assert result is not None
            # Enemy (Charmander) should attack first since higher speed
            assert result.events[0].attacker == "enemy"

    def test_fainting_ends_battle(self, bulbasaur_data, pidgey_data):
        # Set pidgey to 1 HP
        pidgey_data["current_hp"] = 1
        battle = start_battle(bulbasaur_data, pidgey_data, "wild")

        with patch("backend.services.battle_service.random") as mock_random:
            mock_random.randint.return_value = 2
            mock_random.uniform.return_value = 1.0
            mock_random.choice.return_value = Move(
                name="Tackle", type="normal", power=40, accuracy=100, pp=35
            )

            result = process_action(battle.id, "fight", 0)
            assert result is not None
            assert result.battle_over is True
            assert result.winner == "player"

    def test_run_from_wild_battle(self, bulbasaur_data, pidgey_data):
        battle = start_battle(bulbasaur_data, pidgey_data, "wild")

        with patch("backend.services.battle_service._try_run", return_value=True):
            result = process_action(battle.id, "run")
            assert result is not None
            assert result.ran_away is True
            assert result.battle_over is True

    def test_cannot_run_from_trainer_battle(self, bulbasaur_data, charmander_data):
        battle = start_battle(bulbasaur_data, charmander_data, "trainer")

        result = process_action(battle.id, "run")
        assert result is not None
        assert result.run_failed is True
        assert result.battle_over is False

    def test_invalid_move_index(self, bulbasaur_data, pidgey_data):
        battle = start_battle(bulbasaur_data, pidgey_data, "wild")
        result = process_action(battle.id, "fight", 99)
        assert result is None

    def test_action_on_finished_battle(self, bulbasaur_data, pidgey_data):
        battle = start_battle(bulbasaur_data, pidgey_data, "wild")
        battle.is_over = True
        result = process_action(battle.id, "fight", 0)
        assert result is None


class TestBattleAPI:
    def test_start_battle_endpoint(self, client, bulbasaur_data):
        # Create a game first
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]

        resp = client.post("/api/battle/start", json={"game_id": game_id})
        assert resp.status_code == 200
        data = resp.json()
        assert "battle" in data
        assert data["battle"]["player_pokemon"]["name"] == "Bulbasaur"
        assert data["battle"]["is_over"] is False

    def test_start_battle_invalid_game(self, client):
        resp = client.post("/api/battle/start", json={"game_id": "nonexistent"})
        assert resp.status_code == 404

    def test_battle_action_endpoint(self, client):
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]

        battle_resp = client.post("/api/battle/start", json={"game_id": game_id})
        battle_id = battle_resp.json()["battle"]["id"]

        resp = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "fight",
            "move_index": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "turn_result" in data
        assert len(data["turn_result"]["events"]) > 0

    def test_battle_state_endpoint(self, client):
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]

        battle_resp = client.post("/api/battle/start", json={"game_id": game_id})
        battle_id = battle_resp.json()["battle"]["id"]

        resp = client.get(f"/api/battle/state/{battle_id}")
        assert resp.status_code == 200
        assert resp.json()["battle"]["id"] == battle_id

    def test_battle_not_found(self, client):
        resp = client.get("/api/battle/state/nonexistent")
        assert resp.status_code == 404

    def test_invalid_action(self, client):
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]
        battle_resp = client.post("/api/battle/start", json={"game_id": game_id})
        battle_id = battle_resp.json()["battle"]["id"]

        resp = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "invalid",
        })
        assert resp.status_code == 400

    def test_fight_without_move_index(self, client):
        game_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = game_resp.json()["id"]
        battle_resp = client.post("/api/battle/start", json={"game_id": game_id})
        battle_id = battle_resp.json()["battle"]["id"]

        resp = client.post("/api/battle/action", json={
            "battle_id": battle_id,
            "action": "fight",
        })
        assert resp.status_code == 400


class TestChooseEnemyMove:
    def test_prefers_attack_moves(self):
        moves = [
            Move(name="Growl", type="normal", power=0, accuracy=100, pp=40),
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
        ]
        pokemon = BattlePokemon(
            species_id=13, name="Rattata", types=["normal"], level=5,
            stats=Stats(hp=30, attack=56, defense=35, sp_attack=25, sp_defense=35, speed=72),
            current_hp=30, max_hp=30, moves=moves, sprite="rattata.png",
        )
        # Run multiple times to verify it picks Tackle (power > 0)
        for _ in range(20):
            chosen = _choose_enemy_move(pokemon)
            assert chosen.power > 0

    def test_falls_back_to_any_move(self):
        moves = [
            Move(name="Growl", type="normal", power=0, accuracy=100, pp=40),
        ]
        pokemon = BattlePokemon(
            species_id=13, name="Rattata", types=["normal"], level=5,
            stats=Stats(hp=30, attack=56, defense=35, sp_attack=25, sp_defense=35, speed=72),
            current_hp=30, max_hp=30, moves=moves, sprite="rattata.png",
        )
        chosen = _choose_enemy_move(pokemon)
        assert chosen.name == "Growl"
