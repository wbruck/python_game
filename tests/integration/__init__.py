"""Integration test package for the ecosystem simulation game.

This package contains comprehensive integration tests that verify
the correct interaction between different game components.

Common test fixtures and utilities are defined here for use across
all integration test modules.
"""

import pytest
from game.board import Board, Position
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import Predator, Grazer
from game.plants.plant_types import BasicPlant

@pytest.fixture
def standard_board():
    """Create a standard 10x10 board for testing."""
    return Board(width=10, height=10)

@pytest.fixture
def standard_config():
    """Create a standard configuration for testing."""
    return Config()

@pytest.fixture
def empty_game(standard_board, standard_config):
    """Create a game loop with empty board."""
    return GameLoop(board=standard_board, config=standard_config)

@pytest.fixture
def basic_ecosystem(standard_board, standard_config):
    """Create a game loop with a basic ecosystem setup."""
    game_loop = GameLoop(board=standard_board, config=standard_config)
    
    # Add basic units
    predator = Predator(x=1, y=1)
    grazer = Grazer(x=8, y=8)
    game_loop.add_unit(predator)
    game_loop.add_unit(grazer)
    standard_board.place_object(predator, 1, 1)
    standard_board.place_object(grazer, 8, 8)
    
    # Add basic plants
    grass = BasicPlant(Position(4, 4))
    game_loop.add_plant(grass)
    standard_board.add_plant(grass)
    
    return game_loop, standard_board, [predator, grazer], [grass]
