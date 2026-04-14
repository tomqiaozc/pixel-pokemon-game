from __future__ import annotations

from typing import Optional

from ..models.cave import (
    CaveState,
    CaveTransitionResponse,
    FlashResponse,
)
from .game_service import get_game
from .map_service import get_map, get_all_maps

# In-memory stores
_cave_lit: dict[str, set[str]] = {}  # game_id -> set of lit map_ids


def is_dark_cave(map_id: str) -> bool:
    """Check if a map is a dark cave."""
    game_map = get_map(map_id)
    if game_map is None:
        return False
    return game_map.is_dark


def get_cave_state(game_id: str, map_id: str) -> Optional[CaveState]:
    """Return darkness/visibility state for a cave."""
    game_map = get_map(map_id)
    if game_map is None:
        return None

    if game_map.map_type != "cave":
        return None

    lit_caves = _cave_lit.get(game_id, set())
    is_lit = map_id in lit_caves or not game_map.is_dark

    return CaveState(
        game_id=game_id,
        map_id=map_id,
        is_lit=is_lit,
        visibility_radius=10 if is_lit else 2,
    )


def use_flash_in_cave(game_id: str, map_id: str, pokemon_index: int) -> FlashResponse:
    """Validate Flash + illuminate cave."""
    game_map = get_map(map_id)
    if game_map is None:
        return FlashResponse(success=False, visibility_radius=2, message="Map not found!")

    if game_map.map_type != "cave":
        return FlashResponse(success=False, visibility_radius=10, message="This isn't a cave!")

    if not game_map.is_dark:
        return FlashResponse(success=False, visibility_radius=10, message="This cave is already bright!")

    lit_caves = _cave_lit.get(game_id, set())
    if map_id in lit_caves:
        return FlashResponse(success=True, visibility_radius=10, message="The cave is already lit!")

    # Light the cave
    if game_id not in _cave_lit:
        _cave_lit[game_id] = set()
    _cave_lit[game_id].add(map_id)

    return FlashResponse(
        success=True,
        visibility_radius=10,
        message="You used Flash! The cave is now lit!",
    )


def get_cave_transition(
    game_id: str, from_map_id: str, ladder_x: int, ladder_y: int
) -> Optional[CaveTransitionResponse]:
    """Handle cave floor transitions (ladders/stairs)."""
    game_map = get_map(from_map_id)
    if game_map is None:
        return None

    # Define ladder/stair connections between cave floors
    cave_transitions = {
        ("mt_moon_entrance", 12, 5): ("mt_moon_b1", 15, 28),
        ("mt_moon_b1", 15, 28): ("mt_moon_entrance", 12, 5),
    }

    key = (from_map_id, ladder_x, ladder_y)
    target = cave_transitions.get(key)
    if target is None:
        return None

    target_map_id, spawn_x, spawn_y = target
    target_map = get_map(target_map_id)
    if target_map is None:
        return None

    # Update player position
    game = get_game(game_id)
    if game is not None:
        game["player"]["position"]["map_id"] = target_map_id
        game["player"]["position"]["x"] = spawn_x
        game["player"]["position"]["y"] = spawn_y

    return CaveTransitionResponse(
        target_map_id=target_map_id,
        spawn_x=spawn_x,
        spawn_y=spawn_y,
        is_dark=target_map.is_dark,
        cave_level=target_map.cave_level,
    )


def get_cave_encounter_modifier(cave_level: int) -> float:
    """Higher cave levels = higher encounter rate modifier."""
    return 1.0 + (cave_level * 0.1)


def get_cave_maps() -> list[dict]:
    """List all cave maps."""
    all_maps = get_all_maps()
    return [
        {
            "id": m.id,
            "display_name": m.display_name,
            "is_dark": m.is_dark,
            "cave_level": m.cave_level,
        }
        for m in all_maps
        if m.map_type == "cave"
    ]
