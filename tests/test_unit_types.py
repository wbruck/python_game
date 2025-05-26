import pytest
from game.units.unit_types import Predator, Scavenger, Grazer
from game.board import Board

@pytest.fixture
def board():
    from game.board import MovementType
    return Board(width=10, height=10, movement_type=MovementType.DIAGONAL)

@pytest.fixture
def predator():
    return Predator(x=5, y=5)

@pytest.fixture
def scavenger():
    return Scavenger(x=3, y=3)

@pytest.fixture
def grazer():
    return Grazer(x=7, y=7)

def test_unit_initialization():
    """Test that units are initialized with correct base stats."""
    predator = Predator(x=0, y=0)
    assert predator.hp == 120
    assert predator.energy == 80
    assert predator.strength == 15
    assert predator.speed == 2
    assert predator.vision == 6

    scavenger = Scavenger(x=0, y=0)
    assert scavenger.hp == 100
    assert scavenger.energy == 110
    assert scavenger.strength == 8
    assert scavenger.speed == 1
    assert scavenger.vision == 8

    grazer = Grazer(x=0, y=0)
    assert grazer.hp == 90
    assert grazer.energy == 130
    assert grazer.strength == 5
    assert grazer.speed == 1
    assert grazer.vision == 5

def test_experience_system():
    """Test that units gain experience and level up properly."""
    predator = Predator(x=0, y=0)
    
    # Test initial state
    assert predator.level == 1
    assert predator.experience == 0
    assert len(predator.traits) == 0
    
    # Test experience gain
    predator.gain_experience("combat", 10)
    assert predator.level == 2
    assert "battle_hardened" in predator.traits
    assert predator.strength > 15  # Should have increased due to combat specialization

def test_unit_behaviors(board, predator, scavenger, grazer):
    """Test that units exhibit their specialized behaviors."""
    # Place units on board
    board.place_object(predator, predator.x, predator.y)
    board.place_object(scavenger, scavenger.x, scavenger.y)
    board.place_object(grazer, grazer.x, grazer.y)
    
    # Test predator hunting behavior
    initial_energy = predator.energy
    predator.update(board)
    assert predator.energy < initial_energy  # Should have spent energy moving/hunting
    
    # Test grazer fleeing from predator
    grazer_pos = (grazer.x, grazer.y)
    grazer.update(board)
    assert (grazer.x, grazer.y) != grazer_pos  # Should have moved away from predator
    
    # Test scavenger behavior with dead unit
    dead_unit = Grazer(x=2, y=2)  # Place dead unit where it won't collide with predator
    dead_unit.alive = False
    board.place_object(dead_unit, dead_unit.x, dead_unit.y)
    scavenger_pos = (scavenger.x, scavenger.y)
    scavenger.update(board)
    assert (scavenger.x, scavenger.y) != scavenger_pos  # Should move toward dead unit

def test_unit_evolution():
    """Test that units evolve and specialize based on their actions."""
    grazer = Grazer(x=0, y=0)
    
    # Simulate successful feeding actions
    for _ in range(15):
        grazer.gain_experience("feeding")
    
    assert grazer.level > 1
    assert "efficient_digestion" in grazer.traits
    assert grazer.max_energy > 130  # Should have increased due to feeding specialization
