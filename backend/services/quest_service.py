"""Quest system, story flags, and progression service."""
from __future__ import annotations

from copy import deepcopy
from typing import Optional

from ..models.quest import (
    Quest,
    QuestCheckResult,
    QuestCompleteResult,
    QuestObjective,
    QuestReward,
    StoryFlags,
)
from .game_service import get_game

# In-memory stores (per game_id)
_player_quests: dict[str, list[Quest]] = {}
_story_flags: dict[str, dict[str, bool]] = {}

# --- Seed quest definitions ---
_QUEST_DEFS: list[dict] = [
    {
        "id": "new_adventure",
        "name": "A New Adventure",
        "description": "Choose your starter Pokemon and begin your journey!",
        "type": "main",
        "objectives": [
            {"id": "choose_starter", "description": "Choose a starter Pokemon", "type": "collect_item", "target": "starter", "required_progress": 1},
        ],
        "rewards": {"money": 500, "items": [{"item_id": 7, "quantity": 5}], "unlock_flags": ["has_starter"]},
        "prerequisite_quests": [],
        "status": "active",
    },
    {
        "id": "oaks_parcel",
        "name": "Oak's Parcel",
        "description": "Buy a parcel at Viridian Mart and deliver it to Professor Oak.",
        "type": "main",
        "objectives": [
            {"id": "visit_viridian", "description": "Visit Viridian City", "type": "visit_location", "target": "viridian_city", "required_progress": 1},
            {"id": "deliver_parcel", "description": "Deliver the parcel to Professor Oak", "type": "deliver_item", "target": "oaks_lab", "required_progress": 1},
        ],
        "rewards": {"money": 1000, "unlock_flags": ["has_pokedex", "oak_parcel_delivered"]},
        "prerequisite_quests": ["new_adventure"],
    },
    {
        "id": "boulder_badge",
        "name": "The Boulder Badge",
        "description": "Defeat Brock at Pewter City Gym to earn the Boulder Badge.",
        "type": "main",
        "objectives": [
            {"id": "defeat_brock", "description": "Defeat Gym Leader Brock", "type": "defeat_gym", "target": "pewter_gym", "required_progress": 1},
        ],
        "rewards": {"money": 2000, "unlock_flags": ["badge_boulder"]},
        "prerequisite_quests": ["oaks_parcel"],
    },
    {
        "id": "cascade_badge",
        "name": "The Cascade Badge",
        "description": "Defeat Misty at Cerulean City Gym to earn the Cascade Badge.",
        "type": "main",
        "objectives": [
            {"id": "defeat_misty", "description": "Defeat Gym Leader Misty", "type": "defeat_gym", "target": "cerulean_gym", "required_progress": 1},
        ],
        "rewards": {"money": 3000, "unlock_flags": ["badge_cascade"]},
        "prerequisite_quests": ["boulder_badge"],
    },
    {
        "id": "rival_showdown_1",
        "name": "Rival Showdown I",
        "description": "Your rival is waiting on Route 2. Defeat them to prove your strength!",
        "type": "main",
        "objectives": [
            {"id": "defeat_rival_route2", "description": "Defeat your rival on Route 2", "type": "defeat_trainer", "target": "rival_route2", "required_progress": 1},
        ],
        "rewards": {"money": 1500, "unlock_flags": ["rival_defeated_route2"]},
        "prerequisite_quests": ["oaks_parcel"],
    },
    {
        "id": "nugget_bridge",
        "name": "Nugget Bridge Challenge",
        "description": "Defeat all 5 trainers on Route 24's Nugget Bridge to earn a prize!",
        "type": "main",
        "objectives": [
            {"id": "defeat_bridge_trainers", "description": "Defeat 5 trainers on Nugget Bridge", "type": "defeat_trainer", "target": "nugget_bridge", "required_progress": 5},
        ],
        "rewards": {"money": 500, "items": [{"item_id": 51, "quantity": 1}], "unlock_flags": ["nugget_bridge_complete"]},
        "prerequisite_quests": ["cascade_badge"],
    },
    {
        "id": "bill_rescue",
        "name": "Help Bill!",
        "description": "Visit Bill's House on Route 25 and help him transform back from a Pokemon!",
        "type": "main",
        "objectives": [
            {"id": "rescue_bill", "description": "Help Bill transform back to human", "type": "collect_item", "target": "bill_rescue", "required_progress": 1},
        ],
        "rewards": {"money": 300, "items": [{"item_id": 52, "quantity": 1}], "unlock_flags": ["bill_rescued", "has_ss_ticket"]},
        "prerequisite_quests": ["nugget_bridge"],
    },
    {
        "id": "rocket_cerulean",
        "name": "The Cerulean Robbery",
        "description": "A Team Rocket grunt has robbed a house in Cerulean City. Find and defeat the grunt!",
        "type": "side",
        "objectives": [
            {"id": "defeat_rocket_cerulean", "description": "Defeat the Rocket Grunt in Cerulean City", "type": "defeat_trainer", "target": "rocket_grunt_cerulean", "required_progress": 1},
        ],
        "rewards": {"money": 500, "exp": 200, "unlock_flags": ["rocket_cerulean_resolved"]},
        "prerequisite_quests": ["cascade_badge"],
    },
    {
        "id": "ss_anne_adventure",
        "name": "S.S. Anne Adventure",
        "description": "Board the S.S. Anne, help the seasick captain, and receive HM01 Cut!",
        "type": "main",
        "objectives": [
            {"id": "board_ss_anne", "description": "Board the S.S. Anne", "type": "visit_location", "target": "ss_anne", "required_progress": 1},
            {"id": "help_captain", "description": "Help the seasick captain", "type": "collect_item", "target": "captain_helped", "required_progress": 1},
            {"id": "receive_hm_cut", "description": "Receive HM01 Cut", "type": "collect_item", "target": "hm01_cut", "required_progress": 1},
        ],
        "rewards": {"money": 3000, "items": [{"item_id": 53, "quantity": 1}], "unlock_flags": ["ss_anne_complete", "has_hm_cut"]},
        "prerequisite_quests": ["bill_rescue"],
    },
    {
        "id": "thunder_badge",
        "name": "The Thunder Badge",
        "description": "Solve Lt. Surge's trash can puzzle and defeat him to earn the Thunder Badge!",
        "type": "main",
        "objectives": [
            {"id": "solve_puzzle", "description": "Solve the trash can puzzle", "type": "collect_item", "target": "trash_puzzle_solved", "required_progress": 1},
            {"id": "defeat_surge", "description": "Defeat Gym Leader Lt. Surge", "type": "defeat_gym", "target": "vermilion_gym", "required_progress": 1},
        ],
        "rewards": {"money": 4000, "unlock_flags": ["badge_thunder"]},
        "prerequisite_quests": ["ss_anne_adventure"],
    },
    {
        "id": "pokemon_tower",
        "name": "The Haunted Tower",
        "description": "Explore Pokemon Tower in Lavender Town and rescue Mr. Fuji from Team Rocket!",
        "type": "main",
        "objectives": [
            {"id": "enter_tower", "description": "Enter Pokemon Tower", "type": "visit_location", "target": "pokemon_tower_1f", "required_progress": 1},
            {"id": "rescue_fuji", "description": "Rescue Mr. Fuji", "type": "collect_item", "target": "fuji_rescued", "required_progress": 1},
        ],
        "rewards": {"money": 5000, "items": [{"item_id": 55, "quantity": 1}], "unlock_flags": ["fuji_rescued", "has_poke_flute"]},
        "prerequisite_quests": ["thunder_badge"],
    },
    {
        "id": "snorlax_road",
        "name": "Sleeping Snorlax",
        "description": "A sleeping Snorlax blocks Route 12. Find a way to wake it!",
        "type": "side",
        "objectives": [
            {"id": "wake_snorlax", "description": "Wake the sleeping Snorlax", "type": "collect_item", "target": "snorlax_awakened", "required_progress": 1},
        ],
        "rewards": {"money": 1000, "exp": 500, "unlock_flags": ["snorlax_cleared"]},
        "prerequisite_quests": ["pokemon_tower"],
    },
    {
        "id": "rainbow_badge",
        "name": "The Rainbow Badge",
        "description": "Defeat Erika at Celadon Gym to earn the Rainbow Badge!",
        "type": "main",
        "objectives": [
            {"id": "defeat_erika", "description": "Defeat Gym Leader Erika", "type": "defeat_gym", "target": "celadon_gym", "required_progress": 1},
        ],
        "rewards": {"money": 5000, "unlock_flags": ["badge_rainbow"]},
        "prerequisite_quests": ["pokemon_tower"],
    },
    {
        "id": "team_rocket_hideout",
        "name": "Team Rocket's Secret Hideout",
        "description": "Infiltrate Team Rocket's hideout beneath the Game Corner and defeat Giovanni!",
        "type": "main",
        "objectives": [
            {"id": "defeat_giovanni", "description": "Defeat Giovanni in the Rocket Hideout", "type": "defeat_boss", "target": "giovanni", "required_progress": 1},
        ],
        "rewards": {"money": 8000, "items": [{"item_id": 54, "quantity": 1}], "unlock_flags": ["giovanni_defeated", "saffron_gate_open"]},
        "prerequisite_quests": ["rainbow_badge"],
    },
    {
        "id": "silph_co_rescue",
        "name": "Silph Co. Under Siege",
        "description": "Infiltrate Silph Co. and defeat Giovanni to free the building from Team Rocket!",
        "type": "main",
        "objectives": [
            {"id": "defeat_giovanni_silph", "description": "Defeat Giovanni at Silph Co.", "type": "defeat_boss", "target": "giovanni_silph", "required_progress": 1},
        ],
        "rewards": {"money": 10000, "items": [{"item_id": 10, "quantity": 1}], "unlock_flags": ["silph_co_cleared", "has_master_ball"]},
        "prerequisite_quests": ["team_rocket_hideout"],
    },
    {
        "id": "marsh_badge",
        "name": "The Marsh Badge",
        "description": "Defeat Sabrina at Saffron Gym to earn the Marsh Badge!",
        "type": "main",
        "objectives": [
            {"id": "defeat_sabrina", "description": "Defeat Gym Leader Sabrina", "type": "defeat_gym", "target": "saffron_gym", "required_progress": 1},
        ],
        "rewards": {"money": 6000, "unlock_flags": ["badge_marsh"]},
        "prerequisite_quests": ["silph_co_rescue"],
    },
    {
        "id": "fighting_dojo",
        "name": "The Fighting Dojo",
        "description": "Defeat all trainers in the Fighting Dojo to earn a Fighting-type Pokemon!",
        "type": "side",
        "objectives": [
            {"id": "defeat_dojo", "description": "Defeat the Karate Master", "type": "defeat_trainer", "target": "dojo_master", "required_progress": 1},
        ],
        "rewards": {"money": 2000},
        "prerequisite_quests": [],
    },
    {
        "id": "soul_badge",
        "name": "The Soul Badge",
        "description": "Navigate Koga's invisible wall maze and defeat him to earn the Soul Badge!",
        "type": "main",
        "objectives": [
            {"id": "defeat_koga", "description": "Defeat Gym Leader Koga", "type": "defeat_gym", "target": "fuchsia_gym", "required_progress": 1},
        ],
        "rewards": {"money": 6500, "unlock_flags": ["badge_soul"]},
        "prerequisite_quests": ["marsh_badge"],
    },
    {
        "id": "safari_zone",
        "name": "Safari Zone Adventure",
        "description": "Explore the Safari Zone to find rare Pokemon and HM03 Surf!",
        "type": "side",
        "objectives": [
            {"id": "explore_safari", "description": "Explore the Safari Zone", "type": "visit_location", "target": "safari_zone_area_1", "required_progress": 1},
        ],
        "rewards": {"money": 3000, "items": [{"item_id": 61, "quantity": 1}], "unlock_flags": ["has_hm_surf"]},
        "prerequisite_quests": [],
    },
    {
        "id": "wardens_teeth",
        "name": "The Warden's Gold Teeth",
        "description": "Find the Warden's Gold Teeth in the Safari Zone and return them for HM04 Strength!",
        "type": "side",
        "objectives": [
            {"id": "find_teeth", "description": "Find the Gold Teeth in Safari Zone", "type": "collect_item", "target": "gold_teeth", "required_progress": 1},
            {"id": "return_teeth", "description": "Return Gold Teeth to the Warden", "type": "deliver_item", "target": "wardens_house", "required_progress": 1},
        ],
        "rewards": {"money": 2000, "items": [{"item_id": 62, "quantity": 1}], "unlock_flags": ["has_hm_strength"]},
        "prerequisite_quests": ["safari_zone"],
    },
    {
        "id": "pokemon_mansion",
        "name": "Pokemon Mansion Mystery",
        "description": "Explore the abandoned Pokemon Mansion on Cinnabar Island and find the Secret Key!",
        "type": "side",
        "objectives": [
            {"id": "explore_mansion", "description": "Explore the Pokemon Mansion", "type": "visit_location", "target": "pokemon_mansion_1f", "required_progress": 1},
            {"id": "find_secret_key", "description": "Find the Secret Key", "type": "collect_item", "target": "secret_key", "required_progress": 1},
        ],
        "rewards": {"money": 4000, "items": [{"item_id": 64, "quantity": 1}], "unlock_flags": ["has_secret_key"]},
        "prerequisite_quests": [],
    },
    {
        "id": "volcano_badge",
        "name": "The Volcano Badge",
        "description": "Answer Blaine's quiz and defeat him to earn the Volcano Badge!",
        "type": "main",
        "objectives": [
            {"id": "defeat_blaine", "description": "Defeat Gym Leader Blaine", "type": "defeat_gym", "target": "cinnabar_gym", "required_progress": 1},
        ],
        "rewards": {"money": 7000, "unlock_flags": ["badge_volcano"]},
        "prerequisite_quests": ["soul_badge"],
    },
    {
        "id": "earth_badge",
        "name": "The Earth Badge",
        "description": "Defeat Giovanni at Viridian Gym to earn the final Earth Badge!",
        "type": "main",
        "objectives": [
            {"id": "defeat_giovanni_gym", "description": "Defeat Gym Leader Giovanni", "type": "defeat_gym", "target": "viridian_gym", "required_progress": 1},
        ],
        "rewards": {"money": 8000, "unlock_flags": ["badge_earth", "all_badges"]},
        "prerequisite_quests": ["volcano_badge"],
    },
    {
        "id": "victory_road",
        "name": "Victory Road",
        "description": "Traverse Victory Road to reach the Indigo Plateau and the Pokemon League!",
        "type": "main",
        "objectives": [
            {"id": "traverse_victory_road", "description": "Traverse Victory Road", "type": "visit_location", "target": "indigo_plateau", "required_progress": 1},
        ],
        "rewards": {"money": 5000, "unlock_flags": ["reached_indigo_plateau"]},
        "prerequisite_quests": ["earth_badge"],
    },
    {
        "id": "elite_four",
        "name": "The Elite Four",
        "description": "Defeat the Elite Four — Lorelei, Bruno, Agatha, and Lance — at the Indigo Plateau!",
        "type": "main",
        "objectives": [
            {"id": "defeat_lorelei", "description": "Defeat Lorelei", "type": "defeat_trainer", "target": "lorelei", "required_progress": 1},
            {"id": "defeat_bruno", "description": "Defeat Bruno", "type": "defeat_trainer", "target": "bruno", "required_progress": 1},
            {"id": "defeat_agatha", "description": "Defeat Agatha", "type": "defeat_trainer", "target": "agatha", "required_progress": 1},
            {"id": "defeat_lance", "description": "Defeat Lance", "type": "defeat_trainer", "target": "lance", "required_progress": 1},
        ],
        "rewards": {"money": 20000, "unlock_flags": ["elite_four_defeated"]},
        "prerequisite_quests": ["victory_road"],
    },
    {
        "id": "champion",
        "name": "The Champion",
        "description": "Defeat the Champion and enter the Hall of Fame to become the Pokemon League Champion!",
        "type": "main",
        "objectives": [
            {"id": "defeat_champion", "description": "Defeat the Champion", "type": "defeat_trainer", "target": "champion", "required_progress": 1},
        ],
        "rewards": {"money": 50000, "unlock_flags": ["pokemon_league_champion", "hall_of_fame"]},
        "prerequisite_quests": ["elite_four"],
    },
    {
        "id": "legendary_articuno",
        "name": "The Legendary Articuno",
        "description": "Deep in the Seafoam Islands, the legendary ice bird Articuno awaits!",
        "type": "side",
        "objectives": [
            {"id": "find_articuno", "description": "Find Articuno in Seafoam Islands B2F", "type": "visit_location", "target": "seafoam_islands_b2f", "required_progress": 1},
            {"id": "catch_articuno", "description": "Catch or defeat Articuno", "type": "defeat_trainer", "target": "articuno", "required_progress": 1},
        ],
        "rewards": {"money": 10000, "unlock_flags": ["articuno_encountered"]},
        "prerequisite_quests": [],
    },
    {
        "id": "legendary_zapdos",
        "name": "The Legendary Zapdos",
        "description": "The abandoned Power Plant hums with electricity — Zapdos roosts within!",
        "type": "side",
        "objectives": [
            {"id": "find_zapdos", "description": "Find Zapdos in the Power Plant", "type": "visit_location", "target": "power_plant", "required_progress": 1},
            {"id": "catch_zapdos", "description": "Catch or defeat Zapdos", "type": "defeat_trainer", "target": "zapdos", "required_progress": 1},
        ],
        "rewards": {"money": 10000, "unlock_flags": ["zapdos_encountered"]},
        "prerequisite_quests": [],
    },
    {
        "id": "legendary_moltres",
        "name": "The Legendary Moltres",
        "description": "A hidden chamber in Victory Road holds the legendary fire bird Moltres!",
        "type": "side",
        "objectives": [
            {"id": "find_moltres", "description": "Find Moltres in Victory Road", "type": "visit_location", "target": "moltres_chamber", "required_progress": 1},
            {"id": "catch_moltres", "description": "Catch or defeat Moltres", "type": "defeat_trainer", "target": "moltres", "required_progress": 1},
        ],
        "rewards": {"money": 10000, "unlock_flags": ["moltres_encountered"]},
        "prerequisite_quests": [],
    },
]


def _init_quests(game_id: str) -> list[Quest]:
    """Initialize quest list for a new player."""
    quests = []
    for qdef in _QUEST_DEFS:
        q = Quest(
            id=qdef["id"],
            name=qdef["name"],
            description=qdef["description"],
            type=qdef.get("type", "main"),
            objectives=[QuestObjective(**o) for o in qdef["objectives"]],
            rewards=QuestReward(**qdef.get("rewards", {})),
            prerequisite_quests=qdef.get("prerequisite_quests", []),
            status=qdef.get("status", "locked"),
        )
        quests.append(q)
    _player_quests[game_id] = quests
    return quests


def _get_quests(game_id: str) -> list[Quest]:
    if game_id not in _player_quests:
        return _init_quests(game_id)
    return _player_quests[game_id]


def _get_flags(game_id: str) -> dict[str, bool]:
    if game_id not in _story_flags:
        _story_flags[game_id] = {}
    return _story_flags[game_id]


# --- Story flags ---

def get_story_flags(game_id: str) -> dict[str, bool]:
    return _get_flags(game_id)


def get_story_flag(game_id: str, flag_name: str) -> bool:
    return _get_flags(game_id).get(flag_name, False)


def set_story_flag(game_id: str, flag_name: str, value: bool = True) -> dict[str, bool]:
    flags = _get_flags(game_id)
    flags[flag_name] = value
    return flags


# --- Quest operations ---

def get_all_quests(game_id: str) -> list[Quest]:
    """Return all quests with current status for the player."""
    game = get_game(game_id)
    if game is None:
        return []
    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)
    return quests


def get_quest(game_id: str, quest_id: str) -> Optional[Quest]:
    quests = _get_quests(game_id)
    for q in quests:
        if q.id == quest_id:
            return q
    return None


def _refresh_quest_status(game_id: str, quests: list[Quest]) -> None:
    """Unlock quests whose prerequisites are all completed."""
    completed_ids = {q.id for q in quests if q.status == "completed"}
    for q in quests:
        if q.status == "locked":
            if all(pid in completed_ids for pid in q.prerequisite_quests):
                q.status = "active"


def check_quest_progress(game_id: str, event_type: str, event_data: dict) -> QuestCheckResult:
    """Check if any active quest objectives were advanced by this event."""
    game = get_game(game_id)
    if game is None:
        return QuestCheckResult()

    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)

    updated: list[Quest] = []
    completed: list[Quest] = []
    newly_active: list[Quest] = []

    for quest in quests:
        if quest.status != "active":
            continue

        quest_updated = False
        for obj in quest.objectives:
            if obj.type == event_type and obj.current_progress < obj.required_progress:
                # Match target
                target_key = _get_target_key(event_type)
                if target_key and event_data.get(target_key) == obj.target:
                    obj.current_progress = min(obj.current_progress + 1, obj.required_progress)
                    quest_updated = True

        if quest_updated:
            updated.append(quest)
            # Check if all objectives complete
            if all(o.current_progress >= o.required_progress for o in quest.objectives):
                _complete_quest(game_id, quest)
                completed.append(quest)

    # Check for newly unlocked quests
    if completed:
        _refresh_quest_status(game_id, quests)
        for q in quests:
            if q.status == "active" and q not in updated:
                newly_active.append(q)

    return QuestCheckResult(
        updated_quests=updated,
        completed_quests=completed,
        newly_active_quests=newly_active,
    )


def _get_target_key(event_type: str) -> Optional[str]:
    """Map event type to the key in event_data that contains the target."""
    mapping = {
        "defeat_trainer": "trainer_id",
        "visit_location": "map_id",
        "collect_item": "item_id",
        "deliver_item": "location_id",
        "catch_pokemon": "species_id",
        "defeat_gym": "gym_id",
    }
    return mapping.get(event_type)


def _complete_quest(game_id: str, quest: Quest) -> None:
    """Mark quest as completed and apply rewards."""
    quest.status = "completed"

    # Set story flags from rewards
    for flag in quest.rewards.unlock_flags:
        set_story_flag(game_id, flag)

    # Apply money reward
    if quest.rewards.money > 0:
        game = get_game(game_id)
        if game:
            money = game["player"].get("money", 0)
            game["player"]["money"] = money + quest.rewards.money

    # Apply item rewards
    if quest.rewards.items:
        game = get_game(game_id)
        if game:
            inventory = game["player"].setdefault("inventory", [])
            for item_reward in quest.rewards.items:
                found = False
                for entry in inventory:
                    if entry.get("item_id") == item_reward["item_id"]:
                        entry["quantity"] += item_reward["quantity"]
                        found = True
                        break
                if not found:
                    inventory.append({"item_id": item_reward["item_id"], "quantity": item_reward["quantity"]})


def complete_quest_manual(game_id: str, quest_id: str) -> Optional[QuestCompleteResult]:
    """Manually mark a quest as complete (for scripted events)."""
    game = get_game(game_id)
    if game is None:
        return None

    quest = get_quest(game_id, quest_id)
    if quest is None or quest.status == "completed":
        return None

    # Force all objectives to complete
    for obj in quest.objectives:
        obj.current_progress = obj.required_progress

    _complete_quest(game_id, quest)

    # Find newly unlocked quests
    quests = _get_quests(game_id)
    _refresh_quest_status(game_id, quests)
    newly_unlocked = [q.id for q in quests if q.status == "active" and q.id != quest_id]

    return QuestCompleteResult(
        quest=quest,
        rewards_given=quest.rewards,
        newly_unlocked_quests=newly_unlocked,
    )


# --- Area gating ---

def check_area_accessible(game_id: str, map_id: str, required_flag: Optional[str] = None) -> dict:
    """Check if a player can enter a map based on story flags."""
    if required_flag is None:
        return {"accessible": True, "reason": None}

    has_flag = get_story_flag(game_id, required_flag)
    if has_flag:
        return {"accessible": True, "reason": None}

    # Generate human-readable reason
    flag_reasons = {
        "has_starter": "You need to choose a starter Pokemon first",
        "has_pokedex": "You need to get the Pokedex from Professor Oak",
        "oak_parcel_delivered": "You need to deliver Oak's Parcel first",
        "badge_boulder": "You need the Boulder Badge to pass",
        "badge_cascade": "You need the Cascade Badge to pass",
        "rival_defeated_route2": "You need to defeat your rival on Route 2 first",
        "nugget_bridge_complete": "You need to complete the Nugget Bridge Challenge first",
        "bill_rescued": "You need to help Bill first",
        "has_ss_ticket": "You need the S.S. Ticket to board",
        "ss_anne_complete": "You need to complete the S.S. Anne adventure first",
        "has_hm_cut": "You need HM01 Cut to pass",
        "badge_thunder": "You need the Thunder Badge to pass",
        "rocket_cerulean_resolved": "You need to defeat the Rocket Grunt first",
        "fuji_rescued": "You need to rescue Mr. Fuji first",
        "has_poke_flute": "You need the Poke Flute",
        "snorlax_cleared": "A sleeping Snorlax blocks the way",
        "badge_rainbow": "You need the Rainbow Badge to pass",
        "badge_soul": "You need the Soul Badge to pass",
        "badge_marsh": "You need the Marsh Badge to pass",
        "has_hm_surf": "You need HM03 Surf",
        "has_hm_strength": "You need HM04 Strength",
        "has_secret_key": "You need the Secret Key to enter Blaine's Gym",
        "badge_volcano": "You need the Volcano Badge to pass",
        "badge_earth": "You need the Earth Badge to pass",
        "all_badges": "You need all 8 badges",
        "reached_indigo_plateau": "You need to reach the Indigo Plateau",
    }
    reason = flag_reasons.get(required_flag, f"You need to complete a requirement: {required_flag}")
    return {"accessible": False, "reason": reason}
