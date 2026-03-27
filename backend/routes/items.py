from fastapi import APIRouter, HTTPException

from ..models.item import (
    BuyRequest,
    CatchRequest,
    SellRequest,
    TossItemRequest,
    UseItemRequest,
)
from ..services.battle_service import get_battle
from ..services.item_service import (
    attempt_catch,
    buy_item,
    get_all_items,
    get_inventory,
    get_item,
    get_shop,
    sell_item,
    toss_item,
    use_item,
)
from ..services.pokedex_service import auto_deposit, register_caught

router = APIRouter(prefix="/api", tags=["items"])


@router.get("/items")
def list_items():
    return get_all_items()


@router.get("/items/{item_id}")
def item_detail(item_id: int):
    item = get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/inventory/{game_id}")
def inventory(game_id: str):
    inv = get_inventory(game_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return inv


@router.post("/inventory/use")
def use(req: UseItemRequest):
    result = use_item(req.game_id, req.item_id, req.target_pokemon_index)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/inventory/toss")
def toss(req: TossItemRequest):
    result = toss_item(req.game_id, req.item_id, req.quantity)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.get("/shop/{shop_id}")
def shop(shop_id: str):
    shop_inv = get_shop(shop_id)
    if shop_inv is None:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop_inv


@router.post("/shop/buy")
def buy(req: BuyRequest):
    result = buy_item(req.game_id, req.shop_id, req.item_id, req.quantity)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/shop/sell")
def sell(req: SellRequest):
    result = sell_item(req.game_id, req.item_id, req.quantity)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


@router.post("/battle/catch")
def catch_pokemon(req: CatchRequest):
    battle = get_battle(req.battle_id)
    if battle is None:
        raise HTTPException(status_code=404, detail="Battle not found")
    if battle.is_over:
        raise HTTPException(status_code=400, detail="Battle is over")
    if battle.battle_type != "wild":
        raise HTTPException(status_code=400, detail="Cannot catch trainer Pokemon")

    item = get_item(req.item_id)
    if item is None or item.effect.type != "catch":
        raise HTTPException(status_code=400, detail="Invalid Pokeball")

    # Deduct item from inventory
    inv = get_inventory(req.game_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check inventory has the ball
    from ..services.game_service import get_game
    game = get_game(req.game_id)
    if game:
        inventory = game["player"].get("inventory", [])
        ball_entry = None
        for e in inventory:
            if e.get("item_id") == req.item_id:
                ball_entry = e
                break
        if ball_entry is None or ball_entry.get("quantity", 0) <= 0:
            raise HTTPException(status_code=400, detail="No Pokeballs in inventory")
        ball_entry["quantity"] -= 1

    enemy = battle.enemy_pokemon
    result = attempt_catch(
        enemy.model_dump(),
        item.effect.modifier or 1.0,
    )

    if result.caught:
        battle.is_over = True
        battle.winner = "player"

        # Add caught Pokemon to player's party or PC
        caught_pokemon = enemy.model_dump()
        # Reset HP to current (battle HP)
        caught_pokemon.pop("catch_rate", None)
        caught_pokemon.pop("base_exp", None)

        if game:
            team = game["player"].get("team", [])
            if len(team) < 6:
                team.append(caught_pokemon)
                result.stored_in = "party"
            else:
                if auto_deposit(req.game_id, caught_pokemon):
                    result.stored_in = "pc"
                else:
                    result.stored_in = "pc_full"

            # Register in Pokedex
            register_caught(req.game_id, enemy.species_id)

    return result
