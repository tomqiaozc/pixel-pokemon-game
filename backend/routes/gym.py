from fastapi import APIRouter, HTTPException

from ..services.gym_service import (
    award_badge,
    challenge_gym,
    defeat_trainer,
    get_all_gyms,
    get_badges,
    get_gym,
    get_trainer,
    get_trainers_on_map,
    start_trainer_battle,
)

router = APIRouter(tags=["gyms-trainers"])


# --- Gym endpoints ---

@router.get("/api/gyms")
def list_gyms():
    return get_all_gyms()


@router.get("/api/gyms/{gym_id}")
def gym_detail(gym_id: str):
    result = get_gym(gym_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gym not found")
    return result


@router.post("/api/gyms/{gym_id}/challenge/{game_id}")
def gym_challenge(gym_id: str, game_id: str):
    result = challenge_gym(game_id, gym_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot challenge this gym")
    return result


@router.post("/api/gyms/{gym_id}/award-badge/{game_id}")
def gym_award_badge(gym_id: str, game_id: str):
    result = award_badge(game_id, gym_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot award badge")
    return result


# --- Badge endpoints ---

@router.get("/api/badges/{game_id}")
def badges(game_id: str):
    return get_badges(game_id)


# --- Trainer endpoints ---

@router.get("/api/trainers/{map_id}")
def trainers_on_map(map_id: str, game_id: str = ""):
    return get_trainers_on_map(map_id, game_id if game_id else None)


@router.get("/api/trainers/detail/{trainer_id}")
def trainer_detail(trainer_id: str):
    result = get_trainer(trainer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return result


@router.post("/api/trainers/{trainer_id}/battle/{game_id}")
def trainer_battle(trainer_id: str, game_id: str):
    result = start_trainer_battle(game_id, trainer_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot battle this trainer")
    return result


@router.post("/api/trainers/{trainer_id}/defeat/{game_id}")
def trainer_defeat(trainer_id: str, game_id: str):
    result = defeat_trainer(game_id, trainer_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Cannot defeat trainer")
    return result
