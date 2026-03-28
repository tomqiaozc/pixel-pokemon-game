"""Pokemon breeding and daycare data models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DaycareSlot(BaseModel):
    """A Pokemon deposited in the daycare."""
    pokemon: dict  # full pokemon dict from player team
    deposited_at: float  # epoch seconds
    steps_gained: int = 0


class DaycareState(BaseModel):
    """Daycare state for a game."""
    slot_1: Optional[DaycareSlot] = None
    slot_2: Optional[DaycareSlot] = None
    egg_ready: bool = False
    egg_steps_accumulated: int = 0
    egg_threshold: int = 100  # steps between egg checks


class EggData(BaseModel):
    """An egg waiting to hatch."""
    species_id: int
    name: str
    ivs: dict  # {"hp": 12, "attack": 28, ...}
    moves: list[dict]
    gender: Optional[str] = None
    hatch_counter: int = 5000  # steps remaining
    is_egg: bool = True
    sprite: str = "egg.png"
    types: list[str] = []
    level: int = 1
    base_stats: Optional[dict] = None


class DepositRequest(BaseModel):
    game_id: str
    pokemon_index: int  # index in player team


class WithdrawRequest(BaseModel):
    game_id: str


class CollectEggRequest(BaseModel):
    game_id: str


class StepRequest(BaseModel):
    game_id: str
    steps: int = 1


class DaycareStatusResponse(BaseModel):
    slot_1: Optional[dict] = None
    slot_2: Optional[dict] = None
    egg_ready: bool = False
    compatible: bool = False
    compatibility_message: str = ""


class HatchResult(BaseModel):
    hatched: bool = False
    pokemon: Optional[dict] = None
    message: str = ""
