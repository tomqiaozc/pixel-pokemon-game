from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .pokemon import Move


class EvolutionCheckResponse(BaseModel):
    can_evolve: bool
    evolves_to: Optional[int] = None
    evolves_to_name: Optional[str] = None
    evolution_level: Optional[int] = None


class EvolutionResult(BaseModel):
    success: bool
    old_species_id: int
    old_name: str
    new_species_id: int
    new_name: str
    new_stats: dict
    new_moves: list[Move]
    new_level: int


class PendingMovesResponse(BaseModel):
    pending_moves: list[dict]  # [{name, type, power, accuracy, pp}]
    current_moves: list[Move]


class LearnMoveRequest(BaseModel):
    move_name: str
    forget_move_index: Optional[int] = None


class LearnMoveResult(BaseModel):
    success: bool
    learned: str
    forgot: Optional[str] = None
    current_moves: list[Move]


class AwardExpRequest(BaseModel):
    game_id: str
    pokemon_index: int  # index in player's team
    defeated_species_id: int
    defeated_level: int


class LevelUpResult(BaseModel):
    exp_gained: int
    new_total_exp: int
    leveled_up: bool
    old_level: int
    new_level: int
    can_evolve: bool
    new_moves: list[str]
    new_stats: Optional[dict] = None
