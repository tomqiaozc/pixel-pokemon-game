from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DialogueAction(BaseModel):
    type: str  # "set_flag", "give_item", "heal", "start_battle"
    flag: Optional[str] = None
    value: Optional[str] = None
    item_id: Optional[int] = None
    quantity: Optional[int] = None


class DialogueChoice(BaseModel):
    label: str
    next: Optional[str] = None


class DialogueNode(BaseModel):
    id: str
    text: str
    next: Optional[str] = None
    choices: Optional[list[DialogueChoice]] = None
    action: Optional[DialogueAction] = None


class DialogueTree(BaseModel):
    id: str
    nodes: list[DialogueNode]


class NPC(BaseModel):
    id: str
    name: str
    sprite_id: str
    position: dict  # {x, y}
    map_id: str
    facing: str = "down"  # up, down, left, right
    npc_type: str = "generic"  # generic, professor, nurse, shopkeeper, trainer
    dialogue_tree_id: str


class DialogueChoiceRequest(BaseModel):
    npc_id: str
    node_id: str
    choice_index: Optional[int] = None


class DialogueResponse(BaseModel):
    node: DialogueNode
    effects: Optional[list[dict]] = None
