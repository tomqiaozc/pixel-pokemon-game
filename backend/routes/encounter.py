from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..models.encounter import EncounterCheckRequest, EncounterCheckResponse
from ..services.encounter_service import (
    check_encounter,
    fish_encounter,
    generate_wild_pokemon,
    get_all_species,
    get_species,
)

router = APIRouter(prefix="/api/encounter", tags=["encounter"])

STARTER_IDS = [1, 4, 7]  # Bulbasaur, Charmander, Squirtle
VALID_ROD_TIERS = {"old", "good", "super"}


class FishRequest(BaseModel):
    area_id: str
    rod_tier: str


@router.get("/starters")
def list_starters():
    """Return the 3 starter Pokemon with preview data."""
    starters = []
    for sid in STARTER_IDS:
        species = get_species(sid)
        if species:
            starters.append({
                "id": species.id,
                "name": species.name,
                "types": species.types,
                "sprite": species.sprite,
                "base_stats": species.stats.model_dump(),
                "description": f"A {'/'.join(species.types).title()}-type Pokemon",
            })
    return starters


@router.post("/check", response_model=EncounterCheckResponse)
def encounter_check(req: EncounterCheckRequest):
    return check_encounter(req.area_id)


@router.get("/species")
def list_species():
    return get_all_species()


@router.get("/species/{species_id}")
def species_detail(species_id: int):
    species = get_species(species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return species


@router.get("/generate/{species_id}/{level}")
def generate_pokemon(species_id: int, level: int):
    if level < 1 or level > 100:
        raise HTTPException(status_code=400, detail="Level must be between 1 and 100")
    try:
        return generate_wild_pokemon(species_id, level)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/fish", response_model=EncounterCheckResponse)
def encounter_fish(req: FishRequest):
    if req.rod_tier not in VALID_ROD_TIERS:
        raise HTTPException(status_code=400, detail=f"Invalid rod tier: {req.rod_tier}")
    result = fish_encounter(req.area_id, req.rod_tier)
    if result is None:
        raise HTTPException(status_code=404, detail="No fishing table for this area")
    return result
