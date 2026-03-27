"""Tests for Game API endpoints."""
import pytest


class TestNewGame:
    def test_create_game_with_bulbasaur(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["player"]["name"] == "Ash"
        assert len(data["player"]["team"]) == 1
        assert data["player"]["team"][0]["name"] == "Bulbasaur"
        assert data["badges"] == 0
        assert data["play_time_seconds"] == 0

    def test_create_game_with_charmander(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Red",
            "starter_pokemon_id": 4,
        })
        assert resp.status_code == 200
        assert resp.json()["player"]["team"][0]["name"] == "Charmander"

    def test_create_game_with_squirtle(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Blue",
            "starter_pokemon_id": 7,
        })
        assert resp.status_code == 200
        assert resp.json()["player"]["team"][0]["name"] == "Squirtle"

    def test_invalid_pokemon_id(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 999,
        })
        assert resp.status_code == 400
        assert "not found" in resp.json()["detail"].lower()

    def test_missing_player_name(self, client):
        resp = client.post("/api/game/new", json={
            "starter_pokemon_id": 1,
        })
        assert resp.status_code == 422

    def test_missing_starter_pokemon_id(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Ash",
        })
        assert resp.status_code == 422

    def test_empty_body(self, client):
        resp = client.post("/api/game/new", json={})
        assert resp.status_code == 422

    def test_game_id_is_unique(self, client):
        resp1 = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        resp2 = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_default_position(self, client):
        resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        pos = resp.json()["player"]["position"]
        assert pos["x"] == 0
        assert pos["y"] == 0
        assert pos["map_id"] == "pallet_town"


class TestGetGame:
    def test_get_existing_game(self, client):
        create_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = create_resp.json()["id"]

        resp = client.get(f"/api/game/{game_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == game_id
        assert resp.json()["player"]["name"] == "Ash"

    def test_game_not_found(self, client):
        resp = client.get("/api/game/nonexistent")
        assert resp.status_code == 404


class TestSaveGame:
    def test_save_updated_position(self, client):
        create_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = create_resp.json()["id"]
        player_data = create_resp.json()["player"]

        # Update position
        player_data["position"]["x"] = 100
        player_data["position"]["y"] = 200

        resp = client.post(f"/api/game/{game_id}/save", json={
            "player": player_data,
        })
        assert resp.status_code == 200
        assert resp.json()["player"]["position"]["x"] == 100
        assert resp.json()["player"]["position"]["y"] == 200

    def test_save_persists(self, client):
        create_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = create_resp.json()["id"]
        player_data = create_resp.json()["player"]
        player_data["position"]["x"] = 50

        client.post(f"/api/game/{game_id}/save", json={
            "player": player_data,
        })

        # Verify via GET
        resp = client.get(f"/api/game/{game_id}")
        assert resp.json()["player"]["position"]["x"] == 50

    def test_save_nonexistent_game(self, client):
        resp = client.post("/api/game/nonexistent/save", json={
            "player": {
                "name": "Ash",
                "team": [],
                "position": {"x": 0, "y": 0, "map_id": "pallet_town"},
                "inventory": [],
            },
        })
        assert resp.status_code == 404

    @pytest.mark.xfail(
        reason="BUG: save_game raises unhandled ValidationError instead of returning 422. "
               "Player(**player_data) in game_service.py:67 needs try/except.",
        strict=True,
    )
    def test_save_invalid_player_data(self, client):
        """Invalid player data should return 422, not crash with 500."""
        create_resp = client.post("/api/game/new", json={
            "player_name": "Ash",
            "starter_pokemon_id": 1,
        })
        game_id = create_resp.json()["id"]

        resp = client.post(f"/api/game/{game_id}/save", json={
            "player": {"invalid": "data"},
        })
        assert resp.status_code == 422


class TestHealthEndpoint:
    def test_health_check(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
