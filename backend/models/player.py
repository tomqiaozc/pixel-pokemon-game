from __future__ import annotations

from pydantic import BaseModel

from .pokemon import Pokemon


class Position(BaseModel):
    x: int = 0
    y: int = 0
    map_id: str = "pallet_town"


class InventoryItem(BaseModel):
    name: str
    quantity: int


class Player(BaseModel):
    name: str
    team: list[Pokemon] = []
    position: Position = Position()
    inventory: list[InventoryItem] = []
