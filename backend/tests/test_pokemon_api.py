"""Tests for Pokemon API endpoints."""


class TestListPokemon:
    def test_returns_all_pokemon(self, client):
        resp = client.get("/api/pokemon")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 9  # 3 evolution lines of 3

    def test_pokemon_have_required_fields(self, client):
        resp = client.get("/api/pokemon")
        for p in resp.json():
            assert "id" in p
            assert "name" in p
            assert "types" in p
            assert "stats" in p
            assert "moves" in p
            assert "level" in p

    def test_pokemon_stats_structure(self, client):
        resp = client.get("/api/pokemon")
        stats_fields = {"hp", "attack", "defense", "sp_attack", "sp_defense", "speed"}
        for p in resp.json():
            assert set(p["stats"].keys()) == stats_fields
            for val in p["stats"].values():
                assert isinstance(val, int)
                assert val > 0

    def test_pokemon_moves_structure(self, client):
        resp = client.get("/api/pokemon")
        for p in resp.json():
            assert len(p["moves"]) > 0
            for m in p["moves"]:
                assert "name" in m
                assert "type" in m
                assert "power" in m
                assert "accuracy" in m
                assert "pp" in m


class TestGetPokemon:
    def test_get_bulbasaur(self, client):
        resp = client.get("/api/pokemon/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Bulbasaur"
        assert data["types"] == ["grass", "poison"]
        assert data["level"] == 5

    def test_get_charmander(self, client):
        resp = client.get("/api/pokemon/4")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Charmander"

    def test_get_squirtle(self, client):
        resp = client.get("/api/pokemon/7")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Squirtle"

    def test_not_found(self, client):
        resp = client.get("/api/pokemon/999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_invalid_id_type(self, client):
        resp = client.get("/api/pokemon/abc")
        assert resp.status_code == 422  # Pydantic validation error
