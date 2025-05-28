"""Integration tests for game loop orchestration and environmental effects.

These tests verify the correct coordination of all game components through
the game loop, including turn processing, environmental cycles, and their
effects on units and plants.
"""

import pytest
from game.game_loop import GameLoop, TimeOfDay, Season
from game.board import Board
from game.units.unit_types import Predator, Grazer
from game.plants.plant_types import BasicPlant
from game.board import Position
from game.config import Config

@pytest.mark.integration
class TestGameLoopIntegration:
    @pytest.fixture
    def game_setup(self):
        """Create a basic game setup with board, units, and plants."""
        board = Board(width=10, height=10)
        config = Config()
        game_loop = GameLoop(board=board, max_turns=100, config=config)
        
        # Add units
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=8, y=8)
        game_loop.add_unit(predator)
        game_loop.add_unit(grazer)
        board.place_object(predator, 1, 1)
        board.place_object(grazer, 8, 8)
        
        # Add plants
        grass = BasicPlant(Position(4, 4))
        game_loop.add_plant(grass)
        board.add_plant(grass)
        
        return game_loop, board, [predator, grazer], [grass]

    def test_full_turn_processing(self, game_setup):
        """Test processing of a complete game turn with all components."""
        game_loop, board, units, plants = game_setup
        predator, grazer = units
        
        initial_positions = [(u.x, u.y) for u in units]
        initial_energies = [u.energy for u in units]
        
        # Process one full turn
        game_loop.process_turn()
        
        # Verify turn effects
        assert game_loop.current_turn == 1
        
        # Check that units moved or acted
        current_positions = [(u.x, u.y) for u in units]
        current_energies = [u.energy for u in units]
        
        assert any(curr != init for curr, init in zip(current_positions, initial_positions)) or \
               any(curr != init for curr, init in zip(current_energies, initial_energies))

    def test_day_night_cycle_effects(self, game_setup):
        """Test the effects of day/night cycle on units and plants."""
        game_loop, board, units, plants = game_setup
        predator, grazer = units
        
        # Record initial stats
        initial_vision = {u: u.vision for u in units}
        
        # Force night time
        game_loop.time_of_day = TimeOfDay.NIGHT
        game_loop.process_turn()
        
        # Verify night effects
        for unit in units:
            assert unit.vision < initial_vision[unit]
        
        # Change to day
        game_loop.time_of_day = TimeOfDay.DAY
        game_loop.process_turn()
        
        # Verify vision restored
        for unit in units:
            assert unit.vision == initial_vision[unit]

    def test_seasonal_effects(self, game_setup):
        """Test seasonal effects on plant growth and unit behavior."""
        game_loop, board, units, plants = game_setup
        grass = plants[0]
        
        # Test winter effects
        game_loop.season = Season.WINTER
        initial_energy = grass.energy_content
        game_loop.process_turn()
        
        # Plants should grow slower in winter
        if grass in game_loop.plants:
            assert grass.energy_content <= initial_energy
        
        # Test spring effects
        game_loop.season = Season.SPRING
        game_loop.process_turn()
        
        # Verify increased growth in spring
        new_grass = board.get_plant_at(grass.x, grass.y)
        if new_grass:
            assert new_grass.energy_content > initial_energy

    def test_multi_turn_scenario(self, game_setup):
        """Test a complex multi-turn scenario with various interactions."""
        game_loop, board, units, plants = game_setup
        predator, grazer = units
        
        # Run multiple turns
        for _ in range(5):
            game_loop.process_turn()
            
            # Verify basic invariants
            assert 0 <= game_loop.current_turn <= game_loop.max_turns
            
            # Check unit states
            for unit in game_loop.units:
                if unit.alive:
                    assert unit.energy > 0
                    assert unit.hp > 0
                    assert unit.state in ["idle", "hunting", "fleeing", "feeding", "resting"]
                else:
                    assert unit.state in ["dead", "decaying"]

    def test_environmental_cycle_transitions(self, game_setup):
        """Test proper transitions of environmental cycles."""
        game_loop, board, units, plants = game_setup
        
        initial_time = game_loop.time_of_day
        initial_season = game_loop.season
        
        # Run enough turns to trigger cycle changes
        for _ in range(game_loop.day_night_cycle_length + 1):
            game_loop.process_turn()
        
        # Verify day/night cycle changed
        assert game_loop.time_of_day != initial_time
        
        # Run enough turns for seasonal change
        for _ in range(game_loop.season_length):
            game_loop.process_turn()
        
        # Verify season changed
        assert game_loop.season != initial_season

    def test_population_dynamics(self, game_setup):
        """Test population dynamics over multiple turns."""
        game_loop, board, units, plants = game_setup
        
        initial_unit_count = len(game_loop.units)
        initial_plant_count = len(game_loop.plants)
        
        # Run several turns
        for _ in range(10):
            game_loop.process_turn()
            
            # Verify population constraints
            assert len(game_loop.units) <= initial_unit_count * 2  # No excessive reproduction
            assert len(game_loop.plants) <= board.width * board.height  # No overgrowth
            
            # Verify basic ecosystem dynamics
            alive_units = [u for u in game_loop.units if u.alive]
            assert len(alive_units) > 0  # Ecosystem hasn't collapsed
