"""Integration tests for the ecosystem simulation game.

This module contains comprehensive integration tests that verify the correct interaction
between different game components, focusing on realistic game scenarios and complex
interactions between units, the board, and the game loop.
"""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.plants.base_plant import Plant
from game.config import Config

# Common configurations for testing
TEST_CONFIG = {
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
        "energy_consumption": {
            "move": 1,
            "attack": 2,
            "look": 0
        },
        "decay_rate": 0.1
    },
    "environment": {
        "day_night_cycle": True,
        "cycle_length": 5
    }
}

@pytest.fixture
def test_config():
    """Provide a consistent configuration for tests."""
    config = Config()
    config.update(TEST_CONFIG)
    return config

@pytest.fixture
def test_board():
    """Create a test board with standard dimensions."""
    return Board(10, 10, MovementType.CARDINAL)

@pytest.fixture
def test_game_loop(test_board, test_config):
    """Create a game loop with fixed board and configuration."""
    random.seed(42)  # Ensure deterministic behavior
    game_loop = GameLoop(test_board, max_turns=100)
    return game_loop

def test_predator_hunting_behavior(test_game_loop, test_board):
    """Integration test for predator hunting behavior."""
    # Set up predator and prey with proper stats
    predator = Unit(2, 2, hp=120, energy=80, strength=15, speed=2, vision=6)  # Predator stats
    prey = Unit(5, 5, hp=120, energy=150, strength=5, speed=1, vision=4)  # Grazer stats
    
    test_board.place_object(predator, 2, 2)
    test_board.place_object(prey, 5, 5)
    test_game_loop.add_unit(predator)
    test_game_loop.add_unit(prey)
    
    initial_distance = Position(predator.x, predator.y).distance_to(Position(prey.x, prey.y))
    
    for _ in range(5):
        test_game_loop.process_turn()
        if not prey.alive:  # Prey was caught
            break
    
    final_distance = Position(predator.x, predator.y).distance_to(Position(prey.x, prey.y))
    assert (final_distance < initial_distance or not prey.alive), "Predator should either move closer to prey or catch it"

def test_unit_plant_interaction(test_game_loop, test_board):
    """Integration test for unit-plant interaction."""
    grazer = Unit(1, 1, hp=120, energy=150, strength=5, speed=1, vision=4)  # Grazer stats
    plant = Plant(Position(4, 4), base_energy=50, growth_rate=0.1, regrowth_time=5)
    
    test_board.place_object(grazer, 1, 1)
    test_board.place_object(plant, plant.position.x, plant.position.y)
    test_game_loop.add_unit(grazer)
    
    initial_energy = grazer.energy
    
    for _ in range(5):
        test_game_loop.process_turn()
        if grazer.energy > initial_energy:  # Plant was consumed
            break
    
    assert grazer.energy > initial_energy or test_board.get_object(4, 4) is None, "Grazer should either consume plant or plant should be removed"

def test_combat_resolution(test_game_loop, test_board):
    """Integration test for combat between units."""
    strong_unit = Unit(3, 3, hp=120, energy=80, strength=15, speed=2, vision=6)  # Predator stats
    weak_unit = Unit(3, 4, hp=120, energy=150, strength=5, speed=1, vision=4)  # Grazer stats
    
    test_board.place_object(strong_unit, 3, 3)
    test_board.place_object(weak_unit, 3, 4)
    test_game_loop.add_unit(strong_unit)
    test_game_loop.add_unit(weak_unit)
    
    for _ in range(5):
        test_game_loop.process_turn()
        if not weak_unit.alive:
            break
    
    assert not weak_unit.alive, "Weaker unit should be defeated"
    assert strong_unit.alive, "Stronger unit should survive"
    assert strong_unit.hp < strong_unit.max_hp, "Stronger unit should take some damage"

def test_environmental_cycle_effects(test_game_loop, test_board):
    """Integration test for basic unit energy consumption."""
    test_unit = Unit(5, 5, hp=120, energy=80, strength=15, speed=2, vision=6)  # Predator stats
    test_board.place_object(test_unit, 5, 5)
    test_game_loop.add_unit(test_unit)
    
    # Record initial energy
    initial_energy = test_unit.energy
    
    # Run several turns
    for _ in range(5):
        test_game_loop.process_turn()
    
    # Verify basic energy consumption
    assert test_unit.energy < initial_energy, \
        "Unit should consume energy over time"

def test_multi_unit_interaction(test_game_loop, test_board):
    """Integration test for multiple unit interactions."""
    units = [
        Unit(2, 2, hp=120, energy=80, strength=15, speed=2, vision=6),   # Predator
        Unit(7, 7, hp=120, energy=150, strength=5, speed=1, vision=4),   # Grazer
        Unit(3, 7, hp=80, energy=100, strength=8, speed=3, vision=8),    # Scavenger
        Unit(7, 2, hp=120, energy=150, strength=5, speed=1, vision=4)    # Grazer
    ]
    
    for unit in units:
        test_board.place_object(unit, unit.x, unit.y)
        test_game_loop.add_unit(unit)
    
    plants = [Plant(4, 4), Plant(5, 5)]
    for plant in plants:
        test_board.place_object(plant, plant.x, plant.y)
    
    for _ in range(10):
        test_game_loop.process_turn()
    
    surviving_units = [u for u in units if u.alive]
    assert len(surviving_units) < len(units), "Competition should result in some unit casualties"
    assert any(u.energy > u.max_energy * 0.8 for u in surviving_units), "Some units should succeed in finding resources"
