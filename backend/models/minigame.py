"""Pydantic models for mini-games, coins, and prize exchange."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CoinTransaction(BaseModel):
    game_id: str
    coins_before: int
    coins_after: int
    money_before: int
    money_after: int
    amount: int


class SlotSymbol(BaseModel):
    name: str
    weight: int  # out of 100


class SlotResult(BaseModel):
    reels: list[str]
    win: bool
    payout: int
    coins_before: int
    coins_after: int


class MemoryCompleteRequest(BaseModel):
    game_id: str
    difficulty: str  # easy, medium, hard
    time_seconds: float
    pairs_matched: int


class MemoryCompleteResult(BaseModel):
    valid: bool
    coins_earned: int
    coins_before: int
    coins_after: int
    message: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: list[str]
    correct_index: int


class QuizSession(BaseModel):
    session_id: str
    game_id: str
    questions: list[QuizQuestion]


class QuizSubmitResult(BaseModel):
    score: int
    total: int
    coins_earned: int
    coins_before: int
    coins_after: int
    results: list[bool]


class Prize(BaseModel):
    id: int
    name: str
    prize_type: str  # "pokemon", "item"
    coin_cost: int
    description: str
    species_id: Optional[int] = None
    level: Optional[int] = None
    item_id: Optional[int] = None


class RedeemResult(BaseModel):
    success: bool
    message: str
    coins_before: int
    coins_after: int
    prize_name: str
