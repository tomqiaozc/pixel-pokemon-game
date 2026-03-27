"""Data models for the Pokemon trading system."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TradeOffer(BaseModel):
    player_id: str  # game_id of the offering player
    pokemon_index: int  # index in player's team


class TradeSession(BaseModel):
    id: str
    trade_code: str
    player1_id: str
    player2_id: Optional[str] = None
    player1_offer: Optional[TradeOffer] = None
    player2_offer: Optional[TradeOffer] = None
    player1_confirmed: bool = False
    player2_confirmed: bool = False
    status: str = "waiting"  # waiting, selecting, confirmed, completed, cancelled
    created_at: datetime
    last_activity: datetime


class TradeResult(BaseModel):
    success: bool
    player1_given: dict  # Pokemon dict
    player1_received: dict
    player2_given: dict
    player2_received: dict
    message: str


class TradeHistoryEntry(BaseModel):
    date: str
    given_pokemon: str  # Pokemon name
    received_pokemon: str
    partner_name: str


# --- Request/Response models ---


class CreateTradeRequest(BaseModel):
    player_id: str  # game_id


class JoinTradeRequest(BaseModel):
    player_id: str  # game_id


class OfferPokemonRequest(BaseModel):
    session_id: str
    player_id: str
    pokemon_index: int  # index in player's team


class ConfirmTradeRequest(BaseModel):
    session_id: str
    player_id: str


class CancelOfferRequest(BaseModel):
    session_id: str
    player_id: str


class TradeSessionResponse(BaseModel):
    session: TradeSession
    player1_team: list[dict]
    player2_team: Optional[list[dict]] = None
