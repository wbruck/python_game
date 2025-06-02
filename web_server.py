from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Union
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Attempt to import game components
try:
    from game.board import Board, Position # Added Position
    from game.units.base_unit import Unit
    from game.plants.base_plant import Plant
    from game.units.unit_types import Predator, Grazer
    from game.plants.plant_types import BasicPlant
    GAME_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import all game components: {e}. Some features might not work as expected.")
    GAME_COMPONENTS_AVAILABLE = False
    # Define dummy classes if imports fail
    class Position:
        def __init__(self, x, y): self.x = x; self.y = y
    class Board:
        def __init__(self, width, height): self.width = width; self.height = height; self.grid = [[None for _ in range(width)] for _ in range(height)]
        def get_object(self, x, y): return self.grid[y][x] if 0 <= y < self.height and 0 <= x < self.width else None
        def place_object(self, obj, x, y):
            if 0 <= y < self.height and 0 <= x < self.width:
                obj.x = x; obj.y = y # Set object's position
                self.grid[y][x] = obj
    class Unit:
        def __init__(self, x=0, y=0, unit_type="unknown", hp=10, max_hp=10, energy=10, max_energy=10, strength=1, speed=1, vision=1, alive=True, state="idle", level=1, experience=0, traits=None):
            self.id = id(self); self.x = x; self.y = y; self.unit_type = unit_type; self.hp = hp; self.max_hp = max_hp; self.energy = energy; self.max_energy = max_energy
            self.strength = strength; self.speed = speed; self.vision = vision; self.alive = alive; self.state = state; self.level = level; self.experience = experience; self.traits = traits or []
        def gain_experience(self, event_type, value): self.experience += value # Dummy method

    class Plant:
        def __init__(self, position=None, base_energy=10.0, growth_rate=0.1, regrowth_time=10, symbol="P", energy_content=5.0, growth_stage=1.0, is_alive=True):
            self.id = id(self); self.x = position.x if position else 0; self.y = position.y if position else 0; self.symbol = symbol
            self.energy_content = energy_content; self.base_energy = base_energy; self.growth_stage = growth_stage; self.is_alive = is_alive; self.state = type('PlantState', (), {'current_energy': energy_content, 'growth_progress': growth_stage, 'is_alive': is_alive})() # Dummy state

    if 'Predator' not in globals(): Predator = lambda x,y: Unit(x=x,y=y,unit_type="predator", hp=15, strength=3)
    if 'Grazer' not in globals(): Grazer = lambda x,y: Unit(x=x,y=y,unit_type="grazer", hp=10, speed=2)
    if 'BasicPlant' not in globals(): BasicPlant = lambda position, base_energy, growth_rate, regrowth_time: Plant(position=position, symbol="B", base_energy=base_energy, growth_rate=growth_rate, regrowth_time=regrowth_time)

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for API responses
class Entity(BaseModel):
    id: str
    type: str  # "unit" or "plant"
    x: int
    y: int
    unit_type: Optional[str] = None
    symbol: Optional[str] = None

class BoardResponse(BaseModel):
    width: int
    height: int
    entities: List[Entity]

class UnitStats(BaseModel):
    id: str
    type: str = "unit"
    unit_type: Optional[str] = None
    x: int
    y: int
    hp: int
    max_hp: int
    energy: int
    max_energy: int
    strength: int
    speed: int
    vision: int
    alive: bool
    state: str
    level: Optional[int] = None
    experience: Optional[int] = None
    traits: Optional[List[str]] = None

class PlantStats(BaseModel):
    id: str
    type: str = "plant"
    symbol: Optional[str] = None
    x: int
    y: int
    energy_content: float # Current energy stored
    base_energy: float    # Max energy or potential energy
    growth_stage: float   # E.g., 0.0 to 1.0
    is_alive: bool


# Global store for entities, populated by get_board_state
entity_map: Dict[str, object] = {}

# Shared game board instance
shared_game_board: Optional[Board] = None

def set_game_board(board_instance: Board):
    """Sets the global game board instance for the web server."""
    global shared_game_board
    shared_game_board = board_instance

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/board", response_model=BoardResponse)
async def get_board_state():
    global entity_map # Ensure we're modifying the global map
    entity_map.clear() # Clear map on each call
    entities: List[Entity] = []

    if shared_game_board is None:
        # Return an empty board or a default state if the game board isn't initialized yet
        return BoardResponse(width=0, height=0, entities=[])

    # Use the shared_game_board
    current_board = shared_game_board

    for y_coord in range(current_board.height):
        for x_coord in range(current_board.width):
            obj = current_board.get_object(x_coord, y_coord)
            if obj:
                # Ensure obj has an id, x, and y for robust entity creation
                obj_id_val = getattr(obj, 'id', id(obj))
                entity_id = f"{type(obj).__name__}_{obj_id_val}"

                # Store object in map
                entity_map[entity_id] = obj

                entity_type = "unknown"
                unit_type_attr: Optional[str] = None
                plant_symbol_attr: Optional[str] = None

                if isinstance(obj, Unit) or type(obj).__name__ in ["Unit", "Predator", "Grazer"]: # Check type name for dummies
                    entity_type = "unit"
                    unit_type_attr = getattr(obj, 'unit_type', type(obj).__name__)
                elif isinstance(obj, Plant) or type(obj).__name__ in ["Plant", "BasicPlant"]: # Check type name for dummies
                    entity_type = "plant"
                    plant_symbol_attr = getattr(obj, 'symbol', 'P')

                entities.append(Entity(
                    id=entity_id,
                    type=entity_type,
                    x=getattr(obj, 'x', x_coord), # Prefer actual obj.x if available
                    y=getattr(obj, 'y', y_coord), # Prefer actual obj.y if available
                    unit_type=unit_type_attr,
                    symbol=plant_symbol_attr
                ))
    return BoardResponse(width=current_board.width, height=current_board.height, entities=entities)

@app.get("/entity/{entity_id}", response_model=Union[UnitStats, PlantStats])
async def get_entity_details(entity_id: str):
    obj = entity_map.get(entity_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Entity not found")

    obj_x = getattr(obj, 'x', -1) # Default if not set
    obj_y = getattr(obj, 'y', -1) # Default if not set

    if isinstance(obj, Unit) or type(obj).__name__ in ["Unit", "Predator", "Grazer"]: # Support dummy types
        return UnitStats(
            id=entity_id,
            unit_type=getattr(obj, 'unit_type', type(obj).__name__),
            x=obj_x,
            y=obj_y,
            hp=getattr(obj, 'hp', 0),
            max_hp=getattr(obj, 'max_hp', 0),
            energy=getattr(obj, 'energy', 0),
            max_energy=getattr(obj, 'max_energy', 0),
            strength=getattr(obj, 'strength', 0),
            speed=getattr(obj, 'speed', 0),
            vision=getattr(obj, 'vision', 0),
            alive=getattr(obj, 'alive', False),
            state=getattr(obj, 'state', 'unknown'),
            level=getattr(obj, 'level', None),
            experience=getattr(obj, 'experience', None),
            traits=getattr(obj, 'traits', None)
        )
    elif isinstance(obj, Plant) or type(obj).__name__ in ["Plant", "BasicPlant"]: # Support dummy types
        # For plants, state attributes might be nested or direct
        plant_state = getattr(obj, 'state', None)
        energy_content = getattr(plant_state, 'current_energy', getattr(obj, 'energy_content', 0.0))
        growth_stage = getattr(plant_state, 'growth_progress', getattr(obj, 'growth_stage', 0.0))
        is_alive = getattr(plant_state, 'is_alive', getattr(obj, 'is_alive', False))

        return PlantStats(
            id=entity_id,
            symbol=getattr(obj, 'symbol', 'P'),
            x=obj_x,
            y=obj_y,
            energy_content=energy_content,
            base_energy=getattr(obj, 'base_energy', 0.0),
            growth_stage=growth_stage,
            is_alive=is_alive
        )
    else:
        # This case should ideally not be reached if entity_map is populated correctly
        print(f"Unknown entity type for ID {entity_id}: {type(obj).__name__}")
        raise HTTPException(status_code=500, detail=f"Unknown entity type: {type(obj).__name__}")

if __name__ == "__main__":
    import uvicorn
    print("Starting Uvicorn server for development (web_server.py)...")
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000, reload=True)
