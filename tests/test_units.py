"""
Tests for the game.units package.

This module contains unit tests for the Unit class and its derived classes.
"""

import unittest
import copy # Added for deepcopy
from unittest.mock import Mock, patch

from game.units.base_unit import Unit
from game.units.unit_types import Predator, Scavenger, Grazer
from game.config import Config # Added import

# Helper function to create a test Config object
def create_test_config(custom_settings=None):
    # Pass a dummy path to avoid os.path.exists(None) error in Config
    config_instance = Config(config_path="dummy_test_config.json")
    # Start with a deep copy of default config to isolate changes
    test_config_data = copy.deepcopy(Config.DEFAULT_CONFIG)
    if custom_settings:
        for section, settings in custom_settings.items():
            if section not in test_config_data:
                test_config_data[section] = {}
            for key, value in settings.items():
                # Handle nested dictionaries like 'energy_consumption'
                if isinstance(value, dict) and isinstance(test_config_data[section].get(key), dict):
                    test_config_data[section][key].update(value)
                else:
                    test_config_data[section][key] = value
    config_instance.config = test_config_data
    # Re-initialize unit attributes that depend on config loading in __init__
    # This is a bit of a workaround because Unit's __init__ processes config directly.
    # A more robust way would be for Unit to have a reload_config method or take specific params.
    if hasattr(config_instance, 'SCHEMA'): # Ensure schema is present for get calls
        config_instance.energy_cost_move = config_instance.get("units", "energy_consumption.move")
        config_instance.resting_exit_energy_ratio = config_instance.get("units", "resting_exit_energy_ratio")
        config_instance.max_resting_turns = config_instance.get("units", "max_resting_turns")
        config_instance.min_energy_force_exit_rest_ratio = config_instance.get("units", "min_energy_force_exit_rest_ratio")
    return config_instance

class TestBaseUnit(unittest.TestCase):
    """Test cases for the base Unit class."""
    
    def setUp(self):
        """Set up a unit and board mock for testing."""
        # Default config for most tests. Specific tests can override.
        self.config = create_test_config()
        self.unit = Unit(5, 5, config=self.config)
        self.board = Mock()
        self.board.is_valid_position.return_value = True
        self.board.get_object.return_value = None
        self.board.move_object.return_value = True # Default to successful move for board mock
        
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
        # Test movement with insufficient energy (energy < cost)
        self.unit.energy = 0
        # Ensure energy_cost_move is loaded for the unit
        self.unit.energy_cost_move = self.config.get("units", "energy_consumption.move") if self.config else 1
        if self.unit.energy_cost_move > 0: # Only test if cost is positive
            self.assertFalse(self.unit.move(1, 0, self.board))

        # Test movement when unit is resting
        self.unit.state = "resting"
        self.unit.energy = 100 # Ample energy
        self.assertFalse(self.unit.move(1, 0, self.board))


    def test_unit_can_move_with_exact_energy(self):
        """Test unit can move if energy is exactly equal to move cost."""
        custom_config_settings = {
            "units": {"energy_consumption": {"move": 5}}
        }
        test_config = create_test_config(custom_config_settings)
        unit = Unit(5, 5, config=test_config)
        unit.energy = 5 # Energy exactly equals cost

        self.board.move_object.return_value = True # Ensure board allows move
        self.assertTrue(unit.move(1, 0, self.board), "Unit should move with exact energy.")
        self.assertEqual(unit.energy, 0, "Unit energy should be 0 after moving with exact cost.")

    def test_unit_exits_resting_at_new_threshold(self):
        """Test unit exits resting state based on configured energy ratio."""
        custom_config_settings = {
            "units": {"resting_exit_energy_ratio": 0.7} # 70%
        }
        test_config = create_test_config(custom_config_settings)
        unit = Unit(5, 5, config=test_config)
        unit.max_energy = 100

        # Scenario 1: Energy just above threshold
        unit.energy = 71
        unit.state = "resting"
        unit.update(self.board)
        self.assertEqual(unit.state, "wandering", "Unit should switch to wandering if energy > threshold.")

        # Scenario 2: Energy just below threshold
        unit.energy = 69
        unit.state = "resting"
        unit.update(self.board)
        self.assertEqual(unit.state, "resting", "Unit should remain resting if energy < threshold.")
        
        # Scenario 3: Energy exactly at threshold (should remain resting as condition is energy > ratio)
        unit.energy = 70
        unit.state = "resting"
        unit.update(self.board)
        self.assertEqual(unit.state, "resting", "Unit should remain resting if energy == threshold.")

    def test_unit_forced_exit_from_resting_after_max_turns(self):
        """Test unit is forced out of resting after max_resting_turns if energy is sufficient."""
        custom_config_settings = {
            "units": {
                "max_resting_turns": 5,
                "min_energy_force_exit_rest_ratio": 0.3
            }
        }
        test_config = create_test_config(custom_config_settings)
        unit = Unit(5, 5, config=test_config)
        unit.max_energy = 100
        # Energy must be high enough not to trigger 'feeding' ( > 0.4 * max_energy)
        # and high enough for forced exit ( > min_energy_force_exit_rest_ratio * max_energy, e.g. > 0.3*100=30)
        unit.energy = 41
        unit.state = "resting"
        unit.last_state = "resting" # Ensure state_duration increments correctly
        # state_duration will be incremented before the check.
        # So to trigger when duration becomes max_resting_turns (5), start at 4.
        unit.state_duration = test_config.max_resting_turns - 1

        unit.update(self.board) # Duration increments to max_resting_turns (e.g. 5)
        # With energy = 41, and resting_exit_energy_ratio = 0.6 (default from DEFAULT_CONFIG if not overridden)
        # 41 is not > 60, so it won't exit resting due to high energy.
        # It also won't go to feeding as 41 is not <= 40.
        # So it should remain resting until impatient logic.
        self.assertEqual(unit.state, "wandering", "Unit should switch to wandering after max_resting_turns.")
        self.assertEqual(unit.state_duration, 0, "State duration should reset after forced exit.")

    def test_unit_forced_exit_from_resting_not_triggered_if_energy_too_low(self):
        """Test unit is NOT forced out of resting if energy is below min_energy_force_exit_rest_ratio."""
        custom_config_settings = {
            "units": {
                "max_resting_turns": 5,
                "min_energy_force_exit_rest_ratio": 0.3
            }
        }
        test_config = create_test_config(custom_config_settings)
        unit = Unit(5, 5, config=test_config)
        unit.max_energy = 100
        # Energy must be low enough to initially trigger/maintain resting (e.g. <= 0.2 * max_energy)
        # AND low enough to be below min_energy_force_exit_rest_ratio (e.g. < 0.3 * max_energy)
        unit.energy = 15 # e.g. 15%
        unit.state = "resting"
        unit.state_duration = test_config.max_resting_turns # Duration is at max

        unit.update(self.board)
        # With energy 15, it should remain resting based on the initial general state checks.
        # Then, for impatient rest, 15 is < (0.3 * 100 = 30), so it should not exit.
        self.assertEqual(unit.state, "resting", "Unit should remain resting if energy is too low for forced exit.")

    def test_unit_regenerates_energy_in_resting_state(self):
        """Test unit regenerates energy while resting."""
        test_config = create_test_config() # Using default config (resting regen is +2)
        unit = Unit(5, 5, config=test_config)
        unit.max_energy = 100
        unit.energy = 50
        unit.state = "resting"

        expected_energy_gain = 2 # Default resting energy gain

        unit.update(self.board)

        # Passive drain is handled by GameLoop, Unit.update only handles resting gain.
        # If unit is resting, it should not have passive drain applied by GameLoop.
        # Resting state also increases energy.
        expected_final_energy = min(unit.energy + expected_energy_gain, unit.max_energy)
        # The energy in the previous line was already updated by unit.update().
        # So expected_final_energy should be initial_energy + gain
        self.assertEqual(unit.energy, 50 + expected_energy_gain,
                         f"Unit should regenerate {expected_energy_gain} energy while resting.")

        # Test regeneration does not exceed max_energy
        # For this, unit must remain in resting state.
        # Use a custom config to ensure resting_exit_energy_ratio is high (e.g., 1.0)
        # so that unit.energy = 99 doesn't cause an exit from resting.
        custom_config_settings_high_exit = {
            "units": {"resting_exit_energy_ratio": 1.0}
        }
        test_config_high_exit = create_test_config(custom_config_settings_high_exit)
        unit_high_exit = Unit(5, 5, config=test_config_high_exit)
        unit_high_exit.max_energy = 100
        unit_high_exit.energy = 99
        unit_high_exit.state = "resting"
        unit_high_exit.update(self.board)
        self.assertEqual(unit_high_exit.energy, 100, "Unit energy should not exceed max_energy when resting.")

        unit_high_exit.energy = 100 # Start at max
        unit_high_exit.state = "resting"
        unit_high_exit.update(self.board)
        self.assertEqual(unit_high_exit.energy, 100, "Unit energy should not change if already at max_energy when resting.")

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
