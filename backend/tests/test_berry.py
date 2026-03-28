"""Tests for the Berry Farming & Growth System."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.berry_service import (
    BERRY_DEFS,
    MAX_WATERS,
    PLOT_DEFS,
    WATER_SPEED_FACTOR,
    _berry_plots,
    _berry_pouches,
    _growth_duration_seconds,
    add_berry_to_pouch,
    check_held_berry_trigger,
    get_berry_def,
    get_berry_defs,
    get_berry_pouch,
    get_plots,
    get_plots_for_map,
    harvest_plot,
    plant_berry,
    remove_berry_from_pouch,
    use_berry_in_battle,
    water_plot,
)
from backend.services.game_service import create_game, _games

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean():
    _berry_plots.clear()
    _berry_pouches.clear()
    yield
    _berry_plots.clear()
    _berry_pouches.clear()


def _make_game(name: str = "Alice") -> str:
    game = create_game(name, 1)
    return game["id"]


# ============================================================
# Berry Definitions
# ============================================================

class TestBerryDefs:
    def test_ten_berries_defined(self):
        assert len(BERRY_DEFS) == 10

    def test_all_berries_have_required_fields(self):
        for berry in BERRY_DEFS.values():
            assert berry.id
            assert berry.name
            assert berry.effect_type in ("heal_hp", "cure_status", "restore_pp", "catch_bonus")
            assert berry.yield_min >= 1
            assert berry.yield_max >= berry.yield_min
            assert berry.growth_time_minutes > 0

    def test_oran_berry(self):
        oran = BERRY_DEFS["oran"]
        assert oran.name == "Oran Berry"
        assert oran.effect_type == "heal_hp"
        assert oran.effect_amount == 10

    def test_sitrus_berry(self):
        sitrus = BERRY_DEFS["sitrus"]
        assert sitrus.name == "Sitrus Berry"
        assert sitrus.effect_type == "heal_hp"
        assert sitrus.effect_amount == 25

    def test_status_cure_berries(self):
        status_berries = {
            "cheri": "paralysis",
            "chesto": "sleep",
            "pecha": "poison",
            "rawst": "burn",
            "aspear": "freeze",
        }
        for berry_id, status in status_berries.items():
            berry = BERRY_DEFS[berry_id]
            assert berry.effect_type == "cure_status"
            assert berry.effect_status == status

    def test_lum_berry_cures_any(self):
        lum = BERRY_DEFS["lum"]
        assert lum.effect_type == "cure_status"
        assert lum.effect_status == "any"

    def test_razz_berry(self):
        razz = BERRY_DEFS["razz"]
        assert razz.effect_type == "catch_bonus"
        assert razz.effect_amount == 1.5

    def test_get_berry_defs(self):
        defs = get_berry_defs()
        assert len(defs) == 10

    def test_get_berry_def_found(self):
        assert get_berry_def("oran") is not None

    def test_get_berry_def_not_found(self):
        assert get_berry_def("nonexistent") is None


# ============================================================
# Plot Definitions
# ============================================================

class TestPlotDefs:
    def test_seven_plots_defined(self):
        assert len(PLOT_DEFS) == 7

    def test_pallet_town_plots(self):
        pallet = [p for p in PLOT_DEFS if p["map_id"] == "pallet_town"]
        assert len(pallet) == 2

    def test_route1_plots(self):
        route1 = [p for p in PLOT_DEFS if p["map_id"] == "route_1"]
        assert len(route1) == 3

    def test_viridian_plots(self):
        viridian = [p for p in PLOT_DEFS if p["map_id"] == "viridian_city"]
        assert len(viridian) == 2


# ============================================================
# Growth Duration
# ============================================================

class TestGrowthDuration:
    def test_no_water(self):
        berry = BERRY_DEFS["oran"]
        duration = _growth_duration_seconds(berry, 0)
        assert duration == berry.growth_time_minutes * 60

    def test_one_water(self):
        berry = BERRY_DEFS["oran"]
        base = berry.growth_time_minutes * 60
        duration = _growth_duration_seconds(berry, 1)
        assert duration == base * (1.0 - WATER_SPEED_FACTOR)

    def test_max_water(self):
        berry = BERRY_DEFS["oran"]
        base = berry.growth_time_minutes * 60
        duration = _growth_duration_seconds(berry, MAX_WATERS)
        assert duration == base * (1.0 - MAX_WATERS * WATER_SPEED_FACTOR)

    def test_extra_water_capped(self):
        berry = BERRY_DEFS["oran"]
        d3 = _growth_duration_seconds(berry, MAX_WATERS)
        d5 = _growth_duration_seconds(berry, MAX_WATERS + 2)
        assert d3 == d5


# ============================================================
# Planting
# ============================================================

class TestPlanting:
    def test_plant_berry(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 3)
        result = plant_berry(gid, "pallet_1", "oran")
        assert result.planted_berry == "oran"
        assert result.growth_stage == "planted"
        assert result.berry_name == "Oran Berry"
        # Consumed 1 from pouch
        assert get_berry_pouch(gid)["oran"] == 2

    def test_plant_in_occupied_plot_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 5)
        plant_berry(gid, "pallet_1", "oran")
        with pytest.raises(ValueError, match="not empty"):
            plant_berry(gid, "pallet_1", "oran")

    def test_plant_unknown_berry_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Unknown berry"):
            plant_berry(gid, "pallet_1", "bogus")

    def test_plant_no_berries_in_pouch_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="No berries"):
            plant_berry(gid, "pallet_1", "oran")

    def test_plant_unknown_plot_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        with pytest.raises(ValueError, match="Plot not found"):
            plant_berry(gid, "nonexistent", "oran")


# ============================================================
# Watering
# ============================================================

class TestWatering:
    def test_water_planted_berry(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        result = water_plot(gid, "pallet_1")
        assert result.water_count == 1

    def test_water_multiple_times(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        water_plot(gid, "pallet_1")
        water_plot(gid, "pallet_1")
        result = water_plot(gid, "pallet_1")
        assert result.water_count == 3

    def test_water_exceeds_max_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        for _ in range(MAX_WATERS):
            water_plot(gid, "pallet_1")
        with pytest.raises(ValueError, match="maximum"):
            water_plot(gid, "pallet_1")

    def test_water_empty_plot_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Nothing planted"):
            water_plot(gid, "pallet_1")

    def test_water_ready_berry_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        # Fast-forward time so berry is ready
        plots = _berry_plots[gid]
        plots["pallet_1"].plant_time = time.time() - 99999
        with pytest.raises(ValueError, match="already ready"):
            water_plot(gid, "pallet_1")


# ============================================================
# Harvesting
# ============================================================

class TestHarvesting:
    def test_harvest_ready_berry(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        # Fast-forward
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        result = harvest_plot(gid, "pallet_1")
        assert result.success is True
        assert result.berry_id == "oran"
        assert result.quantity >= BERRY_DEFS["oran"].yield_min

    def test_harvest_not_ready_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        result = harvest_plot(gid, "pallet_1")
        assert result.success is False
        assert "not ready" in result.message

    def test_harvest_empty_plot(self):
        gid = _make_game()
        result = harvest_plot(gid, "pallet_1")
        assert result.success is False

    def test_harvest_adds_to_pouch(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        result = harvest_plot(gid, "pallet_1")
        pouch = get_berry_pouch(gid)
        assert pouch.get("oran", 0) == result.quantity

    def test_harvest_resets_plot(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        harvest_plot(gid, "pallet_1")
        plots = get_plots(gid)
        pallet1 = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet1.growth_stage == "empty"
        assert pallet1.planted_berry is None

    def test_watered_berry_yields_more(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 2)

        # Plant without watering
        plant_berry(gid, "pallet_1", "oran")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        r1 = harvest_plot(gid, "pallet_1")

        # Plant with max watering
        plant_berry(gid, "pallet_1", "oran")
        for _ in range(MAX_WATERS):
            water_plot(gid, "pallet_1")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        r2 = harvest_plot(gid, "pallet_1")

        assert r2.quantity >= r1.quantity

    def test_harvest_nonexistent_plot(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Plot not found"):
            harvest_plot(gid, "bogus")


# ============================================================
# Berry Pouch
# ============================================================

class TestBerryPouch:
    def test_empty_pouch(self):
        gid = _make_game()
        assert get_berry_pouch(gid) == {}

    def test_add_berry(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 5)
        assert get_berry_pouch(gid)["oran"] == 5

    def test_add_multiple_types(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 3)
        add_berry_to_pouch(gid, "sitrus", 2)
        pouch = get_berry_pouch(gid)
        assert pouch["oran"] == 3
        assert pouch["sitrus"] == 2

    def test_add_invalid_berry_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="Unknown berry"):
            add_berry_to_pouch(gid, "bogus", 1)

    def test_add_zero_quantity_fails(self):
        gid = _make_game()
        with pytest.raises(ValueError, match="positive"):
            add_berry_to_pouch(gid, "oran", 0)

    def test_remove_berry(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 5)
        assert remove_berry_from_pouch(gid, "oran", 3) is True
        assert get_berry_pouch(gid)["oran"] == 2

    def test_remove_all_berries(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 3)
        assert remove_berry_from_pouch(gid, "oran", 3) is True
        assert "oran" not in get_berry_pouch(gid)

    def test_remove_too_many_fails(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 2)
        assert remove_berry_from_pouch(gid, "oran", 5) is False
        assert get_berry_pouch(gid)["oran"] == 2


# ============================================================
# Growth Stages
# ============================================================

class TestGrowthStages:
    def test_stages_progress(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        berry = BERRY_DEFS["oran"]
        total = _growth_duration_seconds(berry, 0)

        # Just planted
        plots = get_plots(gid)
        pallet = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet.growth_stage == "planted"

        # 30% through
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - total * 0.30
        plots = get_plots(gid)
        pallet = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet.growth_stage == "sprouted"

        # 55% through
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - total * 0.55
        plots = get_plots(gid)
        pallet = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet.growth_stage == "growing"

        # 80% through
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - total * 0.80
        plots = get_plots(gid)
        pallet = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet.growth_stage == "flowering"

        # 100% through
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - total * 1.1
        plots = get_plots(gid)
        pallet = [p for p in plots if p.plot_id == "pallet_1"][0]
        assert pallet.growth_stage == "ready"


# ============================================================
# Plot Filtering
# ============================================================

class TestPlotFiltering:
    def test_get_plots_for_map(self):
        gid = _make_game()
        pallet_plots = get_plots_for_map(gid, "pallet_town")
        assert len(pallet_plots) == 2

        route_plots = get_plots_for_map(gid, "route_1")
        assert len(route_plots) == 3

    def test_get_plots_all(self):
        gid = _make_game()
        all_plots = get_plots(gid)
        assert len(all_plots) == 7


# ============================================================
# Berry Battle Effects
# ============================================================

class TestBerryBattleEffects:
    def test_oran_heals_10(self):
        pokemon = {"name": "Pikachu", "current_hp": 30, "max_hp": 50, "stats": {"hp": 50}}
        result = use_berry_in_battle("oran", pokemon)
        assert result is not None
        assert result["type"] == "heal_hp"
        assert result["amount"] == 10
        assert result["new_hp"] == 40

    def test_oran_no_heal_at_full(self):
        pokemon = {"name": "Pikachu", "current_hp": 50, "max_hp": 50, "stats": {"hp": 50}}
        result = use_berry_in_battle("oran", pokemon)
        assert result is None

    def test_oran_heal_capped_at_max(self):
        pokemon = {"name": "Pikachu", "current_hp": 45, "max_hp": 50, "stats": {"hp": 50}}
        result = use_berry_in_battle("oran", pokemon)
        assert result["new_hp"] == 50
        assert result["amount"] == 5

    def test_sitrus_heals_25_percent(self):
        pokemon = {"name": "Snorlax", "current_hp": 50, "max_hp": 200, "stats": {"hp": 200}}
        result = use_berry_in_battle("sitrus", pokemon)
        assert result is not None
        assert result["amount"] == 50  # 25% of 200
        assert result["new_hp"] == 100

    def test_cheri_cures_paralysis(self):
        pokemon = {"name": "Pikachu", "status": "paralysis"}
        result = use_berry_in_battle("cheri", pokemon)
        assert result is not None
        assert result["type"] == "cure_status"
        assert result["status"] == "paralysis"

    def test_cheri_no_effect_wrong_status(self):
        pokemon = {"name": "Pikachu", "status": "burn"}
        result = use_berry_in_battle("cheri", pokemon)
        assert result is None

    def test_cheri_no_effect_no_status(self):
        pokemon = {"name": "Pikachu", "status": None}
        result = use_berry_in_battle("cheri", pokemon)
        assert result is None

    def test_lum_cures_any_status(self):
        for status in ["paralysis", "sleep", "poison", "burn", "freeze"]:
            pokemon = {"name": "Pikachu", "status": status}
            result = use_berry_in_battle("lum", pokemon)
            assert result is not None
            assert result["type"] == "cure_status"

    def test_leppa_restores_pp(self):
        pokemon = {"name": "Pikachu"}
        result = use_berry_in_battle("leppa", pokemon)
        assert result is not None
        assert result["type"] == "restore_pp"
        assert result["amount"] == 10

    def test_razz_catch_bonus(self):
        pokemon = {"name": "Pidgey"}
        result = use_berry_in_battle("razz", pokemon)
        assert result is not None
        assert result["type"] == "catch_bonus"
        assert result["multiplier"] == 1.5

    def test_unknown_berry_returns_none(self):
        result = use_berry_in_battle("bogus", {"name": "Pikachu"})
        assert result is None


# ============================================================
# Held Berry Auto-Trigger
# ============================================================

class TestHeldBerryTrigger:
    def test_oran_triggers_at_half_hp(self):
        pokemon = {"current_hp": 25, "max_hp": 50}
        assert check_held_berry_trigger("oran", pokemon) is True

    def test_oran_does_not_trigger_above_half(self):
        pokemon = {"current_hp": 30, "max_hp": 50}
        assert check_held_berry_trigger("oran", pokemon) is False

    def test_cheri_triggers_with_paralysis(self):
        pokemon = {"status": "paralysis"}
        assert check_held_berry_trigger("cheri", pokemon) is True

    def test_cheri_does_not_trigger_wrong_status(self):
        pokemon = {"status": "burn"}
        assert check_held_berry_trigger("cheri", pokemon) is False

    def test_lum_triggers_with_any_status(self):
        pokemon = {"status": "sleep"}
        assert check_held_berry_trigger("lum", pokemon) is True

    def test_unknown_berry_no_trigger(self):
        assert check_held_berry_trigger("bogus", {"current_hp": 1, "max_hp": 100}) is False


# ============================================================
# API Tests
# ============================================================

class TestBerryAPI:
    def test_list_berry_types(self):
        resp = client.get("/api/berry/types")
        assert resp.status_code == 200
        assert len(resp.json()) == 10

    def test_get_plots_api(self):
        gid = _make_game()
        resp = client.get(f"/api/berry/plots/{gid}")
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    def test_get_plots_not_found(self):
        resp = client.get("/api/berry/plots/nope")
        assert resp.status_code == 404

    def test_get_plots_by_map(self):
        gid = _make_game()
        resp = client.get(f"/api/berry/plots/{gid}/pallet_town")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_plant_api(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 3)
        resp = client.post("/api/berry/plant", json={
            "game_id": gid, "plot_id": "pallet_1", "berry_id": "oran"
        })
        assert resp.status_code == 200
        assert resp.json()["growth_stage"] == "planted"

    def test_plant_api_bad_game(self):
        resp = client.post("/api/berry/plant", json={
            "game_id": "nope", "plot_id": "pallet_1", "berry_id": "oran"
        })
        assert resp.status_code == 404

    def test_plant_api_no_berries(self):
        gid = _make_game()
        resp = client.post("/api/berry/plant", json={
            "game_id": gid, "plot_id": "pallet_1", "berry_id": "oran"
        })
        assert resp.status_code == 400

    def test_water_api(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        resp = client.post("/api/berry/water/pallet_1", json={"game_id": gid})
        assert resp.status_code == 200
        assert resp.json()["water_count"] == 1

    def test_water_api_bad_game(self):
        resp = client.post("/api/berry/water/pallet_1", json={"game_id": "nope"})
        assert resp.status_code == 404

    def test_harvest_api(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999
        resp = client.post("/api/berry/harvest/pallet_1", json={"game_id": gid})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["quantity"] >= 1

    def test_harvest_api_not_ready(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        resp = client.post("/api/berry/harvest/pallet_1", json={"game_id": gid})
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_berry_inventory_api(self):
        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 5)
        resp = client.get(f"/api/berry/inventory/{gid}")
        assert resp.status_code == 200
        assert resp.json()["oran"] == 5

    def test_berry_inventory_not_found(self):
        resp = client.get("/api/berry/inventory/nope")
        assert resp.status_code == 404

    def test_give_berry_api(self):
        gid = _make_game()
        resp = client.post(f"/api/berry/give?game_id={gid}&berry_id=oran&quantity=3")
        assert resp.status_code == 200
        assert get_berry_pouch(gid)["oran"] == 3


# ============================================================
# Achievement Integration
# ============================================================

class TestBerryAchievements:
    def test_harvest_records_berry_achievement(self):
        from backend.services.leaderboard_service import _player_stats, _achievements
        _player_stats.clear()
        _achievements.clear()

        gid = _make_game()
        add_berry_to_pouch(gid, "oran", 1)
        plant_berry(gid, "pallet_1", "oran")
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 99999

        # Harvest via API to trigger achievement check
        resp = client.post("/api/berry/harvest/pallet_1", json={"game_id": gid})
        assert resp.json()["success"] is True

        # Check stats were updated
        stats = _player_stats.get(gid, {})
        assert stats.get("berries_harvested", 0) >= 1

        _player_stats.clear()
        _achievements.clear()
