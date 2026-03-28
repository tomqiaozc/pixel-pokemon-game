from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.battle import router as battle_router
from .routes.encounter import router as encounter_router
from .routes.evolution import router as evolution_router
from .routes.game import router as game_router
from .routes.gym import router as gym_router
from .routes.items import router as items_router
from .routes.leaderboard import router as leaderboard_router
from .routes.legendary import router as legendary_router
from .routes.map import router as map_router
from .routes.npc import router as npc_router
from .routes.pokedex import router as pokedex_router
from .routes.pokemon import router as pokemon_router
from .routes.pvp import router as pvp_router
from .routes.quest import router as quest_router
from .routes.rival import router as rival_router
from .routes.trade import router as trade_router

app = FastAPI(title="Pixel Pokemon Game API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pokemon_router)
app.include_router(game_router)
app.include_router(encounter_router)
app.include_router(battle_router)
app.include_router(npc_router)
app.include_router(evolution_router)
app.include_router(gym_router)
app.include_router(items_router)
app.include_router(map_router)
app.include_router(pokedex_router)
app.include_router(trade_router)
app.include_router(pvp_router)
app.include_router(leaderboard_router)
app.include_router(quest_router)
app.include_router(rival_router)
app.include_router(legendary_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
