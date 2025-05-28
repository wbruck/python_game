"""Integration tests for configuration impact on game behavior.

These tests verify that configuration changes properly affect
game mechanics, unit behavior, and environmental systems.
"""

import pytest
import json
from game.config import Config
from game.game_loop import GameLoop
from game.board import Board
from game.units.unit_types import Predator, Grazer
from game.plants.plant_types import BasicPlant
from game.board import Position

@pytest.mark.integration
class TestConfigIntegration:
    @pytest.fixture
    def base_config(self, tmp_path):
        """Create a base configuration file."""
        config_path = tmp_path / "test_config.json"
        config_data = {
            "board": {
                "width": 20,
                "height": 20,
                "allow_diagonal_movement": False
            },
            "environment": {
                "cycle_length": 10,
                "day_night_cycle": True,
                "seasonal_effects": True
            },
            "units": {
                "predator": {
                    "base_energy": 100,
                    "vision_range": 5,
                    "attack_strength": 15
                },
                "grazer": {
                    "base_energy": 80,
                    "vision_range": 4,
                    "flee_speed": 2
                }
            },
            "plants": {
                "growth_rate": 0.1,
                "max_energy": 50
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        return Config(config_path)

    def test_board_config_effects(self, base_config):
        """Test that board configuration properly affects movement mechanics."""
        # Create board with diagonal movement disabled
        board = Board(
            width=base_config.get("board", "width"),
            height=base_config.get("board", "height"),
            allow_diagonal=base_config.get("board", "allow_diagonal_movement")
        )
        
        unit = Predator(x=1, y=1)
        board.place_unit(unit, 1, 1)
        
        # Attempt diagonal movement (should fail)
        can_move = board.move_unit(unit, 2, 2)
        assert not can_move
        assert unit.x == 1 and unit.y == 1
        
        # Attempt cardinal movement (should succeed)
        can_move = board.move_unit(unit, 1, 2)
        assert can_move
        assert unit.x == 1 and unit.y == 2

    def test_unit_config_effects(self, base_config):
        """Test that unit configuration properly affects unit attributes."""
        predator = Predator(x=0, y=0)
        grazer = Grazer(x=5, y=5)
        
        # Verify configured attributes
        assert predator.energy == base_config.get("units", "predator.base_energy")
        assert predator.vision == base_config.get("units", "predator.vision_range")
        assert predator.strength == base_config.get("units", "predator.attack_strength")
        
        assert grazer.energy == base_config.get("units", "grazer.base_energy")
        assert grazer.vision == base_config.get("units", "grazer.vision_range")
        assert grazer.speed == base_config.get("units", "grazer.flee_speed")

    def test_environment_config_effects(self, base_config):
        """Test that environmental configuration affects game mechanics."""
        board = Board(width=10, height=10)
        game_loop = GameLoop(board=board, config=base_config)
        
        # Verify cycle length configuration
        assert game_loop.day_night_cycle_length == base_config.get("environment", "cycle_length")
        
        # Run through one cycle
        for _ in range(base_config.get("environment", "cycle_length")):
            game_loop.process_turn()
            
        # Verify day/night transition occurred
        assert game_loop.current_turn == base_config.get("environment", "cycle_length")

    def test_plant_config_effects(self, base_config):
        """Test that plant configuration affects growth mechanics."""
        board = Board(width=10, height=10)
        game_loop = GameLoop(board=board, config=base_config)
        
        grass = BasicPlant(Position(5, 5))
        game_loop.add_plant(grass)
        
        initial_energy = grass.energy_content
        
        # Process multiple turns
        for _ in range(5):
            game_loop.process_turn()
            
        # Verify growth constraints
        if grass in game_loop.plants:
            assert grass.energy_content <= base_config.get("plants", "max_energy")
            growth_diff = grass.energy_content - initial_energy
            assert growth_diff >= 0  # Should have grown
            # Growth should be proportional to configured rate
            assert growth_diff <= (5 * base_config.get("plants", "growth_rate") * base_config.get("plants", "max_energy"))

    def test_combat_config_effects(self, base_config):
        """Test that configuration affects combat mechanics."""
        board = Board(width=10, height=10)
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=2, y=2)
        
        board.place_unit(predator, 1, 1)
        board.place_unit(grazer, 2, 2)
        
        initial_grazer_hp = grazer.hp
        predator.attack(grazer)
        
        # Verify damage based on configured strength
        expected_damage = base_config.get("units", "predator.attack_strength")
        actual_damage = initial_grazer_hp - grazer.hp
        assert actual_damage == expected_damage

    def test_config_change_effects(self, base_config, tmp_path):
        """Test that configuration changes affect running game."""
        board = Board(width=10, height=10)
        game_loop = GameLoop(board=board, config=base_config)
        
        # Initial setup
        predator = Predator(x=1, y=1)
        game_loop.add_unit(predator)
        initial_vision = predator.vision
        
        # Modify configuration
        new_config_path = tmp_path / "new_config.json"
        config_data = base_config.config.copy()
        config_data["units"]["predator"]["vision_range"] = initial_vision * 2
        
        with open(new_config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Load new configuration
        new_config = Config(new_config_path)
        game_loop.config = new_config
        
        # Process turn and verify effects
        game_loop.process_turn()
        assert predator.vision == initial_vision * 2

    def test_multiple_config_interactions(self, base_config):
        """Test interactions between different configuration settings."""
        board = Board(width=10, height=10)
        game_loop = GameLoop(board=board, config=base_config)
        
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=8, y=8)
        grass = Grass(x=4, y=4)
        
        game_loop.add_unit(predator)
        game_loop.add_unit(grazer)
        game_loop.add_plant(grass)
        
        # Run multiple turns to test interaction of different configured systems
        for _ in range(base_config.get("environment", "cycle_length")):
            game_loop.process_turn()
            
            # Verify configuration boundaries are respected
            for unit in game_loop.units:
                if isinstance(unit, Predator):
                    assert unit.vision <= base_config.get("units", "predator.vision_range")
                elif isinstance(unit, Grazer):
                    assert unit.speed <= base_config.get("units", "grazer.flee_speed")
            
            for plant in game_loop.plants:
                assert plant.energy_content <= base_config.get("plants", "max_energy")
