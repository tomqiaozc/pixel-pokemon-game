from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..models.npc import DialogueNode, DialogueTree, NPC

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_npcs: list[NPC] = []
_dialogues: dict[str, DialogueTree] = {}


def _load_npcs() -> None:
    global _npcs
    with open(DATA_DIR / "npcs.json") as f:
        raw = json.load(f)
    _npcs = [NPC(**n) for n in raw]


def _load_dialogues() -> None:
    global _dialogues
    with open(DATA_DIR / "dialogues.json") as f:
        raw = json.load(f)
    _dialogues = {k: DialogueTree(**v) for k, v in raw.items()}


def get_npcs_by_map(map_id: str) -> list[NPC]:
    if not _npcs:
        _load_npcs()
    return [n for n in _npcs if n.map_id == map_id]


def get_npc(npc_id: str) -> Optional[NPC]:
    if not _npcs:
        _load_npcs()
    for n in _npcs:
        if n.id == npc_id:
            return n
    return None


def get_dialogue_tree(tree_id: str) -> Optional[DialogueTree]:
    if not _dialogues:
        _load_dialogues()
    return _dialogues.get(tree_id)


def get_dialogue_node(tree: DialogueTree, node_id: str) -> Optional[DialogueNode]:
    for node in tree.nodes:
        if node.id == node_id:
            return node
    return None


def process_dialogue_choice(
    npc_id: str,
    node_id: str,
    choice_index: Optional[int] = None,
) -> tuple[Optional[DialogueNode], list[dict]]:
    """Process a dialogue interaction and return the next node + effects."""
    npc = get_npc(npc_id)
    if npc is None:
        return None, []

    tree = get_dialogue_tree(npc.dialogue_tree_id)
    if tree is None:
        return None, []

    current = get_dialogue_node(tree, node_id)
    if current is None:
        return None, []

    effects: list[dict] = []

    # Process action on current node
    if current.action:
        effects.append(current.action.model_dump())

    # Determine next node
    next_id = None
    if current.choices and choice_index is not None:
        if 0 <= choice_index < len(current.choices):
            next_id = current.choices[choice_index].next
    elif current.next:
        next_id = current.next

    if next_id is None:
        return None, effects

    next_node = get_dialogue_node(tree, next_id)
    if next_node and next_node.action:
        effects.append(next_node.action.model_dump())

    return next_node, effects
