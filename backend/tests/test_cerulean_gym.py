"""Tests for Sprint 11 QA-A3: Cerulean Gym & Misty Battle.

These tests verify the Cerulean Gym setup, Misty's team, Cascade Badge,
gym trainers, challenge flow, and badge prerequisites.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.gym_service import (
    _defeated_trainers,
    _earned_badges,
    award_badge,
    challenge_gym,
    get_badges,
    get_gym,
    get_trainer,
    get_trainers_on_map,
)
from backend.services.map_service import get_map
from backend.services.encounter_service import get_species
from backend.services.game_service import create_game, get_game

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_gym_state():
    _defeated_trainers.clear()
    _earned_badges.clear()
    yield
    _defeated_trainers.clear()
    _earned_badges.clear()


def _create_test_game() -> str:
    game = create_game("GymChallenger", 1)
    return game["id"]


# ──── Gym Data ───────────────────────────────────────────────

class TestCeruleanGymData:
    def test_cerulean_gym_exists(self):
        gym = get_gym("cerulean_gym")
        assert gym is not None
        assert gym.name == "Cerulean City Gym"
        assert gym.type_specialty == "water"

    def test_cascade_badge_name(self):
        gym = get_gym("cerulean_gym")
        assert gym.badge_name == "Cascade Badge"
        assert gym.badge_id == "cascade"

    def test_misty_team_composition(self):
        gym = get_gym("cerulean_gym")
        leader = gym.leader
        assert leader.name == "Misty"
        assert len(leader.pokemon_team) == 2

    def test_misty_staryu(self):
        gym = get_gym("cerulean_gym")
        staryu = gym.leader.pokemon_team[0]
        assert staryu.name == "Staryu"
        assert staryu.level == 18
        assert staryu.species_id == 21

    def test_misty_starmie(self):
        gym = get_gym("cerulean_gym")
        starmie = gym.leader.pokemon_team[1]
        assert starmie.name == "Starmie"
        assert starmie.level == 21
        assert starmie.species_id == 22

    def test_misty_reward_money(self):
        gym = get_gym("cerulean_gym")
        assert gym.leader.reward_money == 2100

    def test_misty_ai_difficulty(self):
        gym = get_gym("cerulean_gym")
        assert gym.leader.ai_difficulty == "hard"


# ──── Gym Map Linkage ────────────────────────────────────────

class TestGymMapLinkage:
    def test_cerulean_gym_map_matches(self):
        """The gym's map_id should match a real map in maps.json."""
        gym = get_gym("cerulean_gym")
        assert gym.map_id == "cerulean_gym"
        game_map = get_map("cerulean_gym")
        assert game_map is not None
        assert game_map.map_type == "gym"

    def test_gym_trainers_in_map(self):
        """Cerulean gym map should have 2 trainers at correct positions."""
        game_map = get_map("cerulean_gym")
        assert len(game_map.trainers) == 2
        trainer_ids = {t.trainer_id if hasattr(t, 'trainer_id')
                       else t.get("trainer_id", t.get("id"))
                       for t in game_map.trainers}
        assert "cerulean_gym_trainer_1" in trainer_ids
        assert "cerulean_gym_trainer_2" in trainer_ids


# ──── Gym Challenge Flow ─────────────────────────────────────

class TestGymChallenge:
    def test_challenge_cerulean_gym(self):
        game_id = _create_test_game()
        result = challenge_gym(game_id, "cerulean_gym")
        assert result is not None
        assert result.leader_name == "Misty"
        assert result.badge_id == "cascade"

    def test_challenge_cerulean_gym_invalid_game(self):
        result = challenge_gym("nonexistent", "cerulean_gym")
        assert result is None


# ──── Badge Award ────────────────────────────────────────────

class TestBadgeAward:
    def test_award_cascade_badge(self):
        game_id = _create_test_game()
        result = award_badge(game_id, "cerulean_gym")
        assert result is not None
        cascade = next(b for b in result if b.badge_id == "cascade")
        assert cascade.earned is True

    def test_cascade_badge_in_game_state(self):
        game_id = _create_test_game()
        award_badge(game_id, "cerulean_gym")
        game = get_game(game_id)
        assert game["badges"] >= 1
        badges = get_badges(game_id)
        cascade = next(b for b in badges if b.badge_id == "cascade")
        assert cascade.earned is True

    def test_award_cascade_gives_money(self):
        game_id = _create_test_game()
        old_money = get_game(game_id)["player"].get("money", 0)
        award_badge(game_id, "cerulean_gym")
        new_money = get_game(game_id)["player"].get("money", 0)
        assert new_money > old_money


# ──── API Endpoint Integration ───────────────────────────────

class TestGymEndpoints:
    def test_cerulean_gym_endpoint(self):
        resp = client.get("/api/gyms/cerulean_gym")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Cerulean City Gym"
        assert data["leader"]["name"] == "Misty"

    def test_challenge_cerulean_gym_endpoint(self):
        game_id = _create_test_game()
        resp = client.post(f"/api/gyms/cerulean_gym/challenge/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["leader_name"] == "Misty"
        assert data["badge_id"] == "cascade"

    def test_award_cascade_badge_endpoint(self):
        game_id = _create_test_game()
        resp = client.post(f"/api/gyms/cerulean_gym/award-badge/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        cascade = next(b for b in data if b["badge_id"] == "cascade")
        assert cascade["earned"] is True
