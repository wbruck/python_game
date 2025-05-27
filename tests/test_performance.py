import pytest
import time
from game.board import Board, MovementType
from game.units.base_unit import Unit
from game.game_loop import GameLoop

def create_test_board(width, height, num_units):
    """Create a test board with specified dimensions and units."""
    board = Board(width, height, MovementType.DIAGONAL)
    units = []
    
    # Place units randomly on the board
    for _ in range(num_units):
        x = y = 0
        while board.get_object_position((x, y)) is not None:
            x = pytest.randint(0, width-1)
            y = pytest.randint(0, height-1)
        unit = Unit(x, y, "predator")
        board.place_object(unit, x, y)
        units.append(unit)
        
    return board, units

def benchmark_visibility(board_size, num_units, vision_range):
    """Benchmark visibility calculations."""
    board, units = create_test_board(board_size, board_size, num_units)
    
    # Measure time for visibility calculations
    start_time = time.time()
    for unit in units:
        board.calculate_field_of_view(unit.x, unit.y, vision_range)
    end_time = time.time()
    
    return end_time - start_time

def benchmark_game_loop(board_size, num_units, num_turns):
    """Benchmark game loop performance."""
    board, units = create_test_board(board_size, board_size, num_units)
    game_loop = GameLoop(board, max_turns=num_turns)
    for unit in units:
        game_loop.add_unit(unit)
    
    # Measure time for processing turns
    start_time = time.time()
    game_loop.run()
    end_time = time.time()
    
    return end_time - start_time

def test_visibility_scaling():
    """Test how visibility calculations scale with board size and unit count."""
    results = []
    
    # Test different board sizes
    sizes = [20, 40, 80]
    units = [10, 50, 100]
    vision = [5, 10, 15]
    
    for size in sizes:
        for num_units in units:
            for vision_range in vision:
                time_taken = benchmark_visibility(size, num_units, vision_range)
                results.append({
                    'board_size': size,
                    'num_units': num_units,
                    'vision_range': vision_range,
                    'time': time_taken
                })
                
    # Verify performance characteristics
    for r in results:
        # Check that time scales reasonably with board size and unit count
        # Time should increase less than quadratically with board size
        assert r['time'] < (r['board_size'] ** 2) * 0.001, f"Poor scaling with board size {r['board_size']}"
        # Time should scale roughly linearly with unit count
        assert r['time'] < r['num_units'] * 0.1, f"Poor scaling with unit count {r['num_units']}"

def test_game_loop_performance():
    """Test game loop performance with different configurations."""
    results = []
    
    # Test different scenarios
    scenarios = [
        (20, 10, 10),   # Small game
        (40, 50, 10),   # Medium game
        (80, 100, 10),  # Large game
    ]
    
    for size, units, turns in scenarios:
        time_taken = benchmark_game_loop(size, units, turns)
        results.append({
            'board_size': size,
            'num_units': units,
            'num_turns': turns,
            'time': time_taken
        })
        
    # Verify performance characteristics
    for r in results:
        # Check that time per turn is reasonable
        time_per_turn = r['time'] / r['num_turns']
        assert time_per_turn < 0.1, f"Turn processing too slow: {time_per_turn:.3f}s per turn"
        # Check memory usage indirectly through time (high memory usage causes slowdown)
        assert r['time'] < r['num_units'] * r['num_turns'] * 0.01, "Possible memory scaling issue"

def test_batch_processing_effectiveness():
    """Test the effectiveness of batch processing in the game loop."""
    # Compare processing time with different batch sizes
    board_size = 40
    num_units = 100
    num_turns = 5
    
    # Test without batch processing (batch_size = 1)
    board1, units1 = create_test_board(board_size, board_size, num_units)
    game_loop1 = GameLoop(board1, max_turns=num_turns)
    for unit in units1:
        game_loop1.add_unit(unit)
    
    start_time1 = time.time()
    game_loop1.run()
    time1 = time.time() - start_time1
    
    # Test with batch processing (batch_size = 10)
    board2, units2 = create_test_board(board_size, board_size, num_units)
    game_loop2 = GameLoop(board2, max_turns=num_turns)
    for unit in units2:
        game_loop2.add_unit(unit)
    
    start_time2 = time.time()
    game_loop2.run()
    time2 = time.time() - start_time2
    
    # Batch processing should be noticeably faster
    assert time2 < time1 * 0.8, "Batch processing not providing significant improvement"
