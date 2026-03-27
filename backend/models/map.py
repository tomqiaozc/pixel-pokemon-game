from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MapConnection(BaseModel):
    direction: str  # north, south, east, west
    target_map_id: str
    entry_x: int
    entry_y: int


class EncounterZone(BaseModel):
    x: int
    y: int
    width: int
    height: int
    encounter_table_id: str


class MapTrainer(BaseModel):
    trainer_id: str
    x: int
    y: int
    facing: str = "down"
    sight_range: int = 3


class MapNPC(BaseModel):
    npc_id: str
    x: int
    y: int
    facing: str = "down"


class MapBuilding(BaseModel):
    name: str
    x: int
    y: int
    width: int
    height: int
    door_x: int
    door_y: int
    interior_map_id: Optional[str] = None


class GameMap(BaseModel):
    id: str
    name: str
    display_name: str
    map_type: str  # town, route, interior, gym
    width: int
    height: int
    connections: list[MapConnection] = []
    npcs: list[MapNPC] = []
    trainers: list[MapTrainer] = []
    encounter_zones: list[EncounterZone] = []
    buildings: list[MapBuilding] = []
    default_weather: Optional[str] = None


class MapTransitionRequest(BaseModel):
    game_id: str
    from_map: str
    direction: str


class MapTransitionResponse(BaseModel):
    target_map_id: str
    spawn_x: int
    spawn_y: int
    map_data: GameMap


class BuildingEnterRequest(BaseModel):
    game_id: str
    building_door_x: int
    building_door_y: int


class PlayerMoveRequest(BaseModel):
    game_id: str
    x: int
    y: int
    facing: str = "down"


class PlayerMoveResponse(BaseModel):
    x: int
    y: int
    map_id: str
    in_encounter_zone: bool = False
    encounter_table_id: Optional[str] = None
