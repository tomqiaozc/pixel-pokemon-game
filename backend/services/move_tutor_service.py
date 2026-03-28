"""Move Tutor & TM/HM System service.

Provides:
- Move Tutor NPC data (one per major town)
- TM/HM item definitions with compatibility maps
- Teaching moves via tutor, TM, or Move Reminder
- HM move deletion prevention
- Cost deduction and inventory management
"""
from __future__ import annotations

from typing import Optional

from .encounter_service import get_move_data, get_species
from .game_service import get_game


# ============================================================
# HM Move Set — cannot be forgotten
# ============================================================

HM_MOVES: set[str] = {"Cut", "Flash", "Surf", "Strength", "Fly"}


def is_hm_move(move_name: str) -> bool:
    """Check if a move is an HM move (cannot be deleted)."""
    return move_name in HM_MOVES


# ============================================================
# TM/HM Definitions
# ============================================================

# TM/HM number -> move name + metadata
TM_DEFINITIONS: list[dict] = [
    # TMs (single-use)
    {"tm_number": "TM01", "move_name": "Ice Beam", "is_hm": False, "reusable": False, "item_id": 11},
    {"tm_number": "TM02", "move_name": "Thunderbolt", "is_hm": False, "reusable": False, "item_id": 12},
    {"tm_number": "TM03", "move_name": "Psychic", "is_hm": False, "reusable": False, "item_id": 18},
    {"tm_number": "TM04", "move_name": "Earthquake", "is_hm": False, "reusable": False, "item_id": 19},
    {"tm_number": "TM05", "move_name": "Toxic", "is_hm": False, "reusable": False, "item_id": 20},
    {"tm_number": "TM06", "move_name": "Fire Blast", "is_hm": False, "reusable": False, "item_id": 21},
    {"tm_number": "TM07", "move_name": "Blizzard", "is_hm": False, "reusable": False, "item_id": 22},
    {"tm_number": "TM08", "move_name": "Thunder", "is_hm": False, "reusable": False, "item_id": 23},
    {"tm_number": "TM09", "move_name": "Rock Slide", "is_hm": False, "reusable": False, "item_id": 24},
    {"tm_number": "TM10", "move_name": "Swift", "is_hm": False, "reusable": False, "item_id": 25},
    # HMs (reusable)
    {"tm_number": "HM01", "move_name": "Cut", "is_hm": True, "reusable": True, "item_id": 101},
    {"tm_number": "HM02", "move_name": "Flash", "is_hm": True, "reusable": True, "item_id": 102},
    {"tm_number": "HM03", "move_name": "Surf", "is_hm": True, "reusable": True, "item_id": 103},
    {"tm_number": "HM04", "move_name": "Strength", "is_hm": True, "reusable": True, "item_id": 104},
    {"tm_number": "HM05", "move_name": "Fly", "is_hm": True, "reusable": True, "item_id": 105},
]

# TM/HM compatibility: tm_number -> set of species_ids that can learn it
TM_COMPATIBILITY: dict[str, set[int]] = {
    # TM01 Ice Beam: water types, psychic, normal generalists
    "TM01": {7, 8, 9, 21, 22, 54, 55, 60, 61, 72, 73, 90, 116, 117, 118, 119, 129, 130, 134, 137, 147, 1, 2, 3},
    # TM02 Thunderbolt: electric, water/flying, normal
    "TM02": {15, 16, 135, 137, 21, 22, 130, 12},
    # TM03 Psychic: psychic types, poison types, normal
    "TM03": {22, 54, 55, 137, 1, 2, 3, 133, 134, 135, 136},
    # TM04 Earthquake: ground, rock, normal heavy pokemon
    "TM04": {17, 18, 14, 6, 9, 130, 136},
    # TM05 Toxic: almost everyone can learn Toxic
    "TM05": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
             54, 55, 60, 61, 72, 73, 90, 116, 117, 118, 119, 129, 130, 132, 133, 134, 135, 136, 137, 147},
    # TM06 Fire Blast: fire types and dragons
    "TM06": {4, 5, 6, 136, 147, 130},
    # TM07 Blizzard: water, ice types
    "TM07": {7, 8, 9, 21, 22, 54, 55, 60, 61, 72, 73, 90, 116, 117, 118, 119, 130, 134, 147},
    # TM08 Thunder: electric types, dragons
    "TM08": {15, 16, 135, 147, 130},
    # TM09 Rock Slide: rock, ground types
    "TM09": {17, 18, 14, 130, 9},
    # TM10 Swift: almost universal
    "TM10": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 133, 134, 135, 136, 137, 147},
    # HM01 Cut: most pokemon with limbs/claws
    "HM01": {1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 133, 134, 135, 136},
    # HM02 Flash: many pokemon
    "HM02": {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 21, 22, 54, 55, 133, 134, 135, 136, 137},
    # HM03 Surf: water types
    "HM03": {7, 8, 9, 21, 22, 54, 55, 60, 61, 72, 73, 90, 116, 117, 118, 119, 130, 134, 147},
    # HM04 Strength: physically strong pokemon
    "HM04": {1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 17, 18, 130, 133, 134, 135, 136},
    # HM05 Fly: flying types only
    "HM05": {6, 10, 11, 12, 130},
}


def get_all_tms() -> list[dict]:
    """Return all TM/HM definitions."""
    return [dict(d) for d in TM_DEFINITIONS]


def get_tm_by_number(tm_number: str) -> Optional[dict]:
    """Get a TM/HM definition by its number."""
    for d in TM_DEFINITIONS:
        if d["tm_number"] == tm_number:
            return dict(d)
    return None


def check_tm_compatibility(tm_number: str, species_id: int) -> bool:
    """Check if a species can learn a specific TM/HM."""
    compat = TM_COMPATIBILITY.get(tm_number)
    if compat is None:
        return False
    return species_id in compat


# ============================================================
# Move Tutor Definitions
# ============================================================

MOVE_TUTORS: dict[str, dict] = {
    "pallet_tutor": {
        "tutor_id": "pallet_tutor",
        "name": "Move Tutor",
        "location": "pallet_town",
        "required_badges": 0,
        "moves_offered": [
            {"move_name": "Vine Whip", "cost": 1000, "compatible_types": ["grass"]},
            {"move_name": "Ember", "cost": 1000, "compatible_types": ["fire"]},
            {"move_name": "Water Gun", "cost": 1000, "compatible_types": ["water"]},
            {"move_name": "Razor Leaf", "cost": 2000, "compatible_types": ["grass", "poison"]},
            {"move_name": "Flamethrower", "cost": 3000, "compatible_types": ["fire"]},
            {"move_name": "Bubble Beam", "cost": 2000, "compatible_types": ["water"]},
            {"move_name": "Solar Beam", "cost": 4000, "compatible_types": ["grass"]},
            {"move_name": "Hydro Pump", "cost": 4000, "compatible_types": ["water"]},
            {"move_name": "Fire Blast", "cost": 4000, "compatible_types": ["fire"]},
        ],
    },
    "viridian_tutor": {
        "tutor_id": "viridian_tutor",
        "name": "Type Coverage Tutor",
        "location": "viridian_city",
        "required_badges": 1,
        "moves_offered": [
            {"move_name": "Ice Beam", "cost": 3000, "compatible_types": ["water", "ice", "normal", "psychic", "dragon"]},
            {"move_name": "Thunderbolt", "cost": 3000, "compatible_types": ["electric", "normal"]},
            {"move_name": "Psychic", "cost": 3000, "compatible_types": ["psychic", "normal", "water", "poison"]},
            {"move_name": "Swift", "cost": 1500, "compatible_types": ["normal", "fire", "water", "grass", "electric", "flying"]},
            {"move_name": "Headbutt", "cost": 1500, "compatible_types": ["normal", "rock", "ground", "water", "fire", "grass"]},
        ],
    },
    "pewter_tutor": {
        "tutor_id": "pewter_tutor",
        "name": "Rock & Ground Tutor",
        "location": "pewter_city",
        "required_badges": 1,
        "moves_offered": [
            {"move_name": "Rock Throw", "cost": 1500, "compatible_types": ["rock", "ground"]},
            {"move_name": "Rock Slide", "cost": 3000, "compatible_types": ["rock", "ground", "normal"]},
            {"move_name": "Earthquake", "cost": 4000, "compatible_types": ["ground", "rock", "fire", "dragon"]},
            {"move_name": "Defense Curl", "cost": 1000, "compatible_types": ["normal", "rock", "ground", "water"]},
            {"move_name": "Strength", "cost": 2000, "compatible_types": ["normal", "rock", "ground", "fire", "water"]},
        ],
    },
}


def get_tutor(tutor_id: str) -> Optional[dict]:
    """Get a move tutor's data by ID."""
    tutor = MOVE_TUTORS.get(tutor_id)
    if tutor is None:
        return None
    return dict(tutor)


def get_all_tutors() -> list[dict]:
    """Return all move tutors."""
    return [dict(t) for t in MOVE_TUTORS.values()]


def check_tutor_compatibility(tutor_id: str, species_id: int, move_name: str) -> bool:
    """Check if a species can learn a specific move from a tutor."""
    tutor = MOVE_TUTORS.get(tutor_id)
    if tutor is None:
        return False

    species = get_species(species_id)
    if species is None:
        return False

    # Find the move in tutor's catalog
    tutor_move = None
    for m in tutor["moves_offered"]:
        if m["move_name"] == move_name:
            tutor_move = m
            break
    if tutor_move is None:
        return False

    # Check type compatibility
    pokemon_types = [t.lower() for t in species.types]
    return any(t in pokemon_types for t in tutor_move["compatible_types"])


# ============================================================
# Core Teaching Logic
# ============================================================

def _teach_move_to_pokemon(
    pokemon: dict,
    move_name: str,
    forget_move_index: Optional[int] = None,
) -> dict:
    """Core logic to add a move to a Pokemon dict. Returns result dict.

    Validates HM protection and move slot limits.
    """
    # Check if already known
    current_names = {m["name"] for m in pokemon["moves"]}
    if move_name in current_names:
        return {"success": False, "message": f"{pokemon['name']} already knows {move_name}"}

    # Get move data
    md = get_move_data(move_name)
    if md is None:
        return {"success": False, "message": f"Move {move_name} not found"}

    current_moves = pokemon["moves"]

    if len(current_moves) < 4:
        current_moves.append(dict(md))
        return {
            "success": True,
            "message": f"{pokemon['name']} learned {move_name}!",
            "move_learned": move_name,
            "forgot": None,
            "current_moves": current_moves,
        }

    # Need to forget a move
    if forget_move_index is None:
        return {
            "success": False,
            "message": f"{pokemon['name']} already has 4 moves. Choose one to forget.",
        }

    if forget_move_index < 0 or forget_move_index >= len(current_moves):
        return {"success": False, "message": "Invalid forget_move_index"}

    # HM protection
    old_move_name = current_moves[forget_move_index]["name"]
    if is_hm_move(old_move_name):
        return {
            "success": False,
            "message": f"Cannot forget {old_move_name} — HM moves cannot be deleted!",
        }

    forgot_name = current_moves[forget_move_index]["name"]
    current_moves[forget_move_index] = dict(md)
    return {
        "success": True,
        "message": f"{pokemon['name']} forgot {forgot_name} and learned {move_name}!",
        "move_learned": move_name,
        "forgot": forgot_name,
        "current_moves": current_moves,
    }


# ============================================================
# Teach Via Move Tutor
# ============================================================

def teach_move_via_tutor(
    game_id: str,
    pokemon_index: int,
    tutor_id: str,
    move_name: str,
    forget_move_index: Optional[int] = None,
) -> Optional[dict]:
    """Teach a move via Move Tutor. Validates compatibility and deducts cost."""
    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        return {"success": False, "message": "Invalid Pokemon index"}

    pokemon = team[pokemon_index]
    tutor = MOVE_TUTORS.get(tutor_id)
    if tutor is None:
        return {"success": False, "message": "Tutor not found"}

    # Badge requirement
    badges = game.get("badges", 0)
    if badges < tutor["required_badges"]:
        return {
            "success": False,
            "message": f"Need at least {tutor['required_badges']} badge(s) to use this tutor",
        }

    # Find move in tutor catalog
    tutor_move = None
    for m in tutor["moves_offered"]:
        if m["move_name"] == move_name:
            tutor_move = m
            break
    if tutor_move is None:
        return {"success": False, "message": f"{move_name} is not offered by this tutor"}

    # Type compatibility
    if not check_tutor_compatibility(tutor_id, pokemon["id"], move_name):
        return {
            "success": False,
            "message": f"{pokemon['name']} is not compatible with {move_name}",
        }

    # Cost check
    money = game["player"].get("money", 0)
    cost = tutor_move["cost"]
    if money < cost:
        return {"success": False, "message": f"Not enough money (need ${cost}, have ${money})"}

    # Teach the move
    result = _teach_move_to_pokemon(pokemon, move_name, forget_move_index)

    # Deduct cost on success
    if result["success"]:
        game["player"]["money"] = money - cost

    return result


# ============================================================
# Use TM/HM
# ============================================================

def use_tm(
    game_id: str,
    pokemon_index: int,
    tm_number: str,
    forget_move_index: Optional[int] = None,
) -> Optional[dict]:
    """Use a TM/HM on a Pokemon. Checks compatibility and manages inventory."""
    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        return {"success": False, "message": "Invalid Pokemon index"}

    pokemon = team[pokemon_index]

    # Find TM definition
    tm_def = get_tm_by_number(tm_number)
    if tm_def is None:
        return {"success": False, "message": f"TM/HM {tm_number} not found"}

    # Compatibility check
    if not check_tm_compatibility(tm_number, pokemon["id"]):
        return {
            "success": False,
            "message": f"{pokemon['name']} is not compatible with {tm_number} ({tm_def['move_name']})",
        }

    # For TMs (not HMs), check inventory and consume
    if not tm_def["is_hm"]:
        item_id = tm_def.get("item_id")
        if item_id is not None:
            inventory = game["player"].setdefault("inventory", [])
            inv_entry = None
            for e in inventory:
                if e.get("item_id") == item_id:
                    inv_entry = e
                    break
            if inv_entry is None or inv_entry.get("quantity", 0) <= 0:
                return {"success": False, "message": f"You don't have {tm_number} in your inventory"}

    # Teach the move
    result = _teach_move_to_pokemon(pokemon, tm_def["move_name"], forget_move_index)

    # Consume TM on success (not HMs)
    if result["success"] and not tm_def["is_hm"] and tm_def.get("item_id") is not None:
        inventory = game["player"].setdefault("inventory", [])
        for e in inventory:
            if e.get("item_id") == tm_def["item_id"]:
                e["quantity"] -= 1
                break

    return result


# ============================================================
# Move Reminder
# ============================================================

HEART_SCALE_ITEM_ID = 50


def get_forgotten_moves(game_id: str, pokemon_index: int) -> list[dict]:
    """Get moves from species learnset that this Pokemon could re-learn."""
    game = get_game(game_id)
    if game is None:
        return []

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        return []

    pokemon = team[pokemon_index]
    species = get_species(pokemon["id"])
    if species is None:
        return []

    current_names = {m["name"] for m in pokemon["moves"]}
    level = pokemon.get("level", 1)

    forgotten = []
    for entry in species.learnset:
        if entry.level <= level and entry.move not in current_names:
            md = get_move_data(entry.move)
            if md:
                forgotten.append(md)
            else:
                forgotten.append({"name": entry.move, "type": "normal", "power": 0, "accuracy": 100, "pp": 20})

    return forgotten


def remind_move(
    game_id: str,
    pokemon_index: int,
    move_name: str,
    forget_move_index: Optional[int] = None,
) -> Optional[dict]:
    """Re-teach a forgotten move using a Heart Scale."""
    game = get_game(game_id)
    if game is None:
        return None

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        return {"success": False, "message": "Invalid Pokemon index"}

    pokemon = team[pokemon_index]

    # Check Heart Scale in inventory
    inventory = game["player"].setdefault("inventory", [])
    heart_scale = None
    for e in inventory:
        if e.get("item_id") == HEART_SCALE_ITEM_ID:
            heart_scale = e
            break
    if heart_scale is None or heart_scale.get("quantity", 0) <= 0:
        return {"success": False, "message": "You need a Heart Scale to use the Move Reminder"}

    # Verify the move is in forgotten moves
    forgotten = get_forgotten_moves(game_id, pokemon_index)
    forgotten_names = {m["name"] for m in forgotten}
    if move_name not in forgotten_names:
        return {"success": False, "message": f"{pokemon['name']} cannot re-learn {move_name}"}

    # Teach
    result = _teach_move_to_pokemon(pokemon, move_name, forget_move_index)

    # Consume Heart Scale on success
    if result["success"]:
        heart_scale["quantity"] -= 1

    return result


# ============================================================
# Learnable Moves Query
# ============================================================

def get_all_learnable_moves(species_id: int) -> dict:
    """Get all moves a species can learn via tutor, TM, and HM."""
    species = get_species(species_id)
    if species is None:
        return {"tutor_moves": [], "tm_moves": [], "hm_moves": []}

    tutor_moves = []
    for tutor in MOVE_TUTORS.values():
        for m in tutor["moves_offered"]:
            pokemon_types = [t.lower() for t in species.types]
            if any(t in pokemon_types for t in m["compatible_types"]):
                md = get_move_data(m["move_name"])
                if md and md["name"] not in [tm["name"] for tm in tutor_moves]:
                    tutor_moves.append(md)

    tm_moves = []
    hm_moves = []
    for tm_def in TM_DEFINITIONS:
        compat = TM_COMPATIBILITY.get(tm_def["tm_number"], set())
        if species_id in compat:
            md = get_move_data(tm_def["move_name"])
            if md:
                entry = dict(md)
                entry["tm_number"] = tm_def["tm_number"]
                if tm_def["is_hm"]:
                    hm_moves.append(entry)
                else:
                    tm_moves.append(entry)

    return {
        "tutor_moves": tutor_moves,
        "tm_moves": tm_moves,
        "hm_moves": hm_moves,
    }
