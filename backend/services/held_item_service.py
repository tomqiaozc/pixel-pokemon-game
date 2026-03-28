"""Held item service — definitions, battle modifiers, evolution stones."""
from __future__ import annotations

import math
from typing import Optional

from .encounter_service import _calc_stat, _generate_moves_for_level, get_species


# ============================================================
# Held Item Definitions
# ============================================================

HELD_ITEMS: dict[str, dict] = {
    # --- Type-boosting items (1.2x for matching type) ---
    "charcoal": {
        "id": "charcoal", "name": "Charcoal",
        "description": "Boosts Fire-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "fire", "modifier": 1.2,
    },
    "mystic_water": {
        "id": "mystic_water", "name": "Mystic Water",
        "description": "Boosts Water-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "water", "modifier": 1.2,
    },
    "miracle_seed": {
        "id": "miracle_seed", "name": "Miracle Seed",
        "description": "Boosts Grass-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "grass", "modifier": 1.2,
    },
    "magnet": {
        "id": "magnet", "name": "Magnet",
        "description": "Boosts Electric-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "electric", "modifier": 1.2,
    },
    "never_melt_ice": {
        "id": "never_melt_ice", "name": "Never-Melt Ice",
        "description": "Boosts Ice-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "ice", "modifier": 1.2,
    },
    "black_belt": {
        "id": "black_belt", "name": "Black Belt",
        "description": "Boosts Fighting-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "fighting", "modifier": 1.2,
    },
    "poison_barb": {
        "id": "poison_barb", "name": "Poison Barb",
        "description": "Boosts Poison-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "poison", "modifier": 1.2,
    },
    "soft_sand": {
        "id": "soft_sand", "name": "Soft Sand",
        "description": "Boosts Ground-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "ground", "modifier": 1.2,
    },
    "sharp_beak": {
        "id": "sharp_beak", "name": "Sharp Beak",
        "description": "Boosts Flying-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "flying", "modifier": 1.2,
    },
    "twisted_spoon": {
        "id": "twisted_spoon", "name": "Twisted Spoon",
        "description": "Boosts Psychic-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "psychic", "modifier": 1.2,
    },
    "silver_powder": {
        "id": "silver_powder", "name": "Silver Powder",
        "description": "Boosts Bug-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "bug", "modifier": 1.2,
    },
    "hard_stone": {
        "id": "hard_stone", "name": "Hard Stone",
        "description": "Boosts Rock-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "rock", "modifier": 1.2,
    },
    "spell_tag": {
        "id": "spell_tag", "name": "Spell Tag",
        "description": "Boosts Ghost-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "ghost", "modifier": 1.2,
    },
    "dragon_fang": {
        "id": "dragon_fang", "name": "Dragon Fang",
        "description": "Boosts Dragon-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "dragon", "modifier": 1.2,
    },
    "black_glasses": {
        "id": "black_glasses", "name": "Black Glasses",
        "description": "Boosts Dark-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "dark", "modifier": 1.2,
    },
    "metal_coat": {
        "id": "metal_coat", "name": "Metal Coat",
        "description": "Boosts Steel-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "steel", "modifier": 1.2,
    },
    "silk_scarf": {
        "id": "silk_scarf", "name": "Silk Scarf",
        "description": "Boosts Normal-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "normal", "modifier": 1.2,
    },
    "pixie_plate": {
        "id": "pixie_plate", "name": "Pixie Plate",
        "description": "Boosts Fairy-type moves by 20%.",
        "effect_type": "type_boost", "boost_type": "fairy", "modifier": 1.2,
    },

    # --- Stat-boosting items ---
    "choice_band": {
        "id": "choice_band", "name": "Choice Band",
        "description": "Boosts Attack by 50% but locks to one move.",
        "effect_type": "stat_boost", "boost_stat": "attack", "category": "physical",
        "modifier": 1.5,
    },
    "choice_specs": {
        "id": "choice_specs", "name": "Choice Specs",
        "description": "Boosts Sp. Attack by 50% but locks to one move.",
        "effect_type": "stat_boost", "boost_stat": "sp_attack", "category": "special",
        "modifier": 1.5,
    },

    # --- End-of-turn heal ---
    "leftovers": {
        "id": "leftovers", "name": "Leftovers",
        "description": "Restores 1/16 max HP at end of each turn.",
        "effect_type": "end_of_turn_heal", "modifier": 16,
    },

    # --- Damage boost with recoil ---
    "life_orb": {
        "id": "life_orb", "name": "Life Orb",
        "description": "Boosts move damage by 30% but costs 10% max HP per attack.",
        "effect_type": "damage_boost_recoil", "modifier": 1.3, "recoil_percent": 10,
    },

    # --- Survive OHKO ---
    "focus_sash": {
        "id": "focus_sash", "name": "Focus Sash",
        "description": "Survives a one-hit KO with 1 HP when at full HP. Single use.",
        "effect_type": "survive_ohko",
    },

    # --- EXP boost ---
    "lucky_egg": {
        "id": "lucky_egg", "name": "Lucky Egg",
        "description": "Holder gains 50% more EXP from battles.",
        "effect_type": "exp_boost", "modifier": 1.5,
    },

    # --- EV boost (halves speed) ---
    "macho_brace": {
        "id": "macho_brace", "name": "Macho Brace",
        "description": "Doubles EVs gained but halves Speed in battle.",
        "effect_type": "ev_boost", "modifier": 2.0,
    },

    # --- Weather rocks (already used in weather_service) ---
    "damp_rock": {
        "id": "damp_rock", "name": "Damp Rock",
        "description": "Extends Rain to 8 turns.",
        "effect_type": "weather_extend", "weather": "rain",
    },
    "heat_rock": {
        "id": "heat_rock", "name": "Heat Rock",
        "description": "Extends Sun to 8 turns.",
        "effect_type": "weather_extend", "weather": "sun",
    },
    "smooth_rock": {
        "id": "smooth_rock", "name": "Smooth Rock",
        "description": "Extends Sandstorm to 8 turns.",
        "effect_type": "weather_extend", "weather": "sandstorm",
    },
    "icy_rock": {
        "id": "icy_rock", "name": "Icy Rock",
        "description": "Extends Hail to 8 turns.",
        "effect_type": "weather_extend", "weather": "hail",
    },
}


# ============================================================
# Evolution Stone Definitions
# ============================================================

EVOLUTION_STONES: dict[str, dict] = {
    "fire_stone": {"id": "fire_stone", "name": "Fire Stone", "description": "Evolves certain Pokemon when used."},
    "water_stone": {"id": "water_stone", "name": "Water Stone", "description": "Evolves certain Pokemon when used."},
    "thunder_stone": {"id": "thunder_stone", "name": "Thunder Stone", "description": "Evolves certain Pokemon when used."},
    "moon_stone": {"id": "moon_stone", "name": "Moon Stone", "description": "Evolves certain Pokemon when used."},
    "leaf_stone": {"id": "leaf_stone", "name": "Leaf Stone", "description": "Evolves certain Pokemon when used."},
}

# Stone evolution compatibility: species_id -> {stone_id -> target_species_id}
STONE_EVOLUTIONS: dict[int, dict[str, int]] = {
    133: {  # Eevee
        "fire_stone": 136,    # Flareon
        "water_stone": 134,   # Vaporeon
        "thunder_stone": 135, # Jolteon
    },
    15: {  # Pikachu
        "thunder_stone": 16,  # Raichu
    },
    21: {  # Staryu
        "water_stone": 22,    # Starmie
    },
}


# ============================================================
# Public API functions
# ============================================================

def get_all_held_items() -> list[dict]:
    """Return all held item definitions."""
    return list(HELD_ITEMS.values())


def get_held_item(item_id: str) -> Optional[dict]:
    """Return a single held item definition."""
    return HELD_ITEMS.get(item_id)


def get_evolution_stones() -> dict[str, dict]:
    """Return all evolution stone definitions."""
    return EVOLUTION_STONES


def get_held_item_damage_modifier(
    held_item: Optional[str],
    move_type: str,
    move_category: str,
) -> float:
    """Get damage multiplier from held item for a given move type and category.

    Returns 1.0 if no modifier applies.
    """
    if held_item is None:
        return 1.0

    item = HELD_ITEMS.get(held_item)
    if item is None:
        return 1.0

    effect = item["effect_type"]

    if effect == "type_boost":
        if item["boost_type"] == move_type:
            return item["modifier"]
        return 1.0

    if effect == "stat_boost":
        if item["category"] == move_category:
            return item["modifier"]
        return 1.0

    if effect == "damage_boost_recoil":
        return item["modifier"]

    return 1.0


def process_held_item_end_of_turn(pokemon: dict, role: str) -> list[dict]:
    """Process end-of-turn held item effects (Leftovers heal, etc.)."""
    held = pokemon.get("held_item")
    if held is None:
        return []

    item = HELD_ITEMS.get(held)
    if item is None:
        return []

    events = []

    if item["effect_type"] == "end_of_turn_heal":
        current_hp = pokemon.get("current_hp", 0)
        max_hp = pokemon.get("max_hp", 1)
        if current_hp < max_hp:
            heal = max(1, math.floor(max_hp / item["modifier"]))
            new_hp = min(max_hp, current_hp + heal)
            actual_heal = new_hp - current_hp
            pokemon["current_hp"] = new_hp
            events.append({
                "type": "heal",
                "pokemon": role,
                "amount": actual_heal,
                "message": f"{pokemon.get('name', 'Pokemon')}'s Leftovers restored {actual_heal} HP!",
            })

    return events


def process_held_item_after_attack(
    pokemon: dict, role: str, did_damage: bool
) -> list[dict]:
    """Process held item effects after an attack (Life Orb recoil, etc.)."""
    held = pokemon.get("held_item")
    if held is None:
        return []

    item = HELD_ITEMS.get(held)
    if item is None:
        return []

    events = []

    if item["effect_type"] == "damage_boost_recoil" and did_damage:
        max_hp = pokemon.get("max_hp", 1)
        recoil = max(1, math.floor(max_hp * item["recoil_percent"] / 100))
        pokemon["current_hp"] = max(0, pokemon.get("current_hp", 0) - recoil)
        events.append({
            "type": "recoil",
            "pokemon": role,
            "damage": recoil,
            "message": f"{pokemon.get('name', 'Pokemon')} lost {recoil} HP from Life Orb recoil!",
        })

    return events


def apply_focus_sash(pokemon: dict, incoming_damage: int) -> dict:
    """Check if Focus Sash activates. Returns dict with survival info."""
    held = pokemon.get("held_item")
    current_hp = pokemon.get("current_hp", 0)
    max_hp = pokemon.get("max_hp", 1)

    if held != "focus_sash" or current_hp != max_hp or incoming_damage < current_hp:
        return {"survived": False}

    # Activate: survive at 1 HP, consume sash
    pokemon["held_item"] = None
    return {
        "survived": True,
        "new_hp": 1,
        "consumed": True,
        "message": f"{pokemon.get('name', 'Pokemon')} hung on using its Focus Sash!",
    }


def get_exp_multiplier(held_item: Optional[str]) -> float:
    """Get EXP multiplier from held item (Lucky Egg = 1.5x)."""
    if held_item is None:
        return 1.0
    item = HELD_ITEMS.get(held_item)
    if item is None:
        return 1.0
    if item["effect_type"] == "exp_boost":
        return item["modifier"]
    return 1.0


# ============================================================
# Stone Evolution Logic
# ============================================================

def check_stone_evolution(species_id: int, stone_id: str) -> Optional[dict]:
    """Check if a stone can evolve a species. Returns target info or None."""
    if stone_id not in EVOLUTION_STONES:
        return None

    evos = STONE_EVOLUTIONS.get(species_id)
    if evos is None or stone_id not in evos:
        return None

    target_id = evos[stone_id]
    target_species = get_species(target_id)
    if target_species is None:
        return None

    return {
        "to_id": target_id,
        "to_name": target_species.name,
        "to_types": target_species.types,
        "to_sprite": target_species.sprite,
    }


def execute_stone_evolution(pokemon: dict, stone_id: str) -> Optional[dict]:
    """Execute stone evolution on a Pokemon dict. Returns result or None."""
    species_id = pokemon.get("id")
    if species_id is None:
        return None

    check = check_stone_evolution(species_id, stone_id)
    if check is None:
        return None

    target_species = get_species(check["to_id"])
    if target_species is None:
        return None

    level = pokemon.get("level", 1)
    iv = 15  # mid-range approximation (matches evolution_service)

    new_hp = _calc_stat(target_species.stats.hp, level, iv, is_hp=True)
    new_stats = {
        "hp": new_hp,
        "attack": _calc_stat(target_species.stats.attack, level, iv),
        "defense": _calc_stat(target_species.stats.defense, level, iv),
        "sp_attack": _calc_stat(target_species.stats.sp_attack, level, iv),
        "sp_defense": _calc_stat(target_species.stats.sp_defense, level, iv),
        "speed": _calc_stat(target_species.stats.speed, level, iv),
    }

    new_moves = _generate_moves_for_level(target_species, level)

    old_name = pokemon.get("name", "Unknown")
    old_id = species_id

    # Update pokemon in-place
    pokemon["id"] = check["to_id"]
    pokemon["name"] = check["to_name"]
    pokemon["types"] = check["to_types"]
    pokemon["stats"] = new_stats
    pokemon["max_hp"] = new_hp
    pokemon["current_hp"] = new_hp
    pokemon["sprite"] = check["to_sprite"]
    pokemon["moves"] = [m.model_dump() for m in new_moves]

    return {
        "success": True,
        "old_species_id": old_id,
        "old_name": old_name,
        "new_species_id": check["to_id"],
        "new_name": check["to_name"],
        "new_stats": new_stats,
        "new_moves": [m.model_dump() for m in new_moves],
    }


# ============================================================
# Equip/Unequip
# ============================================================

def equip_held_item(game_id: str, pokemon_index: int, item_id: str) -> Optional[dict]:
    """Equip a held item on a team Pokemon. Returns result dict or None if game not found."""
    from .game_service import get_game

    if item_id not in HELD_ITEMS:
        raise ValueError(f"Unknown held item: {item_id}")

    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise ValueError("Invalid Pokemon index")

    pokemon = team[pokemon_index]
    previous = pokemon.get("held_item")
    pokemon["held_item"] = item_id

    return {
        "success": True,
        "held_item": item_id,
        "previous_item": previous,
        "pokemon_name": pokemon.get("name", "Unknown"),
    }


def remove_held_item(game_id: str, pokemon_index: int) -> Optional[dict]:
    """Remove held item from a team Pokemon. Returns result dict or None if game not found."""
    from .game_service import get_game

    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise ValueError("Invalid Pokemon index")

    pokemon = team[pokemon_index]
    removed = pokemon.get("held_item")
    pokemon["held_item"] = None

    return {
        "success": True,
        "removed_item": removed,
        "pokemon_name": pokemon.get("name", "Unknown"),
    }
