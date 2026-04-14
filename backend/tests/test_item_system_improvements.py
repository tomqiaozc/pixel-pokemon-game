"""Tests for Sprint 12 QA-A1: Item System Improvements.

These tests verify the new items (Nugget, S.S. Ticket), the give_item()
function, and key item protection (cannot toss or sell key items).
Written ahead of backend implementation — will FAIL until wiring is done.
"""
from __future__ import annotations

import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.item_service import (
    get_all_items,
    get_item,
    get_inventory,
    give_item,
    sell_item,
    toss_item,
    buy_item,
)
from backend.services.game_service import create_game, get_game

client = TestClient(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load_items_json():
    with open(os.path.join(DATA_DIR, "items.json")) as f:
        return json.load(f)


def _create_test_game() -> str:
    game = create_game("ItemTester", 1)
    return game["id"]


# ──── New Item Data Validation ──────────────────────────────

class TestNewItemData:
    def test_nugget_item_exists(self):
        """items.json must contain Nugget with id 51."""
        items = _load_items_json()
        nugget = next((i for i in items if i["id"] == 51), None)
        assert nugget is not None, "Nugget (id 51) not found in items.json"
        assert nugget["name"] == "Nugget"

    def test_ss_ticket_item_exists(self):
        """items.json must contain S.S. Ticket with id 52."""
        items = _load_items_json()
        ticket = next((i for i in items if i["id"] == 52), None)
        assert ticket is not None, "S.S. Ticket (id 52) not found in items.json"
        assert ticket["name"] == "S.S. Ticket"

    def test_nugget_category(self):
        """Nugget should have category 'treasure'."""
        items = _load_items_json()
        nugget = next(i for i in items if i["id"] == 51)
        assert nugget["category"] == "treasure"

    def test_ss_ticket_category(self):
        """S.S. Ticket should have category 'key_item'."""
        items = _load_items_json()
        ticket = next(i for i in items if i["id"] == 52)
        assert ticket["category"] == "key_item"

    def test_nugget_sell_price(self):
        """Nugget sell_price should be 5000."""
        items = _load_items_json()
        nugget = next(i for i in items if i["id"] == 51)
        assert nugget["sell_price"] == 5000

    def test_ss_ticket_not_sellable(self):
        """S.S. Ticket sell_price should be 0."""
        items = _load_items_json()
        ticket = next(i for i in items if i["id"] == 52)
        assert ticket["sell_price"] == 0


# ──── Give Item Functionality ───────────────────────────────

class TestGiveItem:
    def test_give_item_endpoint(self):
        """POST /api/inventory/give should return 200 with valid item."""
        game_id = _create_test_game()
        resp = client.post("/api/inventory/give", json={
            "game_id": game_id,
            "item_id": 1,
            "quantity": 1,
        })
        assert resp.status_code == 200

    def test_give_item_adds_to_inventory(self):
        """After giving an item, it should appear in the player's inventory."""
        game_id = _create_test_game()
        give_item(game_id, 1, 1)
        inv = get_inventory(game_id)
        assert any(e.item_id == 1 for e in inv), "Given item not found in inventory"

    def test_give_item_quantity(self):
        """Giving 3 of the same item should show quantity 3."""
        game_id = _create_test_game()
        give_item(game_id, 1, 3)
        inv = get_inventory(game_id)
        entry = next(e for e in inv if e.item_id == 1)
        assert entry.quantity == 3

    def test_give_item_invalid_item(self):
        """POST with an invalid item_id should return an error."""
        game_id = _create_test_game()
        resp = client.post("/api/inventory/give", json={
            "game_id": game_id,
            "item_id": 99999,
            "quantity": 1,
        })
        assert resp.status_code >= 400


# ──── Key Item Protection ───────────────────────────────────

class TestKeyItemProtection:
    def test_toss_key_item_blocked(self):
        """Cannot toss a key item (category 'key_item')."""
        game_id = _create_test_game()
        give_item(game_id, 52, 1)  # Give S.S. Ticket (key_item)
        with pytest.raises((ValueError, Exception)):
            toss_item(game_id, 52, 1)

    def test_sell_key_item_blocked(self):
        """Cannot sell a key item (category 'key_item')."""
        game_id = _create_test_game()
        give_item(game_id, 52, 1)  # Give S.S. Ticket (key_item)
        result = sell_item(game_id, 52, 1)
        # Either raises an error or returns failure
        if result is not None:
            assert result.success is False
