from __future__ import annotations

from pydantic import BaseModel


class CaveState(BaseModel):
    game_id: str
    map_id: str
    is_lit: bool = False
    visibility_radius: int = 2  # tiles visible without Flash (2 = minimal)


class FlashRequest(BaseModel):
    game_id: str
    map_id: str
    pokemon_index: int


class FlashResponse(BaseModel):
    success: bool
    visibility_radius: int  # Expands to full visibility (e.g., 10)
    message: str


class CaveTransitionRequest(BaseModel):
    game_id: str
    from_map_id: str
    ladder_x: int
    ladder_y: int


class CaveTransitionResponse(BaseModel):
    target_map_id: str
    spawn_x: int
    spawn_y: int
    is_dark: bool
    cave_level: int
