"""Tests for Sprint 12 QA-A3: Bill's House Event.

These tests verify Bill's NPC, dialogue, transformation event flow,
S.S. Ticket reward, and Route 25 trainers.
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.map_service import get_map
from backend.services.gym_service import get_trainer
from backend.services.npc_service import get_npc
from backend.services.game_service import create_game

client = TestClient(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def _create_test_game() -> str:
    game = create_game("BillTester", 1)
    return game["id"]


# ──── Bill NPC & Dialogue Data ──────────────────────────────

class TestBillNPCData:
    def test_bill_npc_exists(self):
        """npcs.json must have a Bill NPC."""
        bill = get_npc("bill")
        assert bill is not None, "Bill NPC not found"

    def test_bill_dialogue_exists(self):
        """dialogues.json must have bill dialogue."""
        dialogues = _load_json("dialogues.json")
        # Bill's dialogue may be keyed by NPC id or dialogue tree id
        bill_dialogue = None
        if isinstance(dialogues, dict):
            bill_dialogue = dialogues.get("bill") or dialogues.get("bill_dialogue")
        elif isinstance(dialogues, list):
            bill_dialogue = next((d for d in dialogues if d.get("id") == "bill" or d.get("id") == "bill_dialogue"), None)
        assert bill_dialogue is not None, "Bill dialogue not found in dialogues.json"


# ──── Bill Event State Flow ─────────────────────────────────

class TestBillEventFlow:
    def test_bill_initial_state(self):
        """GET /api/bill/state/{game_id} should return 'pokemon' initially."""
        game_id = _create_test_game()
        resp = client.get(f"/api/bill/state/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("state") == "pokemon"

    def test_start_transformation(self):
        """POST /api/bill/transform should change Bill's state."""
        game_id = _create_test_game()
        resp = client.post("/api/bill/transform", json={"game_id": game_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("state") in ("transforming", "human")

    def test_complete_transformation(self):
        """POST /api/bill/complete should advance state to 'human'."""
        game_id = _create_test_game()
        client.post("/api/bill/transform", json={"game_id": game_id})
        resp = client.post("/api/bill/complete", json={"game_id": game_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("state") == "human"

    def test_give_ss_ticket(self):
        """POST /api/bill/ticket should give S.S. Ticket after transformation."""
        game_id = _create_test_game()
        client.post("/api/bill/transform", json={"game_id": game_id})
        client.post("/api/bill/complete", json={"game_id": game_id})
        resp = client.post("/api/bill/ticket", json={"game_id": game_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("state") == "ticket_given"

    def test_ticket_before_transform(self):
        """Cannot get S.S. Ticket before transformation is complete."""
        game_id = _create_test_game()
        resp = client.post("/api/bill/ticket", json={"game_id": game_id})
        assert resp.status_code >= 400

    def test_double_transformation(self):
        """Transformation should be idempotent if already transformed."""
        game_id = _create_test_game()
        client.post("/api/bill/transform", json={"game_id": game_id})
        client.post("/api/bill/complete", json={"game_id": game_id})
        # Trying to transform again should not error
        resp = client.post("/api/bill/transform", json={"game_id": game_id})
        assert resp.status_code == 200

    def test_bill_state_flow(self):
        """Full flow: pokemon -> transforming -> human -> ticket_given."""
        game_id = _create_test_game()
        # Initial
        resp = client.get(f"/api/bill/state/{game_id}")
        assert resp.json().get("state") == "pokemon"
        # Transform
        client.post("/api/bill/transform", json={"game_id": game_id})
        resp = client.get(f"/api/bill/state/{game_id}")
        assert resp.json().get("state") in ("transforming", "human")
        # Complete
        client.post("/api/bill/complete", json={"game_id": game_id})
        resp = client.get(f"/api/bill/state/{game_id}")
        assert resp.json().get("state") == "human"
        # Ticket
        client.post("/api/bill/ticket", json={"game_id": game_id})
        resp = client.get(f"/api/bill/state/{game_id}")
        assert resp.json().get("state") == "ticket_given"


# ──── Route 25 Trainers ─────────────────────────────────────

class TestRoute25Trainers:
    def test_route25_hiker_exists(self):
        """trainers.json must have route25_hiker_1."""
        trainer = get_trainer("route25_hiker_1")
        assert trainer is not None, "route25_hiker_1 not found"
        assert len(trainer.pokemon_team) >= 1

    def test_route25_lass_exists(self):
        """trainers.json must have route25_lass_1."""
        trainer = get_trainer("route25_lass_1")
        assert trainer is not None, "route25_lass_1 not found"
        assert len(trainer.pokemon_team) >= 1


# ──── Bill's House Map ──────────────────────────────────────

class TestBillsHouseMap:
    def test_bills_house_has_bill_npc(self):
        """bills_house map should contain Bill NPC."""
        game_map = get_map("bills_house")
        assert game_map is not None
        npc_ids = {n.npc_id if hasattr(n, 'npc_id') else n.get("npc_id")
                   for n in game_map.npcs}
        assert "bill" in npc_ids, "Bill NPC not in bills_house map"
