from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .pokemon import Move, Stats


class BattlePokemon(BaseModel):
    species_id: int
    name: str
    types: list[str]
    level: int
    stats: Stats
    current_hp: int
    max_hp: int
    moves: list[Move]
    sprite: str


class BattleState(BaseModel):
    id: str
    battle_type: str  # "wild" or "trainer"
    player_pokemon: BattlePokemon
    enemy_pokemon: BattlePokemon
    turn_count: int = 0
    is_over: bool = False
    winner: Optional[str] = None  # "player" or "enemy" or None
    can_run: bool = True
    log: list[dict] = []


class BattleStartRequest(BaseModel):
    game_id: str
    wild_pokemon: Optional[dict] = None


class BattleActionRequest(BaseModel):
    battle_id: str
    action: str  # "fight", "run"
    move_index: Optional[int] = None  # required when action="fight"


class TurnEvent(BaseModel):
    attacker: str  # "player" or "enemy"
    move: str
    damage: int
    effectiveness: str  # "normal", "super_effective", "not_very_effective", "immune"
    critical: bool
    target_hp_remaining: int
    target_fainted: bool


class TurnResult(BaseModel):
    events: list[TurnEvent]
    battle_over: bool
    winner: Optional[str] = None
    ran_away: bool = False
    run_failed: bool = False


class BattleStateResponse(BaseModel):
    battle: BattleState
    turn_result: Optional[TurnResult] = None
