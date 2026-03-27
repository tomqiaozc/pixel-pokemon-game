"""Data models for the leaderboard, player stats, and achievement system."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    player_name: str
    player_id: str
    score: float  # generic score field for sorting


class TrainerLeaderboardEntry(LeaderboardEntry):
    badges: int = 0
    play_time_seconds: int = 0


class PvPLeaderboardEntry(LeaderboardEntry):
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0


class PokedexLeaderboardEntry(LeaderboardEntry):
    caught: int = 0
    total: int = 0
    percentage: float = 0.0


class PlayerStats(BaseModel):
    player_id: str
    player_name: str
    play_time_seconds: int = 0
    pokedex_seen: int = 0
    pokedex_caught: int = 0
    badges_earned: list[str] = []
    pvp_wins: int = 0
    pvp_losses: int = 0
    pvp_win_rate: float = 0.0
    total_pokemon_caught: int = 0
    total_battles_won: int = 0
    trainer_class: str = "Beginner"


class Achievement(BaseModel):
    id: str
    name: str
    description: str
    completed: bool = False
    completed_date: Optional[str] = None


class AchievementCheckResult(BaseModel):
    newly_earned: list[Achievement] = []
    all_achievements: list[Achievement] = []
