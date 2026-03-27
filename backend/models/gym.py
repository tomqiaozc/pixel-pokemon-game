from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .pokemon import Move, Stats


class TrainerPokemon(BaseModel):
    species_id: int
    name: str
    level: int
    moves: list[str]  # move names, resolved at battle time


class Trainer(BaseModel):
    id: str
    name: str
    trainer_class: str  # Youngster, Bug Catcher, Lass, etc.
    sprite_id: str
    pokemon_team: list[TrainerPokemon]
    reward_money: int
    sight_range: int = 3
    dialogue_before: str = ""
    dialogue_after: str = ""
    defeated: bool = False


class GymLeader(BaseModel):
    id: str
    name: str
    sprite_id: str
    pokemon_team: list[TrainerPokemon]
    reward_money: int
    badge_id: str
    dialogue_before: str = ""
    dialogue_after: str = ""
    ai_difficulty: str = "hard"


class Gym(BaseModel):
    id: str
    name: str
    city: str
    type_specialty: str
    badge_name: str
    badge_id: str
    leader: GymLeader
    gym_trainers: list[str] = []  # trainer IDs
    map_id: str


class Badge(BaseModel):
    badge_id: str
    badge_name: str
    gym_name: str
    earned: bool = False


class TrainerBattleResult(BaseModel):
    battle_id: str
    trainer_id: str
    reward_money: int
    dialogue_after: str


class GymChallengeResult(BaseModel):
    battle_id: str
    gym_id: str
    leader_name: str
    badge_id: str
    badge_name: str
    reward_money: int
