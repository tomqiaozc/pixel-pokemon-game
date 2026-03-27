from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .pokemon import Move, Stats


class LearnsetEntry(BaseModel):
    level: int
    move: str


class EvolutionData(BaseModel):
    to: int
    level: int


class PokemonSpecies(BaseModel):
    id: int
    name: str
    types: list[str]
    base_exp: int
    catch_rate: int
    stats: Stats
    learnset: list[LearnsetEntry]
    evolution: Optional[EvolutionData]
    sprite: str
    abilities: list[str] = []


class EncounterEntry(BaseModel):
    species_id: int
    min_level: int
    max_level: int
    weight: int


class EncounterTable(BaseModel):
    name: str
    encounter_type: str
    base_encounter_rate: float
    encounters: list[EncounterEntry]


class WildPokemon(BaseModel):
    species_id: int
    name: str
    types: list[str]
    level: int
    stats: Stats
    current_hp: int
    moves: list[Move]
    catch_rate: int
    base_exp: int
    sprite: str
    ability_id: Optional[str] = None


class EncounterCheckRequest(BaseModel):
    area_id: str


class EncounterCheckResponse(BaseModel):
    encountered: bool
    pokemon: Optional[WildPokemon] = None
