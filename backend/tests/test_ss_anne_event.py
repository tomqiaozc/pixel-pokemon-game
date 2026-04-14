"""Tests for Sprint 13 QA: S.S. Anne event service.

These tests verify the S.S. Anne boarding, rival battle, captain help,
HM01 Cut reward, and ship departure flow.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_service import create_game

client = TestClient(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _create_test_game() -> str:
    game = create_game("AnneTester", 1)
    return game["id"]


# ──── S.S. Anne State ─────────────────────────────────────

class TestSSAnneState:
    def test_ss_anne_initial_state(self):
        """GET /api/ss-anne/state/{game_id} should return initial state."""
        game_id = _create_test_game()
        resp = client.get(f"/api/ss-anne/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("boarded") is False
        assert data.get("ship_departed") is False


# ──── Boarding ─────────────────────────────────────────────

class TestSSAnneBoarding:
    def test_board_without_ticket(self):
        """POST /api/ss-anne/board without ticket should fail (400)."""
        game_id = _create_test_game()
        resp = client.post("/api/ss-anne/board", json={
            "game_id": game_id,
            "has_ticket": False,
        })
        assert resp.status_code == 400

    def test_board_with_ticket(self):
        """POST /api/ss-anne/board with has_ticket=true should succeed."""
        game_id = _create_test_game()
        resp = client.post("/api/ss-anne/board", json={
            "game_id": game_id,
            "has_ticket": True,
        })
        assert resp.status_code == 200

    def test_rival_before_boarding(self):
        """POST /api/ss-anne/rival before boarding should fail."""
        game_id = _create_test_game()
        resp = client.post("/api/ss-anne/rival", json={
            "game_id": game_id,
        })
        assert resp.status_code == 400


# ──── Events on Board ─────────────────────────────────────

class TestSSAnneEvents:
    def _board(self, game_id: str):
        """Helper: board the ship."""
        client.post("/api/ss-anne/board", json={
            "game_id": game_id,
            "has_ticket": True,
        })

    def test_defeat_rival(self):
        """POST /api/ss-anne/rival after boarding should succeed."""
        game_id = _create_test_game()
        self._board(game_id)
        resp = client.post("/api/ss-anne/rival", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200

    def test_help_captain(self):
        """POST /api/ss-anne/captain after boarding should succeed."""
        game_id = _create_test_game()
        self._board(game_id)
        resp = client.post("/api/ss-anne/captain", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200

    def test_hm_before_captain(self):
        """POST /api/ss-anne/hm before helping captain should fail (400)."""
        game_id = _create_test_game()
        self._board(game_id)
        resp = client.post("/api/ss-anne/hm", json={
            "game_id": game_id,
        })
        assert resp.status_code == 400

    def test_receive_hm(self):
        """POST /api/ss-anne/hm after helping captain should succeed."""
        game_id = _create_test_game()
        self._board(game_id)
        client.post("/api/ss-anne/captain", json={"game_id": game_id})
        resp = client.post("/api/ss-anne/hm", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200

    def test_double_hm(self):
        """POST /api/ss-anne/hm twice should return already_received."""
        game_id = _create_test_game()
        self._board(game_id)
        client.post("/api/ss-anne/captain", json={"game_id": game_id})
        client.post("/api/ss-anne/hm", json={"game_id": game_id})
        resp = client.post("/api/ss-anne/hm", json={"game_id": game_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("already_received") is True


# ──── Full Flow ────────────────────────────────────────────

class TestSSAnneFullFlow:
    def test_full_flow(self):
        """board -> rival -> captain -> hm, all succeed."""
        game_id = _create_test_game()
        # Board
        resp = client.post("/api/ss-anne/board", json={
            "game_id": game_id,
            "has_ticket": True,
        })
        assert resp.status_code == 200
        # Rival
        resp = client.post("/api/ss-anne/rival", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200
        # Captain
        resp = client.post("/api/ss-anne/captain", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200
        # HM
        resp = client.post("/api/ss-anne/hm", json={
            "game_id": game_id,
        })
        assert resp.status_code == 200

    def test_ship_departed_after_hm(self):
        """State should show ship_departed=true after receiving HM."""
        game_id = _create_test_game()
        client.post("/api/ss-anne/board", json={
            "game_id": game_id,
            "has_ticket": True,
        })
        client.post("/api/ss-anne/captain", json={"game_id": game_id})
        client.post("/api/ss-anne/hm", json={"game_id": game_id})
        resp = client.get(f"/api/ss-anne/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ship_departed") is True


# ──── HM01 Item Data ──────────────────────────────────────

class TestHM01ItemData:
    def test_hm01_item_exists(self):
        """items.json must have HM01 Cut (id 53)."""
        items = _load_json("items.json")
        hm01 = None
        if isinstance(items, dict):
            hm01 = items.get("53") or items.get(53)
            if hm01 is None:
                # May be keyed by name or in a list
                for key, val in items.items():
                    if isinstance(val, dict) and val.get("id") == 53:
                        hm01 = val
                        break
        elif isinstance(items, list):
            hm01 = next((i for i in items if i.get("id") == 53), None)
        assert hm01 is not None, "HM01 Cut (id 53) not found in items.json"
