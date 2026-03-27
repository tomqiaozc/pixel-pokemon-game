from fastapi import APIRouter, HTTPException

from ..models.npc import DialogueChoiceRequest, DialogueResponse
from ..services.npc_service import (
    get_dialogue_tree,
    get_npc,
    get_npcs_by_map,
    process_dialogue_choice,
)

router = APIRouter(prefix="/api", tags=["npc"])


@router.get("/npcs/{map_id}")
def list_npcs(map_id: str):
    return get_npcs_by_map(map_id)


@router.get("/dialogue/{npc_id}")
def npc_dialogue(npc_id: str):
    npc = get_npc(npc_id)
    if npc is None:
        raise HTTPException(status_code=404, detail="NPC not found")
    tree = get_dialogue_tree(npc.dialogue_tree_id)
    if tree is None:
        raise HTTPException(status_code=404, detail="Dialogue not found")
    return tree


@router.post("/dialogue/choice", response_model=DialogueResponse)
def dialogue_choice(req: DialogueChoiceRequest):
    next_node, effects = process_dialogue_choice(
        req.npc_id, req.node_id, req.choice_index
    )
    if next_node is None and not effects:
        raise HTTPException(status_code=400, detail="Invalid dialogue state")
    if next_node is None:
        # End of dialogue, but return last effects
        from ..models.npc import DialogueNode
        end_node = DialogueNode(id="end", text="")
        return DialogueResponse(node=end_node, effects=effects if effects else None)
    return DialogueResponse(node=next_node, effects=effects if effects else None)
