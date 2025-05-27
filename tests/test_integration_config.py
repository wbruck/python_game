"""Integration tests focusing on configuration-driven behaviors and interactions."""

import pytest
from game.board import Board, MovementType
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.config import Config
from game.plants.base_plant import Plant

@pytest.fixture
def base_config():
    """Create a baseline configuration."""
    return {
        "board": {
            "width": 5,
            "height": 5,
            "movement_type": "DIAGONAL"
        },
        "units": {
            "energy_consumption": {
                "move": 2,
                "attack": 3,
                "idle": 1
            },
            "vision_range": {
                "day": 5,
                "night": 3
            }
        },
        "environment": {
            "cycle_length": 5,
            "plant_growth_rate": 0.2
        }
    }

@pytest.fixture
def configured_game(base_config):
    """Create a game instance with specific configuration."""
    config = Config()
    config.update(base_config)
    board = Board(
        base_config["board"]["width"],
        base_config["board"]["height"],
        MovementType.DIAGONAL
    )
    return GameLoop(board, config=config), board

@pytest.mark.integration
def test_energy_consumption_rates(configured_game):
    """Test that energy consumption matches configuration settings."""
    game_loop, board = configured_game
    unit = Unit(2, 2, unit_type="predator")
    board.place_object(unit, 2, 2)
    game_loop.add_unit(unit)
    
    initial_energy = unit.energy
    
    # Process one turn and verify energy consumption
    game_loop.process_turn()
    
    energy_spent = initial_energy - unit.energy
    assert energy_spent >= game_loop.config.get("units", "energy_consumption.idle"), \
        "Energy consumption should match configured idle rate"

@pytest.mark.integration
def test_vision_range_cycle(configured_game):
    """Test that vision ranges change according to day/night configuration."""
    game_loop, board = configured_game
    unit = Unit(2, 2, unit_type="predator")
    board.place_object(unit, 2, 2)
    game_loop.add_unit(unit)
    
    initial_vision = unit.vision
    
    # Run through a complete day/night cycle
    cycle_length = game_loop.config.get("environment", "cycle_length")
    for _ in range(cycle_length):
        game_loop.process_turn()
    
    # Vision should change during night
    night_vision = game_loop.config.get("units", "vision_range.night")
    assert unit.vision == night_vision, \
        "Unit vision should match configured night vision range"

@pytest.mark.integration
def test_movement_type_behavior(configured_game):
    """Test that movement respects configured movement type."""
    game_loop, board = configured_game
    unit = Unit(2, 2, unit_type="predator")
    board.place_object(unit, 2, 2)
    game_loop.add_unit(unit)
    
    # Get available moves
    moves = board.get_available_moves(2, 2)
    
    # With DIAGONAL movement, should have 8 possible moves
    assert len(moves) == 8, \
        "Diagonal movement configuration should allow 8 directions"

@pytest.mark.integration
def test_plant_growth_rate(configured_game):
    """Test that plant growth follows configured rates."""
    game_loop, board = configured_game
    plant = Plant(2, 2)
    board.place_object(plant, 2, 2)
    
    initial_energy = plant.energy_value
    growth_rate = game_loop.config.get("environment", "plant_growth_rate")
    
    # Run several turns
    for _ in range(5):
        game_loop.process_turn()
        
    # Verify growth matches configuration
    expected_growth = initial_energy * (1 + growth_rate * 5)
    assert abs(plant.energy_value - expected_growth) < 0.01, \
        "Plant growth should follow configured growth rate"

@pytest.mark.integration
def test_config_dependent_combat(configured_game):
    """Test that combat mechanics respect configuration settings."""
    game_loop, board = configured_game
    attacker = Unit(1, 1, unit_type="predator")
    defender = Unit(2, 2, unit_type="grazer")
    
    board.place_object(attacker, 1, 1)
    board.place_object(defender, 2, 2)
    game_loop.add_unit(attacker)
    game_loop.add_unit(defender)
    
    initial_energy = attacker.energy
    attack_cost = game_loop.config.get("units", "energy_consumption.attack")
    
    # Process until combat occurs
    for _ in range(3):
        game_loop.process_turn()
        if attacker.energy < initial_energy:
            break
    
    energy_spent = initial_energy - attacker.energy
    assert energy_spent >= attack_cost, \
        "Combat should consume configured attack energy"
