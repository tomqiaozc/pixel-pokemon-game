from __future__ import annotations

from pydantic import BaseModel


class Move(BaseModel):
    name: str
    type: str
    power: int
    accuracy: int
    pp: int


class Stats(BaseModel):
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int


class Pokemon(BaseModel):
    id: int
    name: str
    types: list[str]
    stats: Stats
    moves: list[Move]
    sprite: str
    level: int
