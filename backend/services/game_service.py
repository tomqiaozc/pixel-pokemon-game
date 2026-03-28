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

    # Assign gender from species data so it survives model_dump(exclude_none=True)
    from .encounter_service import get_species, _generate_gender
    species = get_species(starter_pokemon_id)
    if species is not None:
        starter.gender = _generate_gender(species)

    game_id = uuid.uuid4().hex[:8]
    player = Player(
        name=player_name,
        team=[starter],
        position=Position(),
        inventory=[],
    )
    game_state = {
        "id": game_id,
        "player": player.model_dump(exclude_none=True),
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
            "money": 3000,
        },
        "badges": 0,
        "play_time_seconds": 0,
    }
    _games[game_id] = game_state
    return game_state


def get_game(game_id: str) -> dict | None:
    return _games.get(game_id)


def get_full_game_state(game_id: str) -> dict | None:
    """Return enriched game state with badges, pokedex, and PC data for session restore."""
    game = _games.get(game_id)
    if game is None:
        return None

    from .gym_service import get_badges
    from .pokedex_service import get_pc_boxes, get_pokedex_stats

    badges_list = get_badges(game_id)
    pokedex_stats = get_pokedex_stats(game_id)
    pc_boxes = get_pc_boxes(game_id)

    return {
        **game,
        "badges_list": [b.model_dump() for b in badges_list],
        "pokedex_stats": pokedex_stats.model_dump(),
        "pc_boxes": [b.model_dump() for b in pc_boxes],
    }


def save_game(game_id: str, player_data: dict) -> dict | None:
    if game_id not in _games:
        return None
    # Validate player data through model, exclude_none to avoid injecting None defaults
    player = Player(**player_data)
    _games[game_id]["player"] = player.model_dump(exclude_none=True)
    return _games[game_id]


def update_play_time(game_id: str, seconds: int) -> dict | None:
    """M2: Update play_time_seconds for a game. Called by frontend to sync elapsed time."""
    game = _games.get(game_id)
    if game is None:
        return None
    if seconds < 0:
        return game
    game["play_time_seconds"] = seconds
    return game
