from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, model_validator

from .pokemon import Pokemon


class Position(BaseModel):
    x: int = 0
    y: int = 0
    map_id: str = "pallet_town"
    facing: str = "down"


class InventoryItem(BaseModel):
    item_id: Optional[int] = None
    name: str = ""
    quantity: int

    @model_validator(mode="before")
    @classmethod
    def accept_item_id_or_name(cls, values: dict) -> dict:
        """Accept inventory items with item_id, name, or both."""
        if isinstance(values, dict):
            has_id = "item_id" in values and values["item_id"] is not None
            has_name = "name" in values and values["name"]
            if not has_id and not has_name:
                raise ValueError("InventoryItem must have either item_id or name")
        return values


class Player(BaseModel):
    name: str
    team: list[Pokemon] = []
    position: Position = Position()
    inventory: list[InventoryItem] = []
    money: int = 3000
    coins: int = 0
