"""Tests for gyms, badges, trainers, and AI (Sprint 4 QA-A)."""
import pytest
from unittest.mock import patch

from backend.services.gym_service import (
    ALL_BADGES,
    _build_battle_pokemon,
    _defeated_trainers,
    _earned_badges,
    award_badge,
    challenge_gym,
    defeat_trainer,
    get_all_gyms,
    get_badges,
    get_gym,
    get_trainer,
    get_trainers_on_map,
    start_trainer_battle,
)
from backend.services.ai_service import (
    _choose_easy,
    _choose_hard,
    _choose_normal,
    _move_score,
    get_ai_action,
)
from backend.services.battle_service import get_battle, start_battle
from backend.services.encounter_service import get_species
from backend.services.game_service import create_game, get_game
from backend.models.battle import BattlePokemon
from backend.models.pokemon import Move, Stats


@pytest.fixture(autouse=True)
def reset_gym_state():
    _defeated_trainers.clear()
    _earned_badges.clear()
    yield
    _defeated_trainers.clear()
    _earned_badges.clear()


# ────────────────────────────────────────────
# Gym data tests
# ────────────────────────────────────────────
class TestGymData:
    def test_gyms_loaded(self):
        gyms = get_all_gyms()
        assert len(gyms) == 2  # Pewter and Cerulean

    def test_pewter_gym(self):
        gym = get_gym("pewter_gym")
        assert gym is not None
        assert gym.name == "Pewter City Gym"
        assert gym.type_specialty == "rock"
        assert gym.badge_name == "Boulder Badge"
        assert gym.badge_id == "boulder"

    def test_brock_team(self):
        gym = get_gym("pewter_gym")
        leader = gym.leader
        assert leader.name == "Brock"
        assert leader.ai_difficulty == "hard"
        assert len(leader.pokemon_team) == 2
        geodude = leader.pokemon_team[0]
        assert geodude.name == "Geodude"
        assert geodude.level == 12
        onix = leader.pokemon_team[1]
        assert onix.name == "Onix"
        assert onix.level == 14

    def test_cerulean_gym(self):
        gym = get_gym("cerulean_gym")
        assert gym is not None
        assert gym.type_specialty == "water"
        assert gym.badge_name == "Cascade Badge"

    def test_misty_team(self):
        gym = get_gym("cerulean_gym")
        leader = gym.leader
        assert leader.name == "Misty"
        assert len(leader.pokemon_team) == 2
        staryu = leader.pokemon_team[0]
        assert staryu.name == "Staryu"
        assert staryu.level == 18
        starmie = leader.pokemon_team[1]
        assert starmie.name == "Starmie"
        assert starmie.level == 21

    def test_invalid_gym(self):
        assert get_gym("nonexistent") is None

    def test_gym_has_map_id(self):
        gym = get_gym("pewter_gym")
        assert gym.map_id == "pewter_gym"

    def test_gym_leader_has_dialogue(self):
        gym = get_gym("pewter_gym")
        assert len(gym.leader.dialogue_before) > 0
        assert len(gym.leader.dialogue_after) > 0


# ────────────────────────────────────────────
# Trainer data tests
# ────────────────────────────────────────────
class TestTrainerData:
    def test_trainer_joey(self):
        trainer = get_trainer("youngster_joey")
        assert trainer is not None
        assert trainer.name == "Joey"
        assert trainer.trainer_class == "Youngster"
        assert trainer.reward_money == 120
        assert len(trainer.pokemon_team) == 1
        assert trainer.pokemon_team[0].name == "Rattata"

    def test_trainer_bug_catcher(self):
        trainer = get_trainer("bug_catcher_rick")
        assert trainer is not None
        assert len(trainer.pokemon_team) == 2

    def test_gym_trainer(self):
        trainer = get_trainer("pewter_gym_trainer_1")
        assert trainer is not None
        assert trainer.trainer_class == "Camper"
        assert trainer.pokemon_team[0].species_id == 17  # Geodude

    def test_trainer_has_dialogue(self):
        trainer = get_trainer("youngster_joey")
        assert len(trainer.dialogue_before) > 0
        assert len(trainer.dialogue_after) > 0

    def test_invalid_trainer(self):
        assert get_trainer("nonexistent") is None

    def test_trainer_sight_range(self):
        trainer = get_trainer("bug_catcher_rick")
        assert trainer.sight_range == 4


# ────────────────────────────────────────────
# Build battle Pokemon tests
# ────────────────────────────────────────────
class TestBuildBattlePokemon:
    def test_build_from_species(self):
        result = _build_battle_pokemon(17, "Geodude", 12, ["Tackle", "Defense Curl"])
        assert result["name"] == "Geodude"
        assert result["level"] == 12
        assert result["current_hp"] == result["max_hp"]
        assert result["current_hp"] > 0
        assert len(result["moves"]) == 2

    def test_stats_scale_with_level(self):
        low = _build_battle_pokemon(17, "Geodude", 10, ["Tackle"])
        high = _build_battle_pokemon(17, "Geodude", 30, ["Tackle"])
        assert high["stats"]["hp"] > low["stats"]["hp"]
        assert high["stats"]["attack"] > low["stats"]["attack"]

    def test_unknown_species_fallback(self):
        result = _build_battle_pokemon(9999, "Unknown", 10, ["Tackle"])
        assert result["name"] == "Unknown"
        assert result["current_hp"] > 0
        assert result["types"] == ["normal"]

    def test_moves_resolved(self):
        result = _build_battle_pokemon(18, "Onix", 14, ["Tackle", "Rock Throw"])
        moves = result["moves"]
        assert len(moves) == 2
        # Tackle should have real data
        tackle = next(m for m in moves if m["name"] == "Tackle")
        assert tackle["power"] > 0


# ────────────────────────────────────────────
# Trainer battle tests
# ────────────────────────────────────────────
class TestTrainerBattle:
    def test_start_trainer_battle(self):
        game = create_game("Ash", 4)
        result = start_trainer_battle(game["id"], "youngster_joey")
        assert result is not None
        assert result.battle_id is not None
        assert result.trainer_id == "youngster_joey"
        assert result.reward_money == 120

    def test_trainer_battle_is_trainer_type(self):
        game = create_game("Ash", 4)
        result = start_trainer_battle(game["id"], "youngster_joey")
        battle = get_battle(result.battle_id)
        assert battle.battle_type == "trainer"
        assert battle.can_run is False

    def test_cannot_rebattle_defeated_trainer(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        start_trainer_battle(game_id, "youngster_joey")
        defeat_trainer(game_id, "youngster_joey")
        result = start_trainer_battle(game_id, "youngster_joey")
        assert result is None

    def test_defeat_trainer_awards_money(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        old_money = game["player"].get("money", 0)
        result = defeat_trainer(game_id, "youngster_joey")
        assert result is not None
        assert result["reward_money"] == 120
        assert result["total_money"] == old_money + 120

    def test_defeat_trainer_has_dialogue(self):
        game = create_game("Ash", 4)
        result = defeat_trainer(game["id"], "youngster_joey")
        assert len(result["dialogue_after"]) > 0

    def test_invalid_game_trainer_battle(self):
        result = start_trainer_battle("nonexistent", "youngster_joey")
        assert result is None

    def test_invalid_trainer_battle(self):
        game = create_game("Ash", 4)
        result = start_trainer_battle(game["id"], "nonexistent")
        assert result is None


# ────────────────────────────────────────────
# Gym challenge tests
# ────────────────────────────────────────────
class TestGymChallenge:
    def test_challenge_pewter_gym(self):
        game = create_game("Ash", 4)
        result = challenge_gym(game["id"], "pewter_gym")
        assert result is not None
        assert result.leader_name == "Brock"
        assert result.badge_id == "boulder"
        assert result.badge_name == "Boulder Badge"
        assert result.reward_money == 1400

    def test_gym_battle_is_trainer_type(self):
        game = create_game("Ash", 4)
        result = challenge_gym(game["id"], "pewter_gym")
        battle = get_battle(result.battle_id)
        assert battle.battle_type == "trainer"

    def test_cannot_rechallenge_after_badge(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        challenge_gym(game_id, "pewter_gym")
        award_badge(game_id, "pewter_gym")
        result = challenge_gym(game_id, "pewter_gym")
        assert result is None

    def test_challenge_invalid_gym(self):
        game = create_game("Ash", 4)
        result = challenge_gym(game["id"], "nonexistent")
        assert result is None

    def test_challenge_invalid_game(self):
        result = challenge_gym("nonexistent", "pewter_gym")
        assert result is None


# ────────────────────────────────────────────
# Badge tests
# ────────────────────────────────────────────
class TestBadges:
    def test_all_badges_defined(self):
        assert len(ALL_BADGES) == 8

    def test_badge_names(self):
        names = [b.badge_name for b in ALL_BADGES]
        assert "Boulder Badge" in names
        assert "Cascade Badge" in names
        assert "Earth Badge" in names

    def test_no_badges_initially(self):
        game = create_game("Ash", 4)
        badges = get_badges(game["id"])
        assert len(badges) == 8
        assert all(not b.earned for b in badges)

    def test_award_badge(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        result = award_badge(game_id, "pewter_gym")
        assert result is not None
        boulder = next(b for b in result if b.badge_id == "boulder")
        assert boulder.earned is True
        cascade = next(b for b in result if b.badge_id == "cascade")
        assert cascade.earned is False

    def test_award_badge_updates_game_state(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        award_badge(game_id, "pewter_gym")
        updated = get_game(game_id)
        assert updated["badges"] == 1

    def test_award_badge_gives_money(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        old_money = game["player"].get("money", 0)
        award_badge(game_id, "pewter_gym")
        updated = get_game(game_id)
        assert updated["player"]["money"] == old_money + 1400  # Brock's reward

    def test_award_multiple_badges(self):
        game = create_game("Ash", 4)
        game_id = game["id"]
        award_badge(game_id, "pewter_gym")
        award_badge(game_id, "cerulean_gym")
        badges = get_badges(game_id)
        earned = [b for b in badges if b.earned]
        assert len(earned) == 2
        updated = get_game(game_id)
        assert updated["badges"] == 2

    def test_award_badge_invalid_game(self):
        result = award_badge("nonexistent", "pewter_gym")
        assert result is None

    def test_award_badge_invalid_gym(self):
        game = create_game("Ash", 4)
        result = award_badge(game["id"], "nonexistent")
        assert result is None


# ────────────────────────────────────────────
# AI move scoring tests
# ────────────────────────────────────────────
class TestAIMoveScoring:
    def _make_pokemon(self, types, level=20, stats=None, moves=None):
        if stats is None:
            stats = Stats(hp=60, attack=40, defense=40, sp_attack=40, sp_defense=40, speed=40)
        if moves is None:
            moves = [Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)]
        return BattlePokemon(
            species_id=1, name="Test", types=types, level=level, stats=stats,
            current_hp=stats.hp, max_hp=stats.hp, moves=moves, sprite="test",
        )

    def test_super_effective_scores_higher(self):
        attacker = self._make_pokemon(["fire"])
        defender = self._make_pokemon(["grass"])
        fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)
        normal_move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)
        fire_score = _move_score(fire_move, attacker, defender)
        normal_score = _move_score(normal_move, attacker, defender)
        assert fire_score > normal_score

    def test_stab_increases_score(self):
        attacker = self._make_pokemon(["fire"])
        defender = self._make_pokemon(["normal"])
        fire_move = Move(name="Ember", type="fire", power=40, accuracy=100, pp=25)
        normal_move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)
        fire_score = _move_score(fire_move, attacker, defender)
        normal_score = _move_score(normal_move, attacker, defender)
        assert fire_score > normal_score  # STAB bonus for fire move

    def test_immune_move_negative_score(self):
        attacker = self._make_pokemon(["normal"])
        defender = self._make_pokemon(["ghost"])
        normal_move = Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)
        score = _move_score(normal_move, attacker, defender)
        assert score == -100.0

    def test_zero_power_move_zero_score(self):
        attacker = self._make_pokemon(["normal"])
        defender = self._make_pokemon(["normal"])
        status_move = Move(name="Growl", type="normal", power=0, accuracy=100, pp=40)
        score = _move_score(status_move, attacker, defender)
        assert score == 0.0


# ────────────────────────────────────────────
# AI difficulty tests
# ────────────────────────────────────────────
class TestAIDifficulty:
    def _make_pokemon(self, types, moves, level=20, hp=60):
        stats = Stats(hp=hp, attack=40, defense=40, sp_attack=40, sp_defense=40, speed=40)
        return BattlePokemon(
            species_id=1, name="Test", types=types, level=level, stats=stats,
            current_hp=hp, max_hp=hp,
            moves=[Move(**m) if isinstance(m, dict) else m for m in moves],
            sprite="test",
        )

    def test_easy_picks_attack_move(self):
        enemy = self._make_pokemon(["fire"], [
            Move(name="Growl", type="normal", power=0, accuracy=100, pp=40),
            Move(name="Ember", type="fire", power=40, accuracy=100, pp=25),
        ])
        player = self._make_pokemon(["grass"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
        ])
        decision = _choose_easy(enemy, player)
        assert decision.action_type == "fight"
        assert decision.move_index == 1  # Ember (only attack move)

    def test_easy_falls_back_to_any_move(self):
        enemy = self._make_pokemon(["normal"], [
            Move(name="Growl", type="normal", power=0, accuracy=100, pp=40),
        ])
        player = self._make_pokemon(["normal"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
        ])
        decision = _choose_easy(enemy, player)
        assert decision.action_type == "fight"
        assert decision.move_index == 0

    def test_normal_prefers_super_effective(self):
        enemy = self._make_pokemon(["water"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
            Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25),
        ])
        player = self._make_pokemon(["fire"], [
            Move(name="Ember", type="fire", power=40, accuracy=100, pp=25),
        ])
        decision = _choose_normal(enemy, player)
        assert decision.move_index == 1  # Water Gun (super effective + STAB)

    def test_hard_prefers_stab_super_effective(self):
        enemy = self._make_pokemon(["water"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
            Move(name="Water Gun", type="water", power=40, accuracy=100, pp=25),
        ])
        player = self._make_pokemon(["fire"], [
            Move(name="Ember", type="fire", power=40, accuracy=100, pp=25),
        ])
        decision = _choose_hard(enemy, player)
        assert decision.move_index == 1  # Water Gun (SE + STAB)

    def test_normal_avoids_immune_moves(self):
        enemy = self._make_pokemon(["normal"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
            Move(name="Quick Attack", type="normal", power=40, accuracy=100, pp=30),
        ])
        player = self._make_pokemon(["ghost"], [
            Move(name="Lick", type="ghost", power=30, accuracy=100, pp=30),
        ])
        decision = _choose_normal(enemy, player)
        # Both normal moves are immune against ghost — AI should still pick one as fallback
        assert decision.action_type == "fight"

    def test_hard_penalizes_status_when_can_ko(self):
        enemy = self._make_pokemon(["fire"], [
            Move(name="Growl", type="normal", power=0, accuracy=100, pp=40),
            Move(name="Ember", type="fire", power=40, accuracy=100, pp=25),
        ])
        player = self._make_pokemon(["grass"], [
            Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35),
        ], hp=5)  # Low HP
        player.current_hp = 3  # Very low
        decision = _choose_hard(enemy, player)
        assert decision.move_index == 1  # Should pick Ember, not Growl


# ────────────────────────────────────────────
# AI API tests
# ────────────────────────────────────────────
class TestAIAPI:
    def test_get_ai_action_easy(self):
        game = create_game("Ash", 4)
        stored = get_game(game["id"])
        lead = stored["player"]["team"][0]
        player_data = {
            "species_id": lead["id"], "name": lead["name"], "types": lead["types"],
            "level": lead["level"], "stats": lead["stats"],
            "current_hp": lead["stats"]["hp"], "max_hp": lead["stats"]["hp"],
            "moves": lead["moves"], "sprite": lead["sprite"],
        }
        enemy_data = _build_battle_pokemon(13, "Rattata", 6, ["Tackle", "Tail Whip"])
        battle = start_battle(player_data, enemy_data, "wild")
        decision = get_ai_action(battle.id, "easy")
        assert decision is not None
        assert decision.action_type == "fight"

    def test_get_ai_action_normal(self):
        game = create_game("Ash", 4)
        stored = get_game(game["id"])
        lead = stored["player"]["team"][0]
        player_data = {
            "species_id": lead["id"], "name": lead["name"], "types": lead["types"],
            "level": lead["level"], "stats": lead["stats"],
            "current_hp": lead["stats"]["hp"], "max_hp": lead["stats"]["hp"],
            "moves": lead["moves"], "sprite": lead["sprite"],
        }
        enemy_data = _build_battle_pokemon(13, "Rattata", 6, ["Tackle", "Tail Whip"])
        battle = start_battle(player_data, enemy_data, "trainer")
        decision = get_ai_action(battle.id, "normal")
        assert decision is not None
        assert decision.action_type == "fight"

    def test_get_ai_action_hard(self):
        game = create_game("Ash", 4)
        stored = get_game(game["id"])
        lead = stored["player"]["team"][0]
        player_data = {
            "species_id": lead["id"], "name": lead["name"], "types": lead["types"],
            "level": lead["level"], "stats": lead["stats"],
            "current_hp": lead["stats"]["hp"], "max_hp": lead["stats"]["hp"],
            "moves": lead["moves"], "sprite": lead["sprite"],
        }
        enemy_data = _build_battle_pokemon(17, "Geodude", 12, ["Tackle", "Rock Throw"])
        battle = start_battle(player_data, enemy_data, "trainer")
        decision = get_ai_action(battle.id, "hard")
        assert decision is not None
        assert decision.action_type == "fight"

    def test_ai_action_invalid_battle(self):
        result = get_ai_action("nonexistent")
        assert result is None

    def test_ai_action_finished_battle(self):
        game = create_game("Ash", 4)
        stored = get_game(game["id"])
        lead = stored["player"]["team"][0]
        player_data = {
            "species_id": lead["id"], "name": lead["name"], "types": lead["types"],
            "level": lead["level"], "stats": lead["stats"],
            "current_hp": lead["stats"]["hp"], "max_hp": lead["stats"]["hp"],
            "moves": lead["moves"], "sprite": lead["sprite"],
        }
        enemy_data = _build_battle_pokemon(13, "Rattata", 6, ["Tackle"])
        battle = start_battle(player_data, enemy_data, "wild")
        battle.is_over = True
        result = get_ai_action(battle.id)
        assert result is None


# ────────────────────────────────────────────
# Gym & Trainer API tests
# ────────────────────────────────────────────
class TestGymTrainerAPI:
    def test_list_gyms_endpoint(self, client):
        resp = client.get("/api/gyms")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_gym_detail_endpoint(self, client):
        resp = client.get("/api/gyms/pewter_gym")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Pewter City Gym"

    def test_gym_not_found(self, client):
        resp = client.get("/api/gyms/nonexistent")
        assert resp.status_code == 404

    def test_challenge_gym_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(f"/api/gyms/pewter_gym/challenge/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["leader_name"] == "Brock"
        assert data["badge_id"] == "boulder"

    def test_challenge_gym_invalid(self, client):
        resp = client.post("/api/gyms/pewter_gym/challenge/nonexistent")
        assert resp.status_code == 400

    def test_award_badge_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(f"/api/gyms/pewter_gym/award-badge/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        boulder = next(b for b in data if b["badge_id"] == "boulder")
        assert boulder["earned"] is True

    def test_badges_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.get(f"/api/badges/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 8

    def test_trainer_detail_endpoint(self, client):
        resp = client.get("/api/trainers/detail/youngster_joey")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Joey"

    def test_trainer_not_found(self, client):
        resp = client.get("/api/trainers/detail/nonexistent")
        assert resp.status_code == 404

    def test_trainer_battle_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(f"/api/trainers/youngster_joey/battle/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trainer_id"] == "youngster_joey"

    def test_trainer_defeat_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        resp = client.post(f"/api/trainers/youngster_joey/defeat/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reward_money"] == 120

    def test_ai_action_endpoint(self, client, game_with_pokemon):
        game_id, _ = game_with_pokemon
        stored = get_game(game_id)
        lead = stored["player"]["team"][0]
        player_data = {
            "species_id": lead["id"], "name": lead["name"], "types": lead["types"],
            "level": lead["level"], "stats": lead["stats"],
            "current_hp": lead["stats"]["hp"], "max_hp": lead["stats"]["hp"],
            "moves": lead["moves"], "sprite": lead["sprite"],
        }
        enemy_data = _build_battle_pokemon(13, "Rattata", 6, ["Tackle"])
        battle = start_battle(player_data, enemy_data, "wild")
        resp = client.post("/api/battle/ai-action", json={
            "battle_id": battle.id, "difficulty": "normal",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_type"] == "fight"
