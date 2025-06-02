from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Union, Optional, Set

from game.board import Board
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import UNIT_TYPES
from game.plants.plant_types import PLANT_TYPES
from game.units.base_unit import BaseUnit
from game.plants.base_plant import BasePlant

# Basic FastAPI app setup
app = FastAPI()

# Dictionary to store GameLoop objects
game_instances: dict[str, GameLoop] = {}
entity_map: Dict[str, Dict[str, Any]] = {} # Global entity map for now

# Flag to indicate if game components are available
GAME_COMPONENTS_AVAILABLE = False

try:
    # Attempt to import all necessary game components
    if Board and GameLoop and Config and UNIT_TYPES and PLANT_TYPES and BaseUnit and BasePlant:
        GAME_COMPONENTS_AVAILABLE = True
except ImportError:
    # Handle cases where game components might not be fully available
    # For now, we'll just print a message, but this could be more sophisticated
    print("Warning: Some game components could not be imported. API might not function correctly.")


def create_default_game():
    """
    Initializes a Board and a GameLoop with a default configuration
    and stores it in the game_instances dictionary.
    """
    if not GAME_COMPONENTS_AVAILABLE:
        print("Cannot create default game: Essential game components are missing.")
        return

    try:
        # Load default configuration
        # Assuming config.json is in the root directory and provides necessary settings
        config = Config('config.json') # Changed GameConfig to Config and removed load_config call
    except Exception as e:
        print(f"Failed to load game configuration from 'config.json': {e}. Using hardcoded defaults.")
        # Hardcoded sensible defaults as a fallback
        # Create a new Config instance for defaults if loading failed
        config = Config() # This will use DEFAULT_CONFIG from Config class
        # We will rely on DEFAULT_CONFIG within the Config class,
        # but we can override specific values if absolutely necessary.
        # For now, let's assume DEFAULT_CONFIG is sufficient.
        # If specific overrides are needed:
        # config.set("board", "width", 10)
        # config.set("board", "height", 5)
        # config.set("game", "turn_delay", 0.1) # Assuming game_speed maps to turn_delay
        # config.set("plants", "initial_sunlight", 100) # Assuming this config exists

    # Access config values using the get method
    board_width = config.get("board", "width")
    board_height = config.get("board", "height")
    # game_speed = config.get("game", "turn_delay") # Example, if needed by GameLoop
    # initial_sunlight = config.get("plants", "initial_sunlight") # Example

    if board_width is None or board_height is None:
        print("Critical configuration (board width/height) missing. Using emergency fallbacks.")
        board_width = 10 # Emergency fallback
        board_height = 5  # Emergency fallback

    board = Board(board_width, board_height)
    # GameLoop needs the config object, not individual values like sunlight yet.
    # The GameLoop constructor might need adaptation if it expects specific config values directly.
    # For now, passing the whole config object.
    game_loop = GameLoop(board, config)

    # Store the created GameLoop instance
    game_instances["default_game"] = game_loop
    print("Default game instance created successfully.")


# Call create_default_game() when the module is loaded
if GAME_COMPONENTS_AVAILABLE:
    create_default_game()
else:
    print("Default game not created due to missing components.")

# Placeholder for API endpoints (to be added in subsequent steps)
@app.get("/")
async def root():
    return {"message": "Welcome to the Plant vs. Zombie API Server!"}

# Pydantic models for API response
class Entity(BaseModel):
    id: str
    type: str  # "unit" or "plant"
    x: int
    y: int
    name: str # e.g. "Peashooter", "Zombie"
    details: Dict[str, Any] = {} # For extra info like health, energy for the entity details endpoint

class BoardResponse(BaseModel):
    game_id: str
    turn: int
    board_width: int
    board_height: int
    entities: List[Entity]
    message: str = ""

# Global entity map, cleared and repopulated on each /update or /board call
# This will store more detailed info about each entity, keyed by its unique ID
# The structure might be: entity_map[game_id][entity_api_id] = entity_object_or_detailed_dict

def get_entity_api_id(obj: Any, game_id: str) -> str:
    """Generates a unique API ID for a game entity."""
    # Prefix with game_id to ensure uniqueness across multiple games if entity_map becomes truly global
    # For now, entity_map is cleared per call for a specific game_id, so game_id prefix is for future-proofing
    obj_type_name = type(obj).__name__
    # getattr(obj, 'id', id(obj)) can be problematic if obj.id is not unique enough or id(obj) changes.
    # Using a more robust 'uuid' if available, or a combination of type and internal id.
    internal_id = getattr(obj, 'uuid', getattr(obj, 'id', id(obj)))
    return f"{game_id}_{obj_type_name}_{internal_id}"

@app.post("/game/{game_id}/update", response_model=BoardResponse)
async def update_game_state(game_id: str):
    if not GAME_COMPONENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Game components are not available.")

    if game_id not in game_instances:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found.")

    game_loop = game_instances[game_id]

    # Clear the entity map for the current game_id before processing the turn and repopulating
    # If entity_map becomes structured per game_id, this would be:
    # if game_id in entity_map: entity_map[game_id].clear()
    # else: entity_map[game_id] = {}
    # For a simple global map:
    # current_game_entity_map: Dict[str, Any] = {} # Moved to helper

    game_loop.process_turn()

    entities_on_board, current_game_entity_map = _get_board_state_and_populate_entity_map(game_loop, game_id)

    # Update global entity_map
    global entity_map
    entity_map.clear()
    entity_map.update(current_game_entity_map)

    return BoardResponse(
        game_id=game_id,
        turn=game_loop.current_turn,
        board_width=game_loop.board.width,
        board_height=game_loop.board.height,
        entities=entities_on_board,
        message=f"Turn {game_loop.current_turn} processed for game '{game_id}'."
    )

def _get_board_state_and_populate_entity_map(game_loop: GameLoop, game_id: str) -> tuple[List[Entity], Dict[str, Any]]:
    """
    Scans the board, creates a list of Entity models, and populates a dictionary for the entity_map.
    """
    entities_on_board: List[Entity] = []
    current_game_entity_map: Dict[str, Any] = {}

    for y, row in enumerate(game_loop.board.grid):
        for x, cell_content_list in enumerate(row):
            for obj in cell_content_list:
                entity_api_id = get_entity_api_id(obj, game_id)
                entity_type = ""
                name = ""
                details = {}

                if isinstance(obj, BaseUnit):
                    entity_type = "unit"
                    name = getattr(obj, 'unit_type', type(obj).__name__)
                    details = {
                        "health": getattr(obj, 'health', None),
                        "energy": getattr(obj, 'energy', None),
                        "state": getattr(obj, 'state', None),
                        "age": getattr(obj, 'age', None),
                        # Add any other relevant unit details
                    }
                elif isinstance(obj, BasePlant):
                    entity_type = "plant"
                    name = getattr(obj, 'plant_type', type(obj).__name__) # e.g., "Sunflower" from a subclass or "Plant"

                    # Access state attributes safely
                    plant_state = getattr(obj, 'state', None)
                    energy = getattr(plant_state, 'energy_content', None) if plant_state else None
                    growth_stage = getattr(plant_state, 'growth_stage', None) if plant_state else None

                    details = {
                        "health": getattr(obj, 'health', None), # Remains None if not present
                        "energy": energy,
                        "age": getattr(obj, 'age', None), # Remains None if not present
                        "growth_stage": growth_stage,
                        "symbol": getattr(obj, 'symbol', '?'), # Use getattr for symbol for safety
                    }

                if entity_type:
                    entities_on_board.append(Entity(id=entity_api_id, type=entity_type, x=x, y=y, name=name, details=details))
                    current_game_entity_map[entity_api_id] = obj # Store actual object

    return entities_on_board, current_game_entity_map

@app.get("/game/{game_id}/board", response_model=BoardResponse)
async def get_board_state(game_id: str):
    if not GAME_COMPONENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Game components are not available.")

    if game_id not in game_instances:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found.")

    game_loop = game_instances[game_id]

    entities_on_board, current_game_entity_map = _get_board_state_and_populate_entity_map(game_loop, game_id)

    # Update global entity_map
    global entity_map
    entity_map.clear()
    entity_map.update(current_game_entity_map)

    return BoardResponse(
        game_id=game_id,
        turn=game_loop.current_turn,
        board_width=game_loop.board.width,
        board_height=game_loop.board.height,
        entities=entities_on_board,
        message=f"Current board state for game '{game_id}' at turn {game_loop.current_turn}."
    )

# Pydantic models for entity details
class UnitStats(BaseModel):
    id: str
    type: str = "unit"
    unit_type: Optional[str] = None
    x: int
    y: int
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    energy: Optional[int] = None
    max_energy: Optional[int] = None
    strength: Optional[int] = None
    speed: Optional[int] = None
    vision: Optional[int] = None
    alive: bool
    state: Optional[str] = None
    level: Optional[int] = None
    experience: Optional[int] = None
    traits: Optional[Set[str]] = set()
    # Add any other relevant fields from BaseUnit

class PlantStats(BaseModel):
    id: str
    type: str = "plant"
    plant_type: Optional[str] = None # Name of the plant, e.g. Sunflower
    symbol: Optional[str] = None
    x: int
    y: int
    energy_content: Optional[float] = None
    base_energy: Optional[float] = None # Max energy
    growth_stage: Optional[float] = None
    is_alive: bool
    # Add any other relevant fields from BasePlant (e.g. regrowth_time)
    regrowth_time: Optional[float] = None


@app.get("/game/{game_id}/entity/{entity_id}", response_model=Union[UnitStats, PlantStats])
async def get_entity_details(game_id: str, entity_id: str):
    if not GAME_COMPONENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Game components are not available.")

    # Validate that the entity_id belongs to the specified game_id
    if not entity_id.startswith(game_id + "_"):
        # This check also implicitly handles if game_id itself is not in game_instances,
        # as entity_id would not start with a non-existent game_id prefix if map is correctly populated.
        # However, an explicit check for game_id in game_instances can be added for clarity if desired.
        raise HTTPException(status_code=404, detail=f"Entity with ID '{entity_id}' not found in game '{game_id}'.")

    # Retrieve from the global entity_map
    # The entity_map stores the actual game objects.
    entity_obj = entity_map.get(entity_id)

    if not entity_obj:
        raise HTTPException(status_code=404, detail=f"Entity with ID '{entity_id}' not found.")

    # Check if the game_id from URL actually exists (as an extra layer, though prefix check is good)
    if game_id not in game_instances:
        # This case should ideally be caught by the entity_id prefix check if entity_map is consistent.
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found.")


    if isinstance(entity_obj, BaseUnit):
        # Populate UnitStats
        return UnitStats(
            id=entity_id,
            unit_type=getattr(entity_obj, 'unit_type', type(entity_obj).__name__),
            x=entity_obj.x,
            y=entity_obj.y,
            hp=getattr(entity_obj, 'hp', None),
            max_hp=getattr(entity_obj, 'max_hp', None),
            energy=getattr(entity_obj, 'energy', None),
            max_energy=getattr(entity_obj, 'max_energy', None),
            strength=getattr(entity_obj, 'strength', None),
            speed=getattr(entity_obj, 'speed', None),
            vision=getattr(entity_obj, 'vision', None),
            alive=getattr(entity_obj, 'alive', False),
            state=getattr(entity_obj, 'state', None),
            level=getattr(entity_obj, 'level', None),
            experience=getattr(entity_obj, 'experience', None),
            traits=getattr(entity_obj, 'traits', set())
        )
    elif isinstance(entity_obj, BasePlant):
        # Populate PlantStats
        plant_state = getattr(entity_obj, 'state', None)
        return PlantStats(
            id=entity_id,
            plant_type=getattr(entity_obj, 'plant_type', type(entity_obj).__name__),
            symbol=getattr(entity_obj, 'symbol', None),
            x=entity_obj.position.x, # BasePlant stores position as an object
            y=entity_obj.position.y, # BasePlant stores position as an object
            energy_content=getattr(plant_state, 'energy_content', None) if plant_state else None,
            base_energy=getattr(entity_obj, 'base_energy', None),
            growth_stage=getattr(plant_state, 'growth_stage', None) if plant_state else None,
            is_alive=getattr(plant_state, 'is_alive', False) if plant_state else False,
            regrowth_time=getattr(entity_obj, 'regrowth_time', None)
        )
    else:
        # Should not happen if entity_map is populated correctly
        raise HTTPException(status_code=500, detail=f"Unknown entity type for ID '{entity_id}'.")
