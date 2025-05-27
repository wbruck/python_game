"""
Tests for the plant system implementation.

This module contains unit tests for the base plant class, specific plant types,
and the plant manager to ensure proper functionality of the plant ecosystem.
"""

import pytest
from game.board import Board, Position, MovementType
from game.plants.base_plant import Plant, PlantState
from game.plants.plant_types import BasicPlant, EnergyRichPlant, FastGrowingPlant
from game.plants.plant_manager import PlantManager

def test_base_plant_initialization():
    """Test that plants initialize with correct values."""
    pos = Position(1, 1)
    plant = Plant(pos, base_energy=50.0, growth_rate=0.1, regrowth_time=10.0)
    
    assert plant.position == pos
    assert plant.base_energy == 50.0
    assert plant.growth_rate == 0.1
    assert plant.regrowth_time == 10.0
    assert plant.state.growth_stage == 1.0
    assert plant.state.energy_content == 50.0
    assert plant.state.is_alive is True

def test_plant_consumption():
    """Test that plant consumption works correctly."""
    plant = Plant(Position(0, 0), base_energy=50.0, growth_rate=0.1, regrowth_time=10.0)
    
    # Partial consumption
    consumed = plant.consume(20.0)
    assert consumed == 20.0
    assert plant.state.energy_content == 30.0
    assert plant.state.is_alive is True
    
    # Complete consumption
    consumed = plant.consume(40.0)
    assert consumed == 30.0
    assert plant.state.energy_content == 0.0
    assert plant.state.is_alive is False
    assert plant.state.growth_stage == 0.0

def test_plant_regrowth():
    """Test that plants regrow correctly after consumption."""
    plant = Plant(Position(0, 0), base_energy=50.0, growth_rate=0.1, regrowth_time=10.0)
    
    # Consume plant completely
    plant.consume(50.0)
    assert plant.state.is_alive is False
    
    # Test partial regrowth
    plant.update(5.0)  # Half the regrowth time
    assert 0.0 < plant.state.growth_stage < 1.0
    assert plant.state.is_alive is False
    
    # Test complete regrowth
    plant.update(5.0)  # Complete the regrowth
    assert plant.state.growth_stage == 1.0
    assert plant.state.energy_content == 50.0
    assert plant.state.is_alive is True

def test_plant_types():
    """Test that different plant types have correct characteristics."""
    pos = Position(0, 0)
    
    basic = BasicPlant(pos)
    energy_rich = EnergyRichPlant(pos)
    fast_growing = FastGrowingPlant(pos)
    
    # Test different energy contents
    assert energy_rich.base_energy > basic.base_energy > fast_growing.base_energy
    
    # Test different growth rates
    assert fast_growing.growth_rate > basic.growth_rate > energy_rich.growth_rate
    
    # Test symbols
    assert basic.symbol == "*"
    assert energy_rich.symbol == "%"
    assert fast_growing.symbol == "+"

def test_plant_manager():
    """Test plant manager generation and distribution."""
    config = {
        "plants": {
            "initial_count": 10,
            "growth_rate": 0.08,
            "max_count": 20
        }
    }
    
    board = Board(10, 10, MovementType.CARDINAL)
    manager = PlantManager(board, config)
    
    # Test initial generation
    manager.generate_initial_plants()
    assert len(manager.plants) == 10
    
    # Test plant distribution
    basic_count = 0
    energy_rich_count = 0
    fast_growing_count = 0
    
    for plant in manager.plants.values():
        if isinstance(plant, BasicPlant):
            basic_count += 1
        elif isinstance(plant, EnergyRichPlant):
            energy_rich_count += 1
        elif isinstance(plant, FastGrowingPlant):
            fast_growing_count += 1
    
    # Check rough distribution matches weights
    assert basic_count > energy_rich_count
    assert basic_count > fast_growing_count

def test_plant_manager_updates():
    """Test that plant manager properly updates plants over time."""
    config = {
        "plants": {
            "initial_count": 5,
            "growth_rate": 1.0,  # 100% growth rate for testing
            "max_count": 10
        }
    }
    
    board = Board(5, 5, MovementType.CARDINAL)
    manager = PlantManager(board, config)
    manager.generate_initial_plants()
    
    # Get a plant and consume it
    pos = next(iter(manager.plants.keys()))
    plant = manager.plants[pos]
    plant.consume(plant.base_energy)
    
    # Update should trigger regrowth
    manager.update(10.0)
    assert plant.state.growth_stage > 0.0
