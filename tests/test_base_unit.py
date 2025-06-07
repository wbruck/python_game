import pytest
from game.units.base_unit import Unit, UNIT_TEMPLATES
from game.plants.base_plant import Plant # Import Plant
from game.board import Board, Position # Import real Board and Position

# Mock classes for testing vision
class MockVisibleObject:
    def __init__(self, x, y, name="visible_obj"):
        self.x = x
        self.y = y
        self.name = name
        self.blocks_vision = False # Default, doesn't block vision

class MockObstacle:
    def __init__(self, x, y, blocks_vision=True):
        self.x = x
        self.y = y
        self.blocks_vision = blocks_vision

# Re-using MockBoard from existing tests for some specific isolated tests if needed,
# but for get_potential_moves_in_vision_range, we need the real Board's methods.
class MockBoardForUnitInit: # Simplified MockBoard just for unit initialization if real board is too complex
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        # Add minimal methods required by Unit.__init__ if any
        # For example, if Unit constructor accesses board.height:
        self.board_height = height


def test_unit_initialization(config_defaults): # Added config_defaults
    """Test unit initialization with different parameters"""
    mock_board = MockBoardForUnitInit() # Use simplified mock for init
    # Test default initialization
    unit = Unit(5, 5, config=config_defaults, board=mock_board)
    assert unit.x == 5
    assert unit.y == 5
    assert unit.hp == 100
    assert unit.energy == 100
    assert unit.state == "idle"
    assert unit.alive is True

    # Test template-based initialization
    predator = Unit(0, 0, unit_type="predator", config=config_defaults, board=mock_board)
    assert predator.hp == UNIT_TEMPLATES["predator"]["hp"]
    assert predator.strength == UNIT_TEMPLATES["predator"]["strength"]

    # Test custom stats
    custom = Unit(1, 1, hp=200, energy=150, strength=20, config=config_defaults, board=mock_board)
    assert custom.hp == 200
    assert custom.energy == 150
    assert custom.strength == 20

# --- Tests for get_potential_moves_in_vision_range ---

def test_basic_vision_and_moves(config_defaults):
    board = Board(width=10, height=10)
    unit = Unit(x=5, y=5, speed=1, vision=3, config=config_defaults, board=board)
    board.place_object(unit, unit.x, unit.y) # Place unit on board

    moves, visible_objs = unit.get_potential_moves_in_vision_range(board)

    # Expected moves (cardinal, speed 1)
    expected_moves = [(5, 4), (5, 6), (4, 5), (6, 5)] # Up, Down, Left, Right
    assert len(moves) == 4
    for move in expected_moves:
        assert move in moves

    assert len(visible_objs) == 0, "Should see no other objects on an empty board"

def test_board_edge_cases(config_defaults):
    board = Board(width=5, height=5)

    # Corner case (0,0)
    unit_corner = Unit(x=0, y=0, speed=1, vision=3, config=config_defaults, board=board)
    board.place_object(unit_corner, unit_corner.x, unit_corner.y)
    moves_corner, _ = unit_corner.get_potential_moves_in_vision_range(board)

    expected_corner_moves = [(0, 1), (1, 0)] # Down, Right
    assert len(moves_corner) == 2
    for move in expected_corner_moves:
        assert move in moves_corner

    # Edge case (2,0)
    # Need to clear the board or use a new one for the next unit
    board = Board(width=5, height=5)
    unit_edge = Unit(x=2, y=0, speed=1, vision=3, config=config_defaults, board=board)
    board.place_object(unit_edge, unit_edge.x, unit_edge.y)
    moves_edge, _ = unit_edge.get_potential_moves_in_vision_range(board)

    expected_edge_moves = [(2, 1), (1, 0), (3, 0)] # Down, Left, Right
    assert len(moves_edge) == 3
    for move in expected_edge_moves:
        assert move in moves_edge

def test_vision_range_detection(config_defaults):
    board = Board(width=10, height=10)
    unit = Unit(x=5, y=5, speed=1, vision=2, config=config_defaults, board=board) # Vision 2
    board.place_object(unit, unit.x, unit.y)

    obj_outside_vision = MockVisibleObject(x=5, y=8) # Distance 3 (5,5 -> 5,8)
    board.place_object(obj_outside_vision, obj_outside_vision.x, obj_outside_vision.y)

    _, visible_objs_initial = unit.get_potential_moves_in_vision_range(board)
    assert len(visible_objs_initial) == 0, "Object outside initial vision range should not be visible"

    # Increase vision
    unit.vision = 3
    _, visible_objs_increased_vision = unit.get_potential_moves_in_vision_range(board)
    assert len(visible_objs_increased_vision) == 1, "Object should be visible after increasing vision"
    assert visible_objs_increased_vision[0][0] == obj_outside_vision
    assert visible_objs_increased_vision[0][1] == obj_outside_vision.x
    assert visible_objs_increased_vision[0][2] == obj_outside_vision.y

def test_object_detection_and_self_exclusion(config_defaults):
    board = Board(width=10, height=10)
    unit = Unit(x=5, y=5, speed=1, vision=3, config=config_defaults, board=board)
    board.place_object(unit, unit.x, unit.y)

    other_unit = MockVisibleObject(x=5, y=6, name="other_unit") # Distance 1
    board.place_object(other_unit, other_unit.x, other_unit.y)

    obstacle = MockObstacle(x=4, y=5, blocks_vision=False) # Distance 1, does not block vision
    board.place_object(obstacle, obstacle.x, obstacle.y)

    _, visible_objs = unit.get_potential_moves_in_vision_range(board)

    assert len(visible_objs) == 2, "Should see two objects"

    found_other_unit = False
    found_obstacle = False
    for obj, x, y in visible_objs:
        if obj == other_unit and x == other_unit.x and y == other_unit.y:
            found_other_unit = True
        elif obj == obstacle and x == obstacle.x and y == obstacle.y:
            found_obstacle = True
        elif obj == unit:
            pytest.fail("Unit should not see itself in visible_objects")

    assert found_other_unit, "The other_unit was not found in visible_objects"
    assert found_obstacle, "The obstacle was not found in visible_objects"


def test_obstacles_blocking_movement(config_defaults):
    board = Board(width=5, height=5)
    unit = Unit(x=2, y=2, speed=1, vision=3, config=config_defaults, board=board)
    board.place_object(unit, unit.x, unit.y)

    # Place obstacle directly to the right
    obstacle = MockObstacle(x=3, y=2, blocks_vision=False)
    board.place_object(obstacle, obstacle.x, obstacle.y)

    moves, _ = unit.get_potential_moves_in_vision_range(board)

    # Expected moves: Up, Down, Left. Right (3,2) should be blocked.
    expected_moves = [(2, 1), (2, 3), (1, 2)]
    assert len(moves) == 3
    for move in expected_moves:
        assert move in moves
    assert (3,2) not in moves, "Move to obstacle location should not be possible"

def test_obstacles_blocking_vision(config_defaults):
    board = Board(width=10, height=10)
    unit = Unit(x=5, y=5, speed=1, vision=5, config=config_defaults, board=board)
    board.place_object(unit, unit.x, unit.y)

    # Obstacle between unit and target_obj
    # Unit at (5,5), Obstacle at (5,6), Target at (5,7)
    vision_blocking_obstacle = MockObstacle(x=5, y=6, blocks_vision=True)
    board.place_object(vision_blocking_obstacle, vision_blocking_obstacle.x, vision_blocking_obstacle.y)

    target_obj = MockVisibleObject(x=5, y=7, name="hidden_target")
    board.place_object(target_obj, target_obj.x, target_obj.y)

    # Another object that should be visible
    visible_obj_clear_path = MockVisibleObject(x=4,y=5, name="clear_path_obj")
    board.place_object(visible_obj_clear_path, visible_obj_clear_path.x, visible_obj_clear_path.y)


    _, visible_objs = unit.get_potential_moves_in_vision_range(board)

    assert len(visible_objs) == 2, "Should see the obstacle and the clear_path_obj, but not the hidden target"

    found_hidden_target = False
    found_blocking_obstacle = False
    found_clear_path_obj = False

    for obj, x, y in visible_objs:
        if obj == target_obj:
            found_hidden_target = True
        if obj == vision_blocking_obstacle:
            found_blocking_obstacle = True
        if obj == visible_obj_clear_path:
            found_clear_path_obj = True

    assert not found_hidden_target, "Target object behind vision-blocking obstacle should not be visible"
    assert found_blocking_obstacle, "The vision-blocking obstacle itself should be visible"
    assert found_clear_path_obj, "Object with a clear path should be visible"

# --- End of tests for get_potential_moves_in_vision_range ---

# Keep existing tests below, ensure they use config_defaults and appropriate board mock/instance

class MockBoardForOldTests: # A more complete MockBoard for old tests if they rely on specific mock behaviors
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.objects = {}
        self.movement_vectors = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Cardinal
        
    def is_valid_position(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
        
    def get_object(self, x, y):
        return self.objects.get((x, y))
        
    def place_object(self, obj, x, y): # Added for consistency
        self.objects[(x,y)] = obj
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            obj.x = x
            obj.y = y

    def move_object(self, old_x, old_y, new_x, new_y):
        if not self.is_valid_position(new_x, new_y): return False
        if self.get_object(new_x, new_y) is not None: return False # Cannot move to occupied cell

        obj = self.objects.pop((old_x, old_y), None)
        if obj:
            self.objects[(new_x, new_y)] = obj
            return True
        return False

    def remove_object(self, x, y):
        if (x,y) in self.objects:
            del self.objects[(x,y)]
            return True
        return False

    def get_available_moves(self, x, y):
        # Mocked get_available_moves for old tests if they don't need the real Board's logic
        moves = []
        for dx, dy in self.movement_vectors:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny) and self.get_object(nx, ny) is None:
                moves.append(Position(nx, ny))
        return moves


class MockPlant(Plant):
    def __init__(self, energy_value=50, position: Position = Position(0,0), config=None): # Added config
        super().__init__(
            position=position,
            base_energy=float(energy_value),
            growth_rate=1.0,
            regrowth_time=10.0,
            config=config # Pass config to Plant
        )
        self.state.energy_content = float(energy_value)


def test_movement_mechanics(config_defaults): # Added config_defaults
    """Test movement mechanics and energy consumption"""
    # Using MockBoardForOldTests as the original test was designed with a simpler mock
    board = MockBoardForOldTests()
    unit = Unit(5, 5, speed=2, energy=100, config=config_defaults, board=board)
    board.place_object(unit, 5,5) # Place unit on mock board
    initial_energy = unit.energy
    
    # Test valid cardinal movement (dx=1, dy=0 means speed=1, within unit speed 2)
    # The refactored move method no longer checks speed, relies on caller.
    # So we test a single step move here.
    assert unit.move(1, 0, board) is True, "Should move right"
    assert unit.x == 6 and unit.y == 5, "Position should update"
    assert unit.energy < initial_energy, "Movement should consume energy"
    
    # Reset position and energy
    board.move_object(unit.x, unit.y, 5, 5) # Move back
    unit.x, unit.y = 5, 5
    unit.energy = initial_energy
    
    # Test diagonal movement (dx=1, dy=1 means speed=2, within unit speed 2)
    # Again, testing single step for the move method.
    assert unit.move(1, 1, board) is True, "Should move diagonally"
    assert unit.x == 6 and unit.y == 6, "Position should update"
    assert unit.energy < initial_energy, "Movement should consume energy"
    
    # Reset position and energy
    board.move_object(unit.x, unit.y, 5, 5) # Move back
    unit.x, unit.y = 5, 5
    unit.energy = initial_energy
    
    # Test invalid movement (dx=2, dy=1 means speed=3, unit speed is 2)
    # The 'move' method itself doesn't check speed anymore. This check is now up to the AI using get_potential_moves.
    # So, this specific part of the original test is no longer directly applicable to 'move'.
    # We can test that move still prevents moving to invalid/occupied spots.
    
    # Test movement with low energy
    unit.energy = unit.energy_cost_move - 1 # Ensure energy is less than one move cost
    assert unit.move(1, 0, board) is False, "Should not move with insufficient energy"
    assert unit.x == 5 and unit.y == 5, "Position should not change"
    
    # Test movement restrictions in different states
    unit.energy = initial_energy
    for state in ["dead", "decaying", "resting", "feeding"]:
        unit.state = state
        assert unit.move(0, 1, board) is False, f"Should not move in {state} state"
        assert unit.x == 5 and unit.y == 5, f"Position should not change in {state} state"
    
    # Test movement at board boundaries
    unit.state = "idle"
    unit.x, unit.y = 0, 0
    board.place_object(unit, 0,0) # Update position on board
    assert unit.move(-1, 0, board) is False, "Should not move outside board"
    assert unit.x == 0 and unit.y == 0, "Position should not change"

def test_combat_system(config_defaults): # Added config_defaults
    """Test combat mechanics and state effects"""
    mock_board = MockBoardForUnitInit()
    attacker = Unit(0, 0, strength=10, energy=100, config=config_defaults, board=mock_board)
    defender = Unit(1, 0, hp=50, config=config_defaults, board=mock_board)
    
    initial_hp = defender.hp
    initial_energy = attacker.energy
    
    damage = attacker.attack(defender)
    assert damage > 0
    assert defender.hp < initial_hp
    assert attacker.energy < initial_energy
    
    attacker.state = "hunting"
    attacker.energy = initial_energy
    hunting_damage = attacker.attack(defender)
    assert hunting_damage > damage
    
    attacker.energy = attacker.energy_cost_attack - 1
    no_energy_damage = attacker.attack(defender)
    assert no_energy_damage == 0
    
    defender.hp = 5
    attacker.energy = 100
    attacker.attack(defender)
    assert defender.alive is False
    assert defender.state == "dead"
    assert defender.decay_energy > 0
    
    damage_to_dead = attacker.attack(defender)
    assert damage_to_dead == 0

def test_feeding_mechanics(config_defaults): # Added config_defaults
    """Test feeding behavior and energy gains"""
    mock_board = MockBoardForUnitInit()
    unit = Unit(0, 0, energy=100, config=config_defaults, board=mock_board)
    unit.energy = 50
    initial_energy = unit.energy
    
    plant = MockPlant(energy_value=30, position=Position(1,1), config=config_defaults)
    assert unit.eat(plant) is True
    new_energy = unit.energy
    assert new_energy > initial_energy
    assert new_energy <= unit.max_energy
    assert unit.state == "feeding"
    
    unit.energy = unit.max_energy
    high_energy_plant = MockPlant(energy_value=50, position=Position(1,2), config=config_defaults)
    assert unit.eat(high_energy_plant) is False
    assert unit.energy == unit.max_energy
    
    unit.energy = unit.max_energy - 10
    medium_plant = MockPlant(energy_value=20, position=Position(1,3), config=config_defaults)
    assert unit.eat(medium_plant) is True
    assert unit.energy == unit.max_energy
    
    dead_unit = Unit(0, 1, energy=100, config=config_defaults, board=mock_board)
    dead_unit.alive = False
    dead_unit.state = "dead"
    dead_unit.decay_stage = 1
    dead_unit.decay_energy = 60
    
    unit.energy = 50
    initial_energy_dead_eat = unit.energy
    assert unit.eat(dead_unit) is True
    assert unit.energy > initial_energy_dead_eat
    assert unit.energy <= unit.max_energy
    # This assertion depends on the absorption rate logic in Unit.eat()
    # For now, assuming some energy is transferred. If specific values are needed, Unit.eat() logic must be matched.
    assert dead_unit.decay_energy < 60
    
    living_unit = Unit(0, 2, config=config_defaults, board=mock_board)
    assert unit.eat(living_unit) is False
    assert unit.eat(None) is False
    
    unit.alive = False
    unit.state = "dead"
    assert unit.eat(plant) is False
    assert unit.state == "dead"

    unit.state = "decaying"
    assert unit.eat(plant) is False
    assert unit.state == "decaying"
    
    unit.alive = True
    unit.state = "idle"
    unit.energy = 50

    dead_unit_2 = Unit(1, 0, energy=80, config=config_defaults, board=mock_board)
    dead_unit_2.alive = False
    dead_unit_2.state = "dead"
    dead_unit_2.decay_energy = 40
    
    assert unit.eat(dead_unit_2) is True
    assert unit.energy > 50
    assert dead_unit_2.decay_energy < 40

def test_state_machine(config_defaults): # Added config_defaults
    """Test state transitions and effects"""
    # Using real Board as Unit.update might interact with board state more deeply in future
    board = Board(width=10, height=10)
    unit = Unit(0, 0, energy=100, hp=100, config=config_defaults, board=board)
    board.place_object(unit, 0,0)

    assert unit.state == "idle"
    assert unit.state_duration == 0
    
    unit.energy = int(unit.max_energy * 0.15)
    unit.update(board)
    assert unit.state == "resting"
    
    initial_energy_resting = unit.energy
    unit.update(board)
    assert unit.energy > initial_energy_resting
    assert unit.state == "resting"
    
    unit.energy = int(unit.max_energy * (unit.resting_exit_energy_ratio + 0.1)) # Ensure it's above threshold
    unit.update(board)
    assert unit.state == "wandering"
    
    unit.hp = int(unit.max_hp * 0.25)
    unit.update(board)
    assert unit.state == "fleeing"
    assert unit.speed > unit.base_speed
    
    unit.hp = unit.max_hp
    unit.energy = unit.max_energy
    unit.state = "hunting"
    unit.state_duration = unit.config.get("units", "state_duration_limits.default") + 1 # Exceed default limit
    unit.update(board)
    assert unit.state == "wandering"
    assert unit.state_duration == 0
    
    unit.state = "hunting"
    unit.update(board)
    assert unit.strength > unit.base_strength
    assert unit.vision > unit.base_vision
    
    unit.hp = 0
    unit.update(board) # This call makes the unit dead
    assert unit.state == "dead"
    assert not unit.alive
    assert unit.decay_stage == 1 # First decay update happens when unit dies

def test_decay_mechanics(config_defaults): # Added config_defaults
    """Test decay process for dead units"""
    board = Board(width=10, height=10) # Use real board
    unit = Unit(0, 0, energy=100, config=config_defaults, board=board)
    board.place_object(unit,0,0) # Place unit on board
    initial_decay_energy = unit.energy # This is what becomes decay_energy
    
    unit.hp = 0
    unit.update(board) # Unit dies, state becomes "dead", decay_stage becomes 1, decay_energy is set and reduced once
    assert unit.state == "dead"
    assert not unit.alive
    assert unit.decay_stage == 1

    decay_rate = unit.config.get("units", "decay_rate")
    expected_energy = initial_decay_energy * (1 - decay_rate)
    assert abs(unit.decay_energy - expected_energy) < 0.01

    for i in range(1, 4):
        current_decay_stage = unit.decay_stage
        unit.update(board)
        expected_energy *= (1 - decay_rate)
        
        assert unit.state == "dead" or unit.state == "decaying" # State might change to decaying
        if unit.state == "dead": # Decay stage only increments if still "dead" before this update might flip it to "decaying"
             assert unit.decay_stage == current_decay_stage + 1
        assert abs(unit.decay_energy - expected_energy) < 0.01
        if expected_energy > 1: # only assert if we expect positive energy
            assert unit.decay_energy > 0

    # Continue updates until fully decayed or removed
    # Max decay_stage before removal is typically around 10-11 (5 for dead, 5 for decaying + 1 for final update)
    # The unit is removed from board when decay_stage >= 11
    max_updates_for_removal = 15
    removed = False
    for _ in range(max_updates_for_removal):
        unit.update(board)
        if board.get_object(unit.x, unit.y) != unit : # Check if removed
            removed = True
            break
    
    assert removed, "Unit should eventually be removed from the board after full decay"

# Ensure conftest.py has a config_defaults fixture like:
# @pytest.fixture
# def config_defaults():
#     from game.config import Config
#     return Config() # Or a mock/simplified config
#
# If Config() is too complex or has file dependencies for tests,
# a simpler mock config dictionary might be needed.
# For now, assuming Config() can be instantiated.

# If the `Unit` constructor or other methods called in tests require more from `config_defaults`
# than an empty `Config` object provides, those values would need to be mocked or set up
# in the `config_defaults` fixture. Example:
# @pytest.fixture
# def config_defaults():
#     class MockConfig:
#         def get(self, section, key, default=None):
#             if section == "units":
#                 if key == "energy_consumption.move": return 1
#                 if key == "energy_consumption.attack": return 2
#                 # ... other necessary keys
#                 if key == "state_duration_limits.default": return 10
#                 if key == "decay_rate": return 0.1
#             return default
#     return MockConfig()

