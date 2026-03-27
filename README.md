# Pixel Pokemon Game

A retro pixel-art Pokemon game built with HTML5 Canvas and Python FastAPI.

## Features

### Implemented
- **Overworld Exploration** — tile-based map with 10 terrain types (grass, water, trees, buildings, etc.), smooth 60fps movement, collision detection, camera following
- **Player Movement** — 4-direction walking with WASD/arrow keys, pixel-art character sprite
- **Starter Pokemon Selection** — choose from 3 starter Pokemon with preview, stats, and description
- **Turn-based Battle System** — battle UI with HP bars, move selection menu, attack animations
- **Wild Pokemon Encounters** — random encounters in tall grass with configurable spawn tables per area
- **Pokemon Data** — 9 starter Pokemon with full stats, types, and movesets

### Roadmap
- NPC dialogue system
- Battle engine logic (damage calc, type effectiveness)
- Pokemon evolution & EXP
- Items, inventory & shop
- Pokemon Center & PC Box
- Pokedex
- Gym battles & badges
- Multiplayer trading & battles

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5 Canvas, Vanilla JavaScript |
| Backend | Python 3.11+, FastAPI, Pydantic |
| Art | Programmatic pixel art (drawn via Canvas API) |
| Storage | In-memory (JSON seed data) |

## Getting Started

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/pokemon` | List all Pokemon |
| GET | `/api/pokemon/{id}` | Get Pokemon by ID |
| POST | `/api/game/new` | Create new game (body: `player_name`, `starter_pokemon_id`) |
| GET | `/api/game/{id}` | Get game state |
| POST | `/api/game/{id}/save` | Save game state |
| POST | `/api/encounter/check` | Check for wild encounter (body: `area_id`) |
| GET | `/api/encounter/species` | List all species |
| GET | `/api/encounter/species/{id}` | Get species details |
| GET | `/api/encounter/generate/{species_id}/{level}` | Generate wild Pokemon |

## Project Structure

```
pixel-pokemon-game/
├── frontend/
│   ├── index.html              # Entry point
│   ├── css/style.css           # Game styling
│   └── js/
│       ├── game.js             # Main game loop & state
│       ├── renderer.js         # Canvas pixel rendering
│       ├── map.js              # Tile map & collision
│       ├── sprites.js          # Programmatic sprite drawing
│       ├── input.js            # Keyboard input handler
│       ├── starter.js          # Starter selection screen
│       ├── battle.js           # Battle UI & animations
│       └── encounters.js       # Wild encounter triggers
├── backend/
│   ├── main.py                 # FastAPI app setup
│   ├── requirements.txt
│   ├── models/
│   │   ├── pokemon.py          # Pokemon & move models
│   │   ├── player.py           # Player & team models
│   │   └── encounter.py        # Encounter models
│   ├── routes/
│   │   ├── pokemon.py          # Pokemon CRUD endpoints
│   │   ├── game.py             # Game state endpoints
│   │   └── encounter.py        # Encounter endpoints
│   ├── services/
│   │   ├── game_service.py     # Game logic & state
│   │   └── encounter_service.py # Encounter generation
│   └── data/
│       ├── pokemon_data.json   # Base Pokemon stats
│       ├── pokemon_species.json # Species definitions
│       ├── moves.json          # Move data
│       └── encounter_tables.json # Area spawn tables
└── README.md
```

## Controls

| Key | Action |
|-----|--------|
| W / Arrow Up | Move up |
| A / Arrow Left | Move left |
| S / Arrow Down | Move down |
| D / Arrow Right | Move right |
| Enter / Space | Confirm / Interact |
| Escape | Cancel / Menu |
