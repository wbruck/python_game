"""Integration tests focusing on deterministic component interactions.

These tests verify the correct interaction between core game components:
- Board and Units
- Units and other Units
- Units and Plants
- Game Loop orchestration
"""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.units.unit_types import Predator, Grazer
from game.plants.base_plant import Plant
from game.game_loop import GameLoop, TimeOfDay
from game.config import Config

@pytest.fixture
def fixed_config():
    """Provide a deterministic configuration for tests."""
    config = Config()
    config.update({
        "board": {
            "width": 5,
            "height": 5,
            "allow_diagonal_movement": False
        },
        "game": {
            "max_turns": 20,
            "turn_delay": 0
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
            "day_night_cycle": False,
            "cycle_length": 5
        }
    })
    return config

@pytest.fixture
def test_board(fixed_config):
    """Create a small test board."""
    return Board(
        fixed_config.config["board"]["width"],
        fixed_config.config["board"]["height"],
        MovementType.CARDINAL
    )

@pytest.fixture
def game_loop(test_board, fixed_config):
    """Create a deterministic game loop."""
    random.seed(42)  # Ensure reproducible behavior
    return GameLoop(test_board, config=fixed_config)

@pytest.mark.integration
def test_unit_board_interaction(test_board):
    """Test basic unit placement and movement on board."""
    unit = Unit(0, 0, hp=100, energy=100, strength=10, speed=1, vision=2)
    
    assert test_board.place_object(unit, 0, 0), "Unit should be placed successfully"
    assert test_board.get_object(0, 0) == unit, "Unit should be retrievable from position"
    
    assert unit.move(1, 0, test_board), "Unit should move right"
    assert unit.x == 1 and unit.y == 0, "Unit position should update"
    assert test_board.get_object(1, 0) == unit, "Unit should be at new position"
    assert test_board.get_object(0, 0) is None, "Old position should be empty"

@pytest.mark.integration
def test_combat_interaction(test_board):
    """Test deterministic combat between units."""
    attacker = Unit(1, 1, hp=100, energy=100, strength=20, speed=1, vision=2)
    defender = Unit(1, 2, hp=100, energy=100, strength=10, speed=1, vision=2)
    
    test_board.place_object(attacker, 1, 1)
    test_board.place_object(defender, 1, 2)
    
    initial_defender_hp = defender.hp
    damage = attacker.attack(defender)
    
    assert damage > 0, "Attack should deal damage"
    assert defender.hp < initial_defender_hp, "Defender should lose HP"
    assert defender.hp == initial_defender_hp - damage, "Damage calculation should be deterministic"

@pytest.mark.integration
def test_unit_plant_interaction(game_loop):
    """Test interaction between grazer and plant."""
    grazer = Grazer(1, 1, hp=100, energy=80)
    plant = Plant(Position(1, 2), base_energy=50, growth_rate=0.1)
    
    game_loop.board.place_object(grazer, 1, 1)
    game_loop.board.place_object(plant, 1, 2)
    game_loop.add_unit(grazer)
    
    initial_energy = grazer.energy
    
    for _ in range(3):
        game_loop.process_turn()
    
    assert grazer.energy > initial_energy, "Grazer should gain energy from plant"
    assert game_loop.board.get_object(1, 2) is None, "Plant should be consumed"

@pytest.mark.integration
def test_game_loop_orchestration(game_loop):
    """Test game loop's ability to manage multiple entities."""
    unit1 = Unit(0, 0, hp=100, energy=100)
    unit2 = Unit(4, 4, hp=100, energy=100)
    plant = Plant(Position(2, 2), base_energy=50)
    
    game_loop.board.place_object(unit1, 0, 0)
    game_loop.board.place_object(unit2, 4, 4)
    game_loop.board.place_object(plant, 2, 2)
    game_loop.add_unit(unit1)
    game_loop.add_unit(unit2)
    
    initial_positions = [(unit1.x, unit1.y), (unit2.x, unit2.y)]
    game_loop.process_turn()
    
    assert (unit1.x, unit1.y) != initial_positions[0] or (unit2.x, unit2.y) != initial_positions[1], "Units should move during turn processing"
    assert unit1.energy < 100 or unit2.energy < 100, "Units should consume energy during actions"
