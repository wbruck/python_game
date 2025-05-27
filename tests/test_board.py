"""
Tests for the game.board module.

This module contains unit tests for the Board class and its functionality.
"""

import unittest
from game.board import Board, MovementType, Position

class TestBoard(unittest.TestCase):
    """Test cases for the Board class."""
    
    def setUp(self):
        """Set up boards for testing with different movement types."""
        self.board = Board(10, 10)  # Default CARDINAL movement
        self.diagonal_board = Board(10, 10, MovementType.DIAGONAL)
        
    def test_init(self):
        """Test board initialization."""
        self.assertEqual(self.board.width, 10)
        self.assertEqual(self.board.height, 10)
        self.assertEqual(len(self.board.grid), 10)
        self.assertEqual(len(self.board.grid[0]), 10)
        
    def test_is_valid_position(self):
        """Test the is_valid_position method."""
        # Valid positions
        self.assertTrue(self.board.is_valid_position(0, 0))
        self.assertTrue(self.board.is_valid_position(9, 9))
        self.assertTrue(self.board.is_valid_position(5, 5))
        
        # Invalid positions
        self.assertFalse(self.board.is_valid_position(-1, 0))
        self.assertFalse(self.board.is_valid_position(0, -1))
        self.assertFalse(self.board.is_valid_position(10, 0))
        self.assertFalse(self.board.is_valid_position(0, 10))
        
    def test_place_and_get_object(self):
        """Test placing and getting objects on the board."""
        # Place a dummy object
        dummy_obj = "dummy"
        self.assertTrue(self.board.place_object(dummy_obj, 5, 5))
        
        # Get the object back
        self.assertEqual(self.board.get_object(5, 5), dummy_obj)
        
        # Try to place another object in the same position
        another_obj = "another"
        self.assertFalse(self.board.place_object(another_obj, 5, 5))
        
        # Try to place an object outside the board
        self.assertFalse(self.board.place_object(dummy_obj, 10, 10))
        
    def test_remove_object(self):
        """Test removing objects from the board."""
        # Place a dummy object
        dummy_obj = "dummy"
        self.board.place_object(dummy_obj, 5, 5)
        
        # Remove the object
        removed_obj = self.board.remove_object(5, 5)
        self.assertEqual(removed_obj, dummy_obj)
        self.assertIsNone(self.board.get_object(5, 5))
        
        # Try to remove from an empty position
        self.assertIsNone(self.board.remove_object(6, 6))
        
        # Try to remove from outside the board
        self.assertIsNone(self.board.remove_object(10, 10))
        
    def test_movement_types(self):
        """Test movement restrictions based on movement type."""
        obj = "test_obj"
        
        # Test cardinal movement
        self.board.place_object(obj, 5, 5)
        # Valid cardinal moves
        self.assertTrue(self.board.move_object(5, 5, 5, 6))  # North
        self.assertTrue(self.board.move_object(5, 6, 5, 5))  # South
        self.assertTrue(self.board.move_object(5, 5, 6, 5))  # East
        self.assertTrue(self.board.move_object(6, 5, 5, 5))  # West
        # Invalid diagonal moves
        self.assertFalse(self.board.move_object(5, 5, 6, 6))  # Northeast
        
        # Test diagonal movement
        obj2 = "test_obj2"
        self.diagonal_board.place_object(obj2, 5, 5)
        # Valid diagonal moves
        self.assertTrue(self.diagonal_board.move_object(5, 5, 6, 6))  # Northeast
        self.assertTrue(self.diagonal_board.move_object(6, 6, 5, 5))  # Southwest
        
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
        
    def test_field_of_view(self):
        """Test field of view calculations."""
        # Create a simple setup with an obstacle
        class Obstacle:
            blocks_vision = True
            
        viewer = "viewer"
        obstacle = Obstacle()
        
        self.board.place_object(viewer, 5, 5)
        self.board.place_object(obstacle, 5, 7)
        
        # Test visibility calculations
        visible_positions = self.board.calculate_field_of_view(5, 5, 3)
        
        # Position (5,7) and positions behind it should not be visible
        self.assertTrue(any(p.x == 5 and p.y == 6 for p in visible_positions))  # Position before obstacle
        self.assertFalse(any(p.x == 5 and p.y == 8 for p in visible_positions))  # Position behind obstacle
        
    def test_available_moves(self):
        """Test getting available moves based on movement type."""
        obj = "test_obj"
        self.board.place_object(obj, 5, 5)
        
        # Test cardinal moves
        moves = self.board.get_available_moves(5, 5)
        self.assertEqual(len(moves), 4)  # Should have 4 possible moves
        
        # Test diagonal moves
        # Clear previous test objects and place new object for diagonal test
        obj2 = "test_obj2"
        self.diagonal_board = Board(10, 10, MovementType.DIAGONAL)  # Fresh board
        self.diagonal_board.place_object(obj2, 5, 5)
        diagonal_moves = self.diagonal_board.get_available_moves(5, 5)
        self.assertEqual(len(diagonal_moves), 8)  # Should have 8 possible moves
        
    def test_random_plant_placement(self):
        """Test random plant placement."""
        def plant_factory():
            return "plant"
            
        # Test placing plants
        positions = self.board.place_random_plants(5, plant_factory)
        self.assertEqual(len(positions), 5)
        
        # Verify plants were actually placed
        for pos in positions:
            obj = self.board.get_object(pos.x, pos.y)
            self.assertEqual(obj, "plant")
            
        # Test placing more plants than available spaces
        self.board = Board(2, 2)  # Small board
        positions = self.board.place_random_plants(5, plant_factory)
        self.assertEqual(len(positions), 4)  # Should only place 4 plants (2x2 board)

if __name__ == '__main__':
    unittest.main()
