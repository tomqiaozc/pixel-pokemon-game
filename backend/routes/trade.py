"""Trade system API routes."""
from fastapi import APIRouter, HTTPException

from ..models.trade import (
    CancelOfferRequest,
    ConfirmTradeRequest,
    CreateTradeRequest,
    JoinTradeRequest,
    OfferPokemonRequest,
    TradeResult,
    TradeSessionResponse,
)
from ..services.trade_service import (
    cancel_offer,
    cancel_trade_session,
    confirm_trade,
    create_trade_session,
    get_player_team,
    get_trade_history,
    get_trade_session,
    join_trade_session,
    set_trade_offer,
)

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.post("/create")
def create_trade(req: CreateTradeRequest):
    try:
        session = create_trade_session(req.player_id)
        team = get_player_team(req.player_id)
        return TradeSessionResponse(session=session, player1_team=team or [])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/join/{trade_code}")
def join_trade(trade_code: str, req: JoinTradeRequest):
    try:
        session = join_trade_session(trade_code, req.player_id)
        team1 = get_player_team(session.player1_id)
        team2 = get_player_team(session.player2_id)
        return TradeSessionResponse(
            session=session,
            player1_team=team1 or [],
            player2_team=team2,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}")
def get_session(session_id: str):
    session = get_trade_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Trade session not found or expired")
    team1 = get_player_team(session.player1_id)
    team2 = get_player_team(session.player2_id) if session.player2_id else None
    return TradeSessionResponse(
        session=session,
        player1_team=team1 or [],
        player2_team=team2,
    )


@router.delete("/session/{session_id}")
def delete_session(session_id: str):
    if not cancel_trade_session(session_id):
        raise HTTPException(status_code=404, detail="Trade session not found")
    return {"message": "Trade session cancelled"}


@router.post("/offer")
def offer_pokemon(req: OfferPokemonRequest):
    try:
        session = set_trade_offer(req.session_id, req.player_id, req.pokemon_index)
        team1 = get_player_team(session.player1_id)
        team2 = get_player_team(session.player2_id) if session.player2_id else None
        return TradeSessionResponse(
            session=session,
            player1_team=team1 or [],
            player2_team=team2,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm")
def confirm(req: ConfirmTradeRequest):
    try:
        result = confirm_trade(req.session_id, req.player_id)
        if isinstance(result, TradeResult):
            return {"trade_completed": True, "result": result}
        # Still waiting for other player
        team1 = get_player_team(result.player1_id)
        team2 = get_player_team(result.player2_id) if result.player2_id else None
        return {
            "trade_completed": False,
            "session": TradeSessionResponse(
                session=result,
                player1_team=team1 or [],
                player2_team=team2,
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel")
def cancel(req: CancelOfferRequest):
    try:
        session = cancel_offer(req.session_id, req.player_id)
        team1 = get_player_team(session.player1_id)
        team2 = get_player_team(session.player2_id) if session.player2_id else None
        return TradeSessionResponse(
            session=session,
            player1_team=team1 or [],
            player2_team=team2,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{player_id}")
def trade_history(player_id: str):
    return get_trade_history(player_id)
