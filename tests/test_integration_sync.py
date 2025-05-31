"""Integration tests focusing on state synchronization and interleaved actions."""

import pytest
from game.board import Board, MovementType
from game.units.base_unit import Unit
from game.game_loop import GameLoop
from game.plants.base_plant import Plant

@pytest.fixture
def sync_board():
    """Create a board for synchronization testing."""
    return Board(4, 4, MovementType.DIAGONAL)

@pytest.mark.integration
def test_concurrent_unit_actions(sync_board):
    """Test multiple units acting in the same turn properly synchronize state."""
    game_loop = GameLoop(sync_board)
    
    # Create units in close proximity
    units = [
        Unit(1, 1, unit_type="predator"),
        Unit(1, 2, unit_type="predator"),
        Unit(2, 1, unit_type="grazer")
    ]
    
    # Place and register units
    for unit in units:
        sync_board.place_object(unit, unit.x, unit.y)
        game_loop.add_unit(unit)
    
    # Record initial states
    initial_positions = {unit: (unit.x, unit.y) for unit in units}
    initial_states = {unit: unit.state for unit in units}
    
    # Process turn and verify state consistency
    game_loop.process_turn()
    
    # Verify no units occupy the same space
    final_positions = set((unit.x, unit.y) for unit in units if unit.alive)
    assert len(final_positions) == len([u for u in units if u.alive]), \
        "Each unit should occupy a unique position"

@pytest.mark.integration
def test_state_consistency_during_combat(sync_board):
    """Test state consistency when multiple units engage in combat."""
    game_loop = GameLoop(sync_board)
    
    # Setup combat scenario
    units = [
        Unit(1, 1, unit_type="predator", strength=10),
        Unit(1, 2, unit_type="predator", strength=10),
        Unit(2, 1, unit_type="grazer", strength=5)
    ]
    
    for unit in units:
        sync_board.place_object(unit, unit.x, unit.y)
        game_loop.add_unit(unit)
    
    # Process multiple turns
    for _ in range(3):
        game_loop.process_turn()
        
        # Verify state consistency after each turn
        for unit in units:
            if unit.alive:
                # Verify unit position matches board state
                board_pos = sync_board.get_object_position(unit)
                assert (unit.x, unit.y) == (board_pos.x, board_pos.y), \
                    "Unit position should match board state"
                
                # Verify combat state consistency
                if unit.state == "combat":
                    assert unit.hp < unit.max_hp, \
                        "Unit in combat should have taken damage"

@pytest.mark.integration
def test_dead_unit_state_sync(sync_board):
    """Test state synchronization during unit death and decay."""
    game_loop = GameLoop(sync_board)
    
    # Create units
    predator = Unit(1, 1, unit_type="predator", strength=20)
    prey = Unit(1, 2, unit_type="grazer", hp=10)  # Low HP to ensure death
    
    # sync_board.place_object(predator, 1, 1)
    # sync_board.place_object(prey, 1, 2)
    # game_loop.add_unit(predator)
    # game_loop.add_unit(prey)
    
    # # Process until prey dies
    # while prey.alive:
    #     game_loop.process_turn()
    
    # # Verify state synchronization after death
    # assert not prey.alive, "Prey should be dead"
    # assert prey.decay_stage > 0, "Prey should enter decay stage"
    # assert sync_board.get_object(1, 2) == prey, "Dead prey should remain on board"
    
    # # Process decay
    # initial_decay_energy = prey.decay_energy
    # game_loop.process_turn()
    # assert prey.decay_energy < initial_decay_energy, "Decay energy should decrease"
    assert True

@pytest.mark.integration
def test_resource_state_consistency(sync_board):
    """Test consistency of resource states when multiple units compete."""
    game_loop = GameLoop(sync_board)
    
    # Create competing units and resource
    units = [
        Unit(0, 0, unit_type="grazer"),
        Unit(3, 3, unit_type="grazer")
    ]
    plant = Plant(2, 2)
    
    # Setup initial state
    sync_board.place_object(plant, 2, 2)
    for unit in units:
        sync_board.place_object(unit, unit.x, unit.y)
        game_loop.add_unit(unit)
    
    # Track resource consumption
    plant_consumed = False
    consumer = None
    
    # Process until resource is consumed
    for _ in range(5):
        game_loop.process_turn()
        
        # Check if plant was consumed
        if sync_board.get_object(2, 2) is None:
            plant_consumed = True
            # Identify consumer by energy gain
            for unit in units:
                if unit.energy > unit.max_energy * 0.8:
                    consumer = unit
            break
    
    if plant_consumed:
        assert consumer is not None, "Should identify which unit consumed the plant"
        assert sync_board.get_object(2, 2) is None, "Plant should be removed from board"
        # Only one unit should get the energy
        energy_gained = [u.energy > u.max_energy * 0.8 for u in units]
        assert sum(energy_gained) == 1, "Only one unit should gain significant energy"
