from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class WeatherState(BaseModel):
    current_weather: Optional[str] = None  # "rain", "sun", "sandstorm", "hail"
    turns_remaining: int = 0  # 0 = indefinite (ability-set), >0 = countdown


class WeatherEvent(BaseModel):
    event_type: str  # "weather_set", "weather_damage", "weather_ended"
    weather: Optional[str] = None
    pokemon: Optional[str] = None  # "player" or "enemy" for damage events
    damage: Optional[int] = None
    message: str
