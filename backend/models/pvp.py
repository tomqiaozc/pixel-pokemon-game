"""Data models for the multiplayer PvP battle system."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .battle import BattlePokemon, StatusEvent, TurnEvent
from .weather import WeatherEvent


class PvPSession(BaseModel):
    id: str
    battle_code: str
    player1_id: str
    player2_id: Optional[str] = None
    player1_ready: bool = False
    player2_ready: bool = False
    status: str = "waiting"  # waiting, ready, battling, completed
    created_at: datetime
    last_activity: datetime


class PvPAction(BaseModel):
    action: str  # "fight" or "switch"
    move_index: Optional[int] = None  # for fight actions
    switch_index: Optional[int] = None  # for switch actions (future)


class PvPTurnResult(BaseModel):
    turn_number: int
    events: list[TurnEvent] = []
    status_events: list[StatusEvent] = []
    weather_events: list[WeatherEvent] = []
    battle_over: bool = False
    winner: Optional[str] = None  # "player1" or "player2"


class PvPBattleResult(BaseModel):
    winner_id: str
    loser_id: str
    turns: int
    forfeit: bool = False
    date: str


class PvPHistoryEntry(BaseModel):
    date: str
    opponent_name: str
    result: str  # "win", "loss"
    turns: int
    forfeit: bool = False


# --- Request/Response models ---


class CreatePvPRequest(BaseModel):
    player_id: str


class JoinPvPRequest(BaseModel):
    player_id: str


class ReadyPvPRequest(BaseModel):
    session_id: str
    player_id: str
    lead_pokemon_index: int = 0  # which team member leads


class PvPActionRequest(BaseModel):
    session_id: str
    player_id: str
    action: str  # "fight"
    move_index: Optional[int] = None


class ForfeitRequest(BaseModel):
    session_id: str
    player_id: str


class PvPStateResponse(BaseModel):
    session: PvPSession
    player1_pokemon: Optional[dict] = None
    player2_pokemon: Optional[dict] = None
    turn_number: int = 0
    last_turn_result: Optional[PvPTurnResult] = None
