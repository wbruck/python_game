"""Integration tests for visualization and statistics tracking.

These tests verify that visualization and statistics components correctly
integrate with the game loop and accurately reflect game state.
"""

import pytest
from game.visualization import Visualization
from game.game_loop import GameLoop
from game.board import Board
from game.config import Config
from game.units.unit_types import Predator, Grazer

class TestVisualizer(Visualization):
    """Test visualizer that captures display data for verification."""
    def __init__(self):
        super().__init__()
        self.last_display = None
        self.display_count = 0
        
    def display(self, board, units, plants, stats):
        """Capture display data instead of showing it."""
        self.last_display = {
            'board_size': (board.width, board.height),
            'unit_count': len(units),
            'plant_count': len(plants),
            'stats': stats
        }
        self.display_count += 1

@pytest.mark.integration
class TestVisualizationStatsIntegration:
    @pytest.fixture
    def game_with_visualizer(self, standard_board, standard_config):
        """Create a game setup with test visualizer."""
        game_loop = GameLoop(board=standard_board, config=standard_config)
        visualizer = TestVisualizer()
        game_loop.add_visualizer(visualizer)
        return game_loop, visualizer

    def test_visualization_updates(self, game_with_visualizer):
        """Test that visualization updates properly reflect game state."""
        game_loop, visualizer = game_with_visualizer
        
        # Add units
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=8, y=8)
        game_loop.add_unit(predator)
        game_loop.add_unit(grazer)
        
        # Process turns and verify visualization
        for _ in range(3):
            game_loop.process_turn()
            
            # Verify visualization was updated
            assert visualizer.last_display is not None
            assert visualizer.last_display['unit_count'] == len(game_loop.units)
            assert visualizer.last_display['board_size'] == (game_loop.board.width, game_loop.board.height)
            
            # Verify display called each turn
            assert visualizer.display_count == game_loop.current_turn

    def test_statistics_tracking(self, game_with_visualizer):
        """Test that game statistics are accurately tracked and visualized."""
        game_loop, visualizer = game_with_visualizer
        
        # Add units
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=2, y=2)
        game_loop.add_unit(predator)
        game_loop.add_unit(grazer)
        
        # Initial state
        game_loop.process_turn()
        initial_stats = visualizer.last_display['stats']
        
        # Process combat
        predator.attack(grazer)
        game_loop.process_turn()
        combat_stats = visualizer.last_display['stats']
        
        # Verify combat statistics updated
        assert combat_stats['combat_encounters'] > initial_stats['combat_encounters']
        
        # Process until unit dies
        while grazer.alive:
            predator.attack(grazer)
            game_loop.process_turn()
        
        final_stats = visualizer.last_display['stats']
        assert final_stats['deaths'] > initial_stats['deaths']

    def test_environmental_visualization(self, game_with_visualizer):
        """Test visualization of environmental effects."""
        game_loop, visualizer = game_with_visualizer
        
        # Run through day/night cycle
        for _ in range(game_loop.day_night_cycle_length + 1):
            game_loop.process_turn()
            
            # Verify environmental state displayed
            assert visualizer.last_display is not None
            assert 'time_of_day' in visualizer.last_display['stats']
            assert 'season' in visualizer.last_display['stats']

    def test_population_statistics(self, game_with_visualizer):
        """Test tracking and visualization of population statistics."""
        game_loop, visualizer = game_with_visualizer
        
        # Add multiple units
        for _ in range(3):
            game_loop.add_unit(Predator(x=1, y=1))
        for _ in range(5):
            game_loop.add_unit(Grazer(x=8, y=8))
        
        game_loop.process_turn()
        stats = visualizer.last_display['stats']
        
        # Verify population counts
        assert stats['predator_count'] == 3
        assert stats['grazer_count'] == 5
        
        # Process multiple turns and verify population tracking
        for _ in range(5):
            game_loop.process_turn()
            new_stats = visualizer.last_display['stats']
            
            # Verify population changes are tracked
            assert new_stats['predator_count'] <= stats['predator_count']
            assert new_stats['grazer_count'] <= stats['grazer_count']
            
            stats = new_stats

    def test_energy_statistics(self, game_with_visualizer):
        """Test tracking and visualization of energy-related statistics."""
        game_loop, visualizer = game_with_visualizer
        
        # Add unit and track energy
        unit = Predator(x=1, y=1)
        initial_energy = unit.energy
        game_loop.add_unit(unit)
        
        # Process turns and verify energy tracking
        for _ in range(3):
            game_loop.process_turn()
            stats = visualizer.last_display['stats']
            
            # Energy consumption should be tracked
            assert stats['total_energy_consumed'] > 0
            assert unit.energy < initial_energy  # Energy decreases over time
