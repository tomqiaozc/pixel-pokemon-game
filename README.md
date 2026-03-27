# Pixel Pokemon Game

A retro pixel-art Pokemon game built with HTML5 Canvas and Python FastAPI.

## Features

### Core Gameplay
- **Overworld Exploration** — 5 interconnected maps (Pallet Town, Route 1, Viridian City, Route 2, Pewter City) with smooth 60fps movement, collision detection, camera following
- **Player Movement** — 4-direction walking with WASD/arrow keys, pixel-art character sprite
- **Starter Pokemon Selection** — choose from Bulbasaur, Charmander, or Squirtle with IV-calculated stats
- **Turn-based Battle System** — Gen 1-style damage formula with STAB, type effectiveness (18 types), critical hits, speed-based turn order
- **Wild Pokemon Encounters** — random encounters in tall grass with per-route spawn tables and configurable rates
- **Pokemon Catching** — Pokeball catch mechanic with catch rate calculation, auto-deposit to PC when party full
- **Trainer Battles** — line-of-sight trainer encounters, 3-tier AI (wild/trainer/leader), pre-battle dialogue

### Pokemon Systems
- **Evolution & EXP** — level-up evolution with animations, EXP curve, move learning on evolution
- **Items & Inventory** — buy/sell at shops, use potions/revives/status heals, Pokeball management
- **Pokemon Center** — heal team, PC Box for Pokemon storage
- **Pokedex** — seen/caught tracking, species list with detail view
- **Status Conditions** — 6 status effects, volatile conditions, stat stages (-6 to +6)

### World & NPCs
- **Multi-map System** — seamless map transitions with fade effects, map name popups
- **Gym Battles** — Pewter City gym with Brock, badge collection, gym puzzle layouts
- **NPC Dialogue** — typewriter text, dialogue trees with branching choices
- **Signs & Ledges** — interactive sign posts, one-way ledge jumping with arc animation
- **Trainer Encounters** — line-of-sight detection, "!" alert, walk-to-player trigger

### UI
- **Pause Menu** — party management, inventory, save/load
- **Badge Case** — 8 Kanto badge slots with shine animation
- **Battle UI** — HP bars, move selection with PP/type display, Bag/Pokemon/Run options

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5 Canvas, Vanilla JavaScript |
| Backend | Python 3.11+, FastAPI, Pydantic |
| Art | Programmatic pixel art (drawn via Canvas API) |
| Storage | In-memory (JSON seed data) |
| Tests | pytest (backend), 250+ automated tests |

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

### Game & Pokemon
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/pokemon` | List all Pokemon |
| GET | `/api/pokemon/{id}` | Get Pokemon by ID |
| POST | `/api/game/new` | Create new game |
| GET | `/api/game/{id}` | Get game state |
| POST | `/api/game/{id}/save` | Save game state |

### Battle
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/battle/start` | Initialize battle |
| POST | `/api/battle/action` | Fight, catch, or run |
| GET | `/api/battle/state/{id}` | Get battle state |
| POST | `/api/battle/catch` | Attempt to catch Pokemon |

### Encounter & Maps
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/encounter/check` | Check for wild encounter |
| GET | `/api/encounter/species` | List all species |
| GET | `/api/maps/{map_id}` | Get map data |
| GET | `/api/maps/current/{game_id}` | Get current map |

### Evolution & Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/evolution/evolve` | Evolve a Pokemon |
| POST | `/api/evolution/award-exp` | Award EXP after battle |
| GET | `/api/inventory/{game_id}` | Get player inventory |
| POST | `/api/shop/buy` | Buy items |
| POST | `/api/shop/sell` | Sell items |

### Pokemon Center, Pokedex & Gyms
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pokemon-center/heal/{game_id}` | Heal team |
| GET | `/api/pokedex/{game_id}` | Get Pokedex data |
| GET | `/api/npcs/{map_id}` | Get NPCs for map |
| GET | `/api/gyms/{gym_id}` | Get gym data |

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
│       ├── maploader.js        # Multi-map loading & transitions
│       ├── routes.js           # Route/town map definitions
│       ├── sprites.js          # Programmatic sprite drawing
│       ├── input.js            # Keyboard input handler
│       ├── starter.js          # Starter selection screen
│       ├── battle.js           # Battle UI & animations
│       ├── encounters.js       # Wild encounter triggers
│       ├── evolution.js        # Evolution animations
│       ├── menu.js             # Pause menu & inventory
│       ├── dialogue.js         # NPC dialogue system
│       ├── npc.js              # NPC rendering & interaction
│       ├── pokecenter.js       # Pokemon Center UI
│       ├── pokedex.js          # Pokedex UI
│       ├── gym.js              # Gym interior layouts
│       ├── badges.js           # Badge case UI
│       ├── trainer.js          # Trainer battle UI
│       ├── trainerencounter.js # Trainer line-of-sight
│       ├── signs.js            # Sign interaction
│       └── ledges.js           # Ledge jumping
├── backend/
│   ├── main.py                 # FastAPI app setup
│   ├── requirements.txt
│   ├── models/                 # Pydantic data models
│   │   ├── pokemon.py          # Pokemon, moves, stats
│   │   ├── player.py           # Player, team, inventory
│   │   ├── battle.py           # Battle state & actions
│   │   ├── encounter.py        # Wild encounters
│   │   ├── evolution.py        # Evolution & EXP
│   │   ├── item.py             # Items & shop
│   │   ├── map.py              # Maps & routes
│   │   ├── npc.py              # NPCs & dialogue
│   │   ├── gym.py              # Gyms & badges
│   │   ├── pokedex.py          # Pokedex tracking
│   │   └── ai.py               # Trainer AI models
│   ├── routes/                 # API endpoint handlers
│   ├── services/               # Business logic
│   ├── data/                   # JSON seed data
│   └── tests/                  # pytest test suites
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
| Escape | Pause menu |
| 1-4 | Select move in battle |

## Development

This project is actively developed with sprint-based planning and continuous delivery. 250+ automated tests cover all API endpoints, battle mechanics, evolution, items, encounters, and integration flows.
