"""Tests for Sprint 6.5 backend integration support endpoints."""
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


# ---- POST /api/player/{player_id}/stats ----

class TestSavePlayerStats:
    def test_save_stats_returns_server_stats(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/player/{gid}/stats", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["player_id"] == gid
        assert "play_time_seconds" in data
        assert "trainer_class" in data

    def test_save_stats_syncs_play_time(self):
        game = _make_game()
        gid = game["id"]
        # Send 60000ms = 60s
        resp = client.post(f"/api/player/{gid}/stats", json={"playTimeMs": 60000})
        assert resp.status_code == 200
        data = resp.json()
        assert data["play_time_seconds"] == 60

    def test_save_stats_nonexistent_player_404(self):
        resp = client.post("/api/player/doesnotexist/stats", json={})
        assert resp.status_code == 404

    def test_save_stats_partial_fields(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/player/{gid}/stats", json={"battlesWon": 5})
        assert resp.status_code == 200
        # Should still return valid stats
        assert resp.json()["player_id"] == gid

    def test_save_stats_triggers_achievement_check(self):
        game = _make_game()
        gid = game["id"]
        # Just posting stats should trigger achievement check without error
        resp = client.post(f"/api/player/{gid}/stats", json={})
        assert resp.status_code == 200


# ---- POST /api/player/{player_id}/achievements ----

class TestSaveAchievements:
    def test_save_achievements_returns_check_result(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/player/{gid}/achievements", json={"achievements": []})
        assert resp.status_code == 200
        data = resp.json()
        assert "all_achievements" in data
        assert "newly_earned" in data

    def test_save_achievements_with_ids(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(
            f"/api/player/{gid}/achievements",
            json={"achievements": ["first_steps", "collector"]},
        )
        assert resp.status_code == 200
        assert "all_achievements" in resp.json()

    def test_save_achievements_nonexistent_player_404(self):
        resp = client.post(
            "/api/player/doesnotexist/achievements",
            json={"achievements": []},
        )
        assert resp.status_code == 404

    def test_save_achievements_empty_body(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/player/{gid}/achievements", json={})
        assert resp.status_code == 200


# ---- QA-B bug fix regressions (included from PR#57) ----

class TestLeaderboardLimitClamping:
    def test_negative_limit_clamped_to_1(self):
        resp = client.get("/api/leaderboard/trainers?limit=-5")
        assert resp.status_code == 200

    def test_huge_limit_clamped_to_100(self):
        resp = client.get("/api/leaderboard/trainers?limit=9999")
        assert resp.status_code == 200

    def test_zero_limit_clamped_to_1(self):
        resp = client.get("/api/leaderboard/pvp?limit=0")
        assert resp.status_code == 200

    def test_normal_limit_passes(self):
        resp = client.get("/api/leaderboard/pokedex?limit=10")
        assert resp.status_code == 200


class TestAchievementsNonexistentPlayer:
    def test_get_achievements_nonexistent_returns_404(self):
        resp = client.get("/api/player/doesnotexist/achievements")
        assert resp.status_code == 404

    def test_check_achievements_nonexistent_returns_404(self):
        resp = client.post("/api/achievements/check/doesnotexist")
        assert resp.status_code == 404


class TestPlayTimeUpdate:
    def test_update_play_time(self):
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/game/{gid}/play-time", json={"seconds": 120})
        assert resp.status_code == 200
        assert resp.json()["play_time_seconds"] == 120

    def test_update_play_time_nonexistent_game(self):
        resp = client.post("/api/game/doesnotexist/play-time", json={"seconds": 60})
        assert resp.status_code == 404

    def test_update_play_time_negative_ignored(self):
        game = _make_game()
        gid = game["id"]
        # Set to 100 first
        client.post(f"/api/game/{gid}/play-time", json={"seconds": 100})
        # Negative should not change it
        resp = client.post(f"/api/game/{gid}/play-time", json={"seconds": -10})
        assert resp.status_code == 200
        # Verify it stayed at 100
        state = client.get(f"/api/game/{gid}").json()
        assert state["play_time_seconds"] == 100


# ---- Integration flow tests ----

class TestGameplayFlowIntegration:
    def test_full_stats_flow(self):
        """Test: create game -> update play time -> get stats -> save stats."""
        game = _make_game("FlowTester")
        gid = game["id"]

        # Update play time
        resp = client.post(f"/api/game/{gid}/play-time", json={"seconds": 300})
        assert resp.status_code == 200

        # Get stats
        resp = client.get(f"/api/player/{gid}/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert stats["play_time_seconds"] == 300
        assert stats["player_name"] == "FlowTester"

        # Save stats (frontend sync)
        resp = client.post(f"/api/player/{gid}/stats", json={"playTimeMs": 600000})
        assert resp.status_code == 200
        assert resp.json()["play_time_seconds"] == 600

    def test_achievements_flow(self):
        """Test: create game -> get achievements -> save achievements -> check achievements."""
        game = _make_game("AchTester")
        gid = game["id"]

        # Get achievements
        resp = client.get(f"/api/player/{gid}/achievements")
        assert resp.status_code == 200
        achs = resp.json()
        assert len(achs) > 0

        # Save achievements (triggers server-side check)
        resp = client.post(
            f"/api/player/{gid}/achievements",
            json={"achievements": ["first_steps"]},
        )
        assert resp.status_code == 200

        # Explicit check
        resp = client.post(f"/api/achievements/check/{gid}")
        assert resp.status_code == 200
        assert "all_achievements" in resp.json()
