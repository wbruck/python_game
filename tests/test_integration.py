"""Integration tests for the ecosystem simulation game.

This module contains comprehensive integration tests that verify the correct interaction
between different game components, focusing on realistic game scenarios and complex
interactions between units, the board, and the game loop.
"""

import pytest
import random
from game.board import Board, MovementType, Position
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.plants.base_plant import Plant
from game.config import Config

# Common configurations for testing
TEST_CONFIG = {
    "board": {
        "width": 10,
        "height": 10,
        "allow_diagonal_movement": False
    },
    "game": {
        "max_turns": 100,
        "turn_delay": 0.0
    },
    "units": {
        "energy_consumption": {
            "move": 1,
            "attack": 2,
            "look": 0
        },
        "decay_rate": 0.1
    },
    "environment": {
        "day_night_cycle": True,
        "cycle_length": 5
    }
}

@pytest.mark.integration
def test_predator_hunting_behavior(integration_game_loop, integration_board, configured_unit):
    """Integration test for predator hunting behavior."""
    # Set up predator and prey using configured units
    predator = configured_unit("predator", 2, 2)
    prey = configured_unit("grazer", 5, 5)
    
    integration_board.place_object(predator, 2, 2)
    integration_board.place_object(prey, 5, 5)
    integration_game_loop.add_unit(predator)
    integration_game_loop.add_unit(prey)
    
    # Track initial state
    initial_state = {
        "predator_pos": (predator.x, predator.y),
        "prey_pos": (prey.x, prey.y),
        "predator_energy": predator.energy,
        "distance": Position(predator.x, predator.y).distance_to(Position(prey.x, prey.y))
    }
    
    # Run simulation with clear success criteria
    for turn in range(5):
        integration_game_loop.process_turn()
        current_distance = Position(predator.x, predator.y).distance_to(Position(prey.x, prey.y))
        
        # Either predator has caught prey or is moving toward it
        if not prey.alive:
            assert predator.energy > initial_state["predator_energy"], \
                "Predator should gain energy after successful hunt"
            break
        else:
            assert current_distance <= initial_state["distance"], \
                f"Predator should move closer to prey (turn {turn + 1})"
            assert predator.energy < initial_state["predator_energy"], \
                "Predator should consume energy while hunting"

@pytest.mark.integration
def test_unit_plant_interaction(integration_game_loop, integration_board, configured_unit, integration_config):
    """Integration test for unit-plant interaction."""
    # Create configured grazer and plant
    grazer = configured_unit("grazer", 1, 1)
    plant = Plant(
        Position(4, 4),
        base_energy=50,
        growth_rate=integration_config.get("plants", "growth_rate"),
        regrowth_time=5
    )
    
    integration_board.place_object(grazer, 1, 1)
    integration_board.place_object(plant, plant.position.x, plant.position.y)
    integration_game_loop.add_unit(grazer)
    
    # Track initial state
    initial_state = {
        "grazer_pos": (grazer.x, grazer.y),
        "grazer_energy": grazer.energy,
        "plant_pos": (plant.position.x, plant.position.y)
    }
    
    plant_consumed = False
    for turn in range(5):
        integration_game_loop.process_turn()
        current_plant = integration_board.get_object(plant.position.x, plant.position.y)
        
        if grazer.energy > initial_state["grazer_energy"]:
            plant_consumed = True
            assert current_plant is None, "Plant should be removed after consumption"
            assert (grazer.x, grazer.y) == initial_state["plant_pos"], \
                "Grazer should be at plant position after consuming it"
            break
        else:
            # If plant not yet consumed, grazer should be moving toward it
            current_distance = Position(grazer.x, grazer.y).distance_to(Position(plant.position.x, plant.position.y))
            initial_distance = Position(*initial_state["grazer_pos"]).distance_to(Position(*initial_state["plant_pos"]))
            assert current_distance <= initial_distance, \
                f"Grazer should move closer to plant (turn {turn + 1})"
    
    if not plant_consumed:
        assert grazer.energy < initial_state["grazer_energy"], \
            "Grazer should consume energy while moving"

@pytest.mark.integration
def test_combat_resolution(integration_game_loop, integration_board, configured_unit):
    """Integration test for combat resolution between units."""
    # Create predator (strong) and grazer (weak) units
    strong_unit = configured_unit("predator", 3, 3)
    weak_unit = configured_unit("grazer", 3, 4)
    
    integration_board.place_object(strong_unit, 3, 3)
    integration_board.place_object(weak_unit, 3, 4)
    integration_game_loop.add_unit(strong_unit)
    integration_game_loop.add_unit(weak_unit)
    
    # Track initial state
    initial_state = {
        "strong_unit_hp": strong_unit.hp,
        "strong_unit_energy": strong_unit.energy,
        "weak_unit_hp": weak_unit.hp,
        "weak_unit_energy": weak_unit.energy
    }
    
    combat_resolved = False
    for turn in range(5):
        integration_game_loop.process_turn()
        
        if not weak_unit.alive:
            combat_resolved = True
            assert weak_unit.state == "dead", "Defeated unit should be marked as dead"
            assert strong_unit.energy > initial_state["strong_unit_energy"], \
                "Winning combat should restore some energy"
            break
        else:
            assert weak_unit.hp < initial_state["weak_unit_hp"], \
                f"Combat should damage weaker unit (turn {turn + 1})"
            assert strong_unit.energy < initial_state["strong_unit_energy"], \
                "Combat should consume attacker's energy"
    
    assert combat_resolved, "Combat should resolve within time limit"
    assert strong_unit.alive, "Stronger unit should survive"
    assert strong_unit.hp < strong_unit.max_hp, "Stronger unit should take some damage during combat"

@pytest.mark.integration
def test_environmental_cycle_effects(integration_game_loop, integration_board, configured_unit, integration_config):
    """Integration test for environmental effects on units."""
    test_unit = configured_unit("predator", 5, 5)
    integration_board.place_object(test_unit, 5, 5)
    integration_game_loop.add_unit(test_unit)
    
    # Track initial state
    initial_state = {
        "energy": test_unit.energy,
        "vision": test_unit.vision
    }
    
    cycle_length = integration_config.get("environment", "cycle_length")
    
    # Run through one complete environmental cycle
    for turn in range(cycle_length):
        integration_game_loop.process_turn()
        
        # Verify energy consumption
        assert test_unit.energy < initial_state["energy"], \
            f"Unit should consume energy over time (turn {turn + 1})"
        
        # Verify day/night vision changes if enabled
        if integration_config.get("environment", "day_night_cycle"):
            is_night = (turn >= cycle_length // 2)
            if is_night:
                assert test_unit.vision < initial_state["vision"], \
                    "Unit vision should be reduced during night cycle"

@pytest.mark.integration
def test_multi_unit_interaction(integration_game_loop, integration_board, configured_unit, integration_config):
    """Integration test for multiple unit interactions in a complex ecosystem."""
    # Create a diverse set of units
    units = [
        configured_unit("predator", 2, 2),
        configured_unit("grazer", 7, 7),
        configured_unit("scavenger", 3, 7),
        configured_unit("grazer", 7, 2)
    ]
    
    # Track initial states
    initial_states = {
        i: {
            "position": (unit.x, unit.y),
            "energy": unit.energy,
            "hp": unit.hp
        } for i, unit in enumerate(units)
    }
    
    # Place units and plants
    for unit in units:
        integration_board.place_object(unit, unit.x, unit.y)
        integration_game_loop.add_unit(unit)
    
    plants = [
        Plant(Position(4, 4), 
             base_energy=50,
             growth_rate=integration_config.get("plants", "growth_rate"),
             regrowth_time=5),
        Plant(Position(5, 5),
             base_energy=50,
             growth_rate=integration_config.get("plants", "growth_rate"),
             regrowth_time=5)
    ]
    
    for plant in plants:
        integration_board.place_object(plant, plant.position.x, plant.position.y)
    
    # Run simulation
    for turn in range(10):
        integration_game_loop.process_turn()
        
        # Verify basic behaviors each turn
        for i, unit in enumerate(units):
            if unit.alive:
                # Units should either gain energy (found food) or lose energy (movement/time)
                energy_changed = unit.energy != initial_states[i]["energy"]
                position_changed = (unit.x, unit.y) != initial_states[i]["position"]
                assert energy_changed or position_changed, \
                    f"Unit {i} should either move or change energy (turn {turn + 1})"
    
    # Final state verification
    surviving_units = [u for u in units if u.alive]
    
    # Verify ecosystem dynamics
    assert len(surviving_units) < len(units), \
        "Competition should result in some unit casualties"
    assert any(u.energy > u.max_energy * 0.8 for u in surviving_units), \
        "Some units should succeed in finding resources"
    
    # Verify predator/prey dynamics
    predators = [u for u in surviving_units if u.unit_type == "predator"]
    grazers = [u for u in surviving_units if u.unit_type == "grazer"]
    if predators:
        assert len(grazers) < 2, \
            "Predators should reduce grazer population"
