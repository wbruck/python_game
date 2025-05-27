import pytest
from game.board import Board, MovementType
from game.units.base_unit import Unit
from game.config import Config
from game.game_loop import GameLoop
from unittest.mock import Mock
import json
import os

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock()
    config.config = {
        "environment": {
            "cycle_length": 10,
            "day_night_cycle": True
        },
        "game": {
            "turn_delay": 0.0
        }
    }
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


@pytest.fixture
def integration_config():
    """Create a baseline configuration for integration tests."""
    config = Config()
    # Start with default config and override specific test values
    config.config = {
        **config.DEFAULT_CONFIG,  # Start with all defaults
        "board": {
            "width": 10,
            "height": 10,
            "allow_diagonal_movement": False
        },
        "game": {
            "max_turns": 100,
            "turn_delay": 0.0
        },
        "units": {
            "energy_consumption": config.DEFAULT_CONFIG["units"]["energy_consumption"],
            "decay_rate": config.DEFAULT_CONFIG["units"]["decay_rate"],
            "initial_count": {
                "predator": 0,  # We'll create units explicitly in tests
                "scavenger": 0,
                "grazer": 0
            }
        },
        "environment": {
            "day_night_cycle": True,
            "cycle_length": 5
        }
    }
    return config

@pytest.fixture
def integration_board(integration_config):
    """Create a test board with integration test configuration."""
    return Board(
        integration_config.get("board", "width"),
        integration_config.get("board", "height"),
        MovementType.CARDINAL if not integration_config.get("board", "allow_diagonal_movement") else MovementType.DIAGONAL
    )

@pytest.fixture
def integration_game_loop(integration_board, integration_config):
    """Create a game loop with integration test configuration."""
    return GameLoop(integration_board, config=integration_config)

@pytest.fixture
def configured_unit(integration_config):
    """Factory fixture to create properly configured units."""
    def _create_unit(unit_type, x, y):
        unit = Unit(x, y, unit_type=unit_type)
        # Initialize from config
        unit.energy_consumption = integration_config.get("units", "energy_consumption")
        unit.decay_rate = integration_config.get("units", "decay_rate")
        return unit
    return _create_unit
