"""Leaderboard, stats, and achievement API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.game_service import get_game
from ..services.leaderboard_service import (
    check_achievements,
    get_achievement_summary,
    get_achievements,
    get_player_stats,
    get_pokedex_leaderboard,
    get_pvp_leaderboard,
    get_recent_notifications,
    get_trainer_leaderboard,
)

router = APIRouter(prefix="/api", tags=["leaderboard"])


class SaveStatsRequest(BaseModel):
    """Accept frontend stats sync — fields are optional since frontend may send partial data."""
    battlesWon: Optional[int] = None
    pokemonCaught: Optional[int] = None
    playTimeMs: Optional[int] = None


class SaveAchievementsRequest(BaseModel):
    achievements: list[str] = []


# --- Leaderboards ---

@router.get("/leaderboard/trainers")
def trainers_leaderboard(limit: int = 10):
    return get_trainer_leaderboard(limit)


@router.get("/leaderboard/pvp")
def pvp_leaderboard(limit: int = 10):
    return get_pvp_leaderboard(limit)


@router.get("/leaderboard/pokedex")
def pokedex_leaderboard(limit: int = 10):
    return get_pokedex_leaderboard(limit)


# --- Player Stats ---

@router.get("/player/{player_id}/stats")
def player_stats(player_id: str):
    stats = get_player_stats(player_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return stats


@router.post("/player/{player_id}/stats")
def save_player_stats(player_id: str, req: SaveStatsRequest):
    """Accept frontend stats sync. Backend is authoritative so this triggers
    an achievement check and returns the current server-side stats."""
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Sync play time if provided (frontend sends milliseconds)
    if req.playTimeMs is not None:
        from ..services.game_service import update_play_time
        update_play_time(player_id, req.playTimeMs // 1000)

    # Trigger achievement check
    check_achievements(player_id)

    # Return authoritative server stats
    stats = get_player_stats(player_id)
    return stats


# --- Achievements ---

@router.get("/player/{player_id}/achievements")
def player_achievements(player_id: str):
    # H4: Return 404 for nonexistent players
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return get_achievements(player_id)


@router.post("/player/{player_id}/achievements")
def save_player_achievements(player_id: str, req: SaveAchievementsRequest):
    """Accept frontend achievement sync. Backend is authoritative — this triggers
    a server-side achievement check and returns the current state."""
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Trigger server-side achievement check (backend is source of truth)
    result = check_achievements(player_id)
    return result


@router.post("/achievements/check/{player_id}")
def check_player_achievements(player_id: str):
    # M4: Return 404 for nonexistent players
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    result = check_achievements(player_id)
    return result


@router.get("/achievements/recent/{player_id}")
def recent_achievements(player_id: str, limit: int = 10):
    """Get recently unlocked achievements (drains notification queue)."""
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return get_recent_notifications(player_id, limit)


@router.get("/achievements/summary/{player_id}")
def achievement_summary(player_id: str):
    """Get achievement summary with category breakdown and tier counts."""
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return get_achievement_summary(player_id)
