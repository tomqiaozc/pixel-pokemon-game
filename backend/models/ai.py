from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AIDecision(BaseModel):
    action_type: str  # "fight", "switch", "item"
    move_index: Optional[int] = None
    switch_to: Optional[int] = None
    item_id: Optional[str] = None
    reasoning: str = ""


class AIContext(BaseModel):
    battle_id: str
    difficulty: str = "normal"  # "easy", "normal", "hard"
