"""Pokemon trading system service — session management, offers, and execution."""
from __future__ import annotations

import random
import string
import uuid
from datetime import datetime, timezone

from ..models.trade import (
    TradeHistoryEntry,
    TradeOffer,
    TradeResult,
    TradeSession,
)
from .game_service import get_game
from .pokedex_service import register_caught

# In-memory stores
_trade_sessions: dict[str, TradeSession] = {}
_trade_codes: dict[str, str] = {}  # trade_code -> session_id
_trade_history: dict[str, list[TradeHistoryEntry]] = {}  # player_id -> history

SESSION_TIMEOUT_SECONDS = 300  # 5 minutes


def _generate_trade_code() -> str:
    """Generate a 6-character alphanumeric trade code."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_expired(session: TradeSession) -> bool:
    elapsed = (_now() - session.last_activity).total_seconds()
    return elapsed > SESSION_TIMEOUT_SECONDS


def create_trade_session(player_id: str) -> TradeSession:
    """Create a new trade session and return it."""
    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    session_id = uuid.uuid4().hex[:8]
    trade_code = _generate_trade_code()

    # Ensure unique trade code
    while trade_code in _trade_codes:
        trade_code = _generate_trade_code()

    session = TradeSession(
        id=session_id,
        trade_code=trade_code,
        player1_id=player_id,
        status="waiting",
        created_at=_now(),
        last_activity=_now(),
    )
    _trade_sessions[session_id] = session
    _trade_codes[trade_code] = session_id
    return session


def join_trade_session(trade_code: str, player_id: str) -> TradeSession:
    """Join an existing trade session by trade code."""
    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    session_id = _trade_codes.get(trade_code)
    if session_id is None:
        raise ValueError("Invalid trade code")

    session = _trade_sessions.get(session_id)
    if session is None:
        raise ValueError("Trade session not found")

    if _is_expired(session):
        _cleanup_session(session_id)
        raise ValueError("Trade session has expired")

    if session.player2_id is not None:
        raise ValueError("Trade session is full")

    if session.player1_id == player_id:
        raise ValueError("Cannot join your own trade session")

    session.player2_id = player_id
    session.status = "selecting"
    session.last_activity = _now()
    return session


def get_trade_session(session_id: str) -> TradeSession | None:
    """Get a trade session by ID, cleaning up expired ones."""
    session = _trade_sessions.get(session_id)
    if session is None:
        return None
    if _is_expired(session):
        _cleanup_session(session_id)
        return None
    return session


def set_trade_offer(session_id: str, player_id: str, pokemon_index: int) -> TradeSession:
    """Set a player's trade offer."""
    session = get_trade_session(session_id)
    if session is None:
        raise ValueError("Trade session not found or expired")

    if session.status not in ("selecting", "confirmed"):
        raise ValueError(f"Cannot offer in session status: {session.status}")

    game = get_game(player_id)
    if game is None:
        raise ValueError("Game not found")

    team = game["player"]["team"]
    if pokemon_index < 0 or pokemon_index >= len(team):
        raise ValueError("Invalid Pokemon index")

    # Cannot trade if it would leave player with 0 Pokemon
    if len(team) <= 1:
        raise ValueError("Cannot trade your only Pokemon")

    offer = TradeOffer(player_id=player_id, pokemon_index=pokemon_index)

    if player_id == session.player1_id:
        session.player1_offer = offer
        session.player1_confirmed = False
    elif player_id == session.player2_id:
        session.player2_offer = offer
        session.player2_confirmed = False
    else:
        raise ValueError("Player not in this trade session")

    session.status = "selecting"
    session.last_activity = _now()
    return session


def confirm_trade(session_id: str, player_id: str) -> TradeSession | TradeResult:
    """Confirm trade. If both players confirmed, execute the trade."""
    session = get_trade_session(session_id)
    if session is None:
        raise ValueError("Trade session not found or expired")

    if session.status not in ("selecting", "confirmed"):
        raise ValueError(f"Cannot confirm in session status: {session.status}")

    if player_id == session.player1_id:
        if session.player1_offer is None:
            raise ValueError("No offer set")
        session.player1_confirmed = True
    elif player_id == session.player2_id:
        if session.player2_offer is None:
            raise ValueError("No offer set")
        session.player2_confirmed = True
    else:
        raise ValueError("Player not in this trade session")

    session.last_activity = _now()

    # Both confirmed — execute trade
    if session.player1_confirmed and session.player2_confirmed:
        return _execute_trade(session)

    session.status = "confirmed"
    return session


def cancel_offer(session_id: str, player_id: str) -> TradeSession:
    """Cancel a player's current offer, reset to selection."""
    session = get_trade_session(session_id)
    if session is None:
        raise ValueError("Trade session not found or expired")

    if player_id == session.player1_id:
        session.player1_offer = None
        session.player1_confirmed = False
    elif player_id == session.player2_id:
        session.player2_offer = None
        session.player2_confirmed = False
    else:
        raise ValueError("Player not in this trade session")

    session.status = "selecting"
    session.last_activity = _now()
    return session


def cancel_trade_session(session_id: str) -> bool:
    """Cancel and remove a trade session."""
    session = _trade_sessions.get(session_id)
    if session is None:
        return False
    _cleanup_session(session_id)
    return True


def _execute_trade(session: TradeSession) -> TradeResult:
    """Execute the trade: swap Pokemon between players."""
    game1 = get_game(session.player1_id)
    game2 = get_game(session.player2_id)
    if game1 is None or game2 is None:
        raise ValueError("Game not found for one or both players")

    team1 = game1["player"]["team"]
    team2 = game2["player"]["team"]
    idx1 = session.player1_offer.pokemon_index
    idx2 = session.player2_offer.pokemon_index

    # Re-validate indices
    if idx1 < 0 or idx1 >= len(team1):
        raise ValueError("Player 1's offered Pokemon no longer valid")
    if idx2 < 0 or idx2 >= len(team2):
        raise ValueError("Player 2's offered Pokemon no longer valid")

    # Re-validate team sizes
    if len(team1) <= 1 or len(team2) <= 1:
        raise ValueError("Cannot trade — would leave a player with no Pokemon")

    pokemon1 = team1[idx1].copy()
    pokemon2 = team2[idx2].copy()

    player1_name = game1["player"]["name"]
    player2_name = game2["player"]["name"]
    now_str = _now().isoformat()

    # Set traded metadata on pokemon
    pokemon1["original_trainer"] = player1_name
    pokemon1["is_outsider"] = True
    pokemon1["traded_date"] = now_str

    pokemon2["original_trainer"] = player2_name
    pokemon2["is_outsider"] = True
    pokemon2["traded_date"] = now_str

    # Swap: remove originals, add received
    team1.pop(idx1)
    team1.append(pokemon2)

    team2.pop(idx2)
    team2.append(pokemon1)

    # Update Pokedex for both players (register as caught if new)
    species_id_1 = pokemon1.get("id")
    species_id_2 = pokemon2.get("id")
    if species_id_1 is not None:
        register_caught(session.player2_id, species_id_1)
    if species_id_2 is not None:
        register_caught(session.player1_id, species_id_2)

    # Record trade history
    _record_history(session.player1_id, pokemon1.get("name", "?"), pokemon2.get("name", "?"), player2_name)
    _record_history(session.player2_id, pokemon2.get("name", "?"), pokemon1.get("name", "?"), player1_name)

    # Mark session completed
    session.status = "completed"
    session.last_activity = _now()

    result = TradeResult(
        success=True,
        player1_given=pokemon1,
        player1_received=pokemon2,
        player2_given=pokemon2,
        player2_received=pokemon1,
        message=f"Trade complete! {player1_name} traded {pokemon1.get('name')} for {pokemon2.get('name')}.",
    )

    # Clean up session after execution
    _cleanup_session(session.id)

    return result


def _record_history(player_id: str, given: str, received: str, partner: str) -> None:
    if player_id not in _trade_history:
        _trade_history[player_id] = []
    _trade_history[player_id].append(TradeHistoryEntry(
        date=_now().isoformat(),
        given_pokemon=given,
        received_pokemon=received,
        partner_name=partner,
    ))


def get_trade_history(player_id: str) -> list[TradeHistoryEntry]:
    return _trade_history.get(player_id, [])


def _cleanup_session(session_id: str) -> None:
    session = _trade_sessions.pop(session_id, None)
    if session:
        _trade_codes.pop(session.trade_code, None)


def get_player_team(player_id: str) -> list[dict] | None:
    """Helper to get a player's team for trade session display."""
    game = get_game(player_id)
    if game is None:
        return None
    return game["player"]["team"]
