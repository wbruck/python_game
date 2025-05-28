"""Integration tests for unit combat and interaction mechanics.

These tests verify the correct behavior of unit-to-unit interactions,
including combat, fleeing, and state transitions during encounters.
"""

import pytest
from game.board import Board
from game.units.unit_types import Predator, Grazer, Scavenger
from typing import Tuple, List

@pytest.mark.integration
class TestUnitCombatIntegration:
    @pytest.fixture
    def combat_board(self) -> Tuple[Board, List]:
        """Create a board with predator and prey units."""
        board = Board(width=10, height=10)
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=2, y=2)
        board.place_object(predator, 1, 1)
        board.place_object(grazer, 2, 2)
        return board, [predator, grazer]

    def test_predator_prey_combat(self, combat_board: Tuple[Board, List]):
        """Test basic predator-prey combat mechanics."""
        board, units = combat_board
        predator, grazer = units
        
        initial_predator_energy = predator.energy
        initial_grazer_hp = grazer.hp
        
        # Initiate combat
        predator.state = "hunting"
        combat_result = predator.attack(grazer)
        
        # Verify combat effects
        assert combat_result
        assert grazer.hp < initial_grazer_hp
        assert predator.energy < initial_predator_energy  # Combat costs energy
        
        # If prey dies, verify state changes
        if grazer.hp <= 0:
            assert not grazer.alive
            assert grazer.state == "dead"
            # Predator should gain energy from successful hunt
            assert predator.energy > initial_predator_energy

    def test_fleeing_mechanics(self, combat_board: Tuple[Board, List]):
        """Test prey fleeing mechanics and state transitions."""
        board, units = combat_board
        predator, grazer = units
        
        # Set up fleeing scenario
        grazer.state = "idle"
        visible_units = board.get_units_in_range(predator.x, predator.y, predator.vision)
        
        # Verify prey detects predator and changes state
        if predator in visible_units:
            grazer.state = "fleeing"
            assert grazer.speed > grazer.base_speed  # Speed boost while fleeing
            
            # Try to move away from predator
            initial_distance = abs(predator.x - grazer.x) + abs(predator.y - grazer.y)
            board.move_unit(grazer, 4, 4)  # Move away
            new_distance = abs(predator.x - grazer.x) + abs(predator.y - grazer.y)
            
            assert new_distance > initial_distance

    def test_multi_unit_combat(self):
        """Test combat involving multiple units."""
        board = Board(width=10, height=10)
        predator1 = Predator(x=1, y=1)
        predator2 = Predator(x=1, y=2)
        grazer = Grazer(x=2, y=2)
        
        board.place_object(predator1, 1, 1)
        board.place_object(predator2, 1, 2)
        board.place_object(grazer, 2, 2)
        
        # First predator attacks
        initial_grazer_hp = grazer.hp
        predator1.attack(grazer)
        mid_grazer_hp = grazer.hp
        
        assert mid_grazer_hp < initial_grazer_hp
        
        # Second predator attacks if grazer still alive
        if grazer.alive:
            predator2.attack(grazer)
            assert grazer.hp < mid_grazer_hp

    def test_scavenging_mechanics(self):
        """Test scavenging mechanics with dead units."""
        board = Board(width=10, height=10)
        predator = Predator(x=1, y=1)
        grazer = Grazer(x=2, y=2)
        scavenger = Scavenger(x=3, y=3)
        
        board.place_object(predator, 1, 1)
        board.place_object(grazer, 2, 2)
        board.place_object(scavenger, 3, 3)
        
        # Kill the grazer
        grazer.hp = 0
        grazer.state = "dead"
        assert not grazer.alive
        
        initial_scavenger_energy = scavenger.energy
        
        # Scavenger feeds on dead unit
        scavenger.feed(grazer)
        
        assert scavenger.energy > initial_scavenger_energy
        assert grazer.decay_stage > 0  # Body should start decaying

    def test_combat_energy_mechanics(self, combat_board: Tuple[Board, List]):
        """Test energy consumption during combat."""
        board, units = combat_board
        predator, grazer = units
        
        initial_predator_energy = predator.energy
        initial_grazer_energy = grazer.energy
        
        # Simulate extended chase/combat
        predator.state = "hunting"
        grazer.state = "fleeing"
        
        # Move units within board boundaries to simulate chase
        moves = [(1,0), (1,1), (1,-1)]  # Different movement patterns
        for dx, dy in moves:
            board.move_unit(predator, predator.x + dx, predator.y + dy)
            board.move_unit(grazer, grazer.x + dx, grazer.y - dy)  # Grazer moves opposite direction
            
        # Verify energy consumption
        assert predator.energy < initial_predator_energy
        assert grazer.energy < initial_grazer_energy
        
        # Verify faster fleeing consumes more energy
        assert (initial_grazer_energy - grazer.energy) > (initial_predator_energy - predator.energy)
