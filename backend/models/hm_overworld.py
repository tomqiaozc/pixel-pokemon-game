from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class HMObstacle(BaseModel):
    id: str
    map_id: str
    obstacle_type: str  # "cuttable_tree", "pushable_boulder", "surf_zone"
    x: int
    y: int
    width: int = 1
    height: int = 1
    hm_required: str  # "Cut", "Surf", "Strength", "Flash"
    badge_required: Optional[str] = None
    removed: bool = False
    push_direction: Optional[str] = None
    push_limit: int = 0


class UseHMRequest(BaseModel):
    game_id: str
    hm_move: str  # "Cut", "Surf", "Strength", "Flash"
    map_id: str
    target_x: int
    target_y: int
    pokemon_index: int  # Which party Pokemon knows the HM


class UseHMResponse(BaseModel):
    success: bool
    message: str
    obstacle_id: Optional[str] = None
    effect: Optional[str] = None  # "tree_removed", "surfing_started", "boulder_pushed", "cave_lit"
    new_state: Optional[dict] = None


class SurfStateRequest(BaseModel):
    game_id: str
    map_id: str
    x: int
    y: int


class BoulderPushRequest(BaseModel):
    game_id: str
    obstacle_id: str
    direction: str  # "up", "down", "left", "right"


class BoulderPushResponse(BaseModel):
    success: bool
    new_x: int
    new_y: int
    message: str
