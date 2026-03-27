from fastapi import APIRouter, HTTPException

from ..models.battle import (
    BattleActionRequest,
    BattleStartRequest,
    BattleStateResponse,
)
from ..services.battle_service import get_battle, process_action, start_battle
from ..services.encounter_service import generate_wild_pokemon
from ..services.game_service import get_game

router = APIRouter(prefix="/api/battle", tags=["battle"])


@router.post("/start", response_model=BattleStateResponse)
def battle_start(req: BattleStartRequest):
    game = get_game(req.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    player_team = game["player"]["team"]
    if not player_team:
        raise HTTPException(status_code=400, detail="Player has no Pokemon")

    # Use first non-fainted Pokemon
    lead = player_team[0]
    player_pokemon = {
        "species_id": lead["id"],
        "name": lead["name"],
        "types": lead["types"],
        "level": lead["level"],
        "stats": lead["stats"],
        "current_hp": lead["stats"]["hp"],
        "max_hp": lead["stats"]["hp"],
        "moves": lead["moves"],
        "sprite": lead["sprite"],
    }

    if req.wild_pokemon:
        enemy_pokemon = req.wild_pokemon
        # Ensure max_hp is set
        if "max_hp" not in enemy_pokemon:
            enemy_pokemon["max_hp"] = enemy_pokemon.get("current_hp", enemy_pokemon["stats"]["hp"])
        battle = start_battle(player_pokemon, enemy_pokemon, "wild")
    else:
        # Generate a random wild encounter for testing
        wild = generate_wild_pokemon(10, 5)  # default: Pidgey lv5
        enemy_pokemon = {
            "species_id": wild.species_id,
            "name": wild.name,
            "types": wild.types,
            "level": wild.level,
            "stats": wild.stats.model_dump(),
            "current_hp": wild.current_hp,
            "max_hp": wild.current_hp,
            "moves": [m.model_dump() for m in wild.moves],
            "sprite": wild.sprite,
        }
        battle = start_battle(player_pokemon, enemy_pokemon, "wild")

    return BattleStateResponse(battle=battle)


@router.post("/action", response_model=BattleStateResponse)
def battle_action(req: BattleActionRequest):
    battle = get_battle(req.battle_id)
    if battle is None:
        raise HTTPException(status_code=404, detail="Battle not found")

    if battle.is_over:
        raise HTTPException(status_code=400, detail="Battle is already over")

    if req.action not in ("fight", "run"):
        raise HTTPException(status_code=400, detail="Invalid action. Use 'fight' or 'run'")

    if req.action == "fight" and req.move_index is None:
        raise HTTPException(status_code=400, detail="move_index required for fight action")

    result = process_action(req.battle_id, req.action, req.move_index)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not process action")

    return BattleStateResponse(battle=battle, turn_result=result)


@router.get("/state/{battle_id}", response_model=BattleStateResponse)
def battle_state(battle_id: str):
    battle = get_battle(battle_id)
    if battle is None:
        raise HTTPException(status_code=404, detail="Battle not found")
    return BattleStateResponse(battle=battle)
