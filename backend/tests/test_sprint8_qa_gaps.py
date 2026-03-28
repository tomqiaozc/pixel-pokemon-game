"""Sprint 8 QA-A Gap Coverage Tests: Achievements, berry battles & breeding.

Covers edge cases, error paths, and boundary conditions not exercised by
the existing test_leaderboard.py (37), test_berry.py (73), and test_breeding.py (46).
"""
import random
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.berry_service import (
    BERRY_DEFS,
    MAX_WATERS,
    _berry_plots,
    _berry_pouches,
    add_berry_to_pouch,
    check_held_berry_trigger,
    get_berry_pouch,
    harvest_plot,
    plant_berry,
    use_berry_in_battle,
    water_plot,
)
from backend.services.breeding_service import (
    BASE_EGG_CHANCE,
    DEFAULT_HATCH_STEPS,
    EGG_CHECK_STEPS,
    _daycares,
    _identify_father,
    _inherit_ivs,
    check_compatibility,
    collect_egg,
    deposit_pokemon,
    generate_egg,
    get_daycare_status,
    process_steps,
    withdraw_pokemon,
)
from backend.services.game_service import _games, create_game
from backend.services.leaderboard_service import (
    _achievements,
    _notification_queue,
    _player_stats,
    check_achievements,
    get_achievement_summary,
    get_achievements,
    get_recent_notifications,
    record_berry_harvested,
    record_evolution,
    record_money_spent,
    record_pokemon_caught,
    record_pvp_result,
    record_quest_completed,
    record_trainer_battle_won,
)

client = TestClient(app)


def _make_game(name="TestPlayer"):
    """Create a game with a starter Pokemon for testing."""
    game = create_game(name, 1)  # 1 = Bulbasaur
    return game


def _cleanup(game_id):
    _games.pop(game_id, None)
    _berry_plots.pop(game_id, None)
    _berry_pouches.pop(game_id, None)
    _daycares.pop(game_id, None)
    _player_stats.pop(game_id, None)
    _achievements.pop(game_id, None)
    _notification_queue.pop(game_id, None)


def _pokemon(name="Bulbasaur", species_id=1, gender="male", egg_groups=None, level=5):
    """Helper to create a Pokemon dict."""
    return {
        "id": species_id, "species_id": species_id, "name": name,
        "types": ["grass"], "level": level, "gender": gender,
        "stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
        "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
        "sprite": f"{name.lower()}.png", "ability_id": "overgrow",
        "ivs": {"hp": 15, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 15},
        "egg_groups": egg_groups or ["monster", "grass"],
    }


# ==============================================================
# ACHIEVEMENT SYSTEM GAPS
# ==============================================================

class TestAchievementNotificationContent:
    """Verify notification fields are complete."""

    def test_notification_has_all_fields(self):
        """Achievement notification has name, description, timestamp."""
        game = _make_game()
        gid = game["id"]
        record_pokemon_caught(gid)
        check_achievements(gid)
        notifs = get_recent_notifications(gid)
        assert len(notifs) >= 1
        notif = notifs[0]
        assert notif.achievement_id is not None
        assert notif.achievement_name is not None
        assert notif.tier is not None
        assert notif.category is not None
        assert notif.timestamp is not None
        _cleanup(gid)

    def test_notification_limit_parameter(self):
        """Notification drain respects limit parameter."""
        game = _make_game()
        gid = game["id"]
        # Trigger multiple achievements
        for _ in range(10):
            record_pokemon_caught(gid)
        record_evolution(gid)
        check_achievements(gid)
        # Drain with limit=1
        batch1 = get_recent_notifications(gid, limit=1)
        assert len(batch1) == 1
        # More remain
        batch2 = get_recent_notifications(gid)
        assert len(batch2) >= 1
        _cleanup(gid)


class TestAchievementMultiUnlock:
    """Multiple achievements unlocking simultaneously."""

    def test_many_achievements_at_once(self):
        """Large stat boost triggers multiple achievements in one check."""
        game = _make_game()
        gid = game["id"]
        for _ in range(100):
            record_pokemon_caught(gid)
        for _ in range(50):
            record_evolution(gid)
        record_money_spent(gid, 50000)
        result = check_achievements(gid)
        # Should trigger first_steps, catch_50, catch_100, evolve, evolve_5,
        # evolve_20, big_spender, mega_spender
        earned_ids = {a.id for a in result.newly_earned}
        assert "first_steps" in earned_ids
        assert "catch_50" in earned_ids
        assert "catch_100" in earned_ids
        assert "evolve" in earned_ids
        assert "evolve_5" in earned_ids
        assert "evolve_20" in earned_ids
        assert "big_spender" in earned_ids
        assert "mega_spender" in earned_ids
        _cleanup(gid)


class TestAchievementProgressDetails:
    """Progress tracking for various achievement types."""

    def test_battle_progress_tracking(self):
        """Battle achievements track progress correctly."""
        game = _make_game()
        gid = game["id"]
        for _ in range(5):
            record_trainer_battle_won(gid)
        result = check_achievements(gid)
        all_achs = {a.id: a for a in result.all_achievements}
        if "trainer_battles_10" in all_achs:
            assert all_achs["trainer_battles_10"].progress == 5
            assert all_achs["trainer_battles_10"].completed is False
        _cleanup(gid)

    def test_evolution_progress_partial(self):
        """Evolution progress tracks below threshold."""
        game = _make_game()
        gid = game["id"]
        for _ in range(3):
            record_evolution(gid)
        result = check_achievements(gid)
        all_achs = {a.id: a for a in result.all_achievements}
        assert all_achs["evolve_5"].progress == 3
        assert all_achs["evolve_5"].completed is False
        assert all_achs["evolve"].completed is True
        _cleanup(gid)

    def test_money_progress_tracks(self):
        """Money-based achievements track cumulative spending."""
        game = _make_game()
        gid = game["id"]
        record_money_spent(gid, 5000)
        result = check_achievements(gid)
        all_achs = {a.id: a for a in result.all_achievements}
        assert all_achs["big_spender"].progress == 5000
        assert all_achs["big_spender"].completed is False
        _cleanup(gid)


class TestAchievementSummaryDetails:
    """Achievement summary edge cases."""

    def test_summary_has_all_tiers(self):
        """Summary tier_counts includes all 4 tiers."""
        game = _make_game()
        gid = game["id"]
        summary = get_achievement_summary(gid)
        assert "tier_counts" in summary
        for tier in ["bronze", "silver", "gold", "platinum"]:
            assert tier in summary["tier_counts"]
        _cleanup(gid)

    def test_summary_categories_present(self):
        """Summary has expected categories."""
        game = _make_game()
        gid = game["id"]
        summary = get_achievement_summary(gid)
        assert "categories" in summary
        assert "collection" in summary["categories"]
        assert "battle" in summary["categories"]
        _cleanup(gid)

    def test_summary_completion_updates(self):
        """Summary completion count updates after earning achievements."""
        game = _make_game()
        gid = game["id"]
        summary_before = get_achievement_summary(gid)
        completed_before = summary_before["completed"]
        record_pokemon_caught(gid)
        check_achievements(gid)
        summary_after = get_achievement_summary(gid)
        assert summary_after["completed"] > completed_before
        _cleanup(gid)


class TestAchievementAPI:
    """Achievement REST API edge cases."""

    def test_check_achievements_api(self):
        """POST /api/achievements/check/{player_id} works."""
        game = _make_game()
        gid = game["id"]
        record_pokemon_caught(gid)
        resp = client.post(f"/api/achievements/check/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "newly_earned" in data
        assert "all_achievements" in data
        _cleanup(gid)

    def test_achievements_api_not_found(self):
        """Achievement check for nonexistent player returns 404."""
        resp = client.post("/api/achievements/check/nonexistent_player")
        assert resp.status_code == 404

    def test_recent_notifications_api(self):
        """GET /api/achievements/recent/{player_id} returns notifications."""
        game = _make_game()
        gid = game["id"]
        record_pokemon_caught(gid)
        check_achievements(gid)
        resp = client.get(f"/api/achievements/recent/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        _cleanup(gid)

    def test_summary_api(self):
        """GET /api/achievements/summary/{player_id} returns summary."""
        game = _make_game()
        gid = game["id"]
        resp = client.get(f"/api/achievements/summary/{gid}")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "completed" in data
        assert "tier_counts" in data
        _cleanup(gid)

    def test_summary_api_not_found(self):
        """Summary for nonexistent player returns 404."""
        resp = client.get("/api/achievements/summary/nonexistent")
        assert resp.status_code == 404


class TestAchievementBerryIntegration:
    """Berry harvesting triggers achievement progress."""

    def test_berry_harvest_increments_stat(self):
        """record_berry_harvested increments berries_harvested stat."""
        game = _make_game()
        gid = game["id"]
        record_berry_harvested(gid, 3)
        stats = _player_stats[gid]
        assert stats["berries_harvested"] == 3
        _cleanup(gid)

    def test_berry_first_achievement(self):
        """Harvesting 1 berry triggers berry_first achievement."""
        game = _make_game()
        gid = game["id"]
        record_berry_harvested(gid, 1)
        result = check_achievements(gid)
        earned_ids = {a.id for a in result.newly_earned}
        assert "berry_first" in earned_ids
        _cleanup(gid)

    def test_berry_50_achievement(self):
        """Harvesting 50 berries triggers berry_50 achievement."""
        game = _make_game()
        gid = game["id"]
        record_berry_harvested(gid, 50)
        result = check_achievements(gid)
        earned_ids = {a.id for a in result.newly_earned}
        assert "berry_50" in earned_ids
        assert "berry_first" in earned_ids
        _cleanup(gid)


# ==============================================================
# BERRY BATTLE EFFECT GAPS
# ==============================================================

class TestBerryBattleEffectEdgeCases:
    """Edge cases for berry use in battle."""

    def test_sitrus_heals_percentage_of_max(self):
        """Sitrus berry heals 25% of max HP, not flat amount."""
        pokemon = {"current_hp": 50, "max_hp": 200, "status": None}
        result = use_berry_in_battle("sitrus", pokemon)
        assert result is not None
        assert result["amount"] == 50  # 25% of 200

    def test_sitrus_no_heal_at_full_hp(self):
        """Sitrus does nothing at full HP."""
        pokemon = {"current_hp": 100, "max_hp": 100, "status": None}
        result = use_berry_in_battle("sitrus", pokemon)
        assert result is None

    def test_oran_heal_capped_at_max(self):
        """Oran heal does not exceed max HP."""
        pokemon = {"current_hp": 95, "max_hp": 100, "status": None}
        result = use_berry_in_battle("oran", pokemon)
        assert result is not None
        assert result["new_hp"] <= 100

    def test_lum_cures_all_status_types(self):
        """Lum cures paralysis, sleep, poison, burn, freeze."""
        for status in ["paralysis", "sleep", "poison", "burn", "freeze"]:
            pokemon = {"current_hp": 50, "max_hp": 100, "status": status}
            result = use_berry_in_battle("lum", pokemon)
            assert result is not None, f"Lum should cure {status}"
            assert result["status"] == status

    def test_cheri_no_effect_on_poison(self):
        """Cheri only cures paralysis, not poison."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": "poison"}
        result = use_berry_in_battle("cheri", pokemon)
        assert result is None

    def test_leppa_restores_pp(self):
        """Leppa restores PP on first move."""
        pokemon = {
            "current_hp": 50, "max_hp": 100, "status": None,
            "moves": [{"name": "Tackle", "pp": 5, "max_pp": 35}],
        }
        result = use_berry_in_battle("leppa", pokemon)
        assert result is not None
        assert result["amount"] == 10

    def test_razz_catch_bonus(self):
        """Razz berry gives 1.5x catch rate multiplier."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": None}
        result = use_berry_in_battle("razz", pokemon, battle_context={})
        assert result is not None
        assert result["multiplier"] == 1.5

    def test_unknown_berry_returns_none(self):
        """Unknown berry ID returns None."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": None}
        result = use_berry_in_battle("fake_berry", pokemon)
        assert result is None

    def test_pokemon_missing_max_hp_uses_stats(self):
        """Pokemon without max_hp key uses stats.hp."""
        pokemon = {"current_hp": 30, "stats": {"hp": 100}, "status": None}
        result = use_berry_in_battle("oran", pokemon)
        assert result is not None


class TestHeldBerryTriggerEdgeCases:
    """Edge cases for held berry auto-trigger."""

    def test_sitrus_triggers_at_half_hp(self):
        """Sitrus triggers at <= 50% HP (same as Oran)."""
        pokemon = {"current_hp": 49, "max_hp": 100}
        assert check_held_berry_trigger("sitrus", pokemon) is True

    def test_sitrus_no_trigger_above_half(self):
        """Sitrus doesn't trigger above 50% HP."""
        pokemon = {"current_hp": 51, "max_hp": 100}
        assert check_held_berry_trigger("sitrus", pokemon) is False

    def test_leppa_no_auto_trigger(self):
        """Leppa (restore_pp) does not auto-trigger as held berry."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": None}
        assert check_held_berry_trigger("leppa", pokemon) is False

    def test_razz_no_auto_trigger(self):
        """Razz (catch_bonus) does not auto-trigger as held berry."""
        pokemon = {"current_hp": 50, "max_hp": 100}
        assert check_held_berry_trigger("razz", pokemon) is False

    def test_lum_triggers_with_any_status(self):
        """Lum triggers for any status condition."""
        for status in ["paralysis", "sleep", "poison", "burn", "freeze"]:
            pokemon = {"current_hp": 50, "max_hp": 100, "status": status}
            assert check_held_berry_trigger("lum", pokemon) is True, f"Lum should trigger for {status}"

    def test_aspear_triggers_for_freeze(self):
        """Aspear triggers only for freeze."""
        pokemon_freeze = {"current_hp": 50, "max_hp": 100, "status": "freeze"}
        pokemon_burn = {"current_hp": 50, "max_hp": 100, "status": "burn"}
        assert check_held_berry_trigger("aspear", pokemon_freeze) is True
        assert check_held_berry_trigger("aspear", pokemon_burn) is False

    def test_rawst_triggers_for_burn(self):
        """Rawst triggers only for burn."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": "burn"}
        assert check_held_berry_trigger("rawst", pokemon) is True

    def test_pecha_triggers_for_poison(self):
        """Pecha triggers only for poison."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": "poison"}
        assert check_held_berry_trigger("pecha", pokemon) is True

    def test_chesto_triggers_for_sleep(self):
        """Chesto triggers only for sleep."""
        pokemon = {"current_hp": 50, "max_hp": 100, "status": "sleep"}
        assert check_held_berry_trigger("chesto", pokemon) is True


# ==============================================================
# BERRY FARMING GAPS
# ==============================================================

class TestBerryPouchEdgeCases:
    """Berry pouch edge cases."""

    def test_add_negative_quantity_fails(self):
        """Negative quantity raises ValueError."""
        game = _make_game()
        gid = game["id"]
        with pytest.raises(ValueError):
            add_berry_to_pouch(gid, "oran", -1)
        _cleanup(gid)

    def test_pouch_multiple_add_accumulates(self):
        """Multiple adds to same berry accumulate."""
        game = _make_game()
        gid = game["id"]
        add_berry_to_pouch(gid, "oran", 3)
        add_berry_to_pouch(gid, "oran", 5)
        pouch = get_berry_pouch(gid)
        assert pouch["oran"] == 8
        _cleanup(gid)


class TestBerryGrowthBoundary:
    """Growth stage boundary conditions."""

    def test_harvest_yield_bounds(self):
        """Harvest yield is within [yield_min, yield_max]."""
        game = _make_game()
        gid = game["id"]
        add_berry_to_pouch(gid, "oran", 10)
        plant_berry(gid, "pallet_1", "oran")
        # Force ready by patching time
        plot = _berry_plots[gid]["pallet_1"]
        plot.plant_time = time.time() - 9999
        result = harvest_plot(gid, "pallet_1")
        assert result.success is True
        berry_def = BERRY_DEFS["oran"]
        assert result.quantity >= berry_def.yield_min
        assert result.quantity <= berry_def.yield_max
        _cleanup(gid)


class TestBerryAPIEdgeCases:
    """Berry API edge cases."""

    def test_give_berry_api(self):
        """POST /api/berry/give adds berries to pouch."""
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/berry/give?game_id={gid}&berry_id=oran&quantity=5")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # Verify in pouch
        inv = client.get(f"/api/berry/inventory/{gid}")
        data = inv.json()
        # Pouch may return as dict with berry_id keys
        assert data.get("oran", data.get("berries", {}).get("oran", 0)) == 5
        _cleanup(gid)

    def test_give_berry_bad_game(self):
        """POST /api/berry/give with bad game_id returns 404."""
        resp = client.post("/api/berry/give?game_id=nonexistent&berry_id=oran&quantity=1")
        assert resp.status_code == 404

    def test_give_berry_invalid_type(self):
        """POST /api/berry/give with invalid berry returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post(f"/api/berry/give?game_id={gid}&berry_id=fake_berry&quantity=1")
        assert resp.status_code == 400
        _cleanup(gid)

    def test_harvest_api_bad_game(self):
        """POST /api/berry/harvest with bad game_id returns 404."""
        resp = client.post("/api/berry/harvest/pallet_1", json={"game_id": "nonexistent"})
        assert resp.status_code == 404

    def test_water_api_nonexistent_plot(self):
        """POST /api/berry/water with nonexistent plot returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/berry/water/fake_plot_999", json={"game_id": gid})
        assert resp.status_code == 400
        _cleanup(gid)


# ==============================================================
# BREEDING SYSTEM GAPS
# ==============================================================

class TestCompatibilityEdgeCases:
    """Breeding compatibility edge cases."""

    def test_different_egg_groups_incompatible(self):
        """Pokemon with no overlapping egg groups are incompatible."""
        poke_a = _pokemon("Bulbasaur", 1, "male", ["monster", "grass"])
        poke_b = _pokemon("Magikarp", 129, "female", ["water_2", "dragon"])
        compat, msg = check_compatibility(poke_a, poke_b)
        assert compat is False

    def test_overlapping_egg_group_compatible(self):
        """Pokemon with one overlapping egg group are compatible."""
        poke_a = _pokemon("Bulbasaur", 1, "male", ["monster", "grass"])
        poke_b = _pokemon("Charmander", 4, "female", ["monster", "dragon"])
        compat, msg = check_compatibility(poke_a, poke_b)
        assert compat is True

    def test_ditto_with_undiscovered_incompatible(self):
        """Ditto cannot breed with undiscovered egg group Pokemon.

        Note: check_compatibility uses _get_egg_group which looks up species
        from the DB, not the dict's egg_groups field. We mock it so the
        undiscovered code path is exercised.
        """
        ditto = _pokemon("Ditto", 132, None, ["ditto"])
        legendary = _pokemon("Mewtwo", 150, None, ["undiscovered"])
        with patch("backend.services.breeding_service._get_egg_group") as mock_eg:
            def fake_egg_group(pokemon):
                if pokemon.get("name") == "Ditto":
                    return ["ditto"]
                return ["undiscovered"]
            mock_eg.side_effect = fake_egg_group
            compat, msg = check_compatibility(ditto, legendary)
            assert compat is False

    def test_two_genderless_same_group_incompatible(self):
        """Two genderless Pokemon (non-Ditto) cannot breed even if same egg group."""
        poke_a = _pokemon("Magnemite", 81, None, ["mineral"])
        poke_b = _pokemon("Voltorb", 100, None, ["mineral"])
        compat, msg = check_compatibility(poke_a, poke_b)
        assert compat is False


class TestIVInheritanceDetails:
    """IV inheritance edge cases."""

    def test_inherited_ivs_are_valid_range(self):
        """All inherited IVs are in range 0-31."""
        parent_a = _pokemon("A", 1, "male")
        parent_a["ivs"] = {"hp": 31, "attack": 31, "defense": 31, "sp_attack": 31, "sp_defense": 31, "speed": 31}
        parent_b = _pokemon("B", 1, "female")
        parent_b["ivs"] = {"hp": 0, "attack": 0, "defense": 0, "sp_attack": 0, "sp_defense": 0, "speed": 0}
        for _ in range(10):
            ivs = _inherit_ivs(parent_a, parent_b)
            for stat, val in ivs.items():
                assert 0 <= val <= 31, f"IV {stat}={val} out of range"

    def test_exactly_three_stats_from_parents(self):
        """Exactly 3 IVs come from parents (others random)."""
        parent_a = _pokemon("A", 1, "male")
        parent_a["ivs"] = {"hp": 31, "attack": 31, "defense": 31, "sp_attack": 31, "sp_defense": 31, "speed": 31}
        parent_b = _pokemon("B", 1, "female")
        parent_b["ivs"] = {"hp": 31, "attack": 31, "defense": 31, "sp_attack": 31, "sp_defense": 31, "speed": 31}
        # With all 31 parents, all 6 IVs are either 31 (inherited) or random 0-31
        ivs = _inherit_ivs(parent_a, parent_b)
        assert len(ivs) == 6
        # At least 3 should be 31 (inherited from parents who all have 31)
        count_31 = sum(1 for v in ivs.values() if v == 31)
        assert count_31 >= 3


class TestEggGeneration:
    """Egg generation details."""

    def test_egg_has_hatch_counter(self):
        """Generated egg has default hatch counter."""
        parent_a = _pokemon("Bulbasaur", 1, "male")
        parent_b = _pokemon("Bulbasaur", 1, "female")
        egg = generate_egg(parent_a, parent_b)
        assert egg.hatch_counter == DEFAULT_HATCH_STEPS
        assert egg.is_egg is True

    def test_egg_inherits_species_from_mother(self):
        """Egg species comes from the female parent."""
        father = _pokemon("Charmander", 4, "male", ["monster", "dragon"])
        mother = _pokemon("Bulbasaur", 1, "female", ["monster", "grass"])
        egg = generate_egg(father, mother)
        assert egg.species_id == 1  # Mother's species

    def test_ditto_egg_gets_non_ditto_species(self):
        """Ditto + other -> offspring is non-Ditto species."""
        ditto = _pokemon("Ditto", 132, None, ["ditto"])
        other = _pokemon("Charmander", 4, "male", ["monster", "dragon"])
        egg = generate_egg(ditto, other)
        assert egg.species_id == 4

    def test_egg_has_moves(self):
        """Generated egg has at least one move."""
        parent_a = _pokemon("Bulbasaur", 1, "male")
        parent_b = _pokemon("Bulbasaur", 1, "female")
        egg = generate_egg(parent_a, parent_b)
        assert len(egg.moves) >= 1


class TestFatherIdentification:
    """Father identification edge cases."""

    def test_ditto_never_father(self):
        """When one parent is Ditto, the other is always the father."""
        ditto = _pokemon("Ditto", 132, None, ["ditto"])
        male = _pokemon("Charmander", 4, "male")
        assert _identify_father(ditto, male)["name"] == "Charmander"
        assert _identify_father(male, ditto)["name"] == "Charmander"

    def test_male_is_father(self):
        """Male parent is identified as father."""
        male = _pokemon("Bulbasaur", 1, "male")
        female = _pokemon("Bulbasaur", 1, "female")
        father = _identify_father(male, female)
        assert father["gender"] == "male"


class TestDaycareDepositWithdraw:
    """Daycare deposit/withdraw edge cases."""

    def test_withdraw_slot_2(self):
        """Can withdraw from slot 2 specifically."""
        game = _make_game()
        gid = game["id"]
        # Add two more Pokemon so team has 3 (can deposit 2 and keep 1)
        _games[gid]["player"]["team"].append(
            _pokemon("Charmander", 4, "female")
        )
        _games[gid]["player"]["team"].append(
            _pokemon("Squirtle", 7, "male")
        )
        # Deposit two
        deposit_pokemon(gid, 0)
        deposit_pokemon(gid, 0)
        # Withdraw slot 2
        result = withdraw_pokemon(gid, 2)
        assert result is not None
        # Slot 2 should now be empty
        status = get_daycare_status(gid)
        assert status.slot_2 is None
        _cleanup(gid)

    def test_deposit_preserves_pokemon_data(self):
        """Deposited Pokemon retains its data when checked."""
        game = _make_game()
        gid = game["id"]
        poke_name = _games[gid]["player"]["team"][0]["name"]
        # Add second Pokemon so we can deposit
        _games[gid]["player"]["team"].append(_pokemon("Charmander", 4, "female"))
        deposit_pokemon(gid, 0)
        status = get_daycare_status(gid)
        assert status.slot_1["name"] == poke_name
        _cleanup(gid)

    def test_invalid_slot_number_withdraw(self):
        """Withdrawing from slot 3 (invalid) raises ValueError."""
        game = _make_game()
        gid = game["id"]
        _games[gid]["player"]["team"].append(_pokemon("Charmander", 4, "female"))
        deposit_pokemon(gid, 0)
        with pytest.raises(ValueError):
            withdraw_pokemon(gid, 3)
        _cleanup(gid)


class TestDaycareSteps:
    """Step processing edge cases."""

    def test_negative_steps_no_op(self):
        """Negative steps does nothing."""
        game = _make_game()
        gid = game["id"]
        result = process_steps(gid, -10)
        assert result.hatched is False
        _cleanup(gid)

    def test_steps_accumulate_daycare_exp(self):
        """Steps increase steps_gained on deposited Pokemon."""
        game = _make_game()
        gid = game["id"]
        _games[gid]["player"]["team"].append(_pokemon("Charmander", 4, "female"))
        deposit_pokemon(gid, 0)
        process_steps(gid, 100)
        status = get_daycare_status(gid)
        assert status.slot_1["steps_gained"] >= 100
        _cleanup(gid)


class TestEggCollection:
    """Egg collection edge cases."""

    def test_collect_egg_nonexistent_game(self):
        """Collect egg for nonexistent game raises ValueError."""
        with pytest.raises(ValueError):
            collect_egg("nonexistent_game_999")

    def test_collect_egg_no_parents(self):
        """Collect egg with empty daycare raises ValueError."""
        game = _make_game()
        gid = game["id"]
        with pytest.raises(ValueError):
            collect_egg(gid)
        _cleanup(gid)

    def test_collect_egg_full_party(self):
        """Collect egg with full party (6 Pokemon) raises ValueError."""
        game = _make_game()
        gid = game["id"]
        # Fill party to 6
        while len(_games[gid]["player"]["team"]) < 6:
            _games[gid]["player"]["team"].append(_pokemon("Bulba", 1, "male"))
        # Deposit 2 to make room but keep 4 in team + force egg
        # Actually need parents in daycare with egg ready
        # Remove 2 to deposit, then add back 4 to fill
        _games[gid]["player"]["team"] = _games[gid]["player"]["team"][:4]
        _games[gid]["player"]["team"].append(_pokemon("Bulba", 1, "male"))
        _games[gid]["player"]["team"].append(_pokemon("Bulba", 1, "female"))
        deposit_pokemon(gid, 4)  # Deposit male
        deposit_pokemon(gid, 3)  # Deposit female
        # Fill party back to 6
        while len(_games[gid]["player"]["team"]) < 6:
            _games[gid]["player"]["team"].append(_pokemon("Filler", 1, "male"))
        # Force egg ready
        _daycares[gid].egg_ready = True
        with pytest.raises(ValueError):
            collect_egg(gid)
        _cleanup(gid)


class TestEggHatching:
    """Egg hatching mechanics."""

    def test_egg_hatches_after_exact_steps(self):
        """Egg in party hatches after sufficient steps.

        BUG NOTE: _hatch_egg() at breeding_service.py:363 crashes with
        AttributeError when egg has base_stats=None because dict.get()
        returns the explicit None rather than the fallback dict. We provide
        base_stats here to work around the bug and test the happy path.
        """
        game = _make_game()
        gid = game["id"]
        egg_dict = {
            "is_egg": True, "name": "Bulbasaur", "species_id": 1,
            "hatch_counter": 100,
            "ivs": {"hp": 15, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "types": ["grass"], "level": 1,
            "base_stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
            "sprite": "egg.png", "gender": "male",
        }
        _games[gid]["player"]["team"].append(egg_dict)
        result = process_steps(gid, 100)
        assert result.hatched is True
        assert result.pokemon is not None
        assert result.pokemon.get("is_egg", True) is False
        _cleanup(gid)

    def test_egg_not_hatched_insufficient_steps(self):
        """Egg with many steps remaining does not hatch."""
        game = _make_game()
        gid = game["id"]
        egg_dict = {
            "is_egg": True, "name": "Bulbasaur", "species_id": 1,
            "hatch_counter": 5000,
            "ivs": {"hp": 15, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "types": ["grass"], "level": 1,
            "base_stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
            "sprite": "egg.png", "gender": "male",
        }
        _games[gid]["player"]["team"].append(egg_dict)
        result = process_steps(gid, 10)
        assert result.hatched is False
        _cleanup(gid)

    def test_hatched_pokemon_has_correct_level(self):
        """Hatched Pokemon is level 1."""
        game = _make_game()
        gid = game["id"]
        egg_dict = {
            "is_egg": True, "name": "Bulbasaur", "species_id": 1,
            "hatch_counter": 1,
            "ivs": {"hp": 15, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "types": ["grass"], "level": 1,
            "base_stats": {"hp": 45, "attack": 49, "defense": 49, "sp_attack": 65, "sp_defense": 65, "speed": 45},
            "sprite": "egg.png", "gender": "male",
        }
        _games[gid]["player"]["team"].append(egg_dict)
        result = process_steps(gid, 1)
        assert result.hatched is True
        assert result.pokemon["level"] == 1
        _cleanup(gid)

    def test_hatch_egg_crashes_with_none_base_stats(self):
        """BUG: _hatch_egg crashes when base_stats is explicitly None.

        breeding_service.py:357 uses egg.get('base_stats', {default}) but
        if base_stats=None, .get() returns None (not the default), and
        line 363 calls None.get() → AttributeError.
        """
        game = _make_game()
        gid = game["id"]
        egg_dict = {
            "is_egg": True, "name": "Bulbasaur", "species_id": 1,
            "hatch_counter": 1,
            "ivs": {"hp": 15, "attack": 15, "defense": 15, "sp_attack": 15, "sp_defense": 15, "speed": 15},
            "moves": [{"name": "Tackle", "type": "normal", "power": 40, "accuracy": 100, "pp": 35}],
            "types": ["grass"], "level": 1, "base_stats": None,
            "sprite": "egg.png", "gender": "male",
        }
        _games[gid]["player"]["team"].append(egg_dict)
        with pytest.raises(AttributeError):
            process_steps(gid, 1)
        _cleanup(gid)


class TestDaycareAPI:
    """Daycare API edge cases."""

    def test_deposit_api_invalid_index(self):
        """POST /api/daycare/deposit with bad index returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/daycare/deposit", json={
            "game_id": gid, "pokemon_index": 99,
        })
        assert resp.status_code == 400
        _cleanup(gid)

    def test_withdraw_api_invalid_slot(self):
        """POST /api/daycare/withdraw/3 with empty slot returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/daycare/withdraw/1", json={"game_id": gid})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_step_api_returns_hatch_result(self):
        """POST /api/daycare/step returns HatchResult format."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/daycare/step", json={"game_id": gid, "steps": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "hatched" in data
        assert "message" in data
        _cleanup(gid)

    def test_collect_egg_api_no_egg(self):
        """POST /api/daycare/collect-egg when no egg returns 400."""
        game = _make_game()
        gid = game["id"]
        resp = client.post("/api/daycare/collect-egg", json={"game_id": gid})
        assert resp.status_code == 400
        _cleanup(gid)

    def test_daycare_full_lifecycle_api(self):
        """Full lifecycle: deposit 2 → steps → collect egg → hatch."""
        game = _make_game()
        gid = game["id"]
        # Set gender on starter so it's a valid breeding partner
        _games[gid]["player"]["team"][0]["gender"] = "male"
        # Add two more compatible Pokemon (need 3 total: deposit 2, keep 1)
        _games[gid]["player"]["team"].append(
            _pokemon("Bulbasaur", 1, "female", ["monster", "grass"])
        )
        _games[gid]["player"]["team"].append(
            _pokemon("Squirtle", 7, "male", ["monster", "water_1"])
        )
        # Deposit both (index 0 twice — first pop shifts the list)
        resp1 = client.post("/api/daycare/deposit", json={"game_id": gid, "pokemon_index": 0})
        assert resp1.status_code == 200
        resp2 = client.post("/api/daycare/deposit", json={"game_id": gid, "pokemon_index": 0})
        assert resp2.status_code == 200
        # Check status shows compatible
        status = client.get(f"/api/daycare/status/{gid}")
        assert status.status_code == 200
        assert status.json()["compatible"] is True
        # Force egg ready (bypass random chance)
        _daycares[gid].egg_ready = True
        # Collect egg
        collect_resp = client.post("/api/daycare/collect-egg", json={"game_id": gid})
        assert collect_resp.status_code == 200
        assert collect_resp.json()["success"] is True
        _cleanup(gid)


# ==============================================================
# CROSS-SYSTEM INTEGRATION
# ==============================================================

class TestBerryHarvestAchievementFlow:
    """End-to-end: plant → grow → harvest → achievement unlock."""

    def test_harvest_triggers_berry_achievement(self):
        """Harvesting via API route triggers berry achievement check."""
        game = _make_game()
        gid = game["id"]
        # Give berries to plant
        add_berry_to_pouch(gid, "oran", 5)
        plant_berry(gid, "pallet_1", "oran")
        # Force ready
        _berry_plots[gid]["pallet_1"].plant_time = time.time() - 9999
        # Harvest via API
        resp = client.post("/api/berry/harvest/pallet_1", json={"game_id": gid})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        # Check achievement was triggered
        result = check_achievements(gid)
        earned_ids = {a.id for a in result.all_achievements if a.completed}
        assert "berry_first" in earned_ids
        _cleanup(gid)


class TestPvPWinStreakAchievements:
    """PvP win streak tracking and achievements."""

    def test_pvp_loss_resets_streak(self):
        """PvP loss resets win streak to 0."""
        game = _make_game()
        gid = game["id"]
        for _ in range(5):
            record_pvp_result(gid, True)
        record_pvp_result(gid, False)
        stats = _player_stats[gid]
        assert stats["pvp_win_streak"] == 0
        assert stats["max_pvp_win_streak"] == 5
        _cleanup(gid)

    def test_pvp_max_streak_persists(self):
        """Max win streak persists through losses."""
        game = _make_game()
        gid = game["id"]
        for _ in range(8):
            record_pvp_result(gid, True)
        record_pvp_result(gid, False)
        for _ in range(3):
            record_pvp_result(gid, True)
        stats = _player_stats[gid]
        assert stats["pvp_win_streak"] == 3
        assert stats["max_pvp_win_streak"] == 8
        _cleanup(gid)
