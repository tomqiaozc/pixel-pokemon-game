from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models.secret_area import (
    DiscoverAreaResponse,
    SecretArea,
    SecretAreaReward,
)
from .game_service import get_game
from .gym_service import get_badges

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# In-memory stores
_secret_areas: list[SecretArea] = []
_discovered: dict[str, list[str]] = {}  # game_id -> list of area_ids


def _load_secret_areas() -> None:
    global _secret_areas
    with open(DATA_DIR / "secret_areas.json") as f:
        raw = json.load(f)
    _secret_areas = [SecretArea(**a) for a in raw]


def _ensure_loaded() -> None:
    if not _secret_areas:
        _load_secret_areas()


def load_secret_areas() -> list[SecretArea]:
    _ensure_loaded()
    return list(_secret_areas)


def check_tile_for_secret(game_id: str, map_id: str, x: int, y: int) -> Optional[SecretArea]:
    """Check if walking on a tile triggers a secret area."""
    _ensure_loaded()
    for area in _secret_areas:
        if area.trigger_map_id == map_id and area.trigger_x == x and area.trigger_y == y:
            # Already discovered — still return it so frontend knows
            return area
    return None


def can_unlock_area(game_id: str, area: SecretArea) -> bool:
    """Validate unlock conditions (badges, items, pokemon count)."""
    game = get_game(game_id)
    if game is None:
        return False

    conds = area.unlock_conditions

    # Check badge count
    badges = get_badges(game_id)
    earned_count = sum(1 for b in badges if b.earned)
    if earned_count < conds.min_badges:
        return False

    # Check required items
    if conds.required_items:
        inventory = game["player"].get("inventory", [])
        owned_ids = {entry.get("item_id", entry.get("id")) for entry in inventory}
        for item_id in conds.required_items:
            if item_id not in owned_ids:
                return False

    # Check pokemon count
    if conds.required_pokemon_count > 0:
        team_count = len(game["player"].get("team", []))
        if team_count < conds.required_pokemon_count:
            return False

    return True


def discover_area(game_id: str, area_id: str) -> Optional[DiscoverAreaResponse]:
    """Mark area as discovered, grant rewards."""
    _ensure_loaded()
    game = get_game(game_id)
    if game is None:
        return None

    # Find the area
    area = None
    for a in _secret_areas:
        if a.id == area_id:
            area = a
            break
    if area is None:
        return None

    # Check if already discovered
    discovered_list = _discovered.get(game_id, [])
    if area_id in discovered_list:
        return DiscoverAreaResponse(
            discovered=True,
            area_id=area.id,
            display_name=area.display_name,
            message="You've already discovered this area!",
            rewards=None,
        )

    # Check unlock conditions
    if not can_unlock_area(game_id, area):
        return DiscoverAreaResponse(
            discovered=False,
            message="You don't meet the requirements to access this area.",
        )

    # Mark as discovered
    if game_id not in _discovered:
        _discovered[game_id] = []
    _discovered[game_id].append(area_id)

    # Grant rewards
    if area.rewards.experience > 0:
        team = game["player"].get("team", [])
        if team:
            # Grant XP to first Pokemon
            team[0]["experience"] = team[0].get("experience", 0) + area.rewards.experience

    return DiscoverAreaResponse(
        discovered=True,
        area_id=area.id,
        display_name=area.display_name,
        message=area.discovery_message,
        rewards=area.rewards,
    )


def get_discovered_areas(game_id: str) -> list[str]:
    """Return list of discovered area IDs."""
    return list(_discovered.get(game_id, []))


def is_area_discovered(game_id: str, area_id: str) -> bool:
    """Check single area."""
    return area_id in _discovered.get(game_id, [])
