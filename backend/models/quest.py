"""Quest, story flag, and rival data models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# --- Quest models ---

class QuestReward(BaseModel):
    exp: int = 0
    money: int = 0
    items: list[dict] = []  # [{"item_id": int, "quantity": int}]
    unlock_flags: list[str] = []


class QuestObjective(BaseModel):
    id: str
    description: str
    type: str  # defeat_trainer, visit_location, collect_item, deliver_item, catch_pokemon, defeat_gym
    target: str  # target identifier (trainer_id, map_id, item_id, species_id, gym_id)
    current_progress: int = 0
    required_progress: int = 1


class Quest(BaseModel):
    id: str
    name: str
    description: str
    type: str = "main"  # main, side
    objectives: list[QuestObjective]
    rewards: QuestReward = QuestReward()
    prerequisite_quests: list[str] = []
    status: str = "locked"  # locked, active, completed


class QuestCheckRequest(BaseModel):
    game_id: str
    event_type: str  # defeat_trainer, visit_location, collect_item, catch_pokemon, defeat_gym
    event_data: dict  # {"trainer_id": "brock"}, {"map_id": "viridian_city"}, etc.


class QuestCheckResult(BaseModel):
    updated_quests: list[Quest] = []
    completed_quests: list[Quest] = []
    newly_active_quests: list[Quest] = []


class QuestCompleteResult(BaseModel):
    quest: Quest
    rewards_given: QuestReward
    newly_unlocked_quests: list[str] = []


# --- Story flag models ---

class StoryFlags(BaseModel):
    flags: dict[str, bool] = {}


# --- Rival models ---

class RivalPokemon(BaseModel):
    species_id: int
    name: str
    level: int
    moves: list[str]


class RivalData(BaseModel):
    name: str = "Blue"
    starter_species_id: int = 4  # default counter to Bulbasaur
    current_team: list[RivalPokemon] = []
    encounter_stage: int = 0  # 0=not met, 1=lab, 2=route2, 3=pre-elite


class RivalBattleResult(BaseModel):
    battle_id: str
    rival_name: str
    rival_team_preview: list[str]  # Pokemon names
    reward_money: int
