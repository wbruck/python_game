import pytest
from game.board import Board, MovementType
from unittest.mock import Mock
import json
import os

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock()
    # Store the config dictionary in a way that's accessible for the mock
    _config_data = {
        "environment": {
            "cycle_length": 10,
            "day_night_cycle": True
        },
        "game": {
            "turn_delay": 0.0
        }
    }
    # Mock the .get() method
    def mock_get(section, key):
        return _config_data.get(section, {}).get(key)

    config.get = Mock(side_effect=mock_get)
    # Optionally, still allow access to the raw config if needed elsewhere
    config.config = _config_data
    return config

@pytest.fixture
def game_loop(mock_config):
    """Create a GameLoop instance for testing."""
    from game.game_loop import GameLoop
    mock_board = Mock()
    return GameLoop(mock_board, max_turns=100, config=mock_config)
@pytest.fixture
def board():
    """Create a standard 10x10 board with cardinal movement."""
    return Board(10, 10)

@pytest.fixture
def diagonal_board():
    """Create a standard 10x10 board with diagonal movement."""
    return Board(10, 10, MovementType.DIAGONAL)

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "test_config.json"
    test_config = {
        "board": {
            "width": 30,
            "height": 25,
            "allow_diagonal_movement": False
        },
        "units": {
            "initial_count": {
                "predator": 5,
                "grazer": 10
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(test_config, f)
    return str(config_path)
