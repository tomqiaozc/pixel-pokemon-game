from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ItemEffect(BaseModel):
    type: str  # heal_hp, cure_status, revive, catch, teach_move, level_up, pp_up, fishing, trade_item
    amount: Optional[float] = None
    status: Optional[str] = None
    modifier: Optional[float] = None
    move: Optional[str] = None
    rod_tier: Optional[str] = None


class Item(BaseModel):
    id: int
    name: str
    description: str
    category: str  # potion, status_heal, pokeball, key_item
    price: int
    sell_price: int
    effect: ItemEffect


class InventoryEntry(BaseModel):
    item_id: int
    quantity: int


class UseItemRequest(BaseModel):
    game_id: str
    item_id: int
    target_pokemon_index: Optional[int] = None


class UseItemResult(BaseModel):
    success: bool
    message: str
    healed_amount: Optional[int] = None
    new_hp: Optional[int] = None
    status_removed: Optional[str] = None


class TossItemRequest(BaseModel):
    game_id: str
    item_id: int
    quantity: int = Field(gt=0)


class BuyRequest(BaseModel):
    game_id: str
    shop_id: str
    item_id: int
    quantity: int = Field(gt=0)


class SellRequest(BaseModel):
    game_id: str
    item_id: int
    quantity: int = Field(gt=0)


class ShopItem(BaseModel):
    item_id: int
    name: str
    price: int
    description: str
    stock: int  # -1 for unlimited


class ShopInventory(BaseModel):
    name: str
    items: list[ShopItem]


class TransactionResult(BaseModel):
    success: bool
    message: str
    money: int
    inventory: list[InventoryEntry]


class CatchRequest(BaseModel):
    battle_id: str
    item_id: int  # pokeball item id
    game_id: str


class CatchResult(BaseModel):
    success: bool
    shakes: int  # 0-3
    caught: bool
    message: str
    stored_in: Optional[str] = None  # "party", "pc", "pc_full"
