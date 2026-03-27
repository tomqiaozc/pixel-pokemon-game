from fastapi import APIRouter, HTTPException

from ..services.game_service import get_all_pokemon, get_pokemon_by_id

router = APIRouter(prefix="/api/pokemon", tags=["pokemon"])


@router.get("")
def list_pokemon():
    return get_all_pokemon()


@router.get("/{pokemon_id}")
def get_pokemon(pokemon_id: int):
    pokemon = get_pokemon_by_id(pokemon_id)
    if pokemon is None:
        raise HTTPException(status_code=404, detail="Pokemon not found")
    return pokemon
