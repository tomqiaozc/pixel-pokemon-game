from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models.hm_overworld import (
    BoulderPushResponse,
    HMObstacle,
    UseHMResponse,
)
from .game_service import get_game
from .gym_service import get_badges

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# In-memory stores
_obstacles: list[HMObstacle] = []
_removed_obstacles: dict[str, set[str]] = {}  # game_id -> set of obstacle_ids
_surf_state: dict[str, bool] = {}  # game_id -> is_surfing
_strength_active: dict[str, bool] = {}  # game_id -> strength_enabled
_boulder_positions: dict[str, dict[str, tuple[int, int]]] = {}  # game_id -> {obstacle_id: (x, y)}
_boulder_push_counts: dict[str, dict[str, int]] = {}  # game_id -> {obstacle_id: count}


def _load_obstacles() -> None:
    global _obstacles
    with open(DATA_DIR / "hm_obstacles.json") as f:
        raw = json.load(f)
    _obstacles = [HMObstacle(**{k: v for k, v in o.items() if k in HMObstacle.model_fields}) for o in raw]


def _ensure_loaded() -> None:
    if not _obstacles:
        _load_obstacles()


def load_hm_obstacles() -> list[HMObstacle]:
    _ensure_loaded()
    return list(_obstacles)


def get_obstacles_for_map(map_id: str) -> list[HMObstacle]:
    _ensure_loaded()
    return [o for o in _obstacles if o.map_id == map_id]


def _has_badge(game_id: str, badge_id: str) -> bool:
    badges = get_badges(game_id)
    return any(b.badge_id == badge_id and b.earned for b in badges)


def _pokemon_knows_move(game: dict, pokemon_index: int, hm_move: str) -> bool:
    team = game["player"].get("team", [])
    if pokemon_index < 0 or pokemon_index >= len(team):
        return False
    pokemon = team[pokemon_index]
    moves = pokemon.get("moves", [])
    return any(m.get("name", "").lower() == hm_move.lower() for m in moves)


def can_use_hm(game_id: str, hm_move: str, pokemon_index: int) -> tuple[bool, str]:
    """Validate: Pokemon knows move + player has required badge."""
    game = get_game(game_id)
    if game is None:
        return False, "Game not found"

    if not _pokemon_knows_move(game, pokemon_index, hm_move):
        return False, f"Pokemon doesn't know {hm_move}"

    # Badge requirements for each HM
    hm_badges = {
        "Cut": "cascade",
        "Surf": "soul",
        "Strength": "rainbow",
        "Flash": "boulder",
    }
    required = hm_badges.get(hm_move)
    if required and not _has_badge(game_id, required):
        return False, f"You need the {required.title()} Badge to use {hm_move}"

    return True, "OK"


def use_cut(game_id: str, map_id: str, target_x: int, target_y: int, pokemon_index: int) -> UseHMResponse:
    _ensure_loaded()
    can, msg = can_use_hm(game_id, "Cut", pokemon_index)
    if not can:
        return UseHMResponse(success=False, message=msg)

    # Find cuttable tree at target position
    removed = _removed_obstacles.get(game_id, set())
    for obs in _obstacles:
        if (obs.map_id == map_id and obs.obstacle_type == "cuttable_tree"
                and obs.x == target_x and obs.y == target_y):
            if obs.id in removed:
                return UseHMResponse(
                    success=True,
                    message="This tree has already been cut!",
                    obstacle_id=obs.id,
                    effect="already_removed",
                )
            if game_id not in _removed_obstacles:
                _removed_obstacles[game_id] = set()
            _removed_obstacles[game_id].add(obs.id)
            return UseHMResponse(
                success=True,
                message="You used Cut! The tree was cut down!",
                obstacle_id=obs.id,
                effect="tree_removed",
            )

    return UseHMResponse(success=False, message="There's nothing to cut here!")


def use_strength(game_id: str, map_id: str, target_x: int, target_y: int, pokemon_index: int) -> UseHMResponse:
    _ensure_loaded()
    can, msg = can_use_hm(game_id, "Strength", pokemon_index)
    if not can:
        return UseHMResponse(success=False, message=msg)

    # Check there's a boulder here
    for obs in _obstacles:
        if (obs.map_id == map_id and obs.obstacle_type == "pushable_boulder"
                and obs.x == target_x and obs.y == target_y):
            _strength_active[game_id] = True
            return UseHMResponse(
                success=True,
                message="You used Strength! You can now push boulders!",
                obstacle_id=obs.id,
                effect="strength_activated",
            )

    # Also check moved boulder positions
    moved = _boulder_positions.get(game_id, {})
    for obs_id, (bx, by) in moved.items():
        if bx == target_x and by == target_y:
            _strength_active[game_id] = True
            return UseHMResponse(
                success=True,
                message="You used Strength! You can now push boulders!",
                obstacle_id=obs_id,
                effect="strength_activated",
            )

    return UseHMResponse(success=False, message="There's no boulder here!")


def push_boulder(game_id: str, obstacle_id: str, direction: str) -> BoulderPushResponse:
    _ensure_loaded()
    if not _strength_active.get(game_id, False):
        return BoulderPushResponse(success=False, new_x=0, new_y=0, message="Use Strength first!")

    # Find the boulder
    boulder = None
    for obs in _obstacles:
        if obs.id == obstacle_id:
            boulder = obs
            break
    if boulder is None:
        return BoulderPushResponse(success=False, new_x=0, new_y=0, message="Boulder not found!")

    # Get current position (may have been moved)
    moved = _boulder_positions.get(game_id, {})
    cur_x, cur_y = moved.get(obstacle_id, (boulder.x, boulder.y))

    # Check push limit
    counts = _boulder_push_counts.get(game_id, {})
    push_count = counts.get(obstacle_id, 0)
    if boulder.push_limit > 0 and push_count >= boulder.push_limit:
        return BoulderPushResponse(
            success=False, new_x=cur_x, new_y=cur_y,
            message="This boulder can't be pushed any further!",
        )

    # Calculate new position
    dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(direction, (0, 0))
    if dx == 0 and dy == 0:
        return BoulderPushResponse(
            success=False, new_x=cur_x, new_y=cur_y,
            message="Invalid direction!",
        )

    new_x, new_y = cur_x + dx, cur_y + dy

    # Update position
    if game_id not in _boulder_positions:
        _boulder_positions[game_id] = {}
    _boulder_positions[game_id][obstacle_id] = (new_x, new_y)

    if game_id not in _boulder_push_counts:
        _boulder_push_counts[game_id] = {}
    _boulder_push_counts[game_id][obstacle_id] = push_count + 1

    return BoulderPushResponse(
        success=True, new_x=new_x, new_y=new_y,
        message="You pushed the boulder!",
    )


def use_surf(game_id: str, map_id: str, x: int, y: int, pokemon_index: int) -> UseHMResponse:
    _ensure_loaded()
    can, msg = can_use_hm(game_id, "Surf", pokemon_index)
    if not can:
        return UseHMResponse(success=False, message=msg)

    # Check if there's a surf zone at this position
    for obs in _obstacles:
        if (obs.map_id == map_id and obs.obstacle_type == "surf_zone"
                and obs.x <= x < obs.x + obs.width
                and obs.y <= y < obs.y + obs.height):
            _surf_state[game_id] = True
            return UseHMResponse(
                success=True,
                message="You used Surf!",
                obstacle_id=obs.id,
                effect="surfing_started",
                new_state={"surfing": True},
            )

    return UseHMResponse(success=False, message="There's no water here to surf on!")


def use_flash(game_id: str, map_id: str, pokemon_index: int) -> UseHMResponse:
    """Use Flash — delegates cave lighting to cave_service."""
    can, msg = can_use_hm(game_id, "Flash", pokemon_index)
    if not can:
        return UseHMResponse(success=False, message=msg)

    from .cave_service import use_flash_in_cave
    result = use_flash_in_cave(game_id, map_id, pokemon_index)
    return UseHMResponse(
        success=result.success,
        message=result.message,
        effect="cave_lit" if result.success else None,
        new_state={"visibility_radius": result.visibility_radius} if result.success else None,
    )


def get_surf_state(game_id: str) -> bool:
    return _surf_state.get(game_id, False)


def exit_surf(game_id: str) -> bool:
    if game_id in _surf_state:
        _surf_state[game_id] = False
        return True
    return False


def get_removed_obstacles(game_id: str, map_id: str) -> list[str]:
    """Return list of removed obstacle IDs for this map."""
    _ensure_loaded()
    removed = _removed_obstacles.get(game_id, set())
    return [obs.id for obs in _obstacles if obs.map_id == map_id and obs.id in removed]


def get_obstacle_states(game_id: str, map_id: str) -> list[dict]:
    """Return obstacle states for a specific game and map."""
    _ensure_loaded()
    removed = _removed_obstacles.get(game_id, set())
    moved = _boulder_positions.get(game_id, {})
    result = []
    for obs in _obstacles:
        if obs.map_id != map_id:
            continue
        state = obs.model_dump()
        state["removed"] = obs.id in removed
        if obs.id in moved:
            state["x"], state["y"] = moved[obs.id]
        result.append(state)
    return result
