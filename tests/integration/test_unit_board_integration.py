"""Integration tests for unit and board interactions.

These tests verify that units correctly interact with the game board,
including movement, vision, and collision detection.
"""

import pytest
from game.board import Board
from game.units.base_unit import Unit
from game.units.unit_types import Predator, Grazer
from typing import List, Tuple

@pytest.mark.integration
class TestUnitBoardIntegration:
    @pytest.fixture
    def basic_board(self) -> Board:
        """Create a 10x10 board for testing."""
        return Board(width=10, height=10)
    
    @pytest.fixture
    def populated_board(self, basic_board: Board) -> Tuple[Board, List[Unit]]:
        """Create a board with multiple units in known positions."""
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=8, y=8)
        basic_board.place_object(predator, 1, 1)
        basic_board.place_object(grazer, 8, 8)
        return basic_board, [predator, grazer]

    def test_unit_movement_and_collision(self, basic_board: Board):
        """Test that units properly move and detect collisions."""
        unit1 = Unit(x=0, y=0)
        unit2 = Unit(x=1, y=1)
        
        basic_board.place_object(unit1, 0, 0)
        basic_board.place_object(unit2, 1, 1)
        
        assert unit1.x == 0 and unit1.y == 0
        assert unit2.x == 1 and unit2.y == 1
        
        can_move = basic_board.move_object(0, 0, 0, 1)
        assert can_move
        assert unit1.x == 0 and unit1.y == 1
        
        can_move = basic_board.move_object(0, 1, 1, 1)
        assert not can_move
        assert unit1.x == 0 and unit1.y == 1

    def test_unit_vision_and_detection(self, populated_board: Tuple[Board, List[Unit]]):
        """Test that units can properly detect other units within vision range."""
        board, units = populated_board
        predator, grazer = units
        
        visible_to_predator = board.get_units_in_range(predator.x, predator.y, predator.vision)
        assert grazer not in visible_to_predator
        
        board.move_object(8, 8, 3, 3)
        
        visible_to_predator = board.get_units_in_range(predator.x, predator.y, predator.vision)
        assert grazer in visible_to_predator

    def test_multi_turn_movement_sequence(self, basic_board: Board):
        """Test a sequence of movements over multiple turns."""
        unit = Unit(x=0, y=0, speed=2)
        basic_board.place_object(unit, 0, 0)
        
        moves = [(1, 1), (2, 2), (3, 3), (4, 4)]
        for x, y in moves:
            can_move = basic_board.move_object(unit.x, unit.y, x, y)
            assert can_move
            assert unit.x == x and unit.y == y
            
        can_move = basic_board.move_object(4, 4, 7, 7)
        assert not can_move
        assert unit.x == 4 and unit.y == 4

    def test_board_boundaries(self, basic_board: Board):
        """Test that units cannot move outside board boundaries."""
        unit = Unit(x=0, y=0)
        basic_board.place_object(unit, 0, 0)
        
        can_move = basic_board.move_object(0, 0, -1, 0)
        assert not can_move
        assert unit.x == 0 and unit.y == 0
        
        can_move = basic_board.move_object(0, 0, 9, 9)
        assert can_move
        assert unit.x == 9 and unit.y == 9
        
        can_move = basic_board.move_object(9, 9, 10, 10)
        assert not can_move
        assert unit.x == 9 and unit.y == 9
