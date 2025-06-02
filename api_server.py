from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Union, Optional, Set
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from game.board import Board
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import UNIT_TYPES
from game.plants.plant_types import PLANT_TYPES
from game.units.base_unit import Unit
from game.plants.base_plant import Plant
from game.board import Position


# Basic FastAPI app setup
app = FastAPI()


# Mount the static directory
try:
    static_dir = os.path.abspath("static")
    logger.info(f"Mounting static directory at: {static_dir}")
    if not os.path.exists(static_dir):
        logger.error(f"Static directory not found at: {static_dir}")
        raise RuntimeError(f"Static directory not found at: {static_dir}")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.error(f"Failed to mount static directory: {str(e)}")
    raise


# Flag to indicate if game components are available
GAME_COMPONENTS_AVAILABLE = False

try:
    # Attempt to import all necessary game components

    logger.info("Checking game components...")
    logger.info(f"Board: {Board}")
    logger.info(f"GameLoop: {GameLoop}")
    logger.info(f"Config: {Config}")
    logger.info(f"UNIT_TYPES: {UNIT_TYPES}")
    logger.info(f"PLANT_TYPES: {PLANT_TYPES}")
    logger.info(f"Unit: {Unit}")
    logger.info(f"Plant: {Plant}")
    
    if (Board is not None and 
        GameLoop is not None and 
        Config is not None and 
        UNIT_TYPES is not None and 
        PLANT_TYPES is not None and 
        Unit is not None and 
        Plant is not None):
        GAME_COMPONENTS_AVAILABLE = True
        logger.info("All game components successfully loaded")
        logger.info(f"Available unit types: {list(UNIT_TYPES.keys())}")
        logger.info(f"Available plant types: {list(PLANT_TYPES.keys())}")
    else:
        logger.error("Some game components are None")
except Exception as e:
    logger.error(f"Failed to load game components: {str(e)}")
    print("Warning: Some game components could not be imported. API might not function correctly.")

@app.get("/game/entity-types")
async def get_entity_types():
    """
    Returns the available unit and plant types that can be used in the game.
    """
    if not GAME_COMPONENTS_AVAILABLE:
        logger.error("Game components are not available")
        raise HTTPException(status_code=503, detail="Game components are not available.")
    
    try:
        unit_types = list(UNIT_TYPES.keys())
        plant_types = list(PLANT_TYPES.keys())
        logger.info(f"Returning entity types - Units: {unit_types}, Plants: {plant_types}")
        return {
            "units": unit_types,
            "plants": plant_types
        }
    except Exception as e:
        logger.error(f"Error getting entity types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting entity types: {str(e)}")

# Add a root endpoint that serves the index.html
@app.get("/")
async def root():
    try:
        index_path = os.path.join("static", "index.html")
        logger.info(f"Serving index.html from: {index_path}")
        if not os.path.exists(index_path):
            logger.error(f"index.html not found at: {index_path}")
            raise HTTPException(status_code=404, detail="index.html not found")
        return FileResponse(index_path)
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration models
class EntityConfig(BaseModel):
    type: str  # "unit" or "plant"
    name: str  # e.g., "predator", "basic_plant"
    x: int
    y: int
    hp: Optional[int] = None  # Optional for units
    config: Optional[Dict[str, Any]] = None  # Additional configuration

class BoardConfig(BaseModel):
    width: int
    height: int
    entities: List[EntityConfig] = []

# Dictionary to store GameLoop objects
game_instances: dict[str, GameLoop] = {}
entity_map: Dict[str, Dict[str, Any]] = {} # Global entity map for now

def create_game_instance(game_id: str, config: BoardConfig) -> GameLoop:
    """
    Creates a new game instance with the specified configuration.
    """
    if not GAME_COMPONENTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Game components are not available.")

    try:
        logger.info(f"Creating game instance with ID: {game_id}")
        logger.info(f"Board dimensions: {config.width}x{config.height}")
        logger.info(f"Number of entities to create: {len(config.entities)}")
        
        # Create a new Config instance with default values
        game_config = Config()
        
        # Set board dimensions
        game_config.set("board", "width", config.width)
        game_config.set("board", "height", config.height)

        # Create board and game loop
        board = Board(config.width, config.height)
        max_turns = game_config.get("game", "max_turns")
        if max_turns is None:
            max_turns = 1000  # Default value if not set in config
        game_loop = GameLoop(board, max_turns=max_turns, config=game_config)

        # Add initial entities
        for entity_config in config.entities:
            logger.info(f"Creating entity: type={entity_config.type}, name={entity_config.name}, position=({entity_config.x}, {entity_config.y})")
            if entity_config.type == "unit" and entity_config.name in UNIT_TYPES:
                unit_class = UNIT_TYPES[entity_config.name]
                unit = unit_class(entity_config.x, entity_config.y, hp=entity_config.hp, config=game_config)
                board.place_object(unit, entity_config.x, entity_config.y)
                logger.info(f"Created unit: {unit}")
            elif entity_config.type == "plant" and entity_config.name in PLANT_TYPES:
                plant_class = PLANT_TYPES[entity_config.name]
                position = Position(entity_config.x, entity_config.y)
                plant = plant_class(position)
                board.place_object(plant, entity_config.x, entity_config.y)
                logger.info(f"Created plant: {plant}")
            else:
                logger.warning(f"Unknown entity type or name: type={entity_config.type}, name={entity_config.name}")

        # Store the game instance
        game_instances[game_id] = game_loop
        logger.info(f"Game instance created successfully with {len(config.entities)} entities")
        return game_loop

    except Exception as e:
        logger.error(f"Error creating game instance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/{game_id}/configure")
async def configure_game(game_id: str, config: BoardConfig):
    """
    Configure a game instance with the specified board setup.
    If the game already exists, it will be reconfigured.
    """
    try:
        # If game exists, delete it first
        if game_id in game_instances:
            del game_instances[game_id]
            
        game_loop = create_game_instance(game_id, config)
        return {"message": f"Game '{game_id}' configured successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """
    Delete a game instance.
    """
    if game_id not in game_instances:
        raise HTTPException(status_code=404, detail=f"Game with ID '{game_id}' not found.")
    
    del game_instances[game_id]
    return {"message": f"Game '{game_id}' deleted successfully."}


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

    max_turns = config.get("game", "max_turns")
    if max_turns is None:
        max_turns = 1000  # Default value if not set in config
    game_loop = GameLoop(board, max_turns=max_turns, config=config)


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

        for x, cell_content in enumerate(row):
            # Skip if cell is None or empty
            if cell_content is None:
                continue
                
            obj = cell_content
            entity_api_id = get_entity_api_id(obj, game_id)
            entity_type = ""
            name = ""
            details = {}

            if isinstance(obj, Unit):
                entity_type = "unit"
                name = getattr(obj, 'unit_type', type(obj).__name__)
                details = {
                    "health": getattr(obj, 'hp', None),  # Changed from health to hp to match Unit class
                    "energy": getattr(obj, 'energy', None),
                    "state": getattr(obj, 'state', None),
                    "age": getattr(obj, 'age', None),
                    # Add any other relevant unit details
                }
            elif isinstance(obj, Plant):
                entity_type = "plant"
                name = getattr(obj, 'plant_type', type(obj).__name__) # e.g., "Sunflower" from a subclass or "Plant"

                # Access state attributes safely
                plant_state = getattr(obj, 'state', None)
                energy = getattr(plant_state, 'energy_content', None) if plant_state else None
                growth_stage = getattr(plant_state, 'growth_stage', None) if plant_state else None

                details = {
                    "health": getattr(obj, 'hp', None), # Remains None if not present
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



    if isinstance(entity_obj, Unit):

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

    elif isinstance(entity_obj, Plant):

        # Populate PlantStats
        plant_state = getattr(entity_obj, 'state', None)
        return PlantStats(
            id=entity_id,
            plant_type=getattr(entity_obj, 'plant_type', type(entity_obj).__name__),
            symbol=getattr(entity_obj, 'symbol', None),

            x=entity_obj.position.x, # Plant stores position as an object
            y=entity_obj.position.y, # Plant stores position as an object

            energy_content=getattr(plant_state, 'energy_content', None) if plant_state else None,
            base_energy=getattr(entity_obj, 'base_energy', None),
            growth_stage=getattr(plant_state, 'growth_stage', None) if plant_state else None,
            is_alive=getattr(plant_state, 'is_alive', False) if plant_state else False,
            regrowth_time=getattr(entity_obj, 'regrowth_time', None)
        )
    else:
        # Should not happen if entity_map is populated correctly
        raise HTTPException(status_code=500, detail=f"Unknown entity type for ID '{entity_id}'.")


@app.post("/game/new")
async def create_new_game():
    """
    Creates a new game instance and returns its ID.
    """
    game_id = f"game_{len(game_instances)}"
    # Create an empty game instance with default configuration
    config = Config()
    board_width = config.get("board", "width")
    board_height = config.get("board", "height")
    
    # Use default values if config doesn't have them
    if board_width is None:
        board_width = 10
    if board_height is None:
        board_height = 10
        
    board = Board(board_width, board_height)
    max_turns = config.get("game", "max_turns")
    if max_turns is None:
        max_turns = 1000  # Default value if not set in config
    game_loop = GameLoop(board, max_turns=max_turns, config=config)
    game_instances[game_id] = game_loop
    return {"game_id": game_id}

