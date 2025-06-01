"""Integration tests focusing on complex lifecycle scenarios and state transitions."""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit # Keep for base unit needs if any
from game.units.unit_types import Predator, Grazer # Import specialized types
from game.game_loop import GameLoop
from game.plants.base_plant import Plant
from game.config import Config # Import Config

@pytest.fixture
def lifecycle_board():
    """Create a board suitable for lifecycle testing."""
    return Board(5, 5, MovementType.DIAGONAL)  # Using diagonal movement for more interaction possibilities

@pytest.fixture
def stable_config():
    """Create a game configuration that ensures predictable behavior."""
    random.seed(42)
    config_data = {
        "units": { # Assuming these are under 'units' section based on typical structure
            "energy_consumption": {
                "move": 1,
                "attack": 2
                # "idle": 0.5, // Removed problematic key
            },
            "decay_rate": 0.1
        },
        "plants": { # Assuming this is under 'plants'
             "growth_rate": 0.2
        },
        "environment": { # Add some defaults GameLoop might need
            "cycle_length": 20
        },
        "game": { # Add some defaults GameLoop might need
            "turn_delay": 0.0
        }
    }
    config = Config()
    for section, settings in config_data.items():
        if isinstance(settings, dict):
            for key, value in settings.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        config.set(section, f"{key}.{sub_key}", sub_value)
                else:
                    config.set(section, key, value)
    return config

@pytest.mark.integration
def test_predator_lifecycle(lifecycle_board):
    """Test complete lifecycle of a predator unit from hunting to death."""
    # Setup predator and prey
    # Pass config=None as these tests are for general lifecycle, not specific config values.
    # The unit methods have fallbacks if config is None or a value isn't found.
    predator = Predator(1, 1, config=None)
    prey = Grazer(3, 3, config=None)
    
    lifecycle_board.place_object(predator, 1, 1)
    lifecycle_board.place_object(prey, 3, 3)
    
    game_loop = GameLoop(lifecycle_board)
    game_loop.add_unit(predator)
    game_loop.add_unit(prey)
    
    # Track lifecycle phases
    hunting_phase = False
    combat_phase = False
    feeding_phase = False
    death_phase = False
    
    # Run through lifecycle
    for _ in range(20):  # Allow sufficient turns for lifecycle
        game_loop.process_turn()
        
        # Check phase transitions
        if predator.state == "hunting" and not hunting_phase:
            hunting_phase = True
        elif predator.state == "combat" and not combat_phase:
            combat_phase = True
        elif predator.state == "feeding" and not feeding_phase:
            feeding_phase = True
        elif not predator.alive and not death_phase:
            death_phase = True
            break
    
    # Verify lifecycle progression
    assert hunting_phase, "Predator should enter hunting phase"
    assert combat_phase or feeding_phase, "Predator should either engage in combat or feed"

@pytest.mark.integration
def test_state_transitions(lifecycle_board):
    """Test unit state transitions under different conditions."""
    unit = Predator(2, 2, config=None) # Changed to Predator
    lifecycle_board.place_object(unit, 2, 2)
    
    game_loop = GameLoop(lifecycle_board)
    game_loop.add_unit(unit)
    
    states_seen = set()
    initial_energy = unit.energy
    
    # Run through various states
    for _ in range(15):
        game_loop.process_turn()
        states_seen.add(unit.state)
        
        # Manipulate conditions to force state changes
        if len(states_seen) == 1:
            unit.energy = unit.max_energy * 0.2  # Should trigger resting state
        elif len(states_seen) == 2:
            unit.energy = unit.max_energy  # Should enable active states again
    
    # Verify state transitions
    assert len(states_seen) >= 3, "Unit should transition through multiple states"
    assert "resting" in states_seen, "Unit should enter resting state when energy is low"

@pytest.mark.integration
def test_deterministic_energy_transfer_cycle(lifecycle_board, stable_config): # Added stable_config
    """
    Tests a deterministic energy transfer cycle: Plant -> Grazer -> Predator.
    """
    # Re-initialize board and game_loop for this specific test to ensure isolation
    # The lifecycle_board fixture provides a fresh board. We need a new GameLoop.
    board = lifecycle_board # Use the fixture
    # Pass stable_config to GameLoop as well for consistency, though it might default fine.
    game_loop = GameLoop(board, max_turns=20, config=stable_config)

    # Step 1: Grazer eats Plant
    grazer = Grazer(1, 1, config=stable_config)
    grazer.energy = 10
    grazer.hp = 50
    plant = Plant(Position(1, 2), base_energy=100, growth_rate=1.0, regrowth_time=10.0)

    initial_grazer_energy_step1 = grazer.energy
    initial_plant_energy_step1 = plant.base_energy

    board.place_object(grazer, 1, 1)
    board.place_object(plant, plant.position.x, plant.position.y)
    game_loop.add_unit(grazer)

    for _ in range(2): # Run for 2 turns
        game_loop.process_turn()
        # Early exit if conditions met or Grazer dies unexpectedly
        if grazer.energy > initial_grazer_energy_step1 or not grazer.alive:
             break

    assert grazer.alive, "Grazer should be alive after attempting to eat the plant"
    assert grazer.energy > initial_grazer_energy_step1, "Grazer's energy should increase after eating plant"

    plant_on_board_after_step1 = board.get_object(plant.position.x, plant.position.y)
    if plant_on_board_after_step1 and isinstance(plant_on_board_after_step1, Plant):
        assert plant_on_board_after_step1.state.energy_content < initial_plant_energy_step1, \
            "Plant's energy should decrease after being consumed"
    else:
        assert plant_on_board_after_step1 is None, "Plant should be consumed (None) or have less energy"

    grazer_hp_after_step1 = grazer.hp
    grazer_energy_after_step1 = grazer.energy
    grazer_pos_x, grazer_pos_y = grazer.x, grazer.y # Record grazer's position
    grazer.speed = 0 # Make Grazer stationary for Step 2
    grazer.base_speed = 0 # Ensure speed is not reset by Unit.update()

    # Step 2: Predator eats Grazer
    predator = Predator(grazer_pos_x + 1, grazer_pos_y, config=stable_config)
    predator.energy = 50
    predator.hp = 100

    initial_predator_energy_step2 = predator.energy

    board.place_object(predator, predator.x, predator.y)
    game_loop.add_unit(predator)

    for _ in range(5): # Run for 5 turns (increased from 3)
        if not grazer.alive: # Grazer got eaten
            break
        game_loop.process_turn()

    assert not grazer.alive, "Grazer should be defeated by the predator in Step 2"
    assert predator.alive, "Predator should survive combat in Step 2"
    assert predator.energy > initial_predator_energy_step2, \
        "Predator's energy should increase after consuming the grazer"
