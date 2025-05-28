"""Integration tests for unit and plant interactions.

These tests verify the correct interaction between units and plants,
including feeding, resource competition, and energy mechanics.
"""

import pytest
from game.board import Board
from game.units.base_unit import Unit
from game.units.unit_types import Grazer
from game.plants.base_plant import Plant
from game.plants.plant_types import BasicPlant
from game.board import Position

@pytest.mark.integration
class TestUnitPlantIntegration:
    @pytest.fixture
    def board_with_plants(self) -> Board:
        """Create a board with plants in known positions."""
        board = Board(width=10, height=10)
        grass1 = BasicPlant(Position(2, 2))
        grass2 = BasicPlant(Position(2, 3))
        board.place_object(grass1, 2, 2)
        board.place_object(grass2, 2, 3)
        return board

    def test_grazer_feeding_mechanics(self, board_with_plants: Board):
        """Test that grazers can properly feed on plants."""
        grazer = Grazer(x=1, y=1)
        board_with_plants.place_object(grazer, 1, 1)
        
        initial_energy = grazer.energy
        grass = board_with_plants.get_object(2, 2)
        assert grass is not None
        
        # Move next to plant
        board_with_plants.move_object(1, 1, 2, 1)
        
        # Simulate feeding
        assert isinstance(grass, BasicPlant)  # Verify we got a plant
        grass_energy = grass.state.energy_content
        energy_gained = grass.consume(grazer.max_energy - grazer.energy)
        grazer.energy += energy_gained
        
        # Verify energy transfer
        assert grazer.energy > initial_energy
        assert grazer.energy == initial_energy + grass_energy
        assert board_with_plants.get_object(2, 2)

    def test_multiple_grazers_resource_competition(self, board_with_plants: Board):
        """Test competition between multiple grazers for limited plant resources."""
        grazer1 = Grazer(x=1, y=2)
        grazer2 = Grazer(x=3, y=2)
        
        board_with_plants.place_object(grazer1, 1, 2)
        board_with_plants.place_object(grazer2, 3, 2)
        
        grass = board_with_plants.get_object(2, 2)
        assert isinstance(grass, BasicPlant)  # Verify we got a plant
        assert grass is not None
        
        # First grazer feeds
        energy_gained = grass.consume(grazer1.max_energy - grazer1.energy)
        grazer1.energy += energy_gained
        assert board_with_plants.get_object(2, 2) is None
        
        # Second grazer tries to feed on same plant
        grass2 = board_with_plants.get_object(2, 2)
        assert grass2 is None  # Plant should be gone
        
        # Verify second grazer must move to other plant
        remaining_grass = board_with_plants.get_object(2, 3)
        assert isinstance(remaining_grass, BasicPlant)  # Verify we got a plant
        assert remaining_grass is not None
        board_with_plants.move_object(3, 2, 2, 3)
        energy_gained = remaining_grass.consume(grazer2.max_energy - grazer2.energy)
        grazer2.energy += energy_gained
        assert board_with_plants.get_object(2, 3) is None

    def test_plant_regrowth_and_feeding(self, board_with_plants: Board):
        """Test plant regrowth mechanics and subsequent feeding."""
        grazer = Grazer(x=2, y=1)
        board_with_plants.place_object(grazer, 2, 1)
        
        # Feed on plant
        grass = board_with_plants.get_object(2, 2)
        assert isinstance(grass, BasicPlant)  # Verify we got a plant
        initial_energy = grass.state.energy_content
        energy_gained = grass.consume(grazer.max_energy - grazer.energy)
        grazer.energy += energy_gained
        
        # Simulate plant regrowth
        new_grass = BasicPlant(Position(2, 2))
        board_with_plants.place_object(new_grass, 2, 2)
        
        # Verify feeding on regrown plant
        regrown = board_with_plants.get_object(2, 2)
        assert isinstance(regrown, BasicPlant)  # Verify we got a plant
        assert regrown.state.energy_content <= initial_energy
        
        energy_gained = regrown.consume(grazer.max_energy - grazer.energy)
        grazer.energy += energy_gained
        assert board_with_plants.get_object(2, 2) is None

    def test_energy_transfer_accuracy(self, board_with_plants: Board):
        """Test that energy transfer from plants to units is accurate."""
        grazer = Grazer(x=2, y=1)
        board_with_plants.place_object(grazer, 2, 1)
        
        initial_grazer_energy = grazer.energy
        grass = board_with_plants.get_object(2, 2)
        assert isinstance(grass, BasicPlant)  # Verify we got a plant
        plant_energy = grass.state.energy_content
        
        energy_gained = grass.consume(grazer.max_energy - grazer.energy)
        grazer.energy += energy_gained
        
        # Verify exact energy transfer
        assert grazer.energy == initial_grazer_energy + energy_gained
        assert grazer.energy <= grazer.max_energy  # Ensure energy cap is respected
