"""Leaderboard, player stats, and achievement system service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..models.leaderboard import (
    Achievement,
    AchievementCheckResult,
    AchievementNotification,
    PlayerStats,
    PokedexLeaderboardEntry,
    PvPLeaderboardEntry,
    TrainerLeaderboardEntry,
)
from .game_service import get_game, _games
from .gym_service import _earned_badges
from .pokedex_service import get_pokedex_stats
from .pvp_service import _pvp_history

# In-memory stores
_player_stats: dict[str, dict] = {}  # player_id -> stats counters
_achievements: dict[str, dict[str, Achievement]] = {}  # player_id -> {id: Achievement}
_notification_queue: dict[str, list[AchievementNotification]] = {}  # player_id -> [notifications]

# Achievement definitions with tiers, categories, progress targets, and rewards
_ACHIEVEMENT_DEFS = [
    # --- Collection (catch/pokedex) ---
    {"id": "first_steps", "name": "First Steps", "description": "Catch your first Pokemon",
     "category": "collection", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},
    {"id": "collector", "name": "Collector", "description": "Catch 10 different species",
     "category": "collection", "tier": "silver", "target": 10, "reward_type": "coins", "reward_amount": 50},
    {"id": "gotta_catch_em_all", "name": "Gotta Catch 'Em All", "description": "Complete 50% of the Pokedex",
     "category": "collection", "tier": "gold", "target": 50, "reward_type": "coins", "reward_amount": 200},
    {"id": "pokemon_master", "name": "Pokemon Master", "description": "Complete 100% of the Pokedex",
     "category": "collection", "tier": "platinum", "target": 100, "reward_type": "coins", "reward_amount": 500},
    {"id": "catch_50", "name": "Catch Fever", "description": "Catch 50 total Pokemon",
     "category": "collection", "tier": "silver", "target": 50, "reward_type": "coins", "reward_amount": 100},
    {"id": "catch_100", "name": "Pokemon Ranger", "description": "Catch 100 total Pokemon",
     "category": "collection", "tier": "gold", "target": 100, "reward_type": "coins", "reward_amount": 300},

    # --- Battle ---
    {"id": "battle_tested", "name": "Battle Tested", "description": "Win 10 PvP battles",
     "category": "battle", "tier": "silver", "target": 10, "reward_type": "coins", "reward_amount": 50},
    {"id": "unbeatable", "name": "Unbeatable", "description": "Win 10 PvP battles in a row",
     "category": "battle", "tier": "platinum", "target": 10, "reward_type": "coins", "reward_amount": 500},
    {"id": "first_victory", "name": "First Victory", "description": "Win your first battle",
     "category": "battle", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},
    {"id": "battle_veteran", "name": "Battle Veteran", "description": "Win 25 battles",
     "category": "battle", "tier": "silver", "target": 25, "reward_type": "coins", "reward_amount": 100},
    {"id": "battle_legend", "name": "Battle Legend", "description": "Win 100 battles",
     "category": "battle", "tier": "gold", "target": 100, "reward_type": "coins", "reward_amount": 300},
    {"id": "trainer_battles_10", "name": "Trainer Rival", "description": "Win 10 trainer battles",
     "category": "battle", "tier": "silver", "target": 10, "reward_type": "coins", "reward_amount": 50},

    # --- Gym / Badges ---
    {"id": "rock_solid", "name": "Rock Solid", "description": "Defeat Brock",
     "category": "gym", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 25},
    {"id": "water_works", "name": "Water Works", "description": "Defeat Misty",
     "category": "gym", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 25},
    {"id": "badge_collector_4", "name": "Rising Star", "description": "Earn 4 gym badges",
     "category": "gym", "tier": "silver", "target": 4, "reward_type": "coins", "reward_amount": 100},
    {"id": "badge_collector_8", "name": "League Challenger", "description": "Earn all 8 gym badges",
     "category": "gym", "tier": "platinum", "target": 8, "reward_type": "coins", "reward_amount": 500},

    # --- Evolution ---
    {"id": "evolve", "name": "Evolve!", "description": "Evolve a Pokemon for the first time",
     "category": "evolution", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},
    {"id": "evolve_5", "name": "Evolution Expert", "description": "Evolve 5 Pokemon",
     "category": "evolution", "tier": "silver", "target": 5, "reward_type": "coins", "reward_amount": 50},
    {"id": "evolve_20", "name": "Evolution Master", "description": "Evolve 20 Pokemon",
     "category": "evolution", "tier": "gold", "target": 20, "reward_type": "coins", "reward_amount": 200},

    # --- Story / Quests ---
    {"id": "quest_1", "name": "Adventurer", "description": "Complete your first quest",
     "category": "story", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},
    {"id": "quest_5", "name": "Quest Seeker", "description": "Complete 5 quests",
     "category": "story", "tier": "silver", "target": 5, "reward_type": "coins", "reward_amount": 50},
    {"id": "quest_all", "name": "Completionist", "description": "Complete all story quests",
     "category": "story", "tier": "platinum", "target": 100, "reward_type": "coins", "reward_amount": 500},

    # --- Legendary ---
    {"id": "legendary_1", "name": "Legendary Encounter", "description": "Catch your first legendary Pokemon",
     "category": "story", "tier": "gold", "target": 1, "reward_type": "coins", "reward_amount": 200},
    {"id": "legendary_all", "name": "Legendary Collector", "description": "Catch all legendary Pokemon",
     "category": "story", "tier": "platinum", "target": 3, "reward_type": "coins", "reward_amount": 500},

    # --- Mini-Games ---
    {"id": "slots_first", "name": "Lucky Spin", "description": "Play the slot machine for the first time",
     "category": "minigame", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 5},
    {"id": "slots_50", "name": "Slot Addict", "description": "Play 50 rounds of slots",
     "category": "minigame", "tier": "silver", "target": 50, "reward_type": "coins", "reward_amount": 50},
    {"id": "quiz_master", "name": "Quiz Master", "description": "Score 10/10 on a quiz",
     "category": "minigame", "tier": "gold", "target": 1, "reward_type": "coins", "reward_amount": 100},
    {"id": "minigame_coins_1000", "name": "High Roller", "description": "Accumulate 1,000 coins",
     "category": "minigame", "tier": "silver", "target": 1000, "reward_type": "coins", "reward_amount": 100},
    {"id": "prize_first", "name": "Winner Winner", "description": "Redeem your first prize",
     "category": "minigame", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},

    # --- Team / Party ---
    {"id": "full_team", "name": "Full Team", "description": "Have 6 Pokemon in your party",
     "category": "collection", "tier": "bronze", "target": 6, "reward_type": "coins", "reward_amount": 15},

    # --- Economy ---
    {"id": "big_spender", "name": "Big Spender", "description": "Spend 10,000 total at shops",
     "category": "economy", "tier": "silver", "target": 10000, "reward_type": "coins", "reward_amount": 50},
    {"id": "mega_spender", "name": "Mega Spender", "description": "Spend 50,000 total at shops",
     "category": "economy", "tier": "gold", "target": 50000, "reward_type": "coins", "reward_amount": 200},

    # --- Speed ---
    {"id": "speed_demon", "name": "Speed Demon", "description": "Beat Brock in under 30 minutes of play time",
     "category": "gym", "tier": "gold", "target": 1, "reward_type": "coins", "reward_amount": 150},

    # --- Berry (stub for Sprint 8) ---
    {"id": "berry_first", "name": "Green Thumb", "description": "Harvest your first berry",
     "category": "farming", "tier": "bronze", "target": 1, "reward_type": "coins", "reward_amount": 10},
    {"id": "berry_50", "name": "Berry Farmer", "description": "Harvest 50 berries",
     "category": "farming", "tier": "silver", "target": 50, "reward_type": "coins", "reward_amount": 50},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_stats(player_id: str) -> dict:
    if player_id not in _player_stats:
        _player_stats[player_id] = {
            "total_pokemon_caught": 0,
            "total_battles_won": 0,
            "total_spent": 0,
            "evolutions": 0,
            "pvp_win_streak": 0,
            "max_pvp_win_streak": 0,
            "quests_completed": 0,
            "legendaries_caught": 0,
            "slots_played": 0,
            "quiz_perfect_scores": 0,
            "prizes_redeemed": 0,
            "berries_harvested": 0,
            "trainer_battles_won": 0,
        }
    return _player_stats[player_id]


def _get_achievements(player_id: str) -> dict[str, Achievement]:
    if player_id not in _achievements:
        _achievements[player_id] = {
            d["id"]: Achievement(
                id=d["id"],
                name=d["name"],
                description=d["description"],
                category=d.get("category", "general"),
                tier=d.get("tier", "bronze"),
                target=d.get("target", 1),
                reward_type=d.get("reward_type"),
                reward_amount=d.get("reward_amount"),
            )
            for d in _ACHIEVEMENT_DEFS
        }
    return _achievements[player_id]


def _get_notification_queue(player_id: str) -> list[AchievementNotification]:
    if player_id not in _notification_queue:
        _notification_queue[player_id] = []
    return _notification_queue[player_id]


def _get_trainer_class(badge_count: int) -> str:
    if badge_count >= 8:
        return "Champion"
    elif badge_count >= 4:
        return "Ace Trainer"
    elif badge_count >= 1:
        return "Pokemon Trainer"
    return "Beginner"


# --- Stats Recording ---

def record_pokemon_caught(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["total_pokemon_caught"] = stats.get("total_pokemon_caught", 0) + 1


def record_battle_won(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["total_battles_won"] = stats.get("total_battles_won", 0) + 1


def record_money_spent(player_id: str, amount: int) -> None:
    stats = _get_stats(player_id)
    stats["total_spent"] = stats.get("total_spent", 0) + amount


def record_evolution(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["evolutions"] = stats.get("evolutions", 0) + 1


def record_pvp_result(player_id: str, won: bool) -> None:
    stats = _get_stats(player_id)
    if won:
        stats["pvp_win_streak"] = stats.get("pvp_win_streak", 0) + 1
        stats["max_pvp_win_streak"] = max(
            stats.get("max_pvp_win_streak", 0), stats["pvp_win_streak"]
        )
    else:
        stats["pvp_win_streak"] = 0


def record_quest_completed(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["quests_completed"] = stats.get("quests_completed", 0) + 1


def record_legendary_caught(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["legendaries_caught"] = stats.get("legendaries_caught", 0) + 1


def record_slots_played(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["slots_played"] = stats.get("slots_played", 0) + 1


def record_quiz_perfect(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["quiz_perfect_scores"] = stats.get("quiz_perfect_scores", 0) + 1


def record_prize_redeemed(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["prizes_redeemed"] = stats.get("prizes_redeemed", 0) + 1


def record_berry_harvested(player_id: str, count: int = 1) -> None:
    stats = _get_stats(player_id)
    stats["berries_harvested"] = stats.get("berries_harvested", 0) + count


def record_trainer_battle_won(player_id: str) -> None:
    stats = _get_stats(player_id)
    stats["trainer_battles_won"] = stats.get("trainer_battles_won", 0) + 1


# --- Player Stats ---

def get_player_stats(player_id: str) -> PlayerStats | None:
    game = get_game(player_id)
    if game is None:
        return None

    raw = _get_stats(player_id)
    badges = list(_earned_badges.get(player_id, set()))
    dex = get_pokedex_stats(player_id)

    pvp_h = _pvp_history.get(player_id, [])
    pvp_wins = sum(1 for h in pvp_h if h.result == "win")
    pvp_losses = sum(1 for h in pvp_h if h.result == "loss")
    total_pvp = pvp_wins + pvp_losses
    win_rate = round(pvp_wins / total_pvp * 100, 1) if total_pvp > 0 else 0.0

    return PlayerStats(
        player_id=player_id,
        player_name=game["player"]["name"],
        play_time_seconds=game.get("play_time_seconds", 0),
        pokedex_seen=dex.seen_count,
        pokedex_caught=dex.caught_count,
        badges_earned=badges,
        pvp_wins=pvp_wins,
        pvp_losses=pvp_losses,
        pvp_win_rate=win_rate,
        total_pokemon_caught=raw.get("total_pokemon_caught", 0),
        total_battles_won=raw.get("total_battles_won", 0),
        trainer_class=_get_trainer_class(len(badges)),
    )


# --- Leaderboards ---

def _clamp_limit(limit: int) -> int:
    """H1: Validate and clamp leaderboard limit to [1, 100]."""
    return max(1, min(limit, 100))


def get_trainer_leaderboard(limit: int = 10) -> list[TrainerLeaderboardEntry]:
    limit = _clamp_limit(limit)
    entries = []
    for gid, game in _games.items():
        badges = len(_earned_badges.get(gid, set()))
        play_time = game.get("play_time_seconds", 0)
        entries.append({
            "player_id": gid,
            "player_name": game["player"]["name"],
            "badges": badges,
            "play_time_seconds": play_time,
        })
    # Sort: most badges first, then least play time
    entries.sort(key=lambda e: (-e["badges"], e["play_time_seconds"]))
    return [
        TrainerLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["badges"],
            badges=e["badges"],
            play_time_seconds=e["play_time_seconds"],
        )
        for i, e in enumerate(entries[:limit])
    ]


def get_pvp_leaderboard(limit: int = 10, min_battles: int = 5) -> list[PvPLeaderboardEntry]:
    limit = _clamp_limit(limit)
    player_records: dict[str, dict] = {}
    for pid, history in _pvp_history.items():
        wins = sum(1 for h in history if h.result == "win")
        losses = sum(1 for h in history if h.result == "loss")
        total = wins + losses
        if total < min_battles:
            continue
        game = get_game(pid)
        name = game["player"]["name"] if game else "Unknown"
        player_records[pid] = {
            "player_id": pid,
            "player_name": name,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
        }

    # H2: Sort by win_rate descending, then by total wins descending as tie-breaker
    sorted_records = sorted(
        player_records.values(),
        key=lambda e: (-e["win_rate"], -e["wins"]),
    )
    return [
        PvPLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["win_rate"],
            wins=e["wins"],
            losses=e["losses"],
            win_rate=e["win_rate"],
        )
        for i, e in enumerate(sorted_records[:limit])
    ]


def get_pokedex_leaderboard(limit: int = 10) -> list[PokedexLeaderboardEntry]:
    limit = _clamp_limit(limit)
    entries = []
    for gid, game in _games.items():
        dex = get_pokedex_stats(gid)
        entries.append({
            "player_id": gid,
            "player_name": game["player"]["name"],
            "caught": dex.caught_count,
            "total": dex.total_species,
            "percentage": dex.completion_percentage,
        })
    entries.sort(key=lambda e: -e["percentage"])
    return [
        PokedexLeaderboardEntry(
            rank=i + 1,
            player_name=e["player_name"],
            player_id=e["player_id"],
            score=e["percentage"],
            caught=e["caught"],
            total=e["total"],
            percentage=e["percentage"],
        )
        for i, e in enumerate(entries[:limit])
    ]


# --- Achievements ---

def check_achievements(player_id: str) -> AchievementCheckResult:
    """Check and award any newly earned achievements, with progress tracking."""
    game = get_game(player_id)
    if game is None:
        return AchievementCheckResult()

    achs = _get_achievements(player_id)
    raw = _get_stats(player_id)
    badges = _earned_badges.get(player_id, set())
    dex = get_pokedex_stats(player_id)
    team = game["player"]["team"]
    coins = game["player"].get("coins", 0)

    pvp_h = _pvp_history.get(player_id, [])
    pvp_wins = sum(1 for h in pvp_h if h.result == "win")

    newly_earned: list[Achievement] = []
    now = _now_iso()
    queue = _get_notification_queue(player_id)

    def _award(ach_id: str) -> None:
        ach = achs.get(ach_id)
        if ach is None:
            return
        if not ach.completed:
            ach.completed = True
            ach.completed_date = now
            newly_earned.append(ach)
            queue.append(AchievementNotification(
                achievement_id=ach.id,
                achievement_name=ach.name,
                tier=ach.tier,
                category=ach.category,
                description=ach.description,
                timestamp=now,
            ))

    def _update_progress(ach_id: str, current: int) -> None:
        ach = achs.get(ach_id)
        if ach is None:
            return
        ach.progress = min(current, ach.target)
        if current >= ach.target:
            _award(ach_id)

    # --- Collection achievements ---
    total_caught = raw.get("total_pokemon_caught", 0)
    _update_progress("first_steps", total_caught)
    _update_progress("collector", dex.caught_count)
    _update_progress("gotta_catch_em_all", int(dex.completion_percentage))
    _update_progress("pokemon_master", int(dex.completion_percentage))
    _update_progress("catch_50", total_caught)
    _update_progress("catch_100", total_caught)
    _update_progress("full_team", len(team))

    # --- Battle achievements ---
    total_battles = raw.get("total_battles_won", 0)
    _update_progress("first_victory", total_battles)
    _update_progress("battle_veteran", total_battles)
    _update_progress("battle_legend", total_battles)
    _update_progress("trainer_battles_10", raw.get("trainer_battles_won", 0))

    # PvP
    _update_progress("battle_tested", pvp_wins)
    _update_progress("unbeatable", raw.get("max_pvp_win_streak", 0))

    # --- Gym achievements ---
    badge_count = len(badges)
    if "boulder" in badges:
        _update_progress("rock_solid", 1)
    if "cascade" in badges:
        _update_progress("water_works", 1)
    _update_progress("badge_collector_4", badge_count)
    _update_progress("badge_collector_8", badge_count)

    # Speed demon: beat Brock under 30 min
    if "boulder" in badges and game.get("play_time_seconds", 0) < 1800:
        _update_progress("speed_demon", 1)

    # --- Evolution achievements ---
    evolutions = raw.get("evolutions", 0)
    _update_progress("evolve", evolutions)
    _update_progress("evolve_5", evolutions)
    _update_progress("evolve_20", evolutions)

    # --- Story/Quest achievements ---
    quests_done = raw.get("quests_completed", 0)
    _update_progress("quest_1", quests_done)
    _update_progress("quest_5", quests_done)
    _update_progress("quest_all", quests_done)

    # --- Legendary achievements ---
    legendaries = raw.get("legendaries_caught", 0)
    _update_progress("legendary_1", legendaries)
    _update_progress("legendary_all", legendaries)

    # --- Mini-game achievements ---
    _update_progress("slots_first", raw.get("slots_played", 0))
    _update_progress("slots_50", raw.get("slots_played", 0))
    _update_progress("quiz_master", raw.get("quiz_perfect_scores", 0))
    _update_progress("minigame_coins_1000", coins)
    _update_progress("prize_first", raw.get("prizes_redeemed", 0))

    # --- Economy achievements ---
    total_spent = raw.get("total_spent", 0)
    _update_progress("big_spender", total_spent)
    _update_progress("mega_spender", total_spent)

    # --- Berry achievements (stub) ---
    berries = raw.get("berries_harvested", 0)
    _update_progress("berry_first", berries)
    _update_progress("berry_50", berries)

    return AchievementCheckResult(
        newly_earned=newly_earned,
        all_achievements=list(achs.values()),
    )


def get_achievements(player_id: str) -> list[Achievement]:
    # H4: Only return achievements for existing players
    game = get_game(player_id)
    if game is None:
        return []
    return list(_get_achievements(player_id).values())


def get_recent_notifications(player_id: str, limit: int = 10) -> list[AchievementNotification]:
    """Get and drain the notification queue for a player."""
    queue = _get_notification_queue(player_id)
    result = queue[:limit]
    del queue[:limit]
    return result


def get_achievement_summary(player_id: str) -> dict:
    """Get achievement summary grouped by category and tier counts."""
    game = get_game(player_id)
    if game is None:
        return {}

    achs = _get_achievements(player_id)
    categories: dict[str, dict] = {}
    tier_counts = {"bronze": 0, "silver": 0, "gold": 0, "platinum": 0}
    total_completed = 0
    total_count = len(achs)

    for ach in achs.values():
        cat = ach.category
        if cat not in categories:
            categories[cat] = {"total": 0, "completed": 0}
        categories[cat]["total"] += 1
        if ach.completed:
            categories[cat]["completed"] += 1
            tier_counts[ach.tier] += 1
            total_completed += 1

    return {
        "total": total_count,
        "completed": total_completed,
        "completion_percentage": round(total_completed / total_count * 100, 1) if total_count > 0 else 0.0,
        "tier_counts": tier_counts,
        "categories": categories,
    }
