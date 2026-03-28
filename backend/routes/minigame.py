"""Mini-game, coin, and prize exchange API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.minigame_service import (
    COIN_PRICE,
    COINS_PER_PURCHASE,
    buy_coins,
    complete_memory_game,
    get_coin_balance,
    get_prizes,
    redeem_prize,
    spin_slots,
    start_memory_game,
    start_quiz,
    submit_quiz,
)

router = APIRouter(prefix="/api/minigames", tags=["minigames"])


# ── Coin System ──

class BuyCoinsRequest(BaseModel):
    game_id: str
    money_amount: Optional[int] = None
    amount: int = 1


@router.get("/coins/{game_id}")
def coins_balance(game_id: str):
    result = get_coin_balance(game_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/coins/buy")
def coins_buy(req: BuyCoinsRequest):
    if req.money_amount is not None:
        purchase_count = req.money_amount // COIN_PRICE
    else:
        purchase_count = req.amount
    result = buy_coins(req.game_id, purchase_count)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot buy coins — insufficient money or invalid amount")
    return result.model_dump()


# ── Slot Machine ──

class SlotSpinRequest(BaseModel):
    game_id: str
    bet: int = 1


@router.post("/slots/spin")
def slots_spin(req: SlotSpinRequest):
    result = spin_slots(req.game_id, req.bet)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot spin — insufficient coins, invalid bet, or rate limited")
    return result.model_dump()


# ── Memory Game ──

class MemoryStartRequest(BaseModel):
    game_id: str
    difficulty: str  # easy, medium, hard


class MemoryCompleteRequest(BaseModel):
    game_id: str
    difficulty: str
    time_seconds: float
    pairs_matched: int


@router.post("/memory/start")
def memory_start(req: MemoryStartRequest):
    result = start_memory_game(req.game_id, req.difficulty)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid difficulty or game not found")
    return result


@router.post("/memory/complete")
def memory_complete(req: MemoryCompleteRequest):
    result = complete_memory_game(req.game_id, req.difficulty, req.time_seconds, req.pairs_matched)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid request")
    return result.model_dump()


# ── Quiz System ──

class QuizStartRequest(BaseModel):
    game_id: str


class QuizSubmitRequest(BaseModel):
    session_id: str
    answers: list[int]


@router.post("/quiz/start")
def quiz_start(req: QuizStartRequest):
    session = start_quiz(req.game_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game not found")
    data = session.model_dump()
    for q in data["questions"]:
        q.pop("correct_index", None)
    return data


@router.post("/quiz/submit")
def quiz_submit(req: QuizSubmitRequest):
    result = submit_quiz(req.session_id, req.answers)
    if result is None:
        raise HTTPException(status_code=400, detail="Invalid or expired quiz session")
    return result.model_dump()


# ── Prize Exchange ──

class RedeemRequest(BaseModel):
    game_id: str
    prize_id: int


@router.get("/prizes")
def list_prizes():
    return [p.model_dump() for p in get_prizes()]


@router.post("/prizes/redeem")
def prize_redeem(req: RedeemRequest):
    result = redeem_prize(req.game_id, req.prize_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result.model_dump()
