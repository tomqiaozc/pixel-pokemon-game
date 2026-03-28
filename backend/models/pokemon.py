from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Move(BaseModel):
    name: str
    type: str
    power: int
    accuracy: int
    pp: int
    contact: bool = False

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        return v.lower()


class Stats(BaseModel):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int


class Pokemon(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    types: list[str]
    stats: Stats
    moves: list[Move]
    sprite: str
    level: int
    current_hp: Optional[int] = None
    max_hp: Optional[int] = None
    ability_id: Optional[str] = None
    status: Optional[str] = None
    held_item: Optional[str] = None
