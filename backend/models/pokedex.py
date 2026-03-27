from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PokedexEntry(BaseModel):
    species_id: int
    name: str
    status: str = "unseen"  # unseen, seen, caught
    first_seen_location: Optional[str] = None
    first_caught_location: Optional[str] = None


class PokedexStats(BaseModel):
    total_species: int
    seen_count: int
    caught_count: int
    completion_percentage: float


class RegisterRequest(BaseModel):
    game_id: str
    species_id: int
    location: str = "unknown"


class HealResult(BaseModel):
    healed_pokemon: list[dict]


class PCBox(BaseModel):
    box_number: int
    pokemon: list[dict]


class DepositRequest(BaseModel):
    game_id: str
    pokemon_index: int  # index in party


class WithdrawRequest(BaseModel):
    game_id: str
    box_number: int
    pokemon_index: int  # index in box
