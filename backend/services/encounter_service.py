from __future__ import annotations

import json
import random
from pathlib import Path

from ..models.encounter import (
    EncounterCheckResponse,
    EncounterEntry,
    EncounterTable,
    PokemonSpecies,
    WildPokemon,
)
from ..models.pokemon import Move, Stats

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_species_db: dict[int, PokemonSpecies] = {}
_encounter_tables: dict[str, EncounterTable] = {}
_moves_db: dict[str, dict] = {}


def _load_species() -> None:
    global _species_db
    with open(DATA_DIR / "pokemon_species.json") as f:
        raw = json.load(f)
    _species_db = {s["id"]: PokemonSpecies(**s) for s in raw}


def _load_encounter_tables() -> None:
    global _encounter_tables
    with open(DATA_DIR / "encounter_tables.json") as f:
        raw = json.load(f)
    _encounter_tables = {k: EncounterTable(**v) for k, v in raw.items()}


def _load_moves() -> None:
    global _moves_db
    with open(DATA_DIR / "moves.json") as f:
        _moves_db = json.load(f)


def get_species(species_id: int) -> PokemonSpecies | None:
    if not _species_db:
        _load_species()
    return _species_db.get(species_id)


def get_all_species() -> list[PokemonSpecies]:
    if not _species_db:
        _load_species()
    return list(_species_db.values())


def get_encounter_table(area_id: str) -> EncounterTable | None:
    if not _encounter_tables:
        _load_encounter_tables()
    return _encounter_tables.get(area_id)


def get_move_data(move_name: str) -> dict | None:
    if not _moves_db:
        _load_moves()
    return _moves_db.get(move_name)


def _calc_stat(base: int, level: int, iv: int, is_hp: bool = False) -> int:
    """Calculate a stat value based on base stat, level, and IV."""
    if is_hp:
        return ((2 * base + iv) * level) // 100 + level + 10
    return ((2 * base + iv) * level) // 100 + 5


def _generate_moves_for_level(species: PokemonSpecies, level: int) -> list[Move]:
    """Get the latest 4 moves a Pokemon would know at the given level."""
    available = [e for e in species.learnset if e.level <= level]
    # Take the latest 4
    latest = available[-4:] if len(available) > 4 else available
    moves = []
    for entry in latest:
        md = get_move_data(entry.move)
        if md:
            moves.append(Move(**md))
        else:
            # Fallback for status/unknown moves
            moves.append(Move(name=entry.move, type="normal", power=0, accuracy=100, pp=20))
    return moves


def _generate_gender(species: PokemonSpecies) -> str | None:
    """Generate a gender based on species gender_ratio.

    gender_ratio is the percentage chance of being female (0-100).
    None means genderless.
    0 means always male, 100 means always female.
    """
    if species.gender_ratio is None:
        return None
    roll = random.random() * 100
    return "female" if roll < species.gender_ratio else "male"


def generate_wild_pokemon(species_id: int, level: int) -> WildPokemon:
    """Generate a wild Pokemon instance with random IVs and level-appropriate moves."""
    species = get_species(species_id)
    if species is None:
        raise ValueError(f"Species {species_id} not found")

    # Generate random IVs (0-31)
    ivs = {
        "hp": random.randint(0, 31),
        "attack": random.randint(0, 31),
        "defense": random.randint(0, 31),
        "sp_attack": random.randint(0, 31),
        "sp_defense": random.randint(0, 31),
        "speed": random.randint(0, 31),
    }

    hp = _calc_stat(species.stats.hp, level, ivs["hp"], is_hp=True)
    stats = Stats(
        hp=hp,
        attack=_calc_stat(species.stats.attack, level, ivs["attack"]),
        defense=_calc_stat(species.stats.defense, level, ivs["defense"]),
        sp_attack=_calc_stat(species.stats.sp_attack, level, ivs["sp_attack"]),
        sp_defense=_calc_stat(species.stats.sp_defense, level, ivs["sp_defense"]),
        speed=_calc_stat(species.stats.speed, level, ivs["speed"]),
    )

    moves = _generate_moves_for_level(species, level)

    # Select random ability from species pool
    from .ability_service import select_ability
    ability_id = select_ability(species.abilities)

    # Generate gender based on species ratio
    gender = _generate_gender(species)

    return WildPokemon(
        species_id=species.id,
        name=species.name,
        types=species.types,
        level=level,
        stats=stats,
        current_hp=hp,
        moves=moves,
        catch_rate=species.catch_rate,
        base_exp=species.base_exp,
        sprite=species.sprite,
        ability_id=ability_id,
        ivs=ivs,
        gender=gender,
    )


def _select_encounter(table: EncounterTable) -> EncounterEntry:
    """Weighted random selection from encounter table."""
    total = sum(e.weight for e in table.encounters)
    roll = random.randint(1, total)
    cumulative = 0
    for entry in table.encounters:
        cumulative += entry.weight
        if roll <= cumulative:
            return entry
    return table.encounters[-1]


def check_encounter(area_id: str) -> EncounterCheckResponse:
    """Check if a wild encounter occurs in the given area."""
    table = get_encounter_table(area_id)
    if table is None:
        return EncounterCheckResponse(encountered=False)

    # Roll for encounter
    if random.random() > table.base_encounter_rate:
        return EncounterCheckResponse(encountered=False)

    # Select which Pokemon
    entry = _select_encounter(table)
    level = random.randint(entry.min_level, entry.max_level)
    wild = generate_wild_pokemon(entry.species_id, level)

    return EncounterCheckResponse(encountered=True, pokemon=wild)


def fish_encounter(area_id: str, rod_tier: str) -> EncounterCheckResponse | None:
    """Attempt a fishing encounter. Returns None if no fishing table for this area/rod."""
    table_id = f"{area_id}_fishing_{rod_tier}"
    table = get_encounter_table(table_id)
    if table is None:
        return None

    # Fishing always succeeds (rate=1.0), but still use the table's rate
    if random.random() > table.base_encounter_rate:
        return EncounterCheckResponse(encountered=False)

    entry = _select_encounter(table)
    level = random.randint(entry.min_level, entry.max_level)
    wild = generate_wild_pokemon(entry.species_id, level)
    return EncounterCheckResponse(encountered=True, pokemon=wild)
