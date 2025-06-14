"""
Tests for the game.game_loop module.

This module contains unit tests for the GameLoop class and its functionality.
"""

from unittest.mock import Mock, patch
import pytest
from game.game_loop import GameLoop, TimeOfDay, Season

def test_init(game_loop, mock_config):
    """Test game loop initialization."""
    assert isinstance(game_loop.board, Mock)
    assert game_loop.max_turns == 100
    assert game_loop.current_turn == 0
    assert len(game_loop.units) == 0
    assert len(game_loop.plants) == 0
    assert not game_loop.is_running
        
def test_add_unit(game_loop):
    """Test adding units to the game loop."""
    unit = Mock()
    game_loop.add_unit(unit)
    assert len(game_loop.units) == 1
    assert game_loop.units[0] == unit

def test_add_plant(game_loop):
    """Test adding plants to the game loop."""
    plant = Mock()
    game_loop.add_plant(plant)
    assert len(game_loop.plants) == 1
    assert game_loop.plants[0] == plant

def test_start_stop(game_loop):
    """Test starting and stopping the game loop."""
    # Mock the run method to avoid actually running the loop
    game_loop.run = Mock()
    
    # Test start
    game_loop.start()
    assert game_loop.is_running
    game_loop.run.assert_called_once()
    
    # Test stop
    game_loop.stop()
    assert not game_loop.is_running
        
@patch('random.shuffle')
def test_process_turn(mock_shuffle, game_loop):
    """Test processing a single turn."""
    # Set up mocks
    unit1 = Mock()
    unit1.x = 0 # Add x attribute
    unit1.y = 0 # Add y attribute
    unit1.alive = True
    unit1.base_vision = 10
    unit1.vision = 10
    unit1.energy = 100.0  # Use float for energy
    unit1.state = "idle"
    unit1.update = Mock()  # Add explicit mock for update
    unit1.apply_environmental_effects = Mock()
    
    unit2 = Mock()
    unit2.x = 1 # Add x attribute
    unit2.y = 1 # Add y attribute
    unit2.alive = False
    unit2.decay_stage = 0
    unit2.state = "decaying"
    unit2.update = Mock()  # Add explicit mock for update
    unit2.apply_environmental_effects = Mock()
    
    plant = Mock()
    plant.base_growth_rate = 1.0
    plant.update = Mock()
    plant.apply_environmental_effects = Mock()
    
    game_loop.units = [unit1, unit2]
    game_loop.plants = [plant]
    
    # Process a turn
    game_loop.process_turn()
    
    # Verify that the turn was processed correctly
    assert game_loop.current_turn == 1
    mock_shuffle.assert_called_once_with(game_loop.units)
    unit1.update.assert_called_once_with(game_loop.board)
    unit2.update.assert_called_once_with(game_loop.board) # Dead units are updated for decay
    plant.update.assert_called_once()
        
def test_environmental_cycles(game_loop):
    """Test environmental cycle updates and effects."""
    # Test initial state
    assert game_loop.time_of_day.value == "day"
    assert game_loop.season.value == "spring"
    
    # Test day/night cycle
    for _ in range(10):  # One complete cycle
        game_loop.process_turn()
    assert game_loop.time_of_day.value == "night"
    
    # Test seasonal change (40 turns = 4 day/night cycles = 1 season)
    for _ in range(30):  # Complete first season
        game_loop.process_turn()
    assert game_loop.season.value == "summer"

def test_environmental_effects(game_loop):
    """Test that environmental conditions affect units and plants."""
    # Setup test units and plants
    unit = Mock()
    unit.alive = True
    unit.base_vision = 10
    unit.energy = 100.0  # Use float for energy
    unit.update = Mock()  # Add mock for update
    unit.apply_environmental_effects = Mock()

    plant = Mock()
    plant.base_growth_rate = 1.0
    plant.energy = 100.0  # Use float for energy
    plant.min_energy = 50.0  # Use float for min_energy
    plant.update = Mock()  # Add mock for update
    plant.apply_environmental_effects = Mock()
    
    game_loop.units = [unit]
    game_loop.plants = [plant]
    
    # Process turn during day
    game_loop.process_turn()
    unit.apply_environmental_effects.assert_called_once()
    plant.apply_environmental_effects.assert_called_once()

    # Process turn during night (after 10 turns)
    for _ in range(9):  # Already did 1 turn above
        game_loop.process_turn()
    
    # Reset mocks and process another turn
    unit.apply_environmental_effects.reset_mock()
    plant.apply_environmental_effects.reset_mock()
    game_loop.process_turn()
    
    # Verify night effects are applied
    unit.apply_environmental_effects.assert_called_once()
    plant.apply_environmental_effects.assert_called_once()

def test_vision_changes(game_loop):
    """Test that unit vision changes with time of day."""
    unit = Mock()
    unit.alive = True
    unit.base_vision = 10
    unit.vision = 10
    unit.energy = 100.0  # Add float energy value
    unit.update = Mock()  # Add mock for update method
    game_loop.units = [unit]

    # Test vision during day
    game_loop.process_turn()
    assert unit.vision == 10  # Normal vision during day

    # Test vision during night (after 10 turns)
    for _ in range(9):  # Already did 1 turn above
        game_loop.process_turn()
    assert unit.vision == 5  # Reduced vision during night

def test_get_stats(game_loop):
    """Test getting game statistics with environmental information."""
    # Set up some units
    unit1 = Mock(alive=True)
    unit2 = Mock(alive=False)
    plant = Mock()
    
    game_loop.units = [unit1, unit2]
    game_loop.plants = [plant]
    
    stats = game_loop.get_stats()
    assert stats["current_turn"] == 0
    assert stats["living_units"] == 1
    assert stats["dead_units"] == 1
    assert stats["plant_count"] == 1
    assert stats["time_of_day"] == "day"
    assert stats["season"] == "spring"

def test_run(game_loop):
    """Test running the game loop."""
    # Ensure no delay between turns
    game_loop.turn_delay = 0
    
    # Test normal completion
    game_loop.max_turns = 5
    original_process_turn = game_loop.process_turn
    process_turn_mock = Mock(side_effect=original_process_turn)
    game_loop.process_turn = process_turn_mock
    
    game_loop.run()
    assert game_loop.current_turn == 5
    assert not game_loop.is_running
    assert process_turn_mock.call_count == 5

    # Test early stopping
    game_loop.current_turn = 0
    game_loop.is_running = False
    
    # Create a new mock that both processes turns and stops after 3
    def process_and_stop():
        original_process_turn()
        if game_loop.current_turn >= 3:
            game_loop.stop()
    
    process_turn_mock = Mock(side_effect=process_and_stop)
    game_loop.process_turn = process_turn_mock
    game_loop.max_turns = 10
    game_loop.run()
    
    assert game_loop.current_turn == 3
    assert not game_loop.is_running
    assert process_turn_mock.call_count == 3
