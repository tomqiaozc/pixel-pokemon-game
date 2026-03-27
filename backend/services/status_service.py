"""Status conditions, stat stages, and volatile status processing."""
from __future__ import annotations

import random

from ..models.battle import BattlePokemon, StatusEvent


# Type immunities to status conditions
_STATUS_IMMUNITIES: dict[str, list[str]] = {
    "brn": ["fire"],
    "par": ["electric"],
    "frz": ["ice"],
    "psn": ["poison", "steel"],
    "tox": ["poison", "steel"],
}

# Stat stage multipliers: stage -> numerator/denominator
def _stage_multiplier(stage: int) -> float:
    stage = max(-6, min(6, stage))
    if stage >= 0:
        return (2 + stage) / 2.0
    else:
        return 2.0 / (2 - stage)


def get_effective_stat(pokemon: BattlePokemon, stat_name: str) -> int:
    """Get a stat value with stage modifiers applied."""
    base = getattr(pokemon.stats, stat_name)
    stage = getattr(pokemon.stat_stages, stat_name, 0)
    modified = int(base * _stage_multiplier(stage))

    # Burn halves attack
    if stat_name == "attack" and pokemon.status == "brn":
        modified = modified // 2

    # Paralysis quarters speed
    if stat_name == "speed" and pokemon.status == "par":
        modified = modified // 4

    return max(1, modified)


def can_apply_status(pokemon: BattlePokemon, status: str) -> bool:
    """Check if a status can be applied (considering type immunities and existing status)."""
    if pokemon.status is not None:
        return False  # already has a primary status
    immune_types = _STATUS_IMMUNITIES.get(status, [])
    for t in pokemon.types:
        if t in immune_types:
            return False
    return True


def apply_status(pokemon: BattlePokemon, status: str, role: str) -> StatusEvent | None:
    """Try to apply a primary status condition. Returns event or None."""
    if not can_apply_status(pokemon, status):
        # Check if immune
        immune_types = _STATUS_IMMUNITIES.get(status, [])
        for t in pokemon.types:
            if t in immune_types:
                return StatusEvent(
                    pokemon=role,
                    event_type="status_prevented",
                    status=status,
                    message=f"{pokemon.name} is immune to {_status_name(status)}!",
                )
        return None  # already has status, silently fail

    pokemon.status = status
    if status == "slp":
        pokemon.status_turns = random.randint(1, 3)
    elif status == "tox":
        pokemon.status_turns = 1
    else:
        pokemon.status_turns = 0

    return StatusEvent(
        pokemon=role,
        event_type="status_applied",
        status=status,
        message=f"{pokemon.name} was {_status_verb(status)}!",
    )


def process_status_before_move(pokemon: BattlePokemon, role: str) -> tuple[bool, list[StatusEvent]]:
    """Process status checks before a Pokemon's move. Returns (can_move, events)."""
    events = []

    # Flinch check
    if pokemon.flinched:
        pokemon.flinched = False
        events.append(StatusEvent(
            pokemon=role,
            event_type="status_prevented",
            status="flinch",
            message=f"{pokemon.name} flinched and couldn't move!",
        ))
        return False, events

    # Freeze check (20% thaw)
    if pokemon.status == "frz":
        if random.random() < 0.20:
            pokemon.status = None
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_cured",
                status="frz",
                message=f"{pokemon.name} thawed out!",
            ))
        else:
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_prevented",
                status="frz",
                message=f"{pokemon.name} is frozen solid!",
            ))
            return False, events

    # Sleep check
    if pokemon.status == "slp":
        pokemon.status_turns -= 1
        if pokemon.status_turns <= 0:
            pokemon.status = None
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_cured",
                status="slp",
                message=f"{pokemon.name} woke up!",
            ))
        else:
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_prevented",
                status="slp",
                message=f"{pokemon.name} is fast asleep!",
            ))
            return False, events

    # Paralysis check (25% full paralysis)
    if pokemon.status == "par":
        if random.random() < 0.25:
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_prevented",
                status="par",
                message=f"{pokemon.name} is fully paralyzed!",
            ))
            return False, events

    # Confusion check
    if pokemon.confused:
        pokemon.confused_turns -= 1
        if pokemon.confused_turns <= 0:
            pokemon.confused = False
            events.append(StatusEvent(
                pokemon=role,
                event_type="status_cured",
                status="confusion",
                message=f"{pokemon.name} snapped out of confusion!",
            ))
        elif random.random() < 0.5:
            # Hit self: 40 power typeless physical attack
            dmg = max(1, int(((2 * pokemon.level / 5 + 2) * 40 * pokemon.stats.attack / pokemon.stats.defense) / 50 + 2))
            pokemon.current_hp = max(0, pokemon.current_hp - dmg)
            events.append(StatusEvent(
                pokemon=role,
                event_type="confused_hit_self",
                damage=dmg,
                message=f"{pokemon.name} hurt itself in confusion!",
            ))
            return False, events

    return True, events


def process_status_end_of_turn(pokemon: BattlePokemon, role: str) -> list[StatusEvent]:
    """Process end-of-turn status damage (poison, burn, toxic)."""
    events = []

    if pokemon.current_hp <= 0:
        return events

    if pokemon.status == "psn":
        dmg = max(1, pokemon.max_hp // 8)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        events.append(StatusEvent(
            pokemon=role,
            event_type="status_damage",
            status="psn",
            damage=dmg,
            message=f"{pokemon.name} was hurt by poison!",
        ))

    elif pokemon.status == "tox":
        dmg = max(1, pokemon.max_hp * pokemon.status_turns // 16)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        pokemon.status_turns += 1
        events.append(StatusEvent(
            pokemon=role,
            event_type="status_damage",
            status="tox",
            damage=dmg,
            message=f"{pokemon.name} was hurt by poison!",
        ))

    elif pokemon.status == "brn":
        dmg = max(1, pokemon.max_hp // 8)
        pokemon.current_hp = max(0, pokemon.current_hp - dmg)
        events.append(StatusEvent(
            pokemon=role,
            event_type="status_damage",
            status="brn",
            damage=dmg,
            message=f"{pokemon.name} was hurt by its burn!",
        ))

    return events


def apply_stat_change(pokemon: BattlePokemon, stat: str, stages: int, role: str) -> StatusEvent | None:
    """Apply stat stage change. Returns event or None if already at max/min."""
    current = getattr(pokemon.stat_stages, stat, 0)
    new_val = max(-6, min(6, current + stages))
    if new_val == current:
        direction = "higher" if stages > 0 else "lower"
        return StatusEvent(
            pokemon=role,
            event_type="stat_change",
            stat=stat,
            stages=0,
            message=f"{pokemon.name}'s {stat} can't go any {direction}!",
        )

    setattr(pokemon.stat_stages, stat, new_val)
    if stages >= 2:
        msg = f"{pokemon.name}'s {stat} rose sharply!"
    elif stages == 1:
        msg = f"{pokemon.name}'s {stat} rose!"
    elif stages == -1:
        msg = f"{pokemon.name}'s {stat} fell!"
    elif stages <= -2:
        msg = f"{pokemon.name}'s {stat} harshly fell!"
    else:
        msg = f"{pokemon.name}'s {stat} changed by {stages}!"

    return StatusEvent(
        pokemon=role,
        event_type="stat_change",
        stat=stat,
        stages=stages,
        message=msg,
    )


# Move effect definitions
_MOVE_STATUS_EFFECTS: dict[str, dict] = {
    # Primary status moves
    "Thunder Wave": {"status": "par", "chance": 100, "target": "enemy"},
    "Sleep Powder": {"status": "slp", "chance": 75, "target": "enemy"},
    # Secondary effects (applied after damage)
    "Thunderbolt": {"status": "par", "chance": 10, "target": "enemy"},
    "Flamethrower": {"status": "brn", "chance": 10, "target": "enemy"},
    "Ember": {"status": "brn", "chance": 10, "target": "enemy"},
    "Fire Blast": {"status": "brn", "chance": 10, "target": "enemy"},
    "Ice Beam": {"status": "frz", "chance": 10, "target": "enemy"},
    "Thunder": {"status": "par", "chance": 30, "target": "enemy"},
    "Poison Sting": {"status": "psn", "chance": 30, "target": "enemy"},
}

_MOVE_STAT_EFFECTS: dict[str, dict] = {
    "Growl": {"stat": "attack", "stages": -1, "target": "enemy"},
    "Tail Whip": {"stat": "defense", "stages": -1, "target": "enemy"},
    "Sand Attack": {"stat": "accuracy", "stages": -1, "target": "enemy"},
    "Screech": {"stat": "defense", "stages": -2, "target": "enemy"},
    "Defense Curl": {"stat": "defense", "stages": 1, "target": "self"},
    "Harden": {"stat": "defense", "stages": 1, "target": "self"},
    "Agility": {"stat": "speed", "stages": 2, "target": "self"},
}


def process_move_effects(
    move_name: str,
    attacker: BattlePokemon,
    defender: BattlePokemon,
    attacker_role: str,
    defender_role: str,
    did_damage: bool,
) -> list[StatusEvent]:
    """Process status and stat effects from a move."""
    events = []

    # Stat effects (always apply for status moves, on hit for others)
    if move_name in _MOVE_STAT_EFFECTS:
        eff = _MOVE_STAT_EFFECTS[move_name]
        if eff["target"] == "enemy":
            evt = apply_stat_change(defender, eff["stat"], eff["stages"], defender_role)
        else:
            evt = apply_stat_change(attacker, eff["stat"], eff["stages"], attacker_role)
        if evt:
            events.append(evt)

    # Status effects
    if move_name in _MOVE_STATUS_EFFECTS:
        eff = _MOVE_STATUS_EFFECTS[move_name]
        if random.randint(1, 100) <= eff["chance"]:
            target = defender if eff["target"] == "enemy" else attacker
            target_role = defender_role if eff["target"] == "enemy" else attacker_role
            evt = apply_status(target, eff["status"], target_role)
            if evt:
                events.append(evt)

    # Fire move thaws frozen target
    if defender.status == "frz" and did_damage:
        from ..services.encounter_service import get_move_data
        md = get_move_data(move_name)
        if md and md.get("type") == "fire":
            defender.status = None
            events.append(StatusEvent(
                pokemon=defender_role,
                event_type="status_cured",
                status="frz",
                message=f"{defender.name} was thawed out by the attack!",
            ))

    return events


def _status_name(status: str) -> str:
    return {
        "psn": "poison",
        "tox": "bad poison",
        "brn": "burn",
        "par": "paralysis",
        "slp": "sleep",
        "frz": "freeze",
    }.get(status, status)


def _status_verb(status: str) -> str:
    return {
        "psn": "poisoned",
        "tox": "badly poisoned",
        "brn": "burned",
        "par": "paralyzed",
        "slp": "put to sleep",
        "frz": "frozen",
    }.get(status, f"afflicted with {status}")
