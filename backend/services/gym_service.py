from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models.battle import BattlePokemon
from ..models.gym import Badge, Gym, GymChallengeResult, Trainer, TrainerBattleResult
from ..models.pokemon import Move, Stats
from .battle_service import start_battle
from .encounter_service import get_move_data, get_species
from .game_service import get_game

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# In-memory stores
_trainers: dict[str, Trainer] = {}
_gyms: dict[str, Gym] = {}
_defeated_trainers: dict[str, set[str]] = {}  # game_id -> set of trainer_ids
_earned_badges: dict[str, set[str]] = {}  # game_id -> set of badge_ids

ALL_BADGES = [
    Badge(badge_id="boulder", badge_name="Boulder Badge", gym_name="Pewter City Gym"),
    Badge(badge_id="cascade", badge_name="Cascade Badge", gym_name="Cerulean City Gym"),
    Badge(badge_id="thunder", badge_name="Thunder Badge", gym_name="Vermilion City Gym"),
    Badge(badge_id="rainbow", badge_name="Rainbow Badge", gym_name="Celadon City Gym"),
    Badge(badge_id="soul", badge_name="Soul Badge", gym_name="Fuchsia City Gym"),
    Badge(badge_id="marsh", badge_name="Marsh Badge", gym_name="Saffron City Gym"),
    Badge(badge_id="volcano", badge_name="Volcano Badge", gym_name="Cinnabar Island Gym"),
    Badge(badge_id="earth", badge_name="Earth Badge", gym_name="Viridian City Gym"),
]


def _load_trainers() -> None:
    global _trainers
    with open(DATA_DIR / "trainers.json") as f:
        raw = json.load(f)
    _trainers = {t["id"]: Trainer(**t) for t in raw}


def _load_gyms() -> None:
    global _gyms
    with open(DATA_DIR / "gyms.json") as f:
        raw = json.load(f)
    _gyms = {g["id"]: Gym(**g) for g in raw}


def _ensure_loaded() -> None:
    if not _trainers:
        _load_trainers()
    if not _gyms:
        _load_gyms()


def _build_battle_pokemon(species_id: int, name: str, level: int, move_names: list[str]) -> dict:
    """Build a BattlePokemon dict from trainer pokemon data."""
    sp = get_species(species_id)

    # Calculate stats from base stats and level
    if sp:
        base = sp.stats
        hp = int(((base.hp * 2) * level / 100) + level + 10)
        attack = int(((base.attack * 2) * level / 100) + 5)
        defense = int(((base.defense * 2) * level / 100) + 5)
        sp_attack = int(((base.sp_attack * 2) * level / 100) + 5)
        sp_defense = int(((base.sp_defense * 2) * level / 100) + 5)
        speed = int(((base.speed * 2) * level / 100) + 5)
        types = sp.types
        sprite = sp.sprite
    else:
        hp = level * 3 + 10
        attack = defense = sp_attack = sp_defense = speed = level * 2 + 5
        types = ["normal"]
        sprite = "unknown"

    # Resolve moves
    moves = []
    for mname in move_names:
        md = get_move_data(mname)
        if md:
            moves.append(Move(**md))
        else:
            moves.append(Move(name=mname, type="normal", power=40, accuracy=100, pp=35))

    return {
        "species_id": species_id,
        "name": name,
        "types": types,
        "level": level,
        "stats": {"hp": hp, "attack": attack, "defense": defense,
                  "sp_attack": sp_attack, "sp_defense": sp_defense, "speed": speed},
        "current_hp": hp,
        "max_hp": hp,
        "moves": [m.model_dump() for m in moves],
        "sprite": sprite,
    }


# --- Trainer functions ---

def get_trainer(trainer_id: str) -> Optional[Trainer]:
    _ensure_loaded()
    return _trainers.get(trainer_id)


def get_trainers_on_map(map_id: str, game_id: Optional[str] = None) -> list[dict]:
    """Return trainers on a map, with defeated status for the given game."""
    _ensure_loaded()
    from .map_service import get_map
    game_map = get_map(map_id)
    if game_map is None:
        return []

    defeated = _defeated_trainers.get(game_id, set()) if game_id else set()
    result = []
    for mt in game_map.trainers:
        trainer = _trainers.get(mt.trainer_id)
        if trainer is None:
            continue
        result.append({
            "id": trainer.id,
            "name": trainer.name,
            "trainer_class": trainer.trainer_class,
            "sprite_id": trainer.sprite_id,
            "x": mt.x,
            "y": mt.y,
            "facing": mt.facing,
            "sight_range": mt.sight_range,
            "defeated": trainer.id in defeated,
        })
    return result


def start_trainer_battle(game_id: str, trainer_id: str) -> Optional[TrainerBattleResult]:
    """Start a battle with a trainer."""
    _ensure_loaded()
    game = get_game(game_id)
    if game is None:
        return None

    trainer = _trainers.get(trainer_id)
    if trainer is None:
        return None

    # Check if already defeated
    defeated = _defeated_trainers.get(game_id, set())
    if trainer_id in defeated:
        return None

    # Build trainer's first pokemon for battle
    tp = trainer.pokemon_team[0]
    enemy_data = _build_battle_pokemon(tp.species_id, tp.name, tp.level, tp.moves)

    # Get player's lead pokemon
    team = game["player"]["team"]
    if not team:
        return None
    lead = team[0]
    player_data = {
        "species_id": lead["id"],
        "name": lead["name"],
        "types": lead["types"],
        "level": lead["level"],
        "stats": lead["stats"],
        "current_hp": lead.get("current_hp", lead["stats"]["hp"]),
        "max_hp": lead.get("max_hp", lead["stats"]["hp"]),
        "moves": lead["moves"],
        "sprite": lead["sprite"],
    }

    battle = start_battle(player_data, enemy_data, battle_type="trainer")

    return TrainerBattleResult(
        battle_id=battle.id,
        trainer_id=trainer_id,
        reward_money=trainer.reward_money,
        dialogue_after=trainer.dialogue_after,
    )


def defeat_trainer(game_id: str, trainer_id: str) -> Optional[dict]:
    """Mark a trainer as defeated and award money."""
    _ensure_loaded()
    game = get_game(game_id)
    if game is None:
        return None

    trainer = _trainers.get(trainer_id)
    if trainer is None:
        return None

    if game_id not in _defeated_trainers:
        _defeated_trainers[game_id] = set()
    _defeated_trainers[game_id].add(trainer_id)

    # Award money
    money = game["player"].get("money", 0)
    money += trainer.reward_money
    game["player"]["money"] = money

    return {
        "trainer_id": trainer_id,
        "reward_money": trainer.reward_money,
        "total_money": money,
        "dialogue_after": trainer.dialogue_after,
    }


# --- Gym functions ---

def get_all_gyms() -> list[dict]:
    _ensure_loaded()
    return [
        {
            "id": g.id,
            "name": g.name,
            "city": g.city,
            "type_specialty": g.type_specialty,
            "badge_name": g.badge_name,
            "leader_name": g.leader.name,
        }
        for g in _gyms.values()
    ]


def get_gym(gym_id: str) -> Optional[Gym]:
    _ensure_loaded()
    return _gyms.get(gym_id)


def challenge_gym(game_id: str, gym_id: str) -> Optional[GymChallengeResult]:
    """Start a gym leader battle."""
    _ensure_loaded()
    game = get_game(game_id)
    if game is None:
        return None

    gym = _gyms.get(gym_id)
    if gym is None:
        return None

    # Check if already earned badge
    badges = _earned_badges.get(game_id, set())
    if gym.badge_id in badges:
        return None

    # Build leader's first pokemon
    leader = gym.leader
    tp = leader.pokemon_team[0]
    enemy_data = _build_battle_pokemon(tp.species_id, tp.name, tp.level, tp.moves)

    # Get player's lead pokemon
    team = game["player"]["team"]
    if not team:
        return None
    lead = team[0]
    player_data = {
        "species_id": lead["id"],
        "name": lead["name"],
        "types": lead["types"],
        "level": lead["level"],
        "stats": lead["stats"],
        "current_hp": lead.get("current_hp", lead["stats"]["hp"]),
        "max_hp": lead.get("max_hp", lead["stats"]["hp"]),
        "moves": lead["moves"],
        "sprite": lead["sprite"],
    }

    battle = start_battle(player_data, enemy_data, battle_type="trainer")

    return GymChallengeResult(
        battle_id=battle.id,
        gym_id=gym_id,
        leader_name=leader.name,
        badge_id=gym.badge_id,
        badge_name=gym.badge_name,
        reward_money=leader.reward_money,
    )


def award_badge(game_id: str, gym_id: str) -> Optional[list[Badge]]:
    """Award badge after defeating gym leader."""
    _ensure_loaded()
    game = get_game(game_id)
    if game is None:
        return None

    gym = _gyms.get(gym_id)
    if gym is None:
        return None

    if game_id not in _earned_badges:
        _earned_badges[game_id] = set()
    _earned_badges[game_id].add(gym.badge_id)

    # Award money
    money = game["player"].get("money", 0)
    money += gym.leader.reward_money
    game["player"]["money"] = money

    # Update badge count
    game["badges"] = len(_earned_badges[game_id])

    return get_badges(game_id)


def get_badges(game_id: str) -> list[Badge]:
    """Return all badges with earned status for this game."""
    earned = _earned_badges.get(game_id, set())
    return [
        Badge(
            badge_id=b.badge_id,
            badge_name=b.badge_name,
            gym_name=b.gym_name,
            earned=b.badge_id in earned,
        )
        for b in ALL_BADGES
    ]
