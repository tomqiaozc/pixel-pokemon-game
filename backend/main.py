from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.encounter import router as encounter_router
from .routes.game import router as game_router
from .routes.pokemon import router as pokemon_router

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


@app.get("/api/health")
def health():
    return {"status": "ok"}
