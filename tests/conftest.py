import pytest
from game.board import Board, MovementType
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
            "day_night_cycle": True,
            "seasonal_effects": True,
            "season_length": 40
        },
        "game": {
            "turn_delay": 0.0,
            "initial_energy": 100
        },
        "units": {
            "predator": {
                "base_energy": 100,
                "vision_range": 5,
                "attack_strength": 15
            },
            "grazer": {
                "base_energy": 80,
                "vision_range": 4,
                "flee_speed": 2
            }
        },
        "plants": {
            "growth_rate": 0.1,
            "max_energy": 50,
            "regrowth_time": 10
        }
    }
    return config

@pytest.fixture
def game_loop(board, mock_config):
    """Create a GameLoop instance for testing with proper environmental cycles."""
    from game.game_loop import GameLoop
    return GameLoop(
        board=board,
        max_turns=100,
        config=mock_config
    )
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
