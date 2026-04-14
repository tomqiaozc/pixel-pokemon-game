from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class UnlockConditions(BaseModel):
    min_badges: int = 0
    required_items: list[int] = []
    required_pokemon_count: int = 0


class SecretAreaReward(BaseModel):
    items: list[dict] = []
    experience: int = 0


class SecretArea(BaseModel):
    id: str
    display_name: str
    map_id: str
    trigger_map_id: str
    trigger_type: str  # "walk", "interact", "hm_cut"
    trigger_x: int
    trigger_y: int
    unlock_conditions: UnlockConditions
    discovery_message: str
    rewards: SecretAreaReward


class SecretAreaProgress(BaseModel):
    game_id: str
    discovered_areas: list[str] = []


class DiscoverAreaRequest(BaseModel):
    game_id: str
    map_id: str
    x: int
    y: int


class DiscoverAreaResponse(BaseModel):
    discovered: bool
    area_id: Optional[str] = None
    display_name: Optional[str] = None
    message: Optional[str] = None
    rewards: Optional[SecretAreaReward] = None
