"""Leaderboard, player stats, and achievement system service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..models.leaderboard import (
    Achievement,
    AchievementCheckResult,
    PlayerStats,
    PokedexLeaderboardEntry,
    PvPLeaderboardEntry,
    TrainerLeaderboardEntry,
)
from .game_service import get_game, _games
from .gym_service import _earned_badges
from .pokedex_service import get_pokedex_stats
from .pvp_service import _pvp_history

# In-memory stores
_player_stats: dict[str, dict] = {}  # player_id -> stats counters
_achievements: dict[str, dict[str, Achievement]] = {}  # player_id -> {id: Achievement}

# Achievement definitions
_ACHIEVEMENT_DEFS = [
    {"id": "first_steps", "name": "First Steps", "description": "Catch your first Pokemon"},
    {"id": "collector", "name": "Collector", "description": "Catch 10 different species"},
    {"id": "gotta_catch_em_all", "name": "Gotta Catch 'Em All", "description": "Complete 50% of the Pokedex"},
    {"id": "pokemon_master", "name": "Pokemon Master", "description": "Complete 100% of the Pokedex"},
    {"id": "rock_solid", "name": "Rock Solid", "description": "Defeat Brock"},
    {"id": "water_works", "name": "Water Works", "description": "Defeat Misty"},
    {"id": "battle_tested", "name": "Battle Tested", "description": "Win 10 PvP battles"},
    {"id": "unbeatable", "name": "Unbeatable", "description": "Win 10 PvP battles in a row"},
    {"id": "evolve", "name": "Evolve!", "description": "Evolve a Pokemon for the first time"},
    {"id": "full_team", "name": "Full Team", "description": "Have 6 Pokemon in your party"},
    {"id": "big_spender", "name": "Big Spender", "description": "Spend 10,000 total at shops"},
    {"id": "speed_demon", "name": "Speed Demon", "description": "Beat Brock in under 30 minutes of play time"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_stats(player_id: str) -> dict:
    if player_id not in _player_stats:
        _player_stats[player_id] = {
            "total_pokemon_caught": 0,
            "total_battles_won": 0,
            "total_spent": 0,
            "evolutions": 0,
            "pvp_win_streak": 0,
            "max_pvp_win_streak": 0,
        }
    return _player_stats[player_id]


def _get_achievements(player_id: str) -> dict[str, Achievement]:
    if player_id not in _achievements:
        _achievements[player_id] = {
            d["id"]: Achievement(id=d["id"], name=d["name"], description=d["description"])
            for d in _ACHIEVEMENT_DEFS
        }
    return _achievements[player_id]


def _get_trainer_class(badge_count: int) -> str:
    if badge_count >= 8:
        return "Champion"
    elif badge_count >= 4:
        return "Ace Trainer"
    elif badge_count >= 1:
        return "Pokemon Trainer"
    return "Beginner"


# --- Stats ---

def record_pokemon_caught(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["total_pokemon_caught"] = stats.get("total_pokemon_caught", 0) + 1


def record_battle_won(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["total_battles_won"] = stats.get("total_battles_won", 0) + 1


def record_money_spent(player_id: str, amount: int) -> None:
    stats = _get_stats(player_id)
    stats["total_spent"] = stats.get("total_spent", 0) + amount


def record_evolution(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["evolutions"] = stats.get("evolutions", 0) + 1


def record_pvp_result(player_id: str, won: bool) -> None:
    stats = _get_stats(player_id)
    if won:
        stats["pvp_win_streak"] = stats.get("pvp_win_streak", 0) + 1
        stats["max_pvp_win_streak"] = max(
            stats.get("max_pvp_win_streak", 0), stats["pvp_win_streak"]
        )
    else:
        stats["pvp_win_streak"] = 0


def get_player_stats(player_id: str) -> PlayerStats | None:
    game = get_game(player_id)
    if game is None:
        return None

    raw = _get_stats(player_id)
    badges = list(_earned_badges.get(player_id, set()))
    dex = get_pokedex_stats(player_id)

    pvp_h = _pvp_history.get(player_id, [])
    pvp_wins = sum(1 for h in pvp_h if h.result == "win")
    pvp_losses = sum(1 for h in pvp_h if h.result == "loss")
    total_pvp = pvp_wins + pvp_losses
    win_rate = round(pvp_wins / total_pvp * 100, 1) if total_pvp > 0 else 0.0

    return PlayerStats(
        player_id=player_id,
        player_name=game["player"]["name"],
        play_time_seconds=game.get("play_time_seconds", 0),
        pokedex_seen=dex.seen_count,
        pokedex_caught=dex.caught_count,
        badges_earned=badges,
        pvp_wins=pvp_wins,
        pvp_losses=pvp_losses,
        pvp_win_rate=win_rate,
        total_pokemon_caught=raw.get("total_pokemon_caught", 0),
        total_battles_won=raw.get("total_battles_won", 0),
        trainer_class=_get_trainer_class(len(badges)),
    )


# --- Leaderboards ---

def _clamp_limit(limit: int) -> int:
    """H1: Validate and clamp leaderboard limit to [1, 100]."""
    return max(1, min(limit, 100))


def get_trainer_leaderboard(limit: int = 10) -> list[TrainerLeaderboardEntry]:
    limit = _clamp_limit(limit)
    entries = []
    for gid, game in _games.items():
        badges = len(_earned_badges.get(gid, set()))
        play_time = game.get("play_time_seconds", 0)
        entries.append({
            "player_id": gid,
            "player_name": game["player"]["name"],
            "badges": badges,
            "play_time_seconds": play_time,
        })
    # Sort: most badges first, then least play time
    entries.sort(key=lambda e: (-e["badges"], e["play_time_seconds"]))
    return [
        TrainerLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["badges"],
            badges=e["badges"],
            play_time_seconds=e["play_time_seconds"],
        )
        for i, e in enumerate(entries[:limit])
    ]


def get_pvp_leaderboard(limit: int = 10, min_battles: int = 5) -> list[PvPLeaderboardEntry]:
    limit = _clamp_limit(limit)
    player_records: dict[str, dict] = {}
    for pid, history in _pvp_history.items():
        wins = sum(1 for h in history if h.result == "win")
        losses = sum(1 for h in history if h.result == "loss")
        total = wins + losses
        if total < min_battles:
            continue
        game = get_game(pid)
        name = game["player"]["name"] if game else "Unknown"
        player_records[pid] = {
            "player_id": pid,
            "player_name": name,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
        }

    # H2: Sort by win_rate descending, then by total wins descending as tie-breaker
    sorted_records = sorted(
        player_records.values(),
        key=lambda e: (-e["win_rate"], -e["wins"]),
    )
    return [
        PvPLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["win_rate"],
            wins=e["wins"],
            losses=e["losses"],
            win_rate=e["win_rate"],
        )
        for i, e in enumerate(sorted_records[:limit])
    ]


def get_pokedex_leaderboard(limit: int = 10) -> list[PokedexLeaderboardEntry]:
    limit = _clamp_limit(limit)
    entries = []
    for gid, game in _games.items():
        dex = get_pokedex_stats(gid)
        entries.append({
            "player_id": gid,
            "player_name": game["player"]["name"],
            "caught": dex.caught_count,
            "total": dex.total_species,
            "percentage": dex.completion_percentage,
        })
    entries.sort(key=lambda e: -e["percentage"])
    return [
        PokedexLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["percentage"],
            caught=e["caught"],
            total=e["total"],
            percentage=e["percentage"],
        )
        for i, e in enumerate(entries[:limit])
    ]


# --- Achievements ---

def check_achievements(player_id: str) -> AchievementCheckResult:
    """Check and award any newly earned achievements."""
    game = get_game(player_id)
    if game is None:
        return AchievementCheckResult()

    achs = _get_achievements(player_id)
    raw = _get_stats(player_id)
    badges = _earned_badges.get(player_id, set())
    dex = get_pokedex_stats(player_id)
    team = game["player"]["team"]

    pvp_h = _pvp_history.get(player_id, [])
    pvp_wins = sum(1 for h in pvp_h if h.result == "win")

    newly_earned: list[Achievement] = []
    now = _now_iso()

    def _award(ach_id: str) -> None:
        ach = achs[ach_id]
        if not ach.completed:
            ach.completed = True
            ach.completed_date = now
            newly_earned.append(ach)

    # First Steps: catch first Pokemon
    if raw.get("total_pokemon_caught", 0) >= 1:
        _award("first_steps")

    # Collector: 10 species caught
    if dex.caught_count >= 10:
        _award("collector")

    # 50% Pokedex
    if dex.completion_percentage >= 50.0:
        _award("gotta_catch_em_all")

    # 100% Pokedex
    if dex.completion_percentage >= 100.0:
        _award("pokemon_master")

    # Gym badges
    if "boulder" in badges:
        _award("rock_solid")
    if "cascade" in badges:
        _award("water_works")

    # PvP
    if pvp_wins >= 10:
        _award("battle_tested")
    if raw.get("max_pvp_win_streak", 0) >= 10:
        _award("unbeatable")

    # Evolution
    if raw.get("evolutions", 0) >= 1:
        _award("evolve")

    # Full team
    if len(team) >= 6:
        _award("full_team")

    # Big spender
    if raw.get("total_spent", 0) >= 10000:
        _award("big_spender")

    # Speed demon: beat Brock under 30 min
    if "boulder" in badges and game.get("play_time_seconds", 0) < 1800:
        _award("speed_demon")

    return AchievementCheckResult(
        newly_earned=newly_earned,
        all_achievements=list(achs.values()),
    )


def get_achievements(player_id: str) -> list[Achievement]:
    # H4: Only return achievements for existing players
    game = get_game(player_id)
    if game is None:
        return []
    return list(_get_achievements(player_id).values())
