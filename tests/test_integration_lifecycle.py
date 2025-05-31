"""Integration tests focusing on complex lifecycle scenarios and state transitions."""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit # Keep for base unit needs if any
from game.units.unit_types import Predator, Grazer # Import specialized types
from game.game_loop import GameLoop
from game.plants.base_plant import Plant
# Assuming Config might be needed if GameLoop is to be config-aware, or units need it
# from game.config import Config

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
def test_energy_cycle(lifecycle_board):
    """Test energy transfer through the ecosystem (plant -> grazer -> predator)."""
    # Setup ecosystem participants
    plant = Plant(Position(0, 1), base_energy=100, growth_rate=0.1, regrowth_time=10)
    grazer = Grazer(0, 0, config=None)
    predator = Predator(4, 4, config=None) # Predator starts further away

    # Set grazer's initial energy low to encourage eating
    grazer.energy = grazer.max_energy * 0.3
    
    lifecycle_board.place_object(plant, 0, 1) # Plant at (0,1)
    lifecycle_board.place_object(grazer, 0, 0) # Grazer at (0,0), adjacent to plant
    lifecycle_board.place_object(predator, 4, 4) # Predator at (4,4)
    
    game_loop = GameLoop(lifecycle_board)
    game_loop.add_unit(grazer)
    game_loop.add_unit(predator)
    
    # Store initial energy levels for comparison
    grazer_energy_at_test_start = grazer.energy
    predator_energy_at_test_start = predator.energy
    
    plant_was_eaten_by_grazer = False
    grazer_was_eaten_by_predator = False # True if grazer dies AND predator energy increases from its start
    
    for i in range(15): # Max 15 turns for the cycle
        game_loop.process_turn()
        
        # Check if grazer ate the plant (its energy increased from its initial state)
        if not plant_was_eaten_by_grazer and \
           (not plant.state.is_alive or grazer.energy > grazer_energy_at_test_start):
            plant_was_eaten_by_grazer = True
            # This is a crucial point: if grazer ate, its energy is now higher.
            # For the predator eating the grazer part, this new higher energy is the baseline.
            # However, initial_predator_energy_at_start should remain the predator's energy at turn 0.

        # Check if grazer is dead AND predator gained energy compared to its absolute start
        if not grazer_was_eaten_by_predator and not grazer.alive and \
           predator.energy > predator_energy_at_test_start:
            grazer_was_eaten_by_predator = True # Signifies predator successfully consumed grazer for a net energy gain

        # Break conditions
        if plant_was_eaten_by_grazer and grazer_was_eaten_by_predator: # Full cycle achieved
            break
        if not plant_was_eaten_by_grazer and grazer_was_eaten_by_predator: # Predator ate grazer directly
            break
        # Additional break if grazer is dead but predator didn't gain energy (e.g. cost of hunt > gain)
        # to prevent loop from running unnecessarily if main conditions for success are impossible.
        if not grazer.alive and predator.energy <= predator_energy_at_test_start and i > 5: # give a few turns for energy to be gained
             # If grazer is dead, and predator hasn't gained energy from its initial state after a few turns,
             # it's unlikely to, so break to evaluate current flags.
             if grazer_was_eaten_by_predator == False : # only set this if not already true
                  # this case means grazer died, predator did not profit.
                  # grazer_was_eaten_by_predator remains false.
                  pass # let assertions handle this.
             # break # Optional break if we decide this scenario won't lead to success. For now, let it run.


    # Assertion logic:
    if plant_was_eaten_by_grazer:
        assert grazer_was_eaten_by_predator, "If grazer ate plant, it should have been eaten by predator for full cycle."
    else:
        # If plant was not eaten by grazer, we accept if grazer was eaten by predator directly.
        assert grazer_was_eaten_by_predator, "If grazer didn't eat plant, it must have been eaten by predator for energy transfer."

    # To ensure at least one significant event happened:
    assert plant_was_eaten_by_grazer or grazer_was_eaten_by_predator, "Energy transfer (either plant->grazer or grazer->predator) should have occurred."

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
