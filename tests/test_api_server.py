import pytest
from fastapi.testclient import TestClient

# Adjust the import path based on your project structure.
# This assumes api_server.py is in the root directory.
# If api_server.py is in a subdirectory, e.g., 'app', it would be 'from app.api_server import app, game_instances'
import sys
import os

# Add the project root to the Python path to allow importing api_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api_server import app, game_instances, GAME_COMPONENTS_AVAILABLE
from game.game_loop import GameLoop
from game.board import Board # For type checking or specific setup if needed
from game.config import Config # For specific config related tests if any

# Create a TestClient instance
client = TestClient(app)

# Ensure game components are available for the tests to run meaningfully
# api_server.py should set this. This is more of an assertion for test setup.
assert GAME_COMPONENTS_AVAILABLE, "Game components not available, check api_server.py imports and setup."

# --- Test Cases ---

def test_create_default_game_instance():
    """Test that a default game instance is created when api_server is imported."""
    assert "default_game" in game_instances
    assert isinstance(game_instances["default_game"], GameLoop)
    # Ensure the board within the game loop is also initialized
    assert isinstance(game_instances["default_game"].board, Board)
    # Ensure the config is loaded
    assert isinstance(game_instances["default_game"].config, Config)


def test_get_board_state_initial():
    """Test GET /game/default_game/board for initial state."""
    response = client.get("/game/default_game/board")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == "default_game"
    assert data["turn"] == 0
    assert "board_width" in data
    assert "board_height" in data
    assert "entities" in data
    assert isinstance(data["entities"], list)


def test_update_game_state():
    """Test POST /game/default_game/update to advance game turn."""
    # Ensure initial turn is 0 by fetching board state first (optional, but good for baseline)
    initial_response = client.get("/game/default_game/board")
    initial_turn = initial_response.json()["turn"]

    response = client.post("/game/default_game/update")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == "default_game"
    assert data["turn"] == initial_turn + 1
    assert "entities" in data

    # Make another POST request to check if turn increments further
    response_turn_2 = client.post("/game/default_game/update")
    assert response_turn_2.status_code == 200
    data_turn_2 = response_turn_2.json()
    assert data_turn_2["turn"] == initial_turn + 2


def test_get_board_state_after_update():
    """Test GET /game/default_game/board after a game update."""
    # Get current turn first
    current_board_response = client.get("/game/default_game/board")
    current_turn = current_board_response.json()["turn"]

    # Update the game state
    update_response = client.post("/game/default_game/update")
    assert update_response.status_code == 200
    updated_turn_from_post = update_response.json()["turn"]
    assert updated_turn_from_post == current_turn + 1

    # Fetch board state again
    get_response = client.get("/game/default_game/board")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["game_id"] == "default_game"
    assert data["turn"] == updated_turn_from_post # Should be current_turn + 1
    assert data["turn"] == current_turn + 1


def test_get_entity_details():
    """Test GET /game/default_game/entity/{entity_id} for a valid entity."""
    # First, get current board state which also populates entity_map
    board_response = client.get("/game/default_game/board")
    assert board_response.status_code == 200
    board_data = board_response.json()

    if not board_data["entities"]:
        # If no entities, try to advance turn to spawn some.
        # This depends on default game setup having initial entities or spawning them quickly.
        # For a robust test, one might need to ensure entities are present or mock them.
        client.post("/game/default_game/update")
        board_response = client.get("/game/default_game/board")
        board_data = board_response.json()

    assert len(board_data["entities"]) > 0, "No entities found on the board to test details endpoint. Ensure default game creates entities."

    # Get a valid entity_id from the board state
    entity_to_test = board_data["entities"][0]
    entity_id = entity_to_test["id"]
    entity_type_from_board = entity_to_test["type"] # "unit" or "plant"

    # Make a GET request to the entity details endpoint
    entity_response = client.get(f"/game/default_game/entity/{entity_id}")
    assert entity_response.status_code == 200
    entity_data = entity_response.json()

    assert entity_data["id"] == entity_id
    assert entity_data["type"] == entity_type_from_board
    assert "x" in entity_data
    assert "y" in entity_data
    assert entity_data["x"] == entity_to_test["x"]
    assert entity_data["y"] == entity_to_test["y"]

    if entity_data["type"] == "unit":
        assert "hp" in entity_data
        assert "alive" in entity_data
        assert "unit_type" in entity_data
    elif entity_data["type"] == "plant":
        assert "energy_content" in entity_data
        assert "is_alive" in entity_data
        assert "plant_type" in entity_data # Name of plant
        assert "symbol" in entity_data


def test_invalid_game_id_endpoints():
    """Test API calls with an invalid game ID."""
    invalid_game_id = "non_existent_game"

    response_board = client.get(f"/game/{invalid_game_id}/board")
    assert response_board.status_code == 404

    response_update = client.post(f"/game/{invalid_game_id}/update")
    assert response_update.status_code == 404

    # For entity details, the entity_id format itself implies the game_id,
    # so the prefix check in the endpoint should catch this.
    # Here, we test getting an entity for a game_id that doesn't exist.
    response_entity = client.get(f"/game/{invalid_game_id}/entity/some_entity_id_format")
    assert response_entity.status_code == 404 # Due to entity_id not matching game_id prefix rule


def test_invalid_entity_id():
    """Test GET /game/default_game/entity/{entity_id} with an invalid entity ID."""
    response = client.get("/game/default_game/entity/invalid_entity_id_format_that_does_not_exist")
    assert response.status_code == 404


def test_entity_id_mismatch_game_id():
    """Test entity ID from one game requested with a different game ID in URL path."""
    # Ensure entity_map is populated for default_game
    board_response = client.get("/game/default_game/board")
    assert board_response.status_code == 200
    board_data = board_response.json()

    if not board_data["entities"]:
        client.post("/game/default_game/update") # Advance turn if needed
        board_response = client.get("/game/default_game/board")
        board_data = board_response.json()

    assert len(board_data["entities"]) > 0, "No entities on default_game to conduct mismatch test."

    valid_entity_id_from_default_game = board_data["entities"][0]["id"]

    # Attempt to request this entity ID but under a different game_id in the path
    mismatched_game_id_path = "another_game_id"
    response = client.get(f"/game/{mismatched_game_id_path}/entity/{valid_entity_id_from_default_game}")

    # The endpoint should return 404 because valid_entity_id_from_default_game will not start with "another_game_id_"
    assert response.status_code == 404


# Note: To run these tests, Pytest should be used.
# Ensure that api_server.py and its dependencies (game/*) are in PYTHONPATH.
# The sys.path modification at the top helps with this for direct execution scenarios.
# If api_server.py's create_default_game() has issues (e.g. strict config file needs),
# those might need to be addressed, possibly by ensuring a 'config.json' is in the root
# or by mocking config loading within these tests if it becomes a problem.
# The current api_server.py seems to use Config('config.json') which then falls back
# to internal defaults if the file is not found, which is generally test-friendly.

# It's also important that the `game_instances` dictionary is not reset between test functions
# if subsequent tests rely on state from previous ones (like turn incrementing).
# Pytest typically re-imports modules for different test files, but not between functions in the same file.
# So, the state of game_instances (and the game_loop within it) will persist across these tests.
# If full isolation is needed for each test, setup/teardown fixtures (e.g. with `pytest.fixture`)
# would be required to reset or re-initialize the game state or `app` for each test.
# For this set of tests, the sequential nature seems implicitly handled.
