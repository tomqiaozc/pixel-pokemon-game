"""Legendary Pokemon data models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class LegendaryDef(BaseModel):
    """Static definition of a legendary Pokemon."""
    species_id: int
    name: str
    types: list[str]
    level: int
    base_stats: dict  # {"hp": int, ...}
    catch_rate: int = 3
    moves: list[str]
    location: str
    location_name: str
    required_flags: list[str]
    sprite: str
    ability: str = "pressure"


class LegendaryStatus(BaseModel):
    """Per-player tracking of legendary encounter state."""
    species_id: int
    status: str = "available"  # available, in_battle, caught, fainted


class LegendaryCheckResponse(BaseModel):
    """Response for checking legendary availability."""
    species_id: int
    name: str
    available: bool
    location: str
    location_name: str
    requirements_met: bool
    already_caught: bool
    already_fainted: bool
    required_flags: list[str]
    missing_flags: list[str] = []


class LegendaryListEntry(BaseModel):
    """Entry in the legendary list endpoint."""
    species_id: int
    name: str
    types: list[str]
    level: int
    location: str
    location_name: str
    status: str  # available, caught, fainted, locked
    requirements_met: bool


class LegendaryEncounterResponse(BaseModel):
    """Response when starting a legendary encounter."""
    battle_id: str
    legendary_name: str
    legendary_level: int
    message: str
