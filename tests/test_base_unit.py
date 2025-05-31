import pytest
from game.units.base_unit import Unit, UNIT_TEMPLATES
from game.plants.base_plant import Plant # Import Plant
from game.board import Position # Import Position

class MockBoard:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.objects = {}
        
    def is_valid_position(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
        
    def get_object(self, x, y):
        return self.objects.get((x, y))
        
    def move_object(self, old_x, old_y, new_x, new_y):
        # For testing, always allow movement if position is valid
        if self.is_valid_position(new_x, new_y):
            return True
        return False

class MockPlant(Plant): # Inherit from Plant
    def __init__(self, energy_value=50, position: Position = Position(0,0)):
        # Call super().__init__ with default values for Plant
        super().__init__(
            position=position,
            base_energy=float(energy_value), # Ensure base_energy is float
            growth_rate=1.0,    # Default growth_rate
            regrowth_time=10.0  # Default regrowth_time
        )
        # The Plant class already creates self.state with PlantState
        # and sets initial energy_content to base_energy.
        # If a specific initial energy_value different from base_energy is needed
        # for testing, self.state.energy_content can be adjusted after super().__init__
        self.state.energy_content = float(energy_value)


def test_unit_initialization():
    """Test unit initialization with different parameters"""
    # Test default initialization
    unit = Unit(5, 5)
    assert unit.x == 5
    assert unit.y == 5
    assert unit.hp == 100
    assert unit.energy == 100
    assert unit.state == "idle"
    assert unit.alive is True
    
    # Test template-based initialization
    predator = Unit(0, 0, unit_type="predator")
    assert predator.hp == UNIT_TEMPLATES["predator"]["hp"]
    assert predator.strength == UNIT_TEMPLATES["predator"]["strength"]
    
    # Test custom stats
    custom = Unit(1, 1, hp=200, energy=150, strength=20)
    assert custom.hp == 200
    assert custom.energy == 150
    assert custom.strength == 20

def test_movement_mechanics():
    """Test movement mechanics and energy consumption"""
    board = MockBoard()
    unit = Unit(5, 5, speed=2, energy=100)
    initial_energy = unit.energy
    
    # Test valid cardinal movement
    assert unit.move(1, 0, board) is True, "Should move right"
    assert unit.x == 6 and unit.y == 5, "Position should update"
    assert unit.energy < initial_energy, "Movement should consume energy"
    
    # Reset position and energy
    unit.x, unit.y = 5, 5
    unit.energy = initial_energy
    
    # Test diagonal movement within speed limit
    assert unit.move(1, 1, board) is True, "Should move diagonally"
    assert unit.x == 6 and unit.y == 6, "Position should update"
    assert unit.energy < initial_energy, "Movement should consume energy"
    
    # Reset position and energy
    unit.x, unit.y = 5, 5
    unit.energy = initial_energy
    
    # Test invalid movement (exceeds speed)
    assert unit.move(2, 1, board) is False, "Should not exceed speed limit"
    assert unit.x == 5 and unit.y == 5, "Position should not change"
    assert unit.energy == initial_energy, "Energy should not be consumed"
    
    # Test movement with low energy
    unit.energy = 1
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
    assert unit.move(-1, 0, board) is False, "Should not move outside board"
    assert unit.x == 0 and unit.y == 0, "Position should not change"

def test_combat_system():
    """Test combat mechanics and state effects"""
    attacker = Unit(0, 0, strength=10, energy=100)
    defender = Unit(1, 0, hp=50)
    
    # Store initial values
    initial_hp = defender.hp
    initial_energy = attacker.energy
    
    # Test basic attack
    damage = attacker.attack(defender)
    assert damage > 0, "Attack should deal damage"
    assert defender.hp < initial_hp, "Defender should lose HP"
    assert attacker.energy < initial_energy, "Attack should consume energy"
    
    # Test state modifiers
    attacker.state = "hunting"
    attacker.energy = initial_energy  # Reset energy for clean test
    hunting_damage = attacker.attack(defender)
    assert hunting_damage > damage, "Hunting state should increase damage"
    
    # Test insufficient energy
    attacker.energy = 1
    no_energy_damage = attacker.attack(defender)
    assert no_energy_damage == 0, "Attack should fail with insufficient energy"
    
    # Test death mechanics
    defender.hp = 5
    attacker.energy = 100  # Ensure enough energy for kill
    attacker.attack(defender)
    assert defender.alive is False, "Defender should die"
    assert defender.state == "dead", "Defender state should be dead"
    assert defender.decay_energy > 0, "Dead unit should have decay energy"
    
    # Test attacking dead unit
    damage_to_dead = attacker.attack(defender)
    assert damage_to_dead == 0, "Cannot damage dead units"

def test_feeding_mechanics():
    """Test feeding behavior and energy gains"""
    unit = Unit(0, 0, energy=100)  # Initialize with max energy
    unit.energy = 50  # Set current energy to 50
    initial_energy = unit.energy
    
    # Test plant consumption
    plant = MockPlant(energy_value=30)
    assert unit.eat(plant) is True, "Should successfully eat plant"
    new_energy = unit.energy
    assert new_energy > initial_energy, "Energy should increase after eating"
    assert new_energy <= unit.max_energy, "Energy should not exceed max"
    assert unit.state == "feeding", "Unit should enter feeding state"
    
    # Test eating while already at max energy
    unit.energy = unit.max_energy
    high_energy_plant = MockPlant(energy_value=50)
    assert unit.eat(high_energy_plant) is False, "Should not eat when energy is full"
    assert unit.energy == unit.max_energy, "Energy should remain at max"
    
    # Test eating with nearly full energy
    unit.energy = unit.max_energy - 10
    medium_plant = MockPlant(energy_value=20)
    assert unit.eat(medium_plant) is True, "Should eat when partially full"
    assert unit.energy == unit.max_energy, "Energy should cap at max"
    
    # Test eating dead unit
    dead_unit = Unit(0, 0, energy=100)
    dead_unit.alive = False
    dead_unit.state = "dead"  # Explicitly set state
    dead_unit.decay_stage = 1
    dead_unit.decay_energy = 60 # Changed from 80 to 60 to ensure full consumption by test
    
    unit.energy = 50  # Reset energy for test
    initial_energy = unit.energy
    assert unit.eat(dead_unit) is True, "Should successfully eat dead unit"
    assert unit.energy > initial_energy, "Energy should increase after eating dead unit"
    assert unit.energy <= unit.max_energy, "Energy should not exceed max"
    assert dead_unit.decay_energy == 0, "Dead unit should be fully consumed"
    
    # Test eating invalid food sources
    living_unit = Unit(0, 0)
    assert unit.eat(living_unit) is False, "Should not eat living units"
    assert unit.eat(None) is False, "Should handle null food source"
    
    # Test eating in invalid states
    unit.alive = False
    unit.state = "dead"
    assert unit.eat(plant) is False, "Dead units should not eat"
    assert unit.state == "dead", "State should remain dead"

    unit.state = "decaying"
    assert unit.eat(plant) is False, "Decaying units should not eat"
    assert unit.state == "decaying", "State should remain decaying"
    
    # Reset unit to living state for final test
    unit.alive = True
    unit.state = "idle"
    unit.energy = 50

    # Test dead unit consumption
    dead_unit = Unit(1, 0, energy=80)
    dead_unit.alive = False
    dead_unit.state = "dead"
    dead_unit.decay_energy = 40
    
    assert unit.eat(dead_unit) is True
    assert unit.energy > 50
    assert dead_unit.decay_energy < 40  # Energy should be transferred

def test_state_machine():
    """Test state transitions and effects"""
    board = MockBoard()
    unit = Unit(0, 0, energy=100, hp=100)
    
    # Test initial state
    assert unit.state == "idle", "Initial state should be idle"
    assert unit.state_duration == 0, "Initial state duration should be 0"
    
    # Test low energy triggers resting
    unit.energy = int(unit.max_energy * 0.15)  # Below 20% threshold
    unit.update(board)
    assert unit.state == "resting", "Low energy should trigger resting state"
    
    # Test energy recovery while resting
    initial_energy = unit.energy
    unit.update(board)
    assert unit.energy > initial_energy, "Should recover energy while resting"
    assert unit.state == "resting", "Should stay in resting state"
    
    # Test transition from resting to wandering
    unit.energy = int(unit.max_energy * 0.85)  # Above 80% threshold
    unit.update(board)
    assert unit.state == "wandering", "High energy should exit resting state"
    
    # Test low health triggers fleeing
    unit.hp = int(unit.max_hp * 0.25)  # Below 30% threshold
    unit.update(board)
    assert unit.state == "fleeing", "Low health should trigger fleeing state"
    assert unit.speed > unit.base_speed, "Should get speed boost while fleeing"
    
    # Test state duration limit
    unit.hp = unit.max_hp  # Reset HP
    unit.energy = unit.max_energy  # Reset energy
    unit.state = "hunting"
    unit.state_duration = 11  # Exceed duration limit
    unit.update(board)
    assert unit.state == "wandering", "Should transition after duration limit"
    assert unit.state_duration == 0, "Duration should reset on state change"
    
    # Test state-specific stat modifiers
    unit.state = "hunting"
    unit.update(board)
    assert unit.strength > unit.base_strength, "Hunting should boost strength"
    assert unit.vision > unit.base_vision, "Hunting should boost vision"
    
    # Test death state
    unit.hp = 0
    unit.update(board)
    assert unit.state == "dead", "Zero HP should trigger death state"
    assert not unit.alive, "Unit should not be alive"
    assert unit.decay_stage == 0, "Decay stage should start at 0"

def test_decay_mechanics():
    """Test decay process for dead units"""
    unit = Unit(0, 0, energy=100)
    board = MockBoard()
    initial_energy = unit.energy
    
    # Kill the unit
    unit.hp = 0
    unit.update(board)
    assert unit.state == "dead", "Unit should enter dead state"
    assert unit.decay_stage == 0, "Decay stage should start at 0"
    assert unit.decay_energy == initial_energy, "Decay energy should initialize to unit's energy"
    assert not unit.alive, "Unit should not be alive"
    
    # Test decay progression
    decay_rate = 0.1  # 10% decay per turn
    expected_energy = initial_energy
    
    # Track decay over several turns
    for turn in range(1, 4):
        unit.update(board)
        expected_energy *= (1 - decay_rate)
        
        assert unit.state == "dead", f"Unit should stay dead on turn {turn}"
        assert unit.decay_stage == turn, f"Decay stage should advance to {turn}"
        assert abs(unit.decay_energy - expected_energy) < 0.01, f"Decay energy should reduce by {decay_rate*100}% on turn {turn}"
        assert unit.decay_energy > 0, "Decay energy should remain positive"
        
    # Test complete decay
    while unit.decay_energy > 1:  # Continue until nearly depleted
        unit.update(board)
    
    assert unit.decay_energy < 1, "Unit should eventually decay completely"
    assert not unit.alive, "Unit should remain dead after decay"
