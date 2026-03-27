from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError

from ..services.encounter_service import generate_wild_pokemon, get_species
from ..services.game_service import create_game, create_game_with_starter, get_game, save_game

router = APIRouter(prefix="/api/game", tags=["game"])


class NewGameRequest(BaseModel):
    player_name: str
    starter_pokemon_id: int


class ChooseStarterRequest(BaseModel):
    player_name: str
    starter_id: int  # species_id: 1 (Bulbasaur), 4 (Charmander), 7 (Squirtle)


class SaveGameRequest(BaseModel):
    player: dict


@router.post("/new")
def new_game(req: NewGameRequest):
    try:
        return create_game(req.player_name, req.starter_pokemon_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/choose-starter")
def choose_starter(req: ChooseStarterRequest):
    """Create a new game with a properly generated starter Pokemon (with IVs)."""
    valid_starters = [1, 4, 7]
    if req.starter_id not in valid_starters:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid starter. Must be one of: {valid_starters}",
        )
    species = get_species(req.starter_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")

    # Generate starter at level 5 with random IVs
    starter = generate_wild_pokemon(req.starter_id, 5)
    starter_data = {
        "id": starter.species_id,
        "name": starter.name,
        "types": starter.types,
        "stats": starter.stats.model_dump(),
        "moves": [m.model_dump() for m in starter.moves],
        "sprite": starter.sprite,
        "level": starter.level,
        "ability_id": starter.ability_id,
    }

    # Create game with IV-calculated starter
    return create_game_with_starter(req.player_name, starter_data)


@router.get("/{game_id}")
def game_state(game_id: str):
    state = get_game(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


@router.post("/{game_id}/save")
def save(game_id: str, req: SaveGameRequest):
    try:
        state = save_game(game_id, req.player)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return state
