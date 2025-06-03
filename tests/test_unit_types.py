import pytest
from game.units.unit_types import Predator, Scavenger, Grazer
from game.units.base_unit import Unit # For creating generic units / dead units
from game.board import Board, Position
from game.plants.base_plant import Plant # For creating plants
# Assuming BasicPlant might be used if available, or a generic Plant
try:
    from game.plants.plant_types import BasicPlant
except ImportError:
    BasicPlant = Plant # Fallback if BasicPlant is not defined

# Using conftest.py for config_defaults fixture is assumed.
# If not, a local mock_config or simple config might be needed.

# Helper function to create a simple plant
def create_plant(x, y, energy=10, config=None):
    # BasicPlant might require a config. If Plant is used as fallback, it might too.
    # The Plant base class constructor takes: position, base_energy, growth_rate, regrowth_time, config
    # For testing, we often just need position and energy.
    try:
        # Try BasicPlant first, as it's more concrete if available
        return BasicPlant(position=Position(x,y), initial_energy=energy, config=config)
    except TypeError: # Fallback if BasicPlant constructor is different or Plant is used
        return Plant(position=Position(x,y), base_energy=float(energy), config=config)


# Test Initialization (largely unchanged, but ensure config is passed if constructor needs it)
def test_unit_initialization(config_defaults):
    """Test that units are initialized with correct base stats."""
    mock_board = Board(1,1, config=config_defaults) # Dummy board for init
    predator = Predator(x=0, y=0, config=config_defaults, board=mock_board)
    assert predator.hp == 120
    assert predator.energy == 80

    scavenger = Scavenger(x=0, y=0, config=config_defaults, board=mock_board)
    assert scavenger.hp == 100
    assert scavenger.energy == 110

    grazer = Grazer(x=0, y=0, config=config_defaults, board=mock_board)
    assert grazer.hp == 90
    assert grazer.energy == 130

# Predator Tests
def test_predator_attacks_adjacent_grazer(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator = Predator(x=1, y=1, config=config_defaults, board=board)
    initial_grazer_hp = Grazer(x=0,y=0, config=config_defaults, board=board).max_hp # Get default HP
    grazer = Grazer(x=2, y=1, hp=initial_grazer_hp, config=config_defaults, board=board)
    board.place_object(predator, 1, 1)
    board.place_object(grazer, 2, 1)

    predator.update(board)

    assert predator.x == 1 and predator.y == 1 # Did not move
    assert grazer.hp < initial_grazer_hp # Grazer took damage
    assert predator.state == "combat" # Predator should be in combat state

def test_predator_moves_towards_non_adjacent_grazer(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator = Predator(x=1, y=1, speed=1, config=config_defaults, board=board) # Speed 1 for predictable move
    grazer = Grazer(x=4, y=1, config=config_defaults, board=board)
    board.place_object(predator, 1, 1)
    board.place_object(grazer, 4, 1)
    
    predator.state = "hunting" # Ensure it's in a state to hunt
    predator.update(board)

    assert predator.x == 2 and predator.y == 1 # Moved closer
    assert predator.energy < predator.max_energy # Energy consumed

def test_predator_flees_from_stronger_predator(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator_test = Predator(x=5, y=5, speed=1, config=config_defaults, board=board)
    # "Stronger" is not explicitly modeled, but another predator is a threat
    threat_predator = Predator(x=4, y=5, config=config_defaults, board=board)
    board.place_object(predator_test, 5, 5)
    board.place_object(threat_predator, 4, 5)

    predator_test.hp = predator_test.max_hp * 0.2 # Make it want to flee
    predator_test.update(board)
    
    # Should move away from (4,5) -> to (6,5) or (5,4) or (5,6)
    assert (predator_test.x == 6 and predator_test.y == 5) or \
           (predator_test.x == 5 and predator_test.y == 4) or \
           (predator_test.x == 5 and predator_test.y == 6)
    assert predator_test.state == "fleeing"

def test_predator_hunts_closest_if_multiple_prey(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator = Predator(x=5, y=5, speed=1, config=config_defaults, board=board)
    grazer_close = Grazer(x=6, y=5, config=config_defaults, board=board) # distance 1
    grazer_far = Grazer(x=8, y=5, config=config_defaults, board=board)   # distance 3
    board.place_object(predator, 5, 5)
    board.place_object(grazer_close, 6, 5)
    board.place_object(grazer_far, 8, 5)

    predator.state = "hunting"
    predator.update(board)
    # Should attack/move towards grazer_close
    assert grazer_close.hp < grazer_close.max_hp or (predator.x == 6 and predator.y == 5)


def test_predator_eats_dead_unit_when_hungry(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator = Predator(x=1, y=1, config=config_defaults, board=board)
    dead_unit = Unit(x=3, y=1, config=config_defaults, board=board) # Generic dead unit
    dead_unit.alive = False
    dead_unit.decay_stage = 1
    dead_unit.decay_energy = 50
    board.place_object(predator, 1, 1)
    board.place_object(dead_unit, 3, 1)

    predator.energy = predator.max_energy * 0.1 # Make hungry
    predator.update(board) # Should trigger _find_closest_food

    assert predator.x == 2 and predator.y == 1 # Moved towards dead unit
    assert predator.energy < predator.max_energy * 0.1 # Energy spent on move
    
    # Second update: should be adjacent now and eat
    predator.update(board)
    assert predator.x == 2 and predator.y == 1 # Stays to eat
    assert predator.energy > predator.max_energy * 0.1 # Energy gained from eating


def test_predator_explores_when_no_targets(config_defaults):
    board = Board(10, 10, config=config_defaults)
    predator = Predator(x=5, y=5, speed=1, config=config_defaults, board=board)
    board.place_object(predator, 5, 5)
    initial_x, initial_y = predator.x, predator.y

    predator.state = "hunting" # Try to hunt
    predator.update(board) # No prey, should explore

    assert (predator.x != initial_x or predator.y != initial_y) # Should have moved

# Scavenger Tests
def test_scavenger_moves_towards_corpse(config_defaults):
    board = Board(10, 10, config=config_defaults)
    scavenger = Scavenger(x=1, y=1, speed=1, config=config_defaults, board=board)
    dead_unit = Unit(x=4, y=1, config=config_defaults, board=board)
    dead_unit.alive = False
    dead_unit.decay_stage = 1
    dead_unit.decay_energy = 50
    board.place_object(scavenger, 1, 1)
    board.place_object(dead_unit, 4, 1)

    scavenger.update(board)
    assert scavenger.x == 2 and scavenger.y == 1 # Moved closer

def test_scavenger_eats_adjacent_corpse(config_defaults):
    board = Board(10, 10, config=config_defaults)
    scavenger = Scavenger(x=1, y=1, config=config_defaults, board=board)
    dead_unit = Unit(x=2, y=1, config=config_defaults, board=board)
    dead_unit.alive = False
    dead_unit.decay_stage = 1
    dead_unit.decay_energy = 50
    initial_scavenger_energy = scavenger.max_energy * 0.5
    scavenger.energy = initial_scavenger_energy
    board.place_object(scavenger, 1, 1)
    board.place_object(dead_unit, 2, 1)
    
    scavenger.update(board)
    assert scavenger.x == 1 and scavenger.y == 1 # Stays to eat
    assert scavenger.energy > initial_scavenger_energy

def test_scavenger_flees_from_predator(config_defaults):
    board = Board(10, 10, config=config_defaults)
    scavenger = Scavenger(x=5, y=5, speed=1, config=config_defaults, board=board)
    predator = Predator(x=4, y=5, config=config_defaults, board=board)
    board.place_object(scavenger, 5, 5)
    board.place_object(predator, 4, 5)

    scavenger.update(board) # Should flee
    assert (scavenger.x == 6 and scavenger.y == 5) or \
           (scavenger.x == 5 and scavenger.y == 4) or \
           (scavenger.x == 5 and scavenger.y == 6) # Moved away

def test_scavenger_eats_plant_when_hungry_no_corpse(config_defaults):
    board = Board(10, 10, config=config_defaults)
    scavenger = Scavenger(x=1, y=1, config=config_defaults, board=board)
    plant_obj = create_plant(x=2, y=1, energy=20, config=config_defaults)
    board.place_object(scavenger, 1, 1)
    board.place_object(plant_obj, 2, 1)
    
    initial_energy = scavenger.max_energy * 0.1
    scavenger.energy = initial_energy
    scavenger.update(board) # Should eat plant

    assert scavenger.x == 1 and scavenger.y == 1 # Stays to eat
    assert scavenger.energy > initial_energy


# Grazer Tests
def test_grazer_moves_towards_plant(config_defaults):
    board = Board(10, 10, config=config_defaults)
    grazer = Grazer(x=1, y=1, speed=1, config=config_defaults, board=board)
    plant_obj = create_plant(x=4, y=1, config=config_defaults)
    board.place_object(grazer, 1, 1)
    board.place_object(plant_obj, 4, 1)

    grazer.update(board)
    assert grazer.x == 2 and grazer.y == 1 # Moved closer

def test_grazer_eats_adjacent_plant(config_defaults):
    board = Board(10, 10, config=config_defaults)
    grazer = Grazer(x=1, y=1, config=config_defaults, board=board)
    plant_obj = create_plant(x=2, y=1, energy=30, config=config_defaults)
    board.place_object(grazer, 1, 1)
    board.place_object(plant_obj, 2, 1)

    initial_energy = grazer.max_energy * 0.1
    grazer.energy = initial_energy
    grazer.update(board)

    assert grazer.x == 1 and grazer.y == 1 # Stays to eat
    assert grazer.energy > initial_energy

def test_grazer_flees_from_predator(config_defaults):
    board = Board(10, 10, config=config_defaults)
    grazer = Grazer(x=5, y=5, speed=1, config=config_defaults, board=board)
    predator = Predator(x=4, y=5, config=config_defaults, board=board)
    board.place_object(grazer, 5, 5)
    board.place_object(predator, 4, 5)

    grazer.update(board) # Should flee
    assert (grazer.x == 6 and grazer.y == 5) or \
           (grazer.x == 5 and grazer.y == 4) or \
           (grazer.x == 5 and grazer.y == 6) # Moved away

# Edge Case Tests
def test_predator_hunts_near_edge(config_defaults):
    board = Board(5, 5, config=config_defaults) # Small board
    predator = Predator(x=3, y=2, speed=1, config=config_defaults, board=board)
    grazer = Grazer(x=4, y=2, config=config_defaults, board=board) # Target at edge
    board.place_object(predator, 3, 2)
    board.place_object(grazer, 4, 2)

    # Predator is at (3,2), Grazer at (4,2). Predator should attack.
    initial_grazer_hp = grazer.hp
    predator.update(board)
    assert predator.x == 3 and predator.y == 2 # Predator attacks, does not move
    assert grazer.hp < initial_grazer_hp

    # Scenario 2: Move towards prey at edge
    board = Board(5, 5, config=config_defaults) # Reset board
    predator = Predator(x=1, y=2, speed=1, config=config_defaults, board=board)
    grazer = Grazer(x=0, y=2, config=config_defaults, board=board) # Target at edge x=0
    board.place_object(predator, 1, 2)
    board.place_object(grazer, 0, 2)

    predator.update(board)
    # Predator at (1,2) should move to (0,2) and then attack.
    # First update, it moves to (0,2) IF (0,2) is empty.
    # But (0,2) is where grazer is. So it should attack from (1,2)
    # The new logic: if adjacent, attack. If not, score moves.
    # (0,2) is not a "possible_move" for predator because grazer is there.
    # So predator should see grazer at (0,2), determine it's adjacent, and attack.
    assert predator.x == 1 and predator.y == 2
    assert grazer.hp < grazer.max_hp


def test_grazer_flees_near_edge(config_defaults):
    board = Board(5, 5, config=config_defaults) # Small board
    grazer = Grazer(x=0, y=2, speed=1, config=config_defaults, board=board) # Grazer at edge
    predator = Predator(x=1, y=2, config=config_defaults, board=board) # Predator next to it
    board.place_object(grazer, 0, 2)
    board.place_object(predator, 1, 2)

    grazer.update(board)
    # Grazer at (0,2) should flee from Predator at (1,2).
    # Possible moves for Grazer from (0,2) on 5x5 board: (0,1), (0,3). (Not (0,2) itself)
    # It should pick one of these, e.g. (0,1) or (0,3) if empty.
    # (0,0) (0,1) (0,2) (0,3) (0,4)
    # (1,0) (1,1) (1,2)P(1,3) (1,4)
    # G is at (0,2), P is at (1,2).
    # Closest threat is P. Current dist = 1.
    # Move (0,1): new dist to P at (1,2) is abs(1-0) + abs(2-1) = 1+1=2. Score = 2-1=1.
    # Move (0,3): new dist to P at (1,2) is abs(1-0) + abs(2-3) = 1+1=2. Score = 2-1=1.
    # Both are equally good.
    assert grazer.x == 0 and (grazer.y == 1 or grazer.y == 3)


# Ensure exploration tests from original file are maintained and use config_defaults
def test_hungry_grazer_explores_when_no_plant_in_sight(config_defaults):
    board = Board(width=20, height=20, config=config_defaults)
    grazer = Grazer(x=5, y=5, vision=3, config=config_defaults, board=board) # Vision 3
    grazer.energy = grazer.max_energy * 0.1  # Hungry
    board.place_object(grazer, 5, 5)
    # Plant far away, e.g., at (15,15) - well outside vision 3
    plant = create_plant(x=15, y=15, config=config_defaults)
    board.place_object(plant, 15, 15)
    initial_pos = (grazer.x, grazer.y)
    grazer.update(board)
    assert initial_pos != (grazer.x, grazer.y), "Grazer should explore if hungry and no plants in sight"

def test_hungry_scavenger_explores_when_no_food_in_sight(config_defaults):
    board = Board(width=20, height=20, config=config_defaults)
    scavenger = Scavenger(x=5, y=5, vision=4, config=config_defaults, board=board) # Vision 4
    scavenger.energy = scavenger.max_energy * 0.1  # Hungry
    board.place_object(scavenger, 5, 5)
    # Dead unit far away, e.g., at (15,15)
    dead_unit = Unit(x=15, y=15, config=config_defaults, board=board)
    dead_unit.alive = False; dead_unit.decay_stage=1; dead_unit.decay_energy=10
    board.place_object(dead_unit, 15, 15)
    initial_pos = (scavenger.x, scavenger.y)
    scavenger.update(board)
    assert initial_pos != (scavenger.x, scavenger.y), "Scavenger should explore if hungry and no food in sight"

def test_hungry_predator_explores_when_no_food_in_sight(config_defaults):
    board = Board(width=20, height=20, config=config_defaults)
    predator = Predator(x=5, y=5, vision=3, config=config_defaults, board=board) # Vision 3
    predator.energy = predator.max_energy * 0.1  # Hungry
    board.place_object(predator, 5, 5)
    # Prey far away
    grazer = Grazer(x=15, y=15, config=config_defaults, board=board)
    board.place_object(grazer, 15, 15)
    initial_pos = (predator.x, predator.y)
    predator.update(board) # Should try to find food (dead or alive) or hunt
    assert initial_pos != (predator.x, predator.y), "Predator should explore if hungry and no targets in sight"

```
