from fastapi import APIRouter, HTTPException

from ..models.encounter import EncounterCheckRequest, EncounterCheckResponse
from ..services.encounter_service import (
    check_encounter,
    generate_wild_pokemon,
    get_all_species,
    get_species,
)

router = APIRouter(prefix="/api/encounter", tags=["encounter"])


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
