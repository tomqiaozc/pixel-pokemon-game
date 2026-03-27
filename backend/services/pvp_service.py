"""Multiplayer PvP battle system service."""
from __future__ import annotations

import math
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Optional

from ..models.battle import BattlePokemon, BattleState, StatusEvent, TurnEvent
from ..models.pokemon import Move
from ..models.pvp import (
    PvPAction,
    PvPBattleResult,
    PvPHistoryEntry,
    PvPSession,
    PvPTurnResult,
)
from ..models.weather import WeatherEvent
from .battle_service import (
    _calculate_damage,
    _get_type_effectiveness,
)
from .game_service import get_game
from .status_service import (
    get_effective_stat,
    process_move_effects,
    process_status_before_move,
    process_status_end_of_turn,
)
from .ability_service import (
    check_ability_type_immunity,
    get_weather_evasion_check,
    process_ability_damage_modifier,
    process_ability_end_of_turn,
    process_ability_on_hit,
    process_ability_on_ko,
    process_ability_weather_end_of_turn,
)
from .weather_service import (
    WEATHER_MOVES,
    decrement_weather_turns,
    get_weather_accuracy_override,
    process_weather_damage,
    process_weather_move,
)

# In-memory stores
_pvp_sessions: dict[str, PvPSession] = {}
_pvp_codes: dict[str, str] = {}  # battle_code -> session_id
_pvp_battles: dict[str, BattleState] = {}  # session_id -> battle
_pvp_actions: dict[str, dict[str, PvPAction]] = {}  # session_id -> {player_id: action}
_pvp_turn_results: dict[str, PvPTurnResult] = {}  # session_id -> last result
_pvp_history: dict[str, list[PvPHistoryEntry]] = {}  # player_id -> history
_pvp_results: dict[str, PvPBattleResult] = {}  # session_id -> result

SESSION_TIMEOUT_SECONDS = 300
TURN_TIMEOUT_SECONDS = 60


def _generate_battle_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(session: PvPSession) -> bool:
    return (_now() - session.last_activity).total_seconds() > SESSION_TIMEOUT_SECONDS


def create_pvp_session(player_id: str) -> PvPSession:
    """Create a new PvP battle lobby."""
    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    session_id = uuid.uuid4().hex[:8]
    battle_code = _generate_battle_code()
    while battle_code in _pvp_codes:
        battle_code = _generate_battle_code()

    session = PvPSession(
        id=session_id,
        battle_code=battle_code,
        player1_id=player_id,
        status="waiting",
        created_at=_now(),
        last_activity=_now(),
    )
    _pvp_sessions[session_id] = session
    _pvp_codes[battle_code] = session_id
    return session


def join_pvp_session(battle_code: str, player_id: str) -> PvPSession:
    """Join a PvP lobby by battle code."""
    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    session_id = _pvp_codes.get(battle_code)
    if session_id is None:
        raise ValueError("Invalid battle code")

    session = _pvp_sessions.get(session_id)
    if session is None:
        raise ValueError("PvP session not found")

    if _is_expired(session):
        _cleanup_session(session_id)
        raise ValueError("PvP session has expired")

    if session.player2_id is not None:
        raise ValueError("PvP session is full")

    if session.player1_id == player_id:
        raise ValueError("Cannot join your own PvP session")

    session.player2_id = player_id
    session.status = "ready"
    session.last_activity = _now()
    return session


def get_pvp_session(session_id: str) -> PvPSession | None:
    session = _pvp_sessions.get(session_id)
    if session is None:
        return None
    if _is_expired(session):
        _cleanup_session(session_id)
        return None
    return session


def ready_up(session_id: str, player_id: str, lead_pokemon_index: int = 0) -> PvPSession:
    """Signal readiness and pick lead Pokemon."""
    session = get_pvp_session(session_id)
    if session is None:
        raise ValueError("PvP session not found or expired")

    if session.status not in ("ready",):
        raise ValueError("Both players must join before readying up")

    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    team = game["player"]["team"]
    if lead_pokemon_index < 0 or lead_pokemon_index >= len(team):
        raise ValueError("Invalid lead Pokemon index")

    if player_id == session.player1_id:
        session.player1_ready = True
    elif player_id == session.player2_id:
        session.player2_ready = True
    else:
        raise ValueError("Player not in this session")

    session.last_activity = _now()
    return session


def start_pvp_battle(session_id: str) -> BattleState:
    """Start the PvP battle once both players are ready."""
    session = get_pvp_session(session_id)
    if session is None:
        raise ValueError("PvP session not found or expired")

    if not (session.player1_ready and session.player2_ready):
        raise ValueError("Both players must be ready")

    if session.status == "battling":
        # Already started, return existing battle
        battle = _pvp_battles.get(session_id)
        if battle:
            return battle
        raise ValueError("Battle state lost")

    game1 = get_game(session.player1_id)
    game2 = get_game(session.player2_id)
    if game1 is None or game2 is None:
        raise ValueError("Game not found for one or both players")

    team1 = game1["player"]["team"]
    team2 = game2["player"]["team"]
    if not team1 or not team2:
        raise ValueError("Both players must have Pokemon")

    # Use first Pokemon as lead
    p1_data = team1[0].copy()
    p2_data = team2[0].copy()

    # Ensure required BattlePokemon fields
    for pdata in [p1_data, p2_data]:
        pdata.setdefault("species_id", pdata.get("id", 1))
        pdata.setdefault("current_hp", pdata.get("stats", {}).get("hp", 100))
        pdata.setdefault("max_hp", pdata.get("stats", {}).get("hp", 100))

    player_mon = BattlePokemon(**p1_data)
    enemy_mon = BattlePokemon(**p2_data)

    battle = BattleState(
        id=session_id,
        battle_type="pvp",
        player_pokemon=player_mon,
        enemy_pokemon=enemy_mon,
        can_run=False,
    )

    _pvp_battles[session_id] = battle
    _pvp_actions[session_id] = {}
    session.status = "battling"
    session.last_activity = _now()
    return battle


def submit_action(session_id: str, player_id: str, action: PvPAction) -> dict:
    """Submit a turn action. Returns turn result if both submitted, else waiting status."""
    session = get_pvp_session(session_id)
    if session is None:
        raise ValueError("PvP session not found or expired")

    if session.status != "battling":
        raise ValueError("Battle has not started")

    battle = _pvp_battles.get(session_id)
    if battle is None:
        raise ValueError("Battle state not found")

    if battle.is_over:
        raise ValueError("Battle is already over")

    if player_id not in (session.player1_id, session.player2_id):
        raise ValueError("Player not in this session")

    # Validate action
    if action.action == "fight":
        pokemon = battle.player_pokemon if player_id == session.player1_id else battle.enemy_pokemon
        if action.move_index is None or action.move_index < 0 or action.move_index >= len(pokemon.moves):
            raise ValueError("Invalid move index")

    if session_id not in _pvp_actions:
        _pvp_actions[session_id] = {}

    _pvp_actions[session_id][player_id] = action
    session.last_activity = _now()

    # Check if both players have submitted
    actions = _pvp_actions[session_id]
    if session.player1_id in actions and session.player2_id in actions:
        result = _resolve_pvp_turn(session, battle, actions[session.player1_id], actions[session.player2_id])
        _pvp_actions[session_id] = {}  # Reset for next turn
        _pvp_turn_results[session_id] = result

        if result.battle_over:
            _finalize_battle(session, battle, result)

        return {"status": "turn_resolved", "result": result}

    return {"status": "waiting_for_opponent"}


def _resolve_pvp_turn(
    session: PvPSession,
    battle: BattleState,
    p1_action: PvPAction,
    p2_action: PvPAction,
) -> PvPTurnResult:
    """Resolve a PvP turn with both players' actions."""
    battle.turn_count += 1
    events: list[TurnEvent] = []
    status_events: list[StatusEvent] = []
    weather_events: list[WeatherEvent] = []
    current_weather = battle.weather.current_weather

    p1 = battle.player_pokemon
    p2 = battle.enemy_pokemon

    # Determine moves
    p1_move = p1.moves[p1_action.move_index] if p1_action.action == "fight" and p1_action.move_index is not None else p1.moves[0]
    p2_move = p2.moves[p2_action.move_index] if p2_action.action == "fight" and p2_action.move_index is not None else p2.moves[0]

    # Determine turn order by speed
    p1_speed = get_effective_stat(p1, "speed", current_weather)
    p2_speed = get_effective_stat(p2, "speed", current_weather)
    p1_first = p1_speed >= p2_speed if p1_speed != p2_speed else random.random() < 0.5

    if p1_first:
        order = [("player1", p1, p2, p1_move), ("player2", p2, p1, p2_move)]
    else:
        order = [("player2", p2, p1, p2_move), ("player1", p1, p2, p1_move)]

    for role, attacker, defender, move in order:
        if attacker.current_hp <= 0:
            continue

        # Map PvP roles to battle service roles
        atk_role = "player" if role == "player1" else "enemy"
        def_role = "enemy" if role == "player1" else "player"

        # Status before move
        can_move, pre_events = process_status_before_move(attacker, atk_role)
        status_events.extend(pre_events)

        if attacker.current_hp <= 0:
            battle.is_over = True
            battle.winner = "player2" if role == "player1" else "player1"
            break

        if not can_move:
            continue

        # Weather moves
        if move.name in WEATHER_MOVES:
            w_events = process_weather_move(move.name, battle, user=attacker)
            weather_events.extend(w_events)
            current_weather = battle.weather.current_weather
            events.append(TurnEvent(
                attacker=atk_role, move=move.name, damage=0,
                effectiveness="normal", critical=False,
                target_hp_remaining=defender.current_hp, target_fainted=False,
            ))
            continue

        # Accuracy
        move_accuracy = move.accuracy
        weather_acc = get_weather_accuracy_override(move.name, current_weather)
        if weather_acc is not None:
            move_accuracy = weather_acc

        if get_weather_evasion_check(defender, current_weather):
            events.append(TurnEvent(
                attacker=atk_role, move=move.name, damage=0,
                effectiveness="normal", critical=False,
                target_hp_remaining=defender.current_hp, target_fainted=False,
            ))
            continue

        if random.randint(1, 100) > move_accuracy:
            events.append(TurnEvent(
                attacker=atk_role, move=move.name, damage=0,
                effectiveness="normal", critical=False,
                target_hp_remaining=defender.current_hp, target_fainted=False,
            ))
            continue

        dmg, eff, crit = _calculate_damage(attacker, defender, move, current_weather)

        # Ability type immunity
        immune, ab_events = check_ability_type_immunity(defender, move, def_role)
        status_events.extend(ab_events)
        if immune:
            events.append(TurnEvent(
                attacker=atk_role, move=move.name, damage=0,
                effectiveness="immune", critical=False,
                target_hp_remaining=defender.current_hp, target_fainted=False,
            ))
            continue

        # Ability damage modifiers
        dmg, ab_dmg_events = process_ability_damage_modifier(
            attacker, defender, move, dmg, atk_role, def_role,
        )
        status_events.extend(ab_dmg_events)

        did_damage = dmg > 0
        defender.current_hp = max(0, defender.current_hp - dmg)
        fainted = defender.current_hp == 0

        events.append(TurnEvent(
            attacker=atk_role, move=move.name, damage=dmg,
            effectiveness=eff, critical=crit,
            target_hp_remaining=defender.current_hp, target_fainted=fainted,
        ))

        if not fainted:
            move_effects = process_move_effects(move.name, attacker, defender, atk_role, def_role, did_damage)
            status_events.extend(move_effects)
            if did_damage:
                hit_events = process_ability_on_hit(attacker, defender, move, atk_role, def_role)
                status_events.extend(hit_events)
        else:
            ko_events = process_ability_on_ko(attacker, atk_role)
            status_events.extend(ko_events)
            battle.is_over = True
            battle.winner = role
            break

    # End-of-turn effects
    if not battle.is_over:
        for atk_role, pokemon in [("player", p1), ("enemy", p2)]:
            eot_events = process_status_end_of_turn(pokemon, atk_role)
            status_events.extend(eot_events)
            if pokemon.current_hp <= 0:
                battle.is_over = True
                battle.winner = "player2" if atk_role == "player" else "player1"
                break

    if not battle.is_over:
        for atk_role, pokemon in [("player", p1), ("enemy", p2)]:
            ab_eot = process_ability_end_of_turn(pokemon, atk_role)
            status_events.extend(ab_eot)

    if not battle.is_over and battle.weather.current_weather is not None:
        for atk_role, pokemon in [("player", p1), ("enemy", p2)]:
            w_ab = process_ability_weather_end_of_turn(pokemon, atk_role, battle.weather.current_weather)
            weather_events.extend(w_ab)

    if not battle.is_over:
        w_dmg = process_weather_damage(battle)
        weather_events.extend(w_dmg)
        for atk_role, pokemon in [("player", p1), ("enemy", p2)]:
            if pokemon.current_hp <= 0:
                battle.is_over = True
                battle.winner = "player2" if atk_role == "player" else "player1"
                break

    w_end = decrement_weather_turns(battle)
    if w_end:
        weather_events.append(w_end)

    p1.flinched = False
    p2.flinched = False

    return PvPTurnResult(
        turn_number=battle.turn_count,
        events=events,
        status_events=status_events,
        weather_events=weather_events,
        battle_over=battle.is_over,
        winner=battle.winner,
    )


def _finalize_battle(session: PvPSession, battle: BattleState, result: PvPTurnResult) -> None:
    """Record battle result and update history."""
    # Deferred import to avoid circular dependency
    from .leaderboard_service import check_achievements, record_pvp_result

    winner_id = session.player1_id if result.winner == "player1" else session.player2_id
    loser_id = session.player2_id if result.winner == "player1" else session.player1_id

    battle_result = PvPBattleResult(
        winner_id=winner_id,
        loser_id=loser_id,
        turns=battle.turn_count,
        forfeit=False,
        date=_now().isoformat(),
    )
    _pvp_results[session.id] = battle_result
    session.status = "completed"

    # Record history
    game1 = get_game(session.player1_id)
    game2 = get_game(session.player2_id)
    p1_name = game1["player"]["name"] if game1 else "Unknown"
    p2_name = game2["player"]["name"] if game2 else "Unknown"

    _record_history(session.player1_id, p2_name, "win" if winner_id == session.player1_id else "loss", battle.turn_count)
    _record_history(session.player2_id, p1_name, "win" if winner_id == session.player2_id else "loss", battle.turn_count)

    # C1/C2: Record PvP results and check achievements for both players
    record_pvp_result(winner_id, won=True)
    record_pvp_result(loser_id, won=False)
    check_achievements(winner_id)
    check_achievements(loser_id)


def forfeit_battle(session_id: str, player_id: str) -> PvPBattleResult:
    """Forfeit a PvP battle."""
    # Deferred import to avoid circular dependency
    from .leaderboard_service import check_achievements, record_pvp_result

    session = get_pvp_session(session_id)
    if session is None:
        raise ValueError("PvP session not found or expired")

    if session.status != "battling":
        raise ValueError("No active battle to forfeit")

    if player_id not in (session.player1_id, session.player2_id):
        raise ValueError("Player not in this session")

    battle = _pvp_battles.get(session_id)
    turns = battle.turn_count if battle else 0

    winner_id = session.player2_id if player_id == session.player1_id else session.player1_id
    loser_id = player_id

    result = PvPBattleResult(
        winner_id=winner_id,
        loser_id=loser_id,
        turns=turns,
        forfeit=True,
        date=_now().isoformat(),
    )
    _pvp_results[session_id] = result
    session.status = "completed"

    if battle:
        battle.is_over = True
        battle.winner = "player2" if player_id == session.player1_id else "player1"

    game1 = get_game(session.player1_id)
    game2 = get_game(session.player2_id)
    p1_name = game1["player"]["name"] if game1 else "Unknown"
    p2_name = game2["player"]["name"] if game2 else "Unknown"

    _record_history(session.player1_id, p2_name,
                    "win" if winner_id == session.player1_id else "loss", turns, forfeit=True)
    _record_history(session.player2_id, p1_name,
                    "win" if winner_id == session.player2_id else "loss", turns, forfeit=True)

    # C1/C2: Record PvP results and check achievements for both players
    record_pvp_result(winner_id, won=True)
    record_pvp_result(loser_id, won=False)
    check_achievements(winner_id)
    check_achievements(loser_id)

    return result


def _record_history(player_id: str, opponent: str, result: str, turns: int, forfeit: bool = False) -> None:
    if player_id not in _pvp_history:
        _pvp_history[player_id] = []
    _pvp_history[player_id].append(PvPHistoryEntry(
        date=_now().isoformat(),
        opponent_name=opponent,
        result=result,
        turns=turns,
        forfeit=forfeit,
    ))


def get_pvp_history(player_id: str) -> list[PvPHistoryEntry]:
    return _pvp_history.get(player_id, [])


def get_pvp_result(session_id: str) -> PvPBattleResult | None:
    return _pvp_results.get(session_id)


def get_pvp_battle(session_id: str) -> BattleState | None:
    return _pvp_battles.get(session_id)


def get_last_turn_result(session_id: str) -> PvPTurnResult | None:
    return _pvp_turn_results.get(session_id)


def _cleanup_session(session_id: str) -> None:
    session = _pvp_sessions.pop(session_id, None)
    if session:
        _pvp_codes.pop(session.battle_code, None)
    _pvp_battles.pop(session_id, None)
    _pvp_actions.pop(session_id, None)
    _pvp_turn_results.pop(session_id, None)


def cancel_pvp_session(session_id: str) -> bool:
    session = _pvp_sessions.get(session_id)
    if session is None:
        return False
    _cleanup_session(session_id)
    return True
