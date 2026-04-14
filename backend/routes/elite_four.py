from fastapi import APIRouter, HTTPException

from ..services.elite_four_service import (
    defeat_member,
    enter_elite_four,
    enter_hall_of_fame,
    get_elite_four_state,
    get_hall_of_fame,
    get_member_data,
    reset_elite_four,
)

router = APIRouter(tags=["elite-four"])


@router.get("/api/elite-four/{game_id}")
def elite_four_status(game_id: str):
    return get_elite_four_state(game_id)


@router.post("/api/elite-four/{game_id}/enter")
def elite_four_enter(game_id: str):
    result = enter_elite_four(game_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/api/elite-four/member/{member_id}")
def elite_four_member(member_id: str):
    data = get_member_data(member_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return data


@router.post("/api/elite-four/{game_id}/defeat/{member_id}")
def elite_four_defeat(game_id: str, member_id: str):
    result = defeat_member(game_id, member_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/api/elite-four/{game_id}/hall-of-fame")
def elite_four_hall_of_fame(game_id: str):
    result = enter_hall_of_fame(game_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/api/hall-of-fame/{game_id}")
def hall_of_fame(game_id: str):
    return get_hall_of_fame(game_id)


@router.post("/api/elite-four/{game_id}/reset")
def elite_four_reset(game_id: str):
    return reset_elite_four(game_id)
