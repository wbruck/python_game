"""Integration tests focusing on complex lifecycle scenarios and state transitions."""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.plants.base_plant import Plant

@pytest.fixture
def lifecycle_board():
    """Create a board suitable for lifecycle testing."""
    return Board(5, 5, MovementType.DIAGONAL)  # Using diagonal movement for more interaction possibilities

@pytest.fixture
def stable_config():
    """Create a game configuration that ensures predictable behavior."""
    random.seed(42)
    return {
        "energy_consumption": {
            "move": 1,
            "attack": 2,
            "idle": 0.5
        },
        "decay_rate": 0.1,
        "plant_growth_rate": 0.2
    }

def test_predator_lifecycle(lifecycle_board):
    """Test complete lifecycle of a predator unit from hunting to death."""
    # Setup predator and prey
    predator = Unit(1, 1, unit_type="predator")
    prey = Unit(3, 3, unit_type="grazer")
    
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

def test_energy_cycle(lifecycle_board):
    """Test energy transfer through the ecosystem (plant -> grazer -> predator)."""
    # Setup ecosystem participants
    plant = Plant(2, 2)
    grazer = Unit(1, 1, unit_type="grazer")
    predator = Unit(3, 3, unit_type="predator")
    
    # Place all entities
    lifecycle_board.place_object(plant, 2, 2)
    lifecycle_board.place_object(grazer, 1, 1)
    lifecycle_board.place_object(predator, 3, 3)
    
    game_loop = GameLoop(lifecycle_board)
    game_loop.add_unit(grazer)
    game_loop.add_unit(predator)
    
    initial_energies = {
        "grazer": grazer.energy,
        "predator": predator.energy
    }
    
    # Run energy cycle
    plant_consumed = False
    grazer_consumed = False
    
    for _ in range(15):  # Allow energy transfer cycle to complete
        game_loop.process_turn()
        
        # Track energy transfers
        if grazer.energy > initial_energies["grazer"]:
            plant_consumed = True
        if predator.energy > initial_energies["predator"] and not grazer.alive:
            grazer_consumed = True
    
    # Verify energy transfer
    assert plant_consumed or not plant.alive, "Plant should be consumed by grazer"
    assert grazer_consumed or not grazer.alive, "Grazer should be consumed by predator"

def test_state_transitions(lifecycle_board):
    """Test unit state transitions under different conditions."""
    unit = Unit(2, 2, unit_type="predator")
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
