from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Optional

from ..models.item import (
    CatchResult,
    InventoryEntry,
    Item,
    ShopInventory,
    ShopItem,
    TransactionResult,
    UseItemResult,
)
from .game_service import get_game

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_items_db: dict[int, Item] = {}
_shops_db: dict[str, dict] = {}
STARTING_MONEY = 3000


def _load_items() -> None:
    global _items_db
    with open(DATA_DIR / "items.json") as f:
        raw = json.load(f)
    _items_db = {i["id"]: Item(**i) for i in raw}


def _load_shops() -> None:
    global _shops_db
    with open(DATA_DIR / "shops.json") as f:
        _shops_db = json.load(f)


def get_item(item_id: int) -> Optional[Item]:
    if not _items_db:
        _load_items()
    return _items_db.get(item_id)


def get_all_items() -> list[Item]:
    if not _items_db:
        _load_items()
    return list(_items_db.values())


def _get_inventory(game: dict) -> list[dict]:
    return game["player"].setdefault("inventory", [])


def _get_money(game: dict) -> int:
    return game["player"].setdefault("money", STARTING_MONEY)


def _set_money(game: dict, amount: int) -> None:
    game["player"]["money"] = amount


def _find_inventory_item(inventory: list[dict], item_id: int) -> Optional[dict]:
    for entry in inventory:
        if entry.get("item_id") == item_id or entry.get("name") == get_item(item_id).name if get_item(item_id) else False:
            return entry
    return None


def get_inventory(game_id: str) -> Optional[list[InventoryEntry]]:
    game = get_game(game_id)
    if game is None:
        return None
    inv = _get_inventory(game)
    return [InventoryEntry(item_id=e.get("item_id", 0), quantity=e.get("quantity", 0)) for e in inv if "item_id" in e]


def use_item(
    game_id: str,
    item_id: int,
    target_pokemon_index: Optional[int] = None,
) -> Optional[UseItemResult]:
    game = get_game(game_id)
    if game is None:
        return None

    item = get_item(item_id)
    if item is None:
        return UseItemResult(success=False, message="Item not found")

    inventory = _get_inventory(game)
    inv_entry = None
    for e in inventory:
        if e.get("item_id") == item_id:
            inv_entry = e
            break
    if inv_entry is None or inv_entry.get("quantity", 0) <= 0:
        return UseItemResult(success=False, message="Item not in inventory")

    team = game["player"]["team"]
    effect = item.effect

    if effect.type == "heal_hp":
        if target_pokemon_index is None or target_pokemon_index >= len(team):
            return UseItemResult(success=False, message="No target Pokemon specified")
        pokemon = team[target_pokemon_index]
        max_hp = pokemon["stats"]["hp"]
        old_hp = pokemon.get("current_hp", max_hp)
        if old_hp >= max_hp:
            return UseItemResult(success=False, message="HP is already full")
        if old_hp <= 0:
            return UseItemResult(success=False, message="Pokemon is fainted, use Revive")
        new_hp = min(max_hp, old_hp + int(effect.amount or 0))
        healed = new_hp - old_hp
        pokemon["current_hp"] = new_hp
        inv_entry["quantity"] -= 1
        return UseItemResult(success=True, message=f"Healed {healed} HP", healed_amount=healed, new_hp=new_hp)

    if effect.type == "revive":
        if target_pokemon_index is None or target_pokemon_index >= len(team):
            return UseItemResult(success=False, message="No target Pokemon specified")
        pokemon = team[target_pokemon_index]
        if pokemon.get("current_hp", 1) > 0:
            return UseItemResult(success=False, message="Pokemon is not fainted")
        max_hp = pokemon["stats"]["hp"]
        new_hp = max(1, int(max_hp * (effect.amount or 0.5)))
        pokemon["current_hp"] = new_hp
        inv_entry["quantity"] -= 1
        return UseItemResult(success=True, message=f"Revived to {new_hp} HP", new_hp=new_hp)

    if effect.type == "cure_status":
        if target_pokemon_index is None or target_pokemon_index >= len(team):
            return UseItemResult(success=False, message="No target Pokemon specified")
        pokemon = team[target_pokemon_index]
        status = pokemon.get("status")
        if status is None:
            return UseItemResult(success=False, message="Pokemon has no status condition")
        if effect.status != "all" and effect.status != status:
            return UseItemResult(success=False, message=f"Cannot cure {status} with this item")
        pokemon["status"] = None
        inv_entry["quantity"] -= 1
        return UseItemResult(success=True, message=f"Cured {status}", status_removed=status)

    return UseItemResult(success=False, message="Item cannot be used this way")


def toss_item(game_id: str, item_id: int, quantity: int) -> Optional[list[InventoryEntry]]:
    game = get_game(game_id)
    if game is None:
        return None
    inventory = _get_inventory(game)
    for e in inventory:
        if e.get("item_id") == item_id:
            e["quantity"] = max(0, e["quantity"] - quantity)
            break
    return get_inventory(game_id)


def get_shop(shop_id: str) -> Optional[ShopInventory]:
    if not _shops_db:
        _load_shops()
    shop_data = _shops_db.get(shop_id)
    if shop_data is None:
        return None

    items = []
    for si in shop_data["items"]:
        item = get_item(si["item_id"])
        if item:
            items.append(ShopItem(
                item_id=item.id,
                name=item.name,
                price=item.price,
                description=item.description,
                stock=si["stock"],
            ))
    return ShopInventory(name=shop_data["name"], items=items)


def buy_item(
    game_id: str,
    shop_id: str,
    item_id: int,
    quantity: int,
) -> Optional[TransactionResult]:
    game = get_game(game_id)
    if game is None:
        return None

    item = get_item(item_id)
    if item is None:
        return TransactionResult(
            success=False, message="Item not found",
            money=_get_money(game), inventory=get_inventory(game_id) or [],
        )

    total_cost = item.price * quantity
    money = _get_money(game)
    if money < total_cost:
        return TransactionResult(
            success=False, message="Not enough money",
            money=money, inventory=get_inventory(game_id) or [],
        )

    _set_money(game, money - total_cost)
    inventory = _get_inventory(game)

    # Add to inventory
    found = False
    for e in inventory:
        if e.get("item_id") == item_id:
            e["quantity"] += quantity
            found = True
            break
    if not found:
        inventory.append({"item_id": item_id, "quantity": quantity})

    return TransactionResult(
        success=True,
        message=f"Bought {quantity}x {item.name}",
        money=_get_money(game),
        inventory=get_inventory(game_id) or [],
    )


def sell_item(
    game_id: str,
    item_id: int,
    quantity: int,
) -> Optional[TransactionResult]:
    game = get_game(game_id)
    if game is None:
        return None

    item = get_item(item_id)
    if item is None:
        return TransactionResult(
            success=False, message="Item not found",
            money=_get_money(game), inventory=get_inventory(game_id) or [],
        )

    inventory = _get_inventory(game)
    inv_entry = None
    for e in inventory:
        if e.get("item_id") == item_id:
            inv_entry = e
            break
    if inv_entry is None or inv_entry.get("quantity", 0) < quantity:
        return TransactionResult(
            success=False, message="Not enough items to sell",
            money=_get_money(game), inventory=get_inventory(game_id) or [],
        )

    inv_entry["quantity"] -= quantity
    earned = item.sell_price * quantity
    _set_money(game, _get_money(game) + earned)

    return TransactionResult(
        success=True,
        message=f"Sold {quantity}x {item.name} for ${earned}",
        money=_get_money(game),
        inventory=get_inventory(game_id) or [],
    )


def attempt_catch(
    battle_enemy_pokemon: dict,
    ball_modifier: float,
) -> CatchResult:
    """Calculate if a catch attempt succeeds."""
    max_hp = battle_enemy_pokemon.get("max_hp", battle_enemy_pokemon["stats"]["hp"])
    current_hp = battle_enemy_pokemon["current_hp"]
    catch_rate = battle_enemy_pokemon.get("catch_rate", 45)

    # Catch formula: ((3*maxHP - 2*currentHP) * catchRate * ballModifier) / (3*maxHP)
    numerator = (3 * max_hp - 2 * current_hp) * catch_rate * ball_modifier
    denominator = 3 * max_hp
    catch_value = numerator / denominator

    # Each shake has catch_value/255 chance
    shakes = 0
    for _ in range(3):
        if random.randint(0, 255) < catch_value:
            shakes += 1
        else:
            break

    caught = shakes == 3
    if caught:
        return CatchResult(
            success=True, shakes=3, caught=True,
            message="Gotcha! Pokemon was caught!",
        )
    messages = ["Oh no! The Pokemon broke free!", "Aww! It appeared to be caught!", "Aargh! Almost had it!"]
    return CatchResult(
        success=True, shakes=shakes, caught=False,
        message=messages[min(shakes, len(messages) - 1)],
    )
