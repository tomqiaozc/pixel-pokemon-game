"""Mini-games, coins, and prize exchange service."""
from __future__ import annotations

import random
import time
import uuid

from ..models.minigame import (
    CoinTransaction,
    MemoryCompleteResult,
    Prize,
    QuizQuestion,
    QuizSession,
    QuizSubmitResult,
    RedeemResult,
    SlotResult,
)
from .encounter_service import _calc_stat, _generate_moves_for_level, get_species
from .game_service import _games

# ── Constants ──────────────────────────────────────────────

COINS_PER_PURCHASE = 50
COIN_PRICE = 1000

SLOT_SYMBOLS = [
    ("Pokeball", 30),
    ("Cherry", 25),
    ("Bar", 20),
    ("7", 15),
    ("Pikachu", 8),
    ("Mewtwo", 2),
]

SLOT_PAYOUTS = {
    "Cherry": 5,
    "Bar": 10,
    "7": 50,
    "Pikachu": 100,
    "Mewtwo": 300,
    "Pokeball": 3,
}

MEMORY_DIFFICULTY = {
    "easy": {"pairs": 8, "base_coins": 10, "multiplier": 1.0, "max_time": 65},
    "medium": {"pairs": 10, "base_coins": 20, "multiplier": 1.5, "max_time": 80},
    "hard": {"pairs": 12, "base_coins": 40, "multiplier": 2.0, "max_time": 95},
}

QUIZ_COINS_PER_CORRECT = 5
QUIZ_QUESTION_COUNT = 10

PRIZE_CATALOG: list[Prize] = [
    Prize(id=1, name="Porygon", prize_type="pokemon", coin_cost=9999, description="A Pokemon made of programming code.", species_id=137, level=25),
    Prize(id=2, name="Dratini", prize_type="pokemon", coin_cost=4600, description="A mystical Dragon-type Pokemon.", species_id=147, level=18),
    Prize(id=3, name="Eevee", prize_type="pokemon", coin_cost=6666, description="An adaptable Pokemon with many evolutions.", species_id=133, level=25),
    Prize(id=4, name="TM Ice Beam", prize_type="item", coin_cost=4000, description="Teaches Ice Beam (ice, 90 power).", item_id=11),
    Prize(id=5, name="TM Thunderbolt", prize_type="item", coin_cost=4000, description="Teaches Thunderbolt (electric, 95 power).", item_id=12),
    Prize(id=6, name="Rare Candy", prize_type="item", coin_cost=500, description="Instantly raises a Pokemon's level by 1.", item_id=13),
    Prize(id=7, name="PP Up", prize_type="item", coin_cost=1000, description="Raises the max PP of a selected move.", item_id=14),
]

# ── In-memory stores ──────────────────────────────────────

_quiz_sessions: dict[str, QuizSession] = {}  # session_id -> QuizSession
_memory_sessions: dict[str, float] = {}  # session_key -> start_timestamp
_slot_history: dict[str, list[float]] = {}  # game_id -> list of spin timestamps

# Rate limit: max 100 spins per hour
SLOT_RATE_LIMIT = 100
SLOT_RATE_WINDOW = 3600  # seconds


# ── Helpers ────────────────────────────────────────────────

def _get_player(game_id: str) -> dict | None:
    game = _games.get(game_id)
    if game is None:
        return None
    return game["player"]


def _get_coins(game_id: str) -> int:
    player = _get_player(game_id)
    if player is None:
        return 0
    return player.get("coins", 0)


def _set_coins(game_id: str, coins: int) -> None:
    player = _get_player(game_id)
    if player is not None:
        player["coins"] = coins


def _get_money(game_id: str) -> int:
    player = _get_player(game_id)
    if player is None:
        return 0
    return player.get("money", 0)


def _set_money(game_id: str, money: int) -> None:
    player = _get_player(game_id)
    if player is not None:
        player["money"] = money


def _spin_reel() -> str:
    """Pick a symbol using weighted random selection."""
    roll = random.randint(1, 100)
    cumulative = 0
    for symbol, weight in SLOT_SYMBOLS:
        cumulative += weight
        if roll <= cumulative:
            return symbol
    return SLOT_SYMBOLS[0][0]


def _check_slot_rate_limit(game_id: str) -> bool:
    """Return True if player has NOT exceeded rate limit."""
    now = time.time()
    history = _slot_history.get(game_id, [])
    # Prune old entries
    history = [t for t in history if now - t < SLOT_RATE_WINDOW]
    _slot_history[game_id] = history
    return len(history) < SLOT_RATE_LIMIT


# ── Coin System ────────────────────────────────────────────

def get_coin_balance(game_id: str) -> dict | None:
    player = _get_player(game_id)
    if player is None:
        return None
    return {"game_id": game_id, "coins": player.get("coins", 0), "money": player.get("money", 0)}


def buy_coins(game_id: str, amount: int = 1) -> CoinTransaction | None:
    """Buy coins with money. Each purchase = 50 coins for $1000. amount = number of purchases."""
    player = _get_player(game_id)
    if player is None:
        return None
    if amount < 1:
        return None

    total_cost = amount * COIN_PRICE
    current_money = player.get("money", 0)
    if current_money < total_cost:
        return None

    coins_gained = amount * COINS_PER_PURCHASE
    coins_before = player.get("coins", 0)
    money_before = current_money

    _set_money(game_id, money_before - total_cost)
    _set_coins(game_id, coins_before + coins_gained)

    return CoinTransaction(
        game_id=game_id,
        coins_before=coins_before,
        coins_after=coins_before + coins_gained,
        money_before=money_before,
        money_after=money_before - total_cost,
        amount=coins_gained,
    )


# ── Slot Machine ───────────────────────────────────────────

def spin_slots(game_id: str, bet: int = 1) -> SlotResult | None:
    """Spin the slot machine. Bet is in coins. Returns SlotResult or None on error."""
    player = _get_player(game_id)
    if player is None:
        return None
    if bet < 1 or bet > 10:
        return None

    coins = player.get("coins", 0)
    if coins < bet:
        return None

    if not _check_slot_rate_limit(game_id):
        return None

    # Record spin
    _slot_history.setdefault(game_id, []).append(time.time())

    # Spin 3 reels
    reels = [_spin_reel() for _ in range(3)]

    # Deduct bet
    coins_before = coins
    coins -= bet

    # Calculate payout
    payout = 0
    if reels[0] == reels[1] == reels[2]:
        # Triple match
        payout = SLOT_PAYOUTS.get(reels[0], 3) * bet
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        # Double match (middle + one side)
        payout = bet  # Return bet on partial match

    coins += payout
    _set_coins(game_id, coins)

    return SlotResult(
        reels=reels,
        win=payout > 0,
        payout=payout,
        coins_before=coins_before,
        coins_after=coins,
    )


# ── Memory Game ────────────────────────────────────────────

def start_memory_game(game_id: str, difficulty: str) -> dict | None:
    """Start a memory game session. Returns session info or None."""
    if difficulty not in MEMORY_DIFFICULTY:
        return None
    player = _get_player(game_id)
    if player is None:
        return None

    session_key = f"{game_id}:{difficulty}"
    _memory_sessions[session_key] = time.time()

    cfg = MEMORY_DIFFICULTY[difficulty]
    return {
        "game_id": game_id,
        "difficulty": difficulty,
        "pairs": cfg["pairs"],
        "max_time": cfg["max_time"],
        "session_started": True,
    }


def complete_memory_game(
    game_id: str, difficulty: str, time_seconds: float, pairs_matched: int
) -> MemoryCompleteResult | None:
    """Validate and reward a completed memory game."""
    if difficulty not in MEMORY_DIFFICULTY:
        return None
    player = _get_player(game_id)
    if player is None:
        return None

    cfg = MEMORY_DIFFICULTY[difficulty]
    session_key = f"{game_id}:{difficulty}"
    start_time = _memory_sessions.pop(session_key, None)

    # Validate session exists
    if start_time is None:
        return MemoryCompleteResult(
            valid=False, coins_earned=0,
            coins_before=_get_coins(game_id), coins_after=_get_coins(game_id),
            message="No active memory game session",
        )

    # Validate time (allow 2s slack for network)
    if time_seconds < 1 or time_seconds > cfg["max_time"] + 2:
        return MemoryCompleteResult(
            valid=False, coins_earned=0,
            coins_before=_get_coins(game_id), coins_after=_get_coins(game_id),
            message="Invalid completion time",
        )

    # Validate claimed time against server clock (prevent instant completions)
    actual_elapsed = time.time() - start_time
    if time_seconds > actual_elapsed + 2:
        return MemoryCompleteResult(
            valid=False, coins_earned=0,
            coins_before=_get_coins(game_id), coins_after=_get_coins(game_id),
            message="Claimed time exceeds actual elapsed time",
        )

    # Validate pairs
    if pairs_matched < 1 or pairs_matched > cfg["pairs"]:
        return MemoryCompleteResult(
            valid=False, coins_earned=0,
            coins_before=_get_coins(game_id), coins_after=_get_coins(game_id),
            message="Invalid pairs count",
        )

    # Calculate reward
    completion_ratio = pairs_matched / cfg["pairs"]
    base = int(cfg["base_coins"] * cfg["multiplier"] * completion_ratio)

    # Time bonus: faster = more coins
    if time_seconds <= cfg["max_time"] * 0.5:
        time_bonus = 2.0
    elif time_seconds <= cfg["max_time"] * 0.75:
        time_bonus = 1.5
    else:
        time_bonus = 1.0

    coins_earned = int(base * time_bonus)
    coins_before = _get_coins(game_id)
    _set_coins(game_id, coins_before + coins_earned)

    return MemoryCompleteResult(
        valid=True,
        coins_earned=coins_earned,
        coins_before=coins_before,
        coins_after=coins_before + coins_earned,
        message=f"Earned {coins_earned} coins!",
    )


# ── Quiz System ────────────────────────────────────────────

def _generate_quiz_questions() -> list[QuizQuestion]:
    """Auto-generate quiz questions from Pokemon species data."""
    from .encounter_service import get_all_species, _load_moves, _moves_db

    species_list = get_all_species()
    if not _moves_db:
        _load_moves()

    questions: list[QuizQuestion] = []
    qid = 0

    all_types = list({t for sp in species_list for t in sp.types})

    # Type questions: "What type is X?"
    for sp in species_list:
        if len(questions) >= 60:
            break
        correct_type = sp.types[0]
        wrong_types = [t for t in all_types if t not in sp.types]
        if len(wrong_types) < 3:
            continue
        options_wrong = random.sample(wrong_types, 3)
        options = [correct_type] + options_wrong
        random.shuffle(options)
        qid += 1
        questions.append(QuizQuestion(
            id=qid,
            question=f"What type is {sp.name}?",
            options=options,
            correct_index=options.index(correct_type),
        ))

    # Evolution questions: "What does X evolve into?"
    evolving = [sp for sp in species_list if sp.evolution is not None]
    non_evolving_names = [sp.name for sp in species_list]
    for sp in evolving:
        evo_target = next((s for s in species_list if s.id == sp.evolution.to), None)
        if evo_target is None:
            continue
        wrong_names = [n for n in non_evolving_names if n != evo_target.name and n != sp.name]
        if len(wrong_names) < 3:
            continue
        options_wrong = random.sample(wrong_names, 3)
        options = [evo_target.name] + options_wrong
        random.shuffle(options)
        qid += 1
        questions.append(QuizQuestion(
            id=qid,
            question=f"What does {sp.name} evolve into?",
            options=options,
            correct_index=options.index(evo_target.name),
        ))

    # Stat questions: "Which Pokemon has the highest HP/Attack/etc?"
    stat_names = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
    for stat in stat_names:
        sorted_by_stat = sorted(species_list, key=lambda s: getattr(s.stats, stat), reverse=True)
        if len(sorted_by_stat) < 4:
            continue
        top = sorted_by_stat[0]
        others = [s.name for s in sorted_by_stat[1:] if getattr(s.stats, stat) < getattr(top.stats, stat)]
        if len(others) < 3:
            continue
        options_wrong = random.sample(others[:10], 3)
        options = [top.name] + options_wrong
        random.shuffle(options)
        qid += 1
        stat_display = stat.replace("_", " ").title()
        questions.append(QuizQuestion(
            id=qid,
            question=f"Which Pokemon has the highest base {stat_display}?",
            options=options,
            correct_index=options.index(top.name),
        ))

    # Move type questions: "Which move is [type] type?"
    move_items = list(_moves_db.items())
    moves_by_type: dict[str, list[str]] = {}
    for mname, mdata in move_items:
        mtype = mdata.get("type", "normal")
        moves_by_type.setdefault(mtype, []).append(mname)

    for mtype, mnames in moves_by_type.items():
        if len(mnames) < 1:
            continue
        correct = random.choice(mnames)
        wrong_moves = [n for n, d in move_items if d.get("type") != mtype]
        if len(wrong_moves) < 3:
            continue
        options_wrong = random.sample(wrong_moves, 3)
        options = [correct] + options_wrong
        random.shuffle(options)
        qid += 1
        questions.append(QuizQuestion(
            id=qid,
            question=f"Which move is {mtype} type?",
            options=options,
            correct_index=options.index(correct),
        ))

    return questions


def start_quiz(game_id: str) -> QuizSession | None:
    """Start a quiz session with random questions."""
    player = _get_player(game_id)
    if player is None:
        return None

    all_questions = _generate_quiz_questions()
    if len(all_questions) < QUIZ_QUESTION_COUNT:
        selected = all_questions
    else:
        selected = random.sample(all_questions, QUIZ_QUESTION_COUNT)

    # Renumber
    for i, q in enumerate(selected):
        q.id = i + 1

    session_id = uuid.uuid4().hex[:8]
    session = QuizSession(session_id=session_id, game_id=game_id, questions=selected)
    _quiz_sessions[session_id] = session
    return session


def submit_quiz(session_id: str, answers: list[int]) -> QuizSubmitResult | None:
    """Grade a quiz submission. answers = list of selected option indices."""
    session = _quiz_sessions.pop(session_id, None)
    if session is None:
        return None

    game_id = session.game_id
    player = _get_player(game_id)
    if player is None:
        return None

    results = []
    score = 0
    for i, q in enumerate(session.questions):
        if i < len(answers) and answers[i] == q.correct_index:
            results.append(True)
            score += 1
        else:
            results.append(False)

    coins_earned = score * QUIZ_COINS_PER_CORRECT
    coins_before = _get_coins(game_id)
    _set_coins(game_id, coins_before + coins_earned)

    return QuizSubmitResult(
        score=score,
        total=len(session.questions),
        coins_earned=coins_earned,
        coins_before=coins_before,
        coins_after=coins_before + coins_earned,
        results=results,
    )


# ── Prize Exchange ─────────────────────────────────────────

def get_prizes() -> list[Prize]:
    """Return the full prize catalog."""
    return PRIZE_CATALOG


def redeem_prize(game_id: str, prize_id: int) -> RedeemResult | None:
    """Redeem a prize with coins."""
    player = _get_player(game_id)
    if player is None:
        return None

    prize = next((p for p in PRIZE_CATALOG if p.id == prize_id), None)
    if prize is None:
        return RedeemResult(
            success=False, message="Prize not found",
            coins_before=_get_coins(game_id), coins_after=_get_coins(game_id),
            prize_name="",
        )

    coins = _get_coins(game_id)
    if coins < prize.coin_cost:
        return RedeemResult(
            success=False, message="Not enough coins",
            coins_before=coins, coins_after=coins,
            prize_name=prize.name,
        )

    coins_before = coins
    _set_coins(game_id, coins - prize.coin_cost)

    if prize.prize_type == "pokemon" and prize.species_id and prize.level:
        _add_prize_pokemon(game_id, prize.species_id, prize.level)
    elif prize.prize_type == "item" and prize.item_id:
        _add_prize_item(game_id, prize.item_id)

    return RedeemResult(
        success=True,
        message=f"Redeemed {prize.name}!",
        coins_before=coins_before,
        coins_after=coins - prize.coin_cost,
        prize_name=prize.name,
    )


def _add_prize_pokemon(game_id: str, species_id: int, level: int) -> None:
    """Add a prize Pokemon to the player's team, or PC if team is full."""
    species = get_species(species_id)
    if species is None:
        return

    iv = random.randint(15, 31)  # Prize Pokemon get decent IVs
    stats = {
        "hp": _calc_stat(species.stats.hp, level, iv, is_hp=True),
        "attack": _calc_stat(species.stats.attack, level, iv),
        "defense": _calc_stat(species.stats.defense, level, iv),
        "sp_attack": _calc_stat(species.stats.sp_attack, level, iv),
        "sp_defense": _calc_stat(species.stats.sp_defense, level, iv),
        "speed": _calc_stat(species.stats.speed, level, iv),
    }

    moves_list = _generate_moves_for_level(species, level)

    pokemon_data = {
        "id": species.id,
        "name": species.name,
        "types": species.types,
        "level": level,
        "stats": stats,
        "current_hp": stats["hp"],
        "max_hp": stats["hp"],
        "moves": moves_list,
        "sprite": species.sprite,
        "ability_id": species.abilities[0] if species.abilities else "none",
    }

    player = _get_player(game_id)
    if player is None:
        return

    team = player.get("team", [])
    if len(team) < 6:
        team.append(pokemon_data)
    else:
        from .pokedex_service import auto_deposit
        auto_deposit(game_id, pokemon_data)


def _add_prize_item(game_id: str, item_id: int) -> None:
    """Add a prize item to player inventory."""
    player = _get_player(game_id)
    if player is None:
        return

    inventory = player.get("inventory", [])
    # Check if item already in inventory
    for entry in inventory:
        if entry.get("item_id") == item_id:
            entry["quantity"] = entry.get("quantity", 0) + 1
            return

    inventory.append({"item_id": item_id, "quantity": 1})
