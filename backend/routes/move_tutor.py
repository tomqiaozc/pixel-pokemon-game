"""Move Tutor & TM/HM API routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.encounter_service import get_species
from ..services.game_service import get_game
from ..services.move_tutor_service import (
    check_tm_compatibility,
    get_all_learnable_moves,
    get_all_tms,
    get_forgotten_moves,
    get_tm_by_number,
    get_tutor,
    remind_move,
    teach_move_via_tutor,
    use_tm,
)

router = APIRouter(prefix="/api", tags=["move-tutor"])


# ---- Request Models ----

class TeachMoveRequest(BaseModel):
    game_id: str
    pokemon_index: int
    tutor_id: str
    move_name: str
    forget_move_index: Optional[int] = None


class UseTMRequest(BaseModel):
    game_id: str
    pokemon_index: int
    tm_number: str
    forget_move_index: Optional[int] = None


class RemindMoveRequest(BaseModel):
    game_id: str
    pokemon_index: int
    move_name: str
    forget_move_index: Optional[int] = None


# ---- Tutor Endpoints ----
# NOTE: Specific routes MUST come before parameterized /tutor/{tutor_id}

@router.post("/tutor/teach")
def teach_move(req: TeachMoveRequest):
    """Teach a move to a Pokemon via Move Tutor."""
    result = teach_move_via_tutor(
        req.game_id, req.pokemon_index, req.tutor_id,
        req.move_name, req.forget_move_index,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/tutor/remind")
def remind_forgotten_move(req: RemindMoveRequest):
    """Re-teach a forgotten move using a Heart Scale."""
    result = remind_move(req.game_id, req.pokemon_index, req.move_name, req.forget_move_index)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/tutor/reminder/{game_id}/{pokemon_index}")
def get_reminder_moves(game_id: str, pokemon_index: int):
    """Get moves available for re-learning via Move Reminder."""
    game = get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise HTTPException(status_code=400, detail="Invalid Pokemon index")
    moves = get_forgotten_moves(game_id, pokemon_index)
    return {"forgotten_moves": moves}


@router.get("/tutor/{tutor_id}")
def get_tutor_info(tutor_id: str):
    """Get move tutor info and available moves."""
    tutor = get_tutor(tutor_id)
    if tutor is None:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return tutor


# ---- TM/HM Endpoints ----

@router.get("/tm/list")
def list_tms():
    """List all TM/HM definitions."""
    return get_all_tms()


@router.get("/tm/compatible/{tm_number}/{pokemon_id}")
def check_compatibility(tm_number: str, pokemon_id: int):
    """Check if a Pokemon species is compatible with a TM/HM."""
    tm_def = get_tm_by_number(tm_number)
    if tm_def is None:
        raise HTTPException(status_code=404, detail=f"TM/HM {tm_number} not found")
    species = get_species(pokemon_id)
    if species is None:
        raise HTTPException(status_code=404, detail=f"Pokemon species {pokemon_id} not found")
    compatible = check_tm_compatibility(tm_number, pokemon_id)
    return {
        "tm_number": tm_number,
        "pokemon_id": pokemon_id,
        "pokemon_name": species.name,
        "move_name": tm_def["move_name"],
        "compatible": compatible,
    }


@router.post("/tm/use")
def use_tm_item(req: UseTMRequest):
    """Use a TM/HM on a Pokemon."""
    result = use_tm(req.game_id, req.pokemon_index, req.tm_number, req.forget_move_index)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ---- Learnable Moves ----

@router.get("/moves/learnable/{pokemon_id}")
def learnable_moves(pokemon_id: int):
    """Get all moves a Pokemon can learn via tutor, TM, and HM."""
    species = get_species(pokemon_id)
    if species is None:
        raise HTTPException(status_code=404, detail=f"Pokemon species {pokemon_id} not found")
    return get_all_learnable_moves(pokemon_id)
