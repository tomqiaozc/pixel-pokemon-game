from __future__ import annotations

from typing import Optional

from ..models.pokedex import HealResult, PCBox, PokedexEntry, PokedexStats
from .encounter_service import get_all_species, get_species
from .game_service import get_game

# Per-game Pokedex and PC storage
_pokedex: dict[str, dict[int, PokedexEntry]] = {}
_pc_boxes: dict[str, list[list[dict]]] = {}

NUM_BOXES = 5
BOX_SIZE = 30


def _get_pokedex(game_id: str) -> dict[int, PokedexEntry]:
    if game_id not in _pokedex:
        # Initialize with all species as unseen
        entries = {}
        for sp in get_all_species():
            entries[sp.id] = PokedexEntry(
                species_id=sp.id,
                name=sp.name,
                status="unseen",
            )
        _pokedex[game_id] = entries
    return _pokedex[game_id]


def _get_pc(game_id: str) -> list[list[dict]]:
    if game_id not in _pc_boxes:
        _pc_boxes[game_id] = [[] for _ in range(NUM_BOXES)]
    return _pc_boxes[game_id]


def get_pokedex(game_id: str) -> list[PokedexEntry]:
    dex = _get_pokedex(game_id)
    return sorted(dex.values(), key=lambda e: e.species_id)


def get_pokedex_entry(game_id: str, species_id: int) -> Optional[PokedexEntry]:
    dex = _get_pokedex(game_id)
    return dex.get(species_id)


def register_seen(game_id: str, species_id: int, location: str = "unknown") -> PokedexEntry:
    dex = _get_pokedex(game_id)
    entry = dex.get(species_id)
    if entry is None:
        sp = get_species(species_id)
        name = sp.name if sp else f"Unknown #{species_id}"
        entry = PokedexEntry(species_id=species_id, name=name)
        dex[species_id] = entry
    if entry.status == "unseen":
        entry.status = "seen"
        entry.first_seen_location = location
    return entry


def register_caught(game_id: str, species_id: int, location: str = "unknown") -> PokedexEntry:
    dex = _get_pokedex(game_id)
    entry = dex.get(species_id)
    if entry is None:
        sp = get_species(species_id)
        name = sp.name if sp else f"Unknown #{species_id}"
        entry = PokedexEntry(species_id=species_id, name=name)
        dex[species_id] = entry
    if entry.first_seen_location is None:
        entry.first_seen_location = location
    if entry.status != "caught":
        entry.status = "caught"
        entry.first_caught_location = location
    return entry


def get_pokedex_stats(game_id: str) -> PokedexStats:
    dex = _get_pokedex(game_id)
    total = len(dex)
    seen = sum(1 for e in dex.values() if e.status in ("seen", "caught"))
    caught = sum(1 for e in dex.values() if e.status == "caught")
    pct = (caught / total * 100) if total > 0 else 0
    return PokedexStats(
        total_species=total,
        seen_count=seen,
        caught_count=caught,
        completion_percentage=round(pct, 1),
    )


def heal_party(game_id: str) -> Optional[HealResult]:
    game = get_game(game_id)
    if game is None:
        return None

    healed = []
    for pokemon in game["player"]["team"]:
        max_hp = pokemon["stats"]["hp"]
        old_hp = pokemon.get("current_hp", max_hp)
        status = pokemon.get("status")
        pokemon["current_hp"] = max_hp
        pokemon["status"] = None
        healed.append({
            "name": pokemon["name"],
            "old_hp": old_hp,
            "new_hp": max_hp,
            "status_removed": status,
        })
    return HealResult(healed_pokemon=healed)


def get_pc_boxes(game_id: str) -> list[PCBox]:
    boxes = _get_pc(game_id)
    return [PCBox(box_number=i + 1, pokemon=box) for i, box in enumerate(boxes)]


def deposit_pokemon(game_id: str, pokemon_index: int) -> Optional[str]:
    game = get_game(game_id)
    if game is None:
        return "Game not found"

    team = game["player"]["team"]
    if len(team) <= 1:
        return "Cannot deposit — need at least 1 Pokemon in party"
    if pokemon_index < 0 or pokemon_index >= len(team):
        return "Invalid Pokemon index"

    boxes = _get_pc(game_id)
    # Find first box with space
    for i, box in enumerate(boxes):
        if len(box) < BOX_SIZE:
            pokemon = team.pop(pokemon_index)
            box.append(pokemon)
            return None  # success
    return "All PC boxes are full"


def withdraw_pokemon(game_id: str, box_number: int, pokemon_index: int) -> Optional[str]:
    game = get_game(game_id)
    if game is None:
        return "Game not found"

    team = game["player"]["team"]
    if len(team) >= 6:
        return "Party is full (max 6)"

    boxes = _get_pc(game_id)
    box_idx = box_number - 1
    if box_idx < 0 or box_idx >= len(boxes):
        return "Invalid box number"
    box = boxes[box_idx]
    if pokemon_index < 0 or pokemon_index >= len(box):
        return "Invalid Pokemon index in box"

    pokemon = box.pop(pokemon_index)
    team.append(pokemon)
    return None  # success


def auto_deposit(game_id: str, pokemon_data: dict) -> bool:
    """Auto-deposit a Pokemon to PC when party is full. Returns True if deposited."""
    boxes = _get_pc(game_id)
    for box in boxes:
        if len(box) < BOX_SIZE:
            box.append(pokemon_data)
            return True
    return False
