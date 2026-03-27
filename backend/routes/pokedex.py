from fastapi import APIRouter, HTTPException

from ..models.pokedex import DepositRequest, RegisterRequest, WithdrawRequest
from ..services.pokedex_service import (
    auto_deposit,
    deposit_pokemon,
    get_pc_boxes,
    get_pokedex,
    get_pokedex_entry,
    get_pokedex_stats,
    heal_party,
    register_caught,
    register_seen,
    withdraw_pokemon,
)

router = APIRouter(tags=["pokedex-pc"])


# Pokedex endpoints
@router.get("/api/pokedex/{game_id}")
def pokedex(game_id: str):
    return get_pokedex(game_id)


@router.get("/api/pokedex/{game_id}/stats")
def stats(game_id: str):
    return get_pokedex_stats(game_id)


@router.get("/api/pokedex/{game_id}/{species_id}")
def pokedex_entry(game_id: str, species_id: int):
    entry = get_pokedex_entry(game_id, species_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return entry


@router.post("/api/pokedex/register-seen")
def seen(req: RegisterRequest):
    return register_seen(req.game_id, req.species_id, req.location)


@router.post("/api/pokedex/register-caught")
def caught(req: RegisterRequest):
    return register_caught(req.game_id, req.species_id, req.location)


# Pokemon Center
@router.post("/api/pokemon-center/heal/{game_id}")
def heal(game_id: str):
    result = heal_party(game_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return result


# PC Box
@router.get("/api/pc/boxes/{game_id}")
def pc_boxes(game_id: str):
    return get_pc_boxes(game_id)


@router.post("/api/pc/deposit")
def deposit(req: DepositRequest):
    error = deposit_pokemon(req.game_id, req.pokemon_index)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Pokemon deposited to PC"}


@router.post("/api/pc/withdraw")
def withdraw(req: WithdrawRequest):
    error = withdraw_pokemon(req.game_id, req.box_number, req.pokemon_index)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Pokemon withdrawn from PC"}
