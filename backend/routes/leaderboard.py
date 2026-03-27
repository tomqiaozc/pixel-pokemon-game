"""Leaderboard, stats, and achievement API routes."""
from fastapi import APIRouter, HTTPException

from ..services.game_service import get_game
from ..services.leaderboard_service import (
    check_achievements,
    get_achievements,
    get_player_stats,
    get_pokedex_leaderboard,
    get_pvp_leaderboard,
    get_trainer_leaderboard,
)

router = APIRouter(prefix="/api", tags=["leaderboard"])


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


# --- Achievements ---

@router.get("/player/{player_id}/achievements")
def player_achievements(player_id: str):
    # H4: Return 404 for nonexistent players
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return get_achievements(player_id)


@router.post("/achievements/check/{player_id}")
def check_player_achievements(player_id: str):
    # M4: Return 404 for nonexistent players
    game = get_game(player_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Player not found")
    result = check_achievements(player_id)
    return result
