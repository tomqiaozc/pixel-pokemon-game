from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator

from .pokemon import Move, Stats
from .weather import WeatherEvent, WeatherState


class StatStages(BaseModel):
    attack: int = 0
    defense: int = 0
    sp_attack: int = 0
    sp_defense: int = 0
    speed: int = 0
    accuracy: int = 0
    evasion: int = 0


class BattlePokemon(BaseModel):
    species_id: int
    name: str
    types: list[str]
    level: int
    stats: Stats
    current_hp: int
    max_hp: int
    moves: list[Move]
    sprite: str
    status: Optional[str] = None
    status_turns: int = 0
    stat_stages: StatStages = StatStages()
    confused: bool = False
    confused_turns: int = 0
    flinched: bool = False
    ability_id: Optional[str] = None
    flash_fire_activated: bool = False
    held_item: Optional[str] = None
    ivs: Optional[dict] = None
    gender: Optional[str] = None

    @field_validator("types", mode="before")
    @classmethod
    def normalize_types(cls, v: list[str]) -> list[str]:
        return [t.lower() for t in v]


class BattleState(BaseModel):
    id: str
    battle_type: str  # "wild" or "trainer"
    player_pokemon: BattlePokemon
    enemy_pokemon: BattlePokemon
    turn_count: int = 0
    is_over: bool = False
    winner: Optional[str] = None  # "player" or "enemy" or None
    can_run: bool = True
    log: list[dict] = []
    weather: WeatherState = WeatherState()


class BattleStartRequest(BaseModel):
    game_id: str
    wild_pokemon: Optional[dict] = None


class BattleActionRequest(BaseModel):
    battle_id: str
    action: str  # "fight", "run"
    move_index: Optional[int] = None  # required when action="fight"
    game_id: Optional[str] = None  # for tracking stats


class TurnEvent(BaseModel):
    attacker: str  # "player" or "enemy"
    move: str
    damage: int
    effectiveness: str  # "normal", "super_effective", "not_very_effective", "immune"
    critical: bool
    target_hp_remaining: int
    target_fainted: bool


class StatusEvent(BaseModel):
    pokemon: str  # "player" or "enemy"
    event_type: str  # "status_applied", "status_cured", "status_damage", "status_prevented", "stat_change", "confused_hit_self", "ability_activated"
    status: Optional[str] = None
    damage: Optional[int] = None
    stat: Optional[str] = None
    stages: Optional[int] = None
    message: str = ""
    ability_id: Optional[str] = None
    ability_name: Optional[str] = None


class TurnResult(BaseModel):
    events: list[TurnEvent]
    status_events: list[StatusEvent] = []
    weather_events: list[WeatherEvent] = []
    battle_over: bool
    winner: Optional[str] = None
    ran_away: bool = False
    run_failed: bool = False


class BattleStateResponse(BaseModel):
    battle: BattleState
    turn_result: Optional[TurnResult] = None
