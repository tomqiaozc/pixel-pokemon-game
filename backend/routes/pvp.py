"""PvP battle system API routes."""
from fastapi import APIRouter, HTTPException

from ..models.pvp import (
    CreatePvPRequest,
    ForfeitRequest,
    JoinPvPRequest,
    PvPAction,
    PvPActionRequest,
    PvPStateResponse,
    ReadyPvPRequest,
)
from ..services.pvp_service import (
    cancel_pvp_session,
    create_pvp_session,
    forfeit_battle,
    get_last_turn_result,
    get_pvp_battle,
    get_pvp_history,
    get_pvp_result,
    get_pvp_session,
    join_pvp_session,
    ready_up,
    start_pvp_battle,
    submit_action,
)

router = APIRouter(prefix="/api/pvp", tags=["pvp"])


@router.post("/create")
def create_pvp(req: CreatePvPRequest):
    try:
        session = create_pvp_session(req.player_id)
        return {"session": session}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/join/{battle_code}")
def join_pvp(battle_code: str, req: JoinPvPRequest):
    try:
        session = join_pvp_session(battle_code, req.player_id)
        return {"session": session}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}")
def get_session(session_id: str):
    session = get_pvp_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="PvP session not found or expired")

    battle = get_pvp_battle(session_id)
    last_result = get_last_turn_result(session_id)

    response = PvPStateResponse(
        session=session,
        turn_number=battle.turn_count if battle else 0,
        last_turn_result=last_result,
    )

    if battle:
        response.player1_pokemon = {
            "name": battle.player_pokemon.name,
            "current_hp": battle.player_pokemon.current_hp,
            "max_hp": battle.player_pokemon.max_hp,
            "types": battle.player_pokemon.types,
            "level": battle.player_pokemon.level,
            "status": battle.player_pokemon.status,
        }
        response.player2_pokemon = {
            "name": battle.enemy_pokemon.name,
            "current_hp": battle.enemy_pokemon.current_hp,
            "max_hp": battle.enemy_pokemon.max_hp,
            "types": battle.enemy_pokemon.types,
            "level": battle.enemy_pokemon.level,
            "status": battle.enemy_pokemon.status,
        }

    return response


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    if not cancel_pvp_session(session_id):
        raise HTTPException(status_code=404, detail="PvP session not found")
    return {"message": "PvP session cancelled"}


@router.post("/ready")
def ready(req: ReadyPvPRequest):
    try:
        session = ready_up(req.session_id, req.player_id, req.lead_pokemon_index)
        # Auto-start if both ready
        if session.player1_ready and session.player2_ready:
            battle = start_pvp_battle(session.id)
            return {
                "session": session,
                "battle_started": True,
                "battle": {
                    "player1_pokemon": battle.player_pokemon.name,
                    "player2_pokemon": battle.enemy_pokemon.name,
                },
            }
        return {"session": session, "battle_started": False}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/action")
def pvp_action(req: PvPActionRequest):
    try:
        action = PvPAction(action=req.action, move_index=req.move_index)
        result = submit_action(req.session_id, req.player_id, action)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forfeit")
def forfeit(req: ForfeitRequest):
    try:
        result = forfeit_battle(req.session_id, req.player_id)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/state/{session_id}")
def pvp_state(session_id: str):
    """Get current PvP battle state."""
    return get_session(session_id)


@router.get("/result/{session_id}")
def pvp_result(session_id: str):
    result = get_pvp_result(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No result for this session")
    return result


@router.get("/history/{player_id}")
def pvp_history(player_id: str):
    return get_pvp_history(player_id)
