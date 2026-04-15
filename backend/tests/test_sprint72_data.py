"""Tests for Sprint 72: TM/HM list, Kanto region, PP table.

These tests verify TM/HM data, Kanto region overview,
and PP configuration.
"""
import json
import os
import pytest

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


# ──── TM/HM List ────────────────────────────────────────────

class TestTMHMList:
    def test_tm_count(self):
        th = _load_json("tm_hm_list.json")
        assert len(th["tms"]) == 50

    def test_hm_count(self):
        th = _load_json("tm_hm_list.json")
        assert len(th["hms"]) == 5

    def test_total_fields_match(self):
        th = _load_json("tm_hm_list.json")
        assert th["total_tms"] == 50
        assert th["total_hms"] == 5

    def test_tms_have_fields(self):
        th = _load_json("tm_hm_list.json")
        for tm in th["tms"]:
            assert "number" in tm
            assert "move" in tm
            assert "location" in tm
            assert "source" in tm

    def test_tm_numbers_sequential(self):
        th = _load_json("tm_hm_list.json")
        numbers = [tm["number"] for tm in th["tms"]]
        assert numbers == list(range(1, 51))

    def test_hm_numbers_sequential(self):
        th = _load_json("tm_hm_list.json")
        numbers = [hm["number"] for hm in th["hms"]]
        assert numbers == list(range(1, 6))

    def test_all_tm_moves_in_moves_json(self):
        th = _load_json("tm_hm_list.json")
        moves = _load_json("moves.json")
        for tm in th["tms"]:
            assert tm["move"] in moves, f"TM{tm['number']} {tm['move']} not in moves.json"

    def test_all_hm_moves_in_moves_json(self):
        th = _load_json("tm_hm_list.json")
        moves = _load_json("moves.json")
        for hm in th["hms"]:
            assert hm["move"] in moves, f"HM{hm['number']} {hm['move']} not in moves.json"

    def test_hms_not_deletable(self):
        th = _load_json("tm_hm_list.json")
        for hm in th["hms"]:
            assert hm["deletable"] is False

    def test_tm_single_use(self):
        th = _load_json("tm_hm_list.json")
        assert th["tm_rules"]["single_use"] is True
        assert th["tm_rules"]["consumed_on_use"] is True

    def test_hm_infinite_use(self):
        th = _load_json("tm_hm_list.json")
        assert th["hm_rules"]["infinite_use"] is True


# ──── Kanto Region ───────────────────────────────────────────

class TestKantoRegion:
    def test_city_count(self):
        kr = _load_json("kanto_region.json")
        assert len(kr["cities"]) == 11

    def test_route_count(self):
        kr = _load_json("kanto_region.json")
        assert len(kr["routes"]) == 25

    def test_dungeon_count(self):
        kr = _load_json("kanto_region.json")
        assert len(kr["dungeons"]) == 13

    def test_total_fields_match(self):
        kr = _load_json("kanto_region.json")
        assert kr["total_cities"] == len(kr["cities"])
        assert kr["total_routes"] == len(kr["routes"])
        assert kr["total_dungeons"] == len(kr["dungeons"])

    def test_cities_have_fields(self):
        kr = _load_json("kanto_region.json")
        for city in kr["cities"]:
            assert "name" in city
            assert "map_id" in city
            assert "type" in city
            assert "gym" in city
            assert "pokecenter" in city

    def test_eight_gym_cities(self):
        kr = _load_json("kanto_region.json")
        gym_cities = [c for c in kr["cities"] if c["gym"]]
        assert len(gym_cities) == 8

    def test_routes_have_connections(self):
        kr = _load_json("kanto_region.json")
        for route in kr["routes"]:
            assert "connects" in route
            assert len(route["connects"]) == 2

    def test_dungeons_have_floors(self):
        kr = _load_json("kanto_region.json")
        for dungeon in kr["dungeons"]:
            assert "floors" in dungeon
            assert dungeon["floors"] >= 1

    def test_pallet_town_no_gym(self):
        kr = _load_json("kanto_region.json")
        pallet = next(c for c in kr["cities"] if c["name"] == "Pallet Town")
        assert pallet["gym"] is False
        assert pallet["pokecenter"] is False

    def test_region_name(self):
        kr = _load_json("kanto_region.json")
        assert kr["region_name"] == "Kanto"


# ──── PP Table ───────────────────────────────────────────────

class TestPPTable:
    def test_pp_tier_count(self):
        pp = _load_json("pp_table.json")
        assert len(pp["pp_tiers"]) == 8

    def test_total_tiers_match(self):
        pp = _load_json("pp_table.json")
        assert pp["total_pp_tiers"] == len(pp["pp_tiers"])

    def test_pp_up_config(self):
        pp = _load_json("pp_table.json")
        stages = pp["pp_stages"]
        assert stages["max_pp_ups"] == 3
        assert stages["pp_up_increase_percent"] == 20
        assert stages["pp_max_total_increase_percent"] == 60

    def test_pp_restore_items(self):
        pp = _load_json("pp_table.json")
        items = pp["pp_restore_items"]
        assert len(items) >= 4
        names = [i["item"] for i in items]
        assert "Ether" in names
        assert "Max Elixir" in names

    def test_struggle_move(self):
        pp = _load_json("pp_table.json")
        struggle = pp["struggle"]
        assert struggle["name"] == "Struggle"
        assert struggle["power"] == 50
        assert struggle["recoil_percent"] == 25
        assert struggle["pp"] is None

    def test_struggle_at_zero_pp(self):
        pp = _load_json("pp_table.json")
        assert pp["pp_rules"]["struggle_at_zero"] is True

    def test_pokecenter_restores_pp(self):
        pp = _load_json("pp_table.json")
        assert pp["pp_rules"]["pp_restored_at_pokecenter"] is True

    def test_max_pp_calculation(self):
        pp = _load_json("pp_table.json")
        for tier_name, tier in pp["pp_tiers"].items():
            base = tier["base_pp"]
            expected_max = int(base * 1.6)
            assert tier["max_pp"] == expected_max, f"{tier_name}: {tier['max_pp']} != {expected_max}"


# ──── Counts ──────────────────────────────────────────────────

class TestCounts:
    def test_items_unchanged(self):
        items = _load_json("items.json")
        assert len(items) == 93

    def test_moves_unchanged(self):
        moves = _load_json("moves.json")
        assert len(moves) == 174

    def test_species_unchanged(self):
        species = _load_json("pokemon_species.json")
        assert len(species) == 151
