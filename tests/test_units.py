"""
Tests for the game.units package.

This module contains unit tests for the Unit class and its derived classes.
"""

import unittest
from unittest.mock import Mock, patch

from game.units.base_unit import Unit
from game.units.unit_types import Predator, Scavenger, Grazer

class TestBaseUnit(unittest.TestCase):
    """Test cases for the base Unit class."""
    
    def setUp(self):
        """Set up a unit and board mock for testing."""
        self.unit = Unit(5, 5)
        self.board = Mock()
        self.board.is_valid_position.return_value = True
        self.board.get_object.return_value = None
        
    def test_init(self):
        """Test unit initialization."""
        self.assertEqual(self.unit.x, 5)
        self.assertEqual(self.unit.y, 5)
        self.assertEqual(self.unit.hp, 100)
        self.assertEqual(self.unit.max_hp, 100)
        self.assertEqual(self.unit.energy, 100)
        self.assertEqual(self.unit.max_energy, 100)
        self.assertEqual(self.unit.strength, 10)
        self.assertEqual(self.unit.speed, 1)
        self.assertEqual(self.unit.vision, 5)
        self.assertEqual(self.unit.state, "idle")
        self.assertTrue(self.unit.alive)
        self.assertEqual(self.unit.decay_stage, 0)
        
    def test_move(self):
        """Test unit movement."""
        # Set up the board mock
        self.board.move_object.return_value = True
        
        # Test successful movement
        self.assertTrue(self.unit.move(1, 0, self.board))
        self.assertEqual(self.unit.x, 6)
        self.assertEqual(self.unit.y, 5)
        self.assertEqual(self.unit.energy, 99)  # Energy should decrease
        
        # Test movement to invalid position
        self.board.is_valid_position.return_value = False
        self.assertFalse(self.unit.move(1, 0, self.board))
        
        # Test movement to occupied position
        self.board.is_valid_position.return_value = True
        self.board.get_object.return_value = "something"
        self.assertFalse(self.unit.move(1, 0, self.board))
        
        # Test movement with insufficient energy
        self.board.get_object.return_value = None
        self.unit.energy = 0
        self.assertFalse(self.unit.move(1, 0, self.board))
        
    def test_attack(self):
        """Test unit attack."""
        target = Unit(6, 5)
        initial_hp = target.hp
        
        # Test successful attack
        damage = self.unit.attack(target)
        self.assertGreater(damage, 0)
        self.assertLess(target.hp, initial_hp)
        
        # Test attack on dead target
        target.alive = False
        damage = self.unit.attack(target)
        self.assertEqual(damage, 0)
        
        # Test attack when unit is dead
        self.unit.alive = False
        target.alive = True
        damage = self.unit.attack(target)
        self.assertEqual(damage, 0)
        
        # Test attack that kills the target
        self.unit.alive = True
        target.hp = 1
        damage = self.unit.attack(target)
        self.assertEqual(target.hp, 0)
        self.assertFalse(target.alive)
        self.assertEqual(target.state, "dead")
        
    def test_look(self):
        """Test unit looking around."""
        # Mock board to return objects in vision range
        def side_effect(x, y):
            if x == 6 and y == 5:
                return "object1"
            elif x == 4 and y == 5:
                return "object2"
            else:
                return None
                
        self.board.get_object.side_effect = side_effect
        
        visible_objects = self.unit.look(self.board)
        self.assertEqual(len(visible_objects), 2)
        self.assertIn(("object1", 6, 5), visible_objects)
        self.assertIn(("object2", 4, 5), visible_objects)


class TestUnitTypes(unittest.TestCase):
    """Test cases for the derived unit classes."""
    
    def test_predator_init(self):
        """Test predator initialization."""
        predator = Predator(5, 5)
        self.assertEqual(predator.x, 5)
        self.assertEqual(predator.y, 5)
        self.assertEqual(predator.hp, 120)
        self.assertEqual(predator.energy, 80)
        self.assertEqual(predator.strength, 15)
        self.assertEqual(predator.speed, 2)
        self.assertEqual(predator.vision, 6)
        self.assertIsNone(predator.target)
        
    def test_scavenger_init(self):
        """Test scavenger initialization."""
        scavenger = Scavenger(5, 5)
        self.assertEqual(scavenger.x, 5)
        self.assertEqual(scavenger.y, 5)
        self.assertEqual(scavenger.hp, 100)
        self.assertEqual(scavenger.energy, 110)
        self.assertEqual(scavenger.strength, 8)
        self.assertEqual(scavenger.speed, 1)
        self.assertEqual(scavenger.vision, 8)
        
    def test_grazer_init(self):
        """Test grazer initialization."""
        grazer = Grazer(5, 5)
        self.assertEqual(grazer.x, 5)
        self.assertEqual(grazer.y, 5)
        self.assertEqual(grazer.hp, 90)
        self.assertEqual(grazer.energy, 130)
        self.assertEqual(grazer.strength, 5)
        self.assertEqual(grazer.speed, 1)
        self.assertEqual(grazer.vision, 5)

if __name__ == '__main__':
    unittest.main()
