"""
Tests for the game.game_loop module.

This module contains unit tests for the GameLoop class and its functionality.
"""

import unittest
from unittest.mock import Mock, patch

from game.game_loop import GameLoop, TimeOfDay, Season
class TestGameLoop(unittest.TestCase):
    """Test cases for the GameLoop class."""
    
    def setUp(self):
        """Set up a game loop for testing."""
        self.board = Mock()
        self.config = Mock()
        self.config.config = {
            "environment": {
                "cycle_length": 10,
                "day_night_cycle": True
            },
            "game": {
                "turn_delay": 0.0
            }
        }
        self.game_loop = GameLoop(self.board, max_turns=100, config=self.config)
    def test_init(self):
        """Test game loop initialization."""
        self.assertEqual(self.game_loop.board, self.board)
        self.assertEqual(self.game_loop.max_turns, 100)
        self.assertEqual(self.game_loop.current_turn, 0)
        self.assertEqual(len(self.game_loop.units), 0)
        self.assertEqual(len(self.game_loop.plants), 0)
        self.assertFalse(self.game_loop.is_running)
        
    def test_add_unit(self):
        """Test adding units to the game loop."""
        unit = Mock()
        self.game_loop.add_unit(unit)
        self.assertEqual(len(self.game_loop.units), 1)
        self.assertEqual(self.game_loop.units[0], unit)
        
    def test_add_plant(self):
        """Test adding plants to the game loop."""
        plant = Mock()
        self.game_loop.add_plant(plant)
        self.assertEqual(len(self.game_loop.plants), 1)
        self.assertEqual(self.game_loop.plants[0], plant)
        
    def test_start_stop(self):
        """Test starting and stopping the game loop."""
        # Mock the run method to avoid actually running the loop
        self.game_loop.run = Mock()
        
        # Test start
        self.game_loop.start()
        self.assertTrue(self.game_loop.is_running)
        self.game_loop.run.assert_called_once()
        
        # Test stop
        self.game_loop.stop()
        self.assertFalse(self.game_loop.is_running)
        
    @patch('random.shuffle')
    def test_process_turn(self, mock_shuffle):
        """Test processing a single turn."""
        # Set up mocks
        unit1 = Mock()
        unit1.alive = True
        unit1.base_vision = 10  # Add numeric base_vision
        unit1.energy = 100  # Add numeric energy since we do arithmetic with it
        unit2 = Mock()
        unit2.alive = False
        unit2.decay_stage = 0
        
        plant = Mock()
        plant.base_growth_rate = 1.0  # Add numeric base_growth_rate since we do arithmetic with it
        
        self.game_loop.units = [unit1, unit2]
        self.game_loop.plants = [plant]
        
        # Process a turn
        self.game_loop.process_turn()
        
        # Verify that the turn was processed correctly
        self.assertEqual(self.game_loop.current_turn, 1)
        mock_shuffle.assert_called_once_with(self.game_loop.units)
        unit1.update.assert_called_once_with(self.board)
        unit2.update.assert_not_called()  # Dead units should not be updated
        plant.update.assert_called_once()
        
    def test_environmental_cycles(self):
        """Test environmental cycle updates and effects."""
        # Test initial state
        self.assertEqual(self.game_loop.time_of_day.value, "day")
        self.assertEqual(self.game_loop.season.value, "spring")
        
        # Test day/night cycle
        for _ in range(10):  # One complete cycle
            self.game_loop.process_turn()
        self.assertEqual(self.game_loop.time_of_day.value, "night")
        
        # Test seasonal change (40 turns = 4 day/night cycles = 1 season)
        for _ in range(30):  # Complete first season
            self.game_loop.process_turn()
        self.assertEqual(self.game_loop.season.value, "summer")
        
    def test_environmental_effects(self):
        """Test that environmental conditions affect units and plants."""
        # Setup test units and plants
        unit = Mock()
        unit.alive = True
        unit.base_vision = 10
        unit.energy = 100  # Set energy as a number since we do arithmetic with it
        plant = Mock()
        plant.base_growth_rate = 1.0
        plant.min_energy = 50
        plant.energy = 100
        
        self.game_loop.add_unit(unit)
        self.game_loop.add_plant(plant)
        
        # Process turn during day
        self.game_loop.process_turn()
        unit.update.assert_called_once()
        self.assertEqual(unit.vision, 10)  # Normal vision during day
        
        # Move to night
        self.game_loop.time_of_day = TimeOfDay.NIGHT
        self.game_loop.process_turn()
        self.assertEqual(unit.vision, 5)  # Reduced vision at night
        
    def test_get_stats(self):
        """Test getting game statistics with environmental information."""
        # Set up some units
        unit1 = Mock()
        unit1.alive = True
        unit2 = Mock()
        unit2.alive = True
        unit3 = Mock()
        unit3.alive = False
        unit3.state = "decaying"
        
        self.game_loop.units = [unit1, unit2, unit3]
        self.game_loop.plants = [Mock(), Mock()]
        self.game_loop.current_turn = 42
        
        # Get stats
        stats = self.game_loop.get_stats()
        
        # Verify stats
        self.assertEqual(stats["turn"], 42)
        self.assertIn("environment", stats)
        self.assertEqual(stats["environment"]["time_of_day"], "day")
        self.assertEqual(stats["environment"]["season"], "spring")
        self.assertEqual(stats["units"]["decaying"], 1)
        self.assertEqual(stats["max_turns"], 100)
        self.assertEqual(stats["alive_units"], 2)
        self.assertEqual(stats["dead_units"], 1)
        self.assertEqual(stats["plants"], 2)
        
    def test_run(self):
        """Test running the game loop."""
        # Mock process_turn to avoid actual processing
        self.game_loop.process_turn = Mock()
        
        # Set up the game loop to run for a few turns
        self.game_loop.is_running = True
        self.game_loop.max_turns = 3
        
        # Run the game loop
        self.game_loop.run()
        
        # Verify that process_turn was called the right number of times
        self.assertEqual(self.game_loop.process_turn.call_count, 3)
        
        # Test early stopping
        self.game_loop.process_turn.reset_mock()
        self.game_loop.current_turn = 0
        self.game_loop.is_running = True
        
        # Define a side effect to stop after the first turn
        def stop_after_first_turn():
            self.game_loop.current_turn += 1
            if self.game_loop.current_turn == 1:
                self.game_loop.is_running = False
                
        self.game_loop.process_turn.side_effect = stop_after_first_turn
        
        # Run the game loop
        self.game_loop.run()
        
        # Verify that process_turn was called only once
        self.assertEqual(self.game_loop.process_turn.call_count, 1)

if __name__ == '__main__':
    unittest.main()
