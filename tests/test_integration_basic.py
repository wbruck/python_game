"""Basic integration tests for core game mechanics."""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.plants.base_plant import Plant
from game.game_loop import GameLoop
from game.config import Config

@pytest.fixture
def test_config():
    config = Config()
    config.update({
        "board": {"width": 5, "height": 5},
        "game": {"max_turns": 10},
        "units": {"energy_consumption": {"move": 1}}
    })
    return config

@pytest.fixture
def test_board(test_config):
    return Board(5, 5, MovementType.CARDINAL)

@pytest.fixture
def test_game(test_board, test_config):
    random.seed(42)
    return GameLoop(test_board, config=test_config)

@pytest.mark.integration
def test_movement_sequence(test_game):
    unit = Unit(0, 0, hp=100, energy=100)
    test_game.board.place_object(unit, 0, 0)
    test_game.add_unit(unit)
    assert unit.move(1, 0, test_game.board)
    assert unit.x == 1 and unit.y == 0
    assert unit.energy == 99

@pytest.mark.integration
def test_combat_sequence(test_game):
    attacker = Unit(1, 1, hp=100, energy=100, strength=20)
    defender = Unit(1, 2, hp=100, energy=100)
    test_game.board.place_object(attacker, 1, 1)
    test_game.board.place_object(defender, 1, 2)
    damage = attacker.attack(defender)
    assert damage > 0
    assert defender.hp < 100

@pytest.mark.integration
def test_plant_sequence(test_game):
    unit = Unit(1, 1, hp=100, energy=80)
    plant = Plant(Position(1, 2), base_energy=50)
    test_game.board.place_object(unit, 1, 1)
    test_game.board.place_object(plant, 1, 2)
    test_game.add_unit(unit)
    initial_energy = unit.energy
    test_game.process_turn()
    assert unit.energy != initial_energy
