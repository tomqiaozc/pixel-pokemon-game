"""Berry farming data models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BerryDef(BaseModel):
    """Static berry definition."""
    id: str
    name: str
    description: str
    growth_time_minutes: int = 30
    stages: list[str] = ["planted", "sprouted", "growing", "flowering", "ready"]
    yield_min: int = 1
    yield_max: int = 3
    effect_type: str  # heal_hp, cure_status, restore_pp, catch_bonus
    effect_amount: Optional[float] = None
    effect_status: Optional[str] = None
    rarity: str = "common"  # common, uncommon, rare


class BerryPlot(BaseModel):
    """A single berry plot on a map."""
    plot_id: str
    map_id: str
    x: int
    y: int
    planted_berry: Optional[str] = None  # berry id
    plant_time: Optional[float] = None  # epoch seconds
    water_count: int = 0
    growth_stage: str = "empty"  # empty, planted, sprouted, growing, flowering, ready
    ready_time: Optional[float] = None  # epoch seconds when ready


class BerryPouch(BaseModel):
    """Player's berry inventory."""
    berries: dict[str, int] = {}  # berry_id -> quantity


class PlantRequest(BaseModel):
    game_id: str
    plot_id: str
    berry_id: str


class WaterRequest(BaseModel):
    game_id: str


class HarvestRequest(BaseModel):
    game_id: str


class BerryPlotResponse(BaseModel):
    plot_id: str
    map_id: str
    x: int
    y: int
    planted_berry: Optional[str] = None
    berry_name: Optional[str] = None
    growth_stage: str
    water_count: int
    time_remaining_seconds: Optional[int] = None
    yield_estimate: Optional[int] = None


class HarvestResult(BaseModel):
    success: bool
    message: str
    berry_id: Optional[str] = None
    berry_name: Optional[str] = None
    quantity: int = 0
