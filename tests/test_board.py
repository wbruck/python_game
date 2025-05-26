"""
Tests for the game.board module.

This module contains unit tests for the Board class and its functionality.
"""

import pytest
from game.board import Board, MovementType, Position

def test_init(board):
    """Test board initialization."""
    assert board.width == 10
    assert board.height == 10
    assert len(board.grid) == 10
    assert len(board.grid[0]) == 10

def test_is_valid_position(board):
    """Test the is_valid_position method."""
    # Valid positions
    assert board.is_valid_position(0, 0)
    assert board.is_valid_position(9, 9)
    assert board.is_valid_position(5, 5)
    
    # Invalid positions
    assert not board.is_valid_position(-1, 0)
    assert not board.is_valid_position(0, -1)
    assert not board.is_valid_position(10, 0)
    assert not board.is_valid_position(0, 10)
        
def test_place_and_get_object(board):
    """Test placing and getting objects on the board."""
    # Place a dummy object
    dummy_obj = "dummy"
    assert board.place_object(dummy_obj, 5, 5)
    
    # Get the object back
    assert board.get_object(5, 5) == dummy_obj
    
    # Try to place another object in the same position
    another_obj = "another"
    assert not board.place_object(another_obj, 5, 5)
    
    # Try to place an object outside the board
    assert not board.place_object(dummy_obj, 10, 10)
        
def test_remove_object(board):
    """Test removing objects from the board."""
    # Place a dummy object
    dummy_obj = "dummy"
    board.place_object(dummy_obj, 5, 5)
    
    # Remove the object
    removed_obj = board.remove_object(5, 5)
    assert removed_obj == dummy_obj
    assert board.get_object(5, 5) is None
    
    # Try to remove from an empty position
    assert board.remove_object(6, 6) is None
    
    # Try to remove from outside the board
    assert board.remove_object(10, 10) is None
        
def test_movement_types(board, diagonal_board):
    """Test movement restrictions based on movement type."""
    obj = "test_obj"
    
    # Test cardinal movement
    board.place_object(obj, 5, 5)
    # Valid cardinal moves
    assert board.move_object(5, 5, 5, 6)  # North
    assert board.move_object(5, 6, 5, 5)  # South
    assert board.move_object(5, 5, 6, 5)  # East
    assert board.move_object(6, 5, 5, 5)  # West
    # Invalid diagonal moves
    assert not board.move_object(5, 5, 6, 6)  # Northeast
    
    # Test diagonal movement
    obj2 = "test_obj2"
    diagonal_board.place_object(obj2, 5, 5)
    # Valid diagonal moves
    assert diagonal_board.move_object(5, 5, 6, 6)  # Northeast
    assert diagonal_board.move_object(6, 6, 5, 5)  # Southwest
        
    def test_position_tracking(self):
        """Test object position tracking."""
        obj = "test_obj"
        self.board.place_object(obj, 5, 5)
        
        # Test position tracking after placement
        pos = self.board.get_object_position(obj)
        self.assertEqual(pos.x, 5)
        self.assertEqual(pos.y, 5)
        
        # Test position tracking after movement
        self.board.move_object(5, 5, 5, 6)
        pos = self.board.get_object_position(obj)
        self.assertEqual(pos.x, 5)
        self.assertEqual(pos.y, 6)
        
        # Test position tracking after removal
        self.board.remove_object(5, 6)
        self.assertIsNone(self.board.get_object_position(obj))
        
def test_field_of_view(board):
    """Test field of view calculations."""
    # Create a simple setup with an obstacle
    class Obstacle:
        blocks_vision = True
        
    viewer = "viewer"
    obstacle = Obstacle()
    
    board.place_object(viewer, 5, 5)
    board.place_object(obstacle, 5, 7)
    
    # Test visibility calculations
    visible_positions = board.calculate_field_of_view(5, 5, 3)
    
    # Position (5,7) and positions behind it should not be visible
    assert any(p.x == 5 and p.y == 6 for p in visible_positions)  # Position before obstacle
    assert not any(p.x == 5 and p.y == 8 for p in visible_positions)  # Position behind obstacle
        
def test_available_moves(board, diagonal_board):
    """Test getting available moves based on movement type."""
    obj = "test_obj"
    board.place_object(obj, 5, 5)
    
    # Test cardinal moves
    moves = board.get_available_moves(5, 5)
    assert len(moves) == 4  # Should have 4 possible moves
    
    # Test diagonal moves
    obj2 = "test_obj2"
    diagonal_board.place_object(obj2, 5, 5)
    diagonal_moves = diagonal_board.get_available_moves(5, 5)
    assert len(diagonal_moves) == 8  # Should have 8 possible moves
        
def test_random_plant_placement(board):
    """Test random plant placement."""
    def plant_factory():
        return "plant"
        
    # Test placing plants
    positions = board.place_random_plants(5, plant_factory)
    assert len(positions) == 5
    
    # Verify plants were actually placed
    for pos in positions:
        obj = board.get_object(pos.x, pos.y)
        assert obj == "plant"
        
    # Test placing more plants than available spaces
    small_board = Board(2, 2)  # Small board
    positions = small_board.place_random_plants(5, plant_factory)
    assert len(positions) == 4  # Should only place 4 plants (2x2 board)
