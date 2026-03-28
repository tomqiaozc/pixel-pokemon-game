"""Berry farming service — planting, watering, growth, and harvesting."""
from __future__ import annotations

import random
import time
from typing import Optional

from ..models.berry import (
    BerryDef,
    BerryPlot,
    BerryPlotResponse,
    BerryPouch,
    HarvestResult,
)

# --- Berry definitions ---
BERRY_DEFS: dict[str, BerryDef] = {
    "oran": BerryDef(
        id="oran", name="Oran Berry", description="Restores 10 HP when held (auto-use at <50% HP).",
        growth_time_minutes=20, yield_min=2, yield_max=5,
        effect_type="heal_hp", effect_amount=10, rarity="common",
    ),
    "sitrus": BerryDef(
        id="sitrus", name="Sitrus Berry", description="Restores 25% max HP when held (auto-use at <50% HP).",
        growth_time_minutes=30, yield_min=1, yield_max=3,
        effect_type="heal_hp", effect_amount=25, rarity="uncommon",
    ),
    "leppa": BerryDef(
        id="leppa", name="Leppa Berry", description="Restores 10 PP to one move.",
        growth_time_minutes=25, yield_min=1, yield_max=4,
        effect_type="restore_pp", effect_amount=10, rarity="uncommon",
    ),
    "cheri": BerryDef(
        id="cheri", name="Cheri Berry", description="Cures paralysis when held.",
        growth_time_minutes=15, yield_min=2, yield_max=5,
        effect_type="cure_status", effect_status="paralysis", rarity="common",
    ),
    "chesto": BerryDef(
        id="chesto", name="Chesto Berry", description="Cures sleep when held.",
        growth_time_minutes=15, yield_min=2, yield_max=5,
        effect_type="cure_status", effect_status="sleep", rarity="common",
    ),
    "pecha": BerryDef(
        id="pecha", name="Pecha Berry", description="Cures poison when held.",
        growth_time_minutes=15, yield_min=2, yield_max=5,
        effect_type="cure_status", effect_status="poison", rarity="common",
    ),
    "rawst": BerryDef(
        id="rawst", name="Rawst Berry", description="Cures burn when held.",
        growth_time_minutes=15, yield_min=2, yield_max=5,
        effect_type="cure_status", effect_status="burn", rarity="common",
    ),
    "aspear": BerryDef(
        id="aspear", name="Aspear Berry", description="Cures freeze when held.",
        growth_time_minutes=15, yield_min=2, yield_max=5,
        effect_type="cure_status", effect_status="freeze", rarity="common",
    ),
    "lum": BerryDef(
        id="lum", name="Lum Berry", description="Cures any status condition when held.",
        growth_time_minutes=40, yield_min=1, yield_max=2,
        effect_type="cure_status", effect_status="any", rarity="rare",
    ),
    "razz": BerryDef(
        id="razz", name="Razz Berry", description="Increases catch rate by 1.5x when used.",
        growth_time_minutes=25, yield_min=1, yield_max=3,
        effect_type="catch_bonus", effect_amount=1.5, rarity="uncommon",
    ),
}

# --- Plot definitions (7 total across 3 maps) ---
PLOT_DEFS: list[dict] = [
    {"plot_id": "pallet_1", "map_id": "pallet_town", "x": 8, "y": 3},
    {"plot_id": "pallet_2", "map_id": "pallet_town", "x": 9, "y": 3},
    {"plot_id": "route1_1", "map_id": "route_1", "x": 5, "y": 10},
    {"plot_id": "route1_2", "map_id": "route_1", "x": 6, "y": 10},
    {"plot_id": "route1_3", "map_id": "route_1", "x": 7, "y": 10},
    {"plot_id": "viridian_1", "map_id": "viridian_city", "x": 12, "y": 5},
    {"plot_id": "viridian_2", "map_id": "viridian_city", "x": 13, "y": 5},
]

# --- In-memory state per game ---
_berry_plots: dict[str, dict[str, BerryPlot]] = {}  # game_id -> {plot_id -> BerryPlot}
_berry_pouches: dict[str, BerryPouch] = {}  # game_id -> BerryPouch

# Water speed-up: each watering reduces remaining time by 25%, max 3 waterings
MAX_WATERS = 3
WATER_SPEED_FACTOR = 0.25  # 25% faster per water


def _get_plots(game_id: str) -> dict[str, BerryPlot]:
    """Get or initialize berry plots for a game."""
    if game_id not in _berry_plots:
        _berry_plots[game_id] = {
            pd["plot_id"]: BerryPlot(**pd)
            for pd in PLOT_DEFS
        }
    return _berry_plots[game_id]


def _get_pouch(game_id: str) -> BerryPouch:
    """Get or initialize berry pouch for a game."""
    if game_id not in _berry_pouches:
        _berry_pouches[game_id] = BerryPouch()
    return _berry_pouches[game_id]


def _growth_duration_seconds(berry: BerryDef, water_count: int) -> float:
    """Calculate growth duration in seconds, accounting for waterings."""
    base = berry.growth_time_minutes * 60
    reduction = min(water_count, MAX_WATERS) * WATER_SPEED_FACTOR
    return base * (1.0 - reduction)


def _update_growth_stage(plot: BerryPlot) -> None:
    """Update growth stage based on elapsed time."""
    if plot.planted_berry is None or plot.plant_time is None:
        return

    berry = BERRY_DEFS.get(plot.planted_berry)
    if berry is None:
        return

    total_duration = _growth_duration_seconds(berry, plot.water_count)
    elapsed = time.time() - plot.plant_time

    if elapsed >= total_duration:
        plot.growth_stage = "ready"
        if plot.ready_time is None:
            plot.ready_time = plot.plant_time + total_duration
    elif elapsed >= total_duration * 0.75:
        plot.growth_stage = "flowering"
    elif elapsed >= total_duration * 0.50:
        plot.growth_stage = "growing"
    elif elapsed >= total_duration * 0.25:
        plot.growth_stage = "sprouted"
    else:
        plot.growth_stage = "planted"


def _plot_to_response(plot: BerryPlot) -> BerryPlotResponse:
    """Convert plot to API response with computed fields."""
    _update_growth_stage(plot)

    berry_name = None
    time_remaining = None
    yield_est = None

    if plot.planted_berry:
        berry = BERRY_DEFS.get(plot.planted_berry)
        if berry:
            berry_name = berry.name
            total_duration = _growth_duration_seconds(berry, plot.water_count)
            if plot.plant_time and plot.growth_stage != "ready":
                remaining = total_duration - (time.time() - plot.plant_time)
                time_remaining = max(0, int(remaining))
            elif plot.growth_stage == "ready":
                time_remaining = 0
            # Yield estimate: max waters = max yield, no water = min yield
            water_ratio = min(plot.water_count, MAX_WATERS) / MAX_WATERS
            yield_est = int(berry.yield_min + (berry.yield_max - berry.yield_min) * water_ratio)

    return BerryPlotResponse(
        plot_id=plot.plot_id,
        map_id=plot.map_id,
        x=plot.x,
        y=plot.y,
        planted_berry=plot.planted_berry,
        berry_name=berry_name,
        growth_stage=plot.growth_stage,
        water_count=plot.water_count,
        time_remaining_seconds=time_remaining,
        yield_estimate=yield_est,
    )


# --- Public API ---

def get_berry_defs() -> list[BerryDef]:
    """Return all berry definitions."""
    return list(BERRY_DEFS.values())


def get_berry_def(berry_id: str) -> Optional[BerryDef]:
    """Return a single berry definition."""
    return BERRY_DEFS.get(berry_id)


def get_plots(game_id: str) -> list[BerryPlotResponse]:
    """Get all plot states for a game."""
    plots = _get_plots(game_id)
    return [_plot_to_response(p) for p in plots.values()]


def get_plots_for_map(game_id: str, map_id: str) -> list[BerryPlotResponse]:
    """Get plots for a specific map."""
    plots = _get_plots(game_id)
    return [_plot_to_response(p) for p in plots.values() if p.map_id == map_id]


def plant_berry(game_id: str, plot_id: str, berry_id: str) -> BerryPlotResponse:
    """Plant a berry in an empty plot. Consumes from pouch."""
    plots = _get_plots(game_id)
    if plot_id not in plots:
        raise ValueError("Plot not found")

    plot = plots[plot_id]
    if plot.planted_berry is not None:
        _update_growth_stage(plot)
        if plot.growth_stage != "empty":
            raise ValueError("Plot is not empty")

    berry = BERRY_DEFS.get(berry_id)
    if berry is None:
        raise ValueError("Unknown berry type")

    pouch = _get_pouch(game_id)
    if pouch.berries.get(berry_id, 0) <= 0:
        raise ValueError("No berries of this type in pouch")

    # Consume berry from pouch
    pouch.berries[berry_id] -= 1
    if pouch.berries[berry_id] <= 0:
        del pouch.berries[berry_id]

    # Plant
    plot.planted_berry = berry_id
    plot.plant_time = time.time()
    plot.water_count = 0
    plot.growth_stage = "planted"
    plot.ready_time = None

    return _plot_to_response(plot)


def water_plot(game_id: str, plot_id: str) -> BerryPlotResponse:
    """Water a planted berry. Max 3 waterings."""
    plots = _get_plots(game_id)
    if plot_id not in plots:
        raise ValueError("Plot not found")

    plot = plots[plot_id]
    _update_growth_stage(plot)

    if plot.planted_berry is None:
        raise ValueError("Nothing planted here")

    if plot.growth_stage == "ready":
        raise ValueError("Berry is already ready to harvest")

    if plot.water_count >= MAX_WATERS:
        raise ValueError("Plot has been watered the maximum number of times")

    plot.water_count += 1
    return _plot_to_response(plot)


def harvest_plot(game_id: str, plot_id: str) -> HarvestResult:
    """Harvest a ready berry plot."""
    plots = _get_plots(game_id)
    if plot_id not in plots:
        raise ValueError("Plot not found")

    plot = plots[plot_id]
    _update_growth_stage(plot)

    if plot.planted_berry is None:
        return HarvestResult(success=False, message="Nothing planted here")

    if plot.growth_stage != "ready":
        return HarvestResult(success=False, message="Berry is not ready to harvest yet")

    berry = BERRY_DEFS.get(plot.planted_berry)
    if berry is None:
        return HarvestResult(success=False, message="Unknown berry type")

    # Calculate yield based on watering
    water_ratio = min(plot.water_count, MAX_WATERS) / MAX_WATERS
    quantity = int(berry.yield_min + (berry.yield_max - berry.yield_min) * water_ratio)
    quantity = max(berry.yield_min, min(berry.yield_max, quantity))

    # Add to pouch
    pouch = _get_pouch(game_id)
    pouch.berries[berry.id] = pouch.berries.get(berry.id, 0) + quantity

    berry_id = plot.planted_berry

    # Reset plot
    plot.planted_berry = None
    plot.plant_time = None
    plot.water_count = 0
    plot.growth_stage = "empty"
    plot.ready_time = None

    return HarvestResult(
        success=True,
        message=f"Harvested {quantity} {berry.name}{'s' if quantity > 1 else ''}!",
        berry_id=berry_id,
        berry_name=berry.name,
        quantity=quantity,
    )


def get_berry_pouch(game_id: str) -> dict[str, int]:
    """Get berry pouch contents."""
    pouch = _get_pouch(game_id)
    return dict(pouch.berries)


def add_berry_to_pouch(game_id: str, berry_id: str, quantity: int = 1) -> None:
    """Add berries to pouch (e.g., from shop or gift)."""
    if berry_id not in BERRY_DEFS:
        raise ValueError("Unknown berry type")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    pouch = _get_pouch(game_id)
    pouch.berries[berry_id] = pouch.berries.get(berry_id, 0) + quantity


def remove_berry_from_pouch(game_id: str, berry_id: str, quantity: int = 1) -> bool:
    """Remove berries from pouch. Returns False if not enough."""
    pouch = _get_pouch(game_id)
    current = pouch.berries.get(berry_id, 0)
    if current < quantity:
        return False
    pouch.berries[berry_id] = current - quantity
    if pouch.berries[berry_id] <= 0:
        del pouch.berries[berry_id]
    return True


def use_berry_in_battle(berry_id: str, pokemon: dict, battle_context: Optional[dict] = None) -> Optional[dict]:
    """Apply berry effect. Returns effect dict or None if no effect."""
    berry = BERRY_DEFS.get(berry_id)
    if berry is None:
        return None

    if berry.effect_type == "heal_hp":
        max_hp = pokemon.get("max_hp", pokemon.get("stats", {}).get("hp", 100))
        current_hp = pokemon.get("current_hp", max_hp)
        if current_hp >= max_hp:
            return None
        if berry.id == "sitrus":
            heal = int(max_hp * (berry.effect_amount / 100.0))
        else:
            heal = int(berry.effect_amount)
        new_hp = min(max_hp, current_hp + heal)
        return {"type": "heal_hp", "amount": new_hp - current_hp, "new_hp": new_hp,
                "message": f"{pokemon.get('name', 'Pokemon')}'s {berry.name} restored {new_hp - current_hp} HP!"}

    elif berry.effect_type == "cure_status":
        status = pokemon.get("status")
        if status is None:
            return None
        if berry.effect_status == "any" or berry.effect_status == status:
            return {"type": "cure_status", "status": status,
                    "message": f"{pokemon.get('name', 'Pokemon')}'s {berry.name} cured {status}!"}
        return None

    elif berry.effect_type == "restore_pp":
        return {"type": "restore_pp", "amount": int(berry.effect_amount),
                "message": f"{pokemon.get('name', 'Pokemon')}'s {berry.name} restored PP!"}

    elif berry.effect_type == "catch_bonus":
        return {"type": "catch_bonus", "multiplier": berry.effect_amount,
                "message": f"The {berry.name} made the wild Pokemon easier to catch!"}

    return None


def check_held_berry_trigger(berry_id: str, pokemon: dict) -> bool:
    """Check if a held berry should auto-trigger."""
    berry = BERRY_DEFS.get(berry_id)
    if berry is None:
        return False

    if berry.effect_type == "heal_hp":
        max_hp = pokemon.get("max_hp", pokemon.get("stats", {}).get("hp", 100))
        current_hp = pokemon.get("current_hp", max_hp)
        return current_hp <= max_hp * 0.5

    elif berry.effect_type == "cure_status":
        status = pokemon.get("status")
        if status is None:
            return False
        return berry.effect_status == "any" or berry.effect_status == status

    return False
