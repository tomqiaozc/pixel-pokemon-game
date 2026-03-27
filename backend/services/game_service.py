from __future__ import annotations

import json
import uuid
from pathlib import Path

from ..models.player import Player, Position
from ..models.pokemon import Pokemon

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# In-memory stores
_pokemon_db: list[Pokemon] = []
_games: dict[str, dict] = {}


def _load_pokemon() -> None:
    global _pokemon_db
    with open(DATA_DIR / "pokemon_data.json") as f:
        raw = json.load(f)
    _pokemon_db = [Pokemon(**p) for p in raw]


def get_all_pokemon() -> list[Pokemon]:
    if not _pokemon_db:
        _load_pokemon()
    return _pokemon_db


def get_pokemon_by_id(pokemon_id: int) -> Pokemon | None:
    for p in get_all_pokemon():
        if p.id == pokemon_id:
            return p
    return None


def create_game(player_name: str, starter_pokemon_id: int) -> dict:
    starter = get_pokemon_by_id(starter_pokemon_id)
    if starter is None:
        raise ValueError(f"Pokemon with id {starter_pokemon_id} not found")

    game_id = uuid.uuid4().hex[:8]
    player = Player(
        name=player_name,
        team=[starter],
        position=Position(),
        inventory=[],
    )
    game_state = {
        "id": game_id,
        "player": player.model_dump(),
        "badges": 0,
        "play_time_seconds": 0,
    }
    _games[game_id] = game_state
    return game_state


def create_game_with_starter(player_name: str, starter_data: dict) -> dict:
    """Create a game with a pre-built starter Pokemon dict (with IVs applied)."""
    game_id = uuid.uuid4().hex[:8]
    game_state = {
        "id": game_id,
        "player": {
            "name": player_name,
            "team": [starter_data],
            "position": {"x": 0, "y": 0, "map_id": "pallet_town", "facing": "down"},
            "inventory": [],
        },
        "badges": 0,
        "play_time_seconds": 0,
    }
    _games[game_id] = game_state
    return game_state


def get_game(game_id: str) -> dict | None:
    return _games.get(game_id)


def save_game(game_id: str, player_data: dict) -> dict | None:
    if game_id not in _games:
        return None
    # Validate player data through model
    player = Player(**player_data)
    _games[game_id]["player"] = player.model_dump()
    return _games[game_id]
