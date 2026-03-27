"""Tests for data models."""
import pytest
from pydantic import ValidationError

from backend.models.pokemon import Pokemon, Stats, Move
from backend.models.player import Player, Position, InventoryItem


class TestPokemonModel:
    def test_valid_pokemon(self):
        p = Pokemon(
            id=1,
            name="Bulbasaur",
            types=["grass", "poison"],
            stats=Stats(hp=45, attack=49, defense=49, sp_attack=65, sp_defense=65, speed=45),
            moves=[Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)],
            sprite="bulbasaur.png",
            level=5,
        )
        assert p.name == "Bulbasaur"
        assert len(p.types) == 2

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            Pokemon(
                id=1,
                name="Bulbasaur",
                # missing types, stats, moves, sprite, level
            )


class TestPlayerModel:
    def test_default_position(self):
        p = Player(name="Ash")
        assert p.position.x == 0
        assert p.position.y == 0
        assert p.position.map_id == "pallet_town"
        assert p.team == []
        assert p.inventory == []

    def test_player_with_team(self):
        pokemon = Pokemon(
            id=1,
            name="Bulbasaur",
            types=["grass"],
            stats=Stats(hp=45, attack=49, defense=49, sp_attack=65, sp_defense=65, speed=45),
            moves=[Move(name="Tackle", type="normal", power=40, accuracy=100, pp=35)],
            sprite="bulbasaur.png",
            level=5,
        )
        p = Player(name="Ash", team=[pokemon])
        assert len(p.team) == 1
        assert p.team[0].name == "Bulbasaur"

    def test_player_serialization(self):
        p = Player(name="Ash")
        data = p.model_dump()
        assert data["name"] == "Ash"
        assert "position" in data
        assert "team" in data
        assert "inventory" in data

    def test_player_deserialization(self):
        data = {
            "name": "Ash",
            "team": [],
            "position": {"x": 10, "y": 20, "map_id": "route_1"},
            "inventory": [{"name": "Potion", "quantity": 3}],
        }
        p = Player(**data)
        assert p.position.x == 10
        assert p.inventory[0].name == "Potion"
        assert p.inventory[0].quantity == 3


class TestPokemonDataIntegrity:
    """Verify pokemon_data.json loads correctly and has valid data."""

    def test_all_pokemon_load(self):
        from backend.services.game_service import get_all_pokemon
        pokemon = get_all_pokemon()
        assert len(pokemon) == 9

    def test_starter_pokemon_exist(self):
        from backend.services.game_service import get_pokemon_by_id
        bulbasaur = get_pokemon_by_id(1)
        charmander = get_pokemon_by_id(4)
        squirtle = get_pokemon_by_id(7)
        assert bulbasaur is not None and bulbasaur.name == "Bulbasaur"
        assert charmander is not None and charmander.name == "Charmander"
        assert squirtle is not None and squirtle.name == "Squirtle"

    def test_starters_are_level_5(self):
        from backend.services.game_service import get_pokemon_by_id
        for sid in [1, 4, 7]:
            p = get_pokemon_by_id(sid)
            assert p.level == 5, f"{p.name} should be level 5 but is {p.level}"

    def test_all_pokemon_have_moves(self):
        from backend.services.game_service import get_all_pokemon
        for p in get_all_pokemon():
            assert len(p.moves) > 0, f"{p.name} has no moves"

    def test_evolution_lines(self):
        from backend.services.game_service import get_pokemon_by_id
        # Bulbasaur line
        assert get_pokemon_by_id(1).name == "Bulbasaur"
        assert get_pokemon_by_id(2).name == "Ivysaur"
        assert get_pokemon_by_id(3).name == "Venusaur"
        # Charmander line
        assert get_pokemon_by_id(4).name == "Charmander"
        assert get_pokemon_by_id(5).name == "Charmeleon"
        assert get_pokemon_by_id(6).name == "Charizard"
        # Squirtle line
        assert get_pokemon_by_id(7).name == "Squirtle"
        assert get_pokemon_by_id(8).name == "Wartortle"
        assert get_pokemon_by_id(9).name == "Blastoise"
