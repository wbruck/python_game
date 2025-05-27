import pytest
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.plants.base_plant import Plant

@pytest.fixture
def test_board():
    return Board(4, 4, MovementType.CARDINAL)

@pytest.fixture
def test_game(test_board):
    return GameLoop(test_board)

@pytest.mark.integration
def test_basic_movement(test_game):
    unit = Unit(1, 1)
    test_game.board.place_object(unit, 1, 1)
    test_game.add_unit(unit)
    
    initial_pos = (unit.x, unit.y)
    unit.move(1, 0, test_game.board)
    
    assert (unit.x, unit.y) != initial_pos
    assert test_game.board.get_object(2, 1) == unit
    assert test_game.board.get_object(1, 1) is None

@pytest.mark.integration
def test_basic_combat(test_game):
    attacker = Unit(1, 1, strength=10)
    defender = Unit(1, 2, hp=20)
    
    test_game.board.place_object(attacker, 1, 1)
    test_game.board.place_object(defender, 1, 2)
    
    initial_hp = defender.hp
    attacker.attack(defender)
    
    assert defender.hp < initial_hp
    assert test_game.board.get_object(1, 2) == defender

@pytest.mark.integration
def test_basic_plant(test_game):
    unit = Unit(1, 1, energy=50)
    plant = Plant(Position(2, 1), base_energy=20, growth_rate=0.1, regrowth_time=5)
    
    test_game.board.place_object(unit, 1, 1)
    test_game.board.place_object(plant, 2, 1)
    test_game.add_unit(unit)
    
    initial_energy = unit.energy
    test_game.process_turn()
    
    assert unit.energy != initial_energy

@pytest.mark.integration
def test_multi_turn(test_game):
    # Create unit and plant to encourage movement
    unit = Unit(1, 1, energy=100, hp=100)
    plant = Plant(Position(3, 3), base_energy=30, growth_rate=0.1, regrowth_time=5)
    
    test_game.board.place_object(unit, 1, 1)
    test_game.board.place_object(plant, 3, 3)
    test_game.add_unit(unit)
    
    initial_energy = unit.energy
    initial_pos = (unit.x, unit.y)
    
    # Run multiple turns
    for _ in range(3):
        test_game.process_turn()
    
    # Verify state changes occurred
    assert unit.energy < initial_energy, "Energy should be consumed over turns"
    assert (unit.x, unit.y) != initial_pos, "Unit should move during turns"
