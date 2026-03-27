from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.evolution import (
    AwardExpRequest,
    EvolutionCheckResponse,
    LearnMoveRequest,
    LearnMoveResult,
    LevelUpResult,
    PendingMovesResponse,
)
from ..models.pokemon import Move
from ..services.encounter_service import get_move_data
from ..services.evolution_service import (
    award_exp,
    check_evolution,
    evolve_pokemon,
    get_pending_moves,
)
from ..services.game_service import get_game
from ..services.leaderboard_service import check_achievements, record_evolution

router = APIRouter(prefix="/api/evolution", tags=["evolution"])


@router.get("/check/{species_id}/{level}", response_model=EvolutionCheckResponse)
def evolution_check(species_id: int, level: int):
    return check_evolution(species_id, level)


@router.post("/evolve/{game_id}/{pokemon_index}")
def evolve(game_id: str, pokemon_index: int):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise HTTPException(status_code=400, detail="Invalid Pokemon index")

    pokemon = team[pokemon_index]
    result = evolve_pokemon(pokemon)
    if result is None:
        raise HTTPException(status_code=400, detail="Pokemon cannot evolve")

    # Update the Pokemon in the game state
    pokemon["id"] = result.new_species_id
    pokemon["name"] = result.new_name
    pokemon["stats"] = result.new_stats
    pokemon["moves"] = [m.model_dump() for m in result.new_moves]

    # C1/C2: Record evolution and check achievements
    record_evolution(game_id)
    check_achievements(game_id)

    return result


@router.get("/pending-moves/{game_id}/{pokemon_index}", response_model=PendingMovesResponse)
def pending_moves(game_id: str, pokemon_index: int):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise HTTPException(status_code=400, detail="Invalid Pokemon index")

    pokemon = team[pokemon_index]
    pending = get_pending_moves(pokemon["id"], pokemon["level"], pokemon["moves"])
    current = [Move(**m) for m in pokemon["moves"]]

    return PendingMovesResponse(pending_moves=pending, current_moves=current)


@router.post("/learn-move/{game_id}/{pokemon_index}", response_model=LearnMoveResult)
def learn_move(game_id: str, pokemon_index: int, req: LearnMoveRequest):
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise HTTPException(status_code=400, detail="Invalid Pokemon index")

    pokemon = team[pokemon_index]
    md = get_move_data(req.move_name)
    if md is None:
        raise HTTPException(status_code=404, detail="Move not found")

    new_move = Move(**md)
    current_moves = pokemon["moves"]
    forgot = None

    if len(current_moves) < 4:
        current_moves.append(new_move.model_dump())
    elif req.forget_move_index is not None:
        if 0 <= req.forget_move_index < len(current_moves):
            forgot = current_moves[req.forget_move_index]["name"]
            current_moves[req.forget_move_index] = new_move.model_dump()
        else:
            raise HTTPException(status_code=400, detail="Invalid forget_move_index")
    else:
        raise HTTPException(
            status_code=400,
            detail="Pokemon already has 4 moves. Provide forget_move_index.",
        )

    return LearnMoveResult(
        success=True,
        learned=req.move_name,
        forgot=forgot,
        current_moves=[Move(**m) for m in current_moves],
    )


@router.post("/award-exp", response_model=LevelUpResult)
def exp_award(req: AwardExpRequest):
    result = award_exp(req.game_id, req.pokemon_index, req.defeated_species_id, req.defeated_level)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not award EXP")
    return result
