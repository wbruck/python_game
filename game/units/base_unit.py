"""
Base Unit module for the ecosystem simulation game.

This module implements the base Unit class with fundamental RPG-style stats and behaviors.
All other unit types will inherit from this base class.
"""
from game.board import Position
from game.plants.base_plant import Plant # Added import
from typing import Optional, Tuple
import random
import string

def generate_unit_uuid() -> str:
    """Generate a 3-character UUID for units using alphanumeric characters."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=3))

# Predefined unit templates for different roles
UNIT_TEMPLATES = {
    "predator": {
        "hp": 120,
        "energy": 80,
        "strength": 15,
        "speed": 2,
        "vision": 6
    },
    "scavenger": {
        "hp": 100,
        "energy": 110,
        "strength": 8,
        "speed": 1,
        "vision": 8
    },
    "grazer": {
        "hp": 90,
        "energy": 130,
        "strength": 5,
        "speed": 1,
        "vision": 5
    }
}

class Unit:
    """
    Base class for all units in the ecosystem simulation.
    
    This class implements the core attributes and behaviors common to all units,
    including stats, movement, and basic interactions. Units follow a state machine
    pattern for decision making and have sophisticated combat and energy mechanics.
    
    States:
    - idle: Default state, minimal energy consumption
    - hunting: Actively seeking prey, increased vision range
    - fleeing: Running from danger, increased speed but higher energy cost
    - feeding: Consuming food, vulnerable but regenerating energy
    - wandering: Exploring the environment, normal energy consumption
    - resting: Recovering energy, cannot move
    - dead: No actions possible, begins decay process
    - decaying: Gradually losing energy content that can be consumed by others
    """
    
    def __init__(self, x, y, unit_type=None, hp=100, energy=100, strength=10, speed=1, vision=5, config=None, board=None):
        """
        Initialize a new unit with the given attributes.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
            hp (int): Health points. Unit dies when this reaches 0.
            energy (int): Energy for movement and actions. Replenished by eating.
            strength (int): Determines damage in combat.
            speed (int): Affects movement range per turn.
            vision (int): How far the unit can see.
            config (Config, optional): Configuration object for accessing game settings.
            board (Board): The game board this unit belongs to.
        """
        self.config = config  # Store the config object
        self.board = board  # Store the board reference

        # Store unit type and generate unique UUID
        self.unit_type = unit_type
        self.uuid = generate_unit_uuid()

        # Load energy costs from config or use defaults
        if config:
            self.energy_cost_move = config.get("units", "energy_consumption.move")
            self.energy_cost_attack = config.get("units", "energy_consumption.attack")
            self.energy_cost_look = config.get("units", "energy_consumption.look")
            self.resting_exit_energy_ratio = config.get("units", "resting_exit_energy_ratio")
            self.max_resting_turns = config.get("units", "max_resting_turns")
            self.min_energy_force_exit_rest_ratio = config.get("units", "min_energy_force_exit_rest_ratio")

        # Provide hardcoded defaults if config is not present or a key is missing
        if not hasattr(self, 'energy_cost_move') or self.energy_cost_move is None:
            self.energy_cost_move = 1  # Default move cost
        if not hasattr(self, 'energy_cost_attack') or self.energy_cost_attack is None:
            self.energy_cost_attack = 2  # Default attack cost
        if not hasattr(self, 'energy_cost_look') or self.energy_cost_look is None:
            self.energy_cost_look = 0  # Default look cost
        if not hasattr(self, 'resting_exit_energy_ratio') or self.resting_exit_energy_ratio is None:
            self.resting_exit_energy_ratio = 0.6  # Default
        if not hasattr(self, 'max_resting_turns') or self.max_resting_turns is None:
            self.max_resting_turns = 20  # Default
        if not hasattr(self, 'min_energy_force_exit_rest_ratio') or self.min_energy_force_exit_rest_ratio is None:
            self.min_energy_force_exit_rest_ratio = 0.4  # Default

        # Use template if unit_type is provided
        if unit_type and unit_type in UNIT_TEMPLATES:
            template = UNIT_TEMPLATES[unit_type]
            hp = template["hp"]
            energy = template["energy"]
            strength = template["strength"]
            speed = template["speed"]
            vision = template["vision"]

        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.energy = energy
        self.max_energy = energy
        self.strength = strength
        self.base_strength = strength  # Store base value for state modifications
        self.speed = speed
        self.base_speed = speed  # Store base value for state modifications
        self.vision = vision
        self.base_vision = vision  # Store base value for state modifications
        
        # Core state attributes
        self.state = "idle"
        self.alive = True
        self.decay_stage = 0  # 0 means not decaying (alive)
        self.decay_energy = energy  # Energy available when consumed as food
        self.last_state = None  # For tracking state transitions
        self.state_duration = 0  # Turns spent in current state
        
        # Evolution and experience system
        self.experience = 0
        self.level = 1
        self.traits = set()  # Set of acquired traits through evolution
        self.successful_actions = {
            "combat": 0,     # Successful attacks
            "feeding": 0,    # Successfully consumed food
            "fleeing": 0,    # Successfully escaped danger
            "hunting": 0     # Successfully tracked and found prey
        }
        
        # Exploration properties
        self.exploration_direction = (1, 0)  # Start moving right
        self.exploration_distance = 0
        self.board_height = board.height if board else None
        self.quarter_height = (board.height // 4) if board else None
        
        # Set energy costs from config or use defaults
        if config:
            self.energy_cost_rest = config.get("units", "energy_consumption.rest")
            self.energy_gain_eat = config.get("units", "energy_gain.eat")
            self.hp_gain_eat = config.get("units", "hp_gain.eat")
            self.decay_rate = config.get("units", "decay_rate")
            self.decay_energy_gain = config.get("units", "decay_energy_gain")
            self.decay_hp_gain = config.get("units", "decay_hp_gain")
        
        # Set defaults if config values are not available
        if not hasattr(self, 'energy_cost_rest') or self.energy_cost_rest is None:
            self.energy_cost_rest = -5  # Negative means energy gain
        if not hasattr(self, 'energy_gain_eat') or self.energy_gain_eat is None:
            self.energy_gain_eat = 20
        if not hasattr(self, 'hp_gain_eat') or self.hp_gain_eat is None:
            self.hp_gain_eat = 10
        if not hasattr(self, 'decay_rate') or self.decay_rate is None:
            self.decay_rate = 0.1
        if not hasattr(self, 'decay_energy_gain') or self.decay_energy_gain is None:
            self.decay_energy_gain = 5
        if not hasattr(self, 'decay_hp_gain') or self.decay_hp_gain is None:
            self.decay_hp_gain = 2

    def _consume(self, target) -> int:
        """
        Consume another unit or plant for energy.
        
        Args:
            target: The unit or plant to consume
            
        Returns:
            int: Amount of energy gained from consumption
        """
        if hasattr(target, 'decay_energy'):
            energy_gained = target.decay_energy
            target.decay_energy = 0
            return energy_gained
        elif hasattr(target, 'energy'):
            energy_gained = target.energy
            target.energy = 0
            return energy_gained
        return 0

    def gain_experience(self, action_type, amount=1):
        """
        Grant experience points to the unit based on successful actions.
        
        Args:
            action_type (str): Type of action ('combat', 'feeding', 'fleeing', 'hunting')
            amount (int): Amount of experience to grant, defaults to 1
        """
        if action_type in self.successful_actions:
            self.successful_actions[action_type] += amount
            self.experience += amount
            
            # Check for level up (every 10 experience points)
            if self.experience >= self.level * 10:
                self.level_up()
    
    def level_up(self):
        """
        Level up the unit, improving stats and potentially gaining new traits.
        """
        self.level += 1
        
        # Determine specialization based on most successful actions
        max_action = max(self.successful_actions.items(), key=lambda x: x[1])[0]
        
        # Apply stat improvements based on specialization
        if max_action == "combat":
            self.strength = int(self.base_strength * (1 + 0.1 * (self.level - 1)))
            self.traits.add("battle_hardened")
        elif max_action == "feeding":
            self.max_energy = int(self.max_energy * (1 + 0.1 * (self.level - 1)))
            self.traits.add("efficient_digestion")
        elif max_action == "fleeing":
            self.speed = int(self.base_speed * (1 + 0.1 * (self.level - 1)))
            self.traits.add("swift_escape")
        elif max_action == "hunting":
            self.vision = int(self.base_vision * (1 + 0.1 * (self.level - 1)))
            self.traits.add("keen_senses")
            
        # Recover HP and energy on level up
        self.hp = self.max_hp
        self.energy = self.max_energy

    def get_potential_moves_in_vision_range(self, board):
        """
        Calculates potential moves and identifies visible objects within vision range.

        Args:
            board (Board): The game board.

        Returns:
            tuple: A tuple containing:
                - list_of_possible_moves (list): A list of (x, y) tuples representing immediately available moves.
                - visible_objects (list): A list of (object, x, y) tuples for objects within vision range.
        """
        visible_positions = board.calculate_field_of_view(self.x, self.y, self.vision)
        visible_objects = []
        for pos in visible_positions:
            obj = board.get_object(pos.x, pos.y)
            if obj is not None and obj is not self:
                visible_objects.append((obj, pos.x, pos.y))

        available_next_moves = board.get_available_moves(self.x, self.y)
        list_of_possible_moves = []
        for pos in available_next_moves:
            # Ensure moves are within unit's speed (for now, get_available_moves returns single-step moves)
            # This check can be enhanced if get_available_moves changes or AI handles multi-step pathing.
            if abs(pos.x - self.x) + abs(pos.y - self.y) <= self.speed:
                 list_of_possible_moves.append((pos.x, pos.y))

        return list_of_possible_moves, visible_objects

    def move(self, dx, dy, board):
        """
        Move the unit by the given delta if possible.
        
        Args:
            dx (int): The change in x-coordinate.
            dy (int): The change in y-coordinate.
            board (Board): The game board.
            
        Returns:
            bool: True if the move was successful, False otherwise.
        """
        if not self.alive or self.state in ["dead", "decaying", "resting", "feeding"]:
            return False

        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check if movement is possible
        # Note: The speed check (abs(dx) + abs(dy) > self.speed) has been removed
        # as per requirements, to be handled by AI using get_potential_moves_in_vision_range.
        if not board.is_valid_position(new_x, new_y) or board.get_object(new_x, new_y) is not None:
            return False
        
        # Use configured energy cost for movement
        current_move_cost = self.energy_cost_move
        if self.state == "fleeing": # Example: fleeing might have a different base cost or multiplier
            # This specific logic might be better in unit_types.py or handled by a multiplier
            # For now, we'll assume fleeing uses a modified version of the base move cost if not overridden
            # Or, it could use a specific 'energy_cost_move_flee' if loaded by subclass
            pass


        # Check for sufficient energy.
        # The cost is self.energy_cost_move (or current_move_cost if overridden by subclass state)
        # Unit should not move if energy is less than or equal to the cost,
        # meaning the move would leave it with 0 or negative energy.
        # The test `test_movement_mechanics` expects this behavior.
        
        # For non-critical states, maintain a small energy reserve (only when energy is higher)
        # This prevents units from becoming completely drained but allows movement when needed
        min_energy_reserve = 1 if (self.state not in ["fleeing", "hungry"] and self.energy > current_move_cost + 1) else 0
        if self.energy < current_move_cost + min_energy_reserve:
            return False
            
        # Check if movement is possible
        if not board.move_object(self.x, self.y, new_x, new_y):
            return False
            
        # Apply movement and energy cost
        self.x = new_x
        self.y = new_y
        self.energy -= current_move_cost
        return True
    
    def look(self, board):
        """
        Scan surroundings to find other units, plants, and obstacles.
        State affects vision range and energy consumption.
        
        Args:
            board (Board): The game board.
            
        Returns:
            list: A list of visible objects with their positions and distances.
        """
        if not self.alive:
            return []

        # Adjust vision range based on state
        vision_range = self.vision
        if self.state == "hunting":
            vision_range = int(self.vision * 1.5)
        elif self.state == "fleeing":
            vision_range = int(self.vision * 1.2)
        
        # Apply energy cost for looking if it's greater than 0
        if self.energy_cost_look > 0:
            if self.energy < self.energy_cost_look:
                return [] # Not enough energy to look
            self.energy -= self.energy_cost_look

        visible_objects = []
        for y in range(self.y - vision_range, self.y + vision_range + 1):
            for x in range(self.x - vision_range, self.x + vision_range + 1):
                if board.is_valid_position(x, y):
                    obj = board.get_object(x, y)
                    if obj is not None and obj is not self:
                        # Calculate distance for priority assessment
                        distance = abs(x - self.x) + abs(y - self.y)
                        if distance <= vision_range:
                            visible_objects.append((obj, x, y, distance))
        
        # Sort by distance for easier priority assessment
        # Convert to expected format (obj, x, y) without distance
        return [(obj, x, y) for obj, x, y, _ in sorted(visible_objects, key=lambda x: x[3])]
    
    def eat(self, food):
        """
        Consume food (plant or dead unit) to gain energy.
        
        Args:
            food: The food object to eat.
            
        Returns:
            bool: True if the unit successfully ate, False otherwise.
        """
        if not self.alive or self.state in ["dead", "decaying"]:
            return False
            
        # Validate food source
        if food is None:
            return False
            
        # Check eating unit's state first
        if not self.alive or self.state in ["dead", "decaying"]:
            return False

        # Check energy capacity first, as it's common to all food types
        if self.energy >= self.max_energy:
            return False

        energy_gained = 0

        if isinstance(food, Plant):
            if food.state.is_alive and food.state.energy_content > 0:
                needed_energy = self.max_energy - self.energy
                energy_gained = food.consume(needed_energy)
            else:
                return False # Plant is not consumable
        elif isinstance(food, Unit) and not food.alive:
            if not hasattr(food, 'decay_stage'): food.decay_stage = 0
            if not hasattr(food, 'decay_energy') or food.decay_energy is None: food.decay_energy = food.max_energy

            if food.decay_energy > 0:
                energy_available = food.decay_energy
                absorption_rate = 0.8
                can_take = self.max_energy - self.energy
                attempt_to_gain = min(energy_available, can_take / absorption_rate if absorption_rate > 0 else float('inf'))
                energy_gained = attempt_to_gain * absorption_rate
                food.decay_energy -= attempt_to_gain
                food.decay_energy = max(0, food.decay_energy)
            else:
                return False # Dead unit has no energy
        else:
            return False # Not a valid food type

        if energy_gained <= 0:
            return False
            
        self.energy += energy_gained
        self.energy = min(self.energy, self.max_energy)

        if self.alive and self.state not in ["dead", "decaying"]:
            self.last_state = self.state
            self.state = "feeding"
            self.state_duration = 0
        
        return True
    
    def attack(self, target):
        """
        Attack another unit.
        
        Args:
            target (Unit): The unit to attack.
            
        Returns:
            int: The amount of damage dealt.
        """
        if not self.alive or not target.alive or self.state in ["dead", "decaying", "feeding"]:
            return 0
            
        damage = max(1, self.strength)
        
        if self.state == "hunting":
            damage *= 1.5
        elif self.state == "fleeing":
            damage *= 0.5
            
        if self.energy < self.energy_cost_attack:
            return 0 # Not enough energy to attack
            
        self.energy -= self.energy_cost_attack
        target.hp -= damage
        
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            target.state = "dead"
            target.decay_stage = 0
            target.decay_energy = target.energy
            
        return damage
    
    def update(self, board):
        """
        Update the unit's state based on its surroundings and internal state.
        Implements a sophisticated state machine for decision making.
        
        Args:
            board (Board): The game board.
        """
        if self.hp <= 0 and self.alive:
            self.hp = 0
            self.alive = False
            self.state = "dead"
            self.decay_stage = 0
            self.decay_energy = self.energy
            
        if not self.alive:
            self.decay_stage += 1
            decay_rate = 0.1
            self.decay_energy *= (1 - decay_rate)
            
            if self.decay_stage > 5 and self.state == "dead":
                self.state = "decaying"

            if self.decay_stage >= 11:
                board.remove_object(self.x, self.y)
            return
            
        self.strength = self.base_strength
        self.speed = self.base_speed
        self.vision = self.base_vision
        
        if (self.state_duration > 10 and 
            self.state not in ["dead", "decaying", "resting", "wandering"] and 
            self.energy > self.max_energy * 0.4 and 
            self.hp > self.max_hp * 0.3):
            self.state = "wandering"
            self.state_duration = 0
            return

        if self.state == self.last_state:
            self.state_duration += 1
        else:
            self.state_duration = 0
            self.last_state = self.state

        if self.energy <= self.max_energy * 0.2:
            self.state = "resting"
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self.speed = int(self.base_speed * 1.5) + 1
        elif self.energy <= self.max_energy * 0.4:
            self.state = "feeding"
        elif self.state == "resting" and self.energy > self.max_energy * self.resting_exit_energy_ratio: # Lowered threshold
            self.state = "wandering"
        elif self.state == "feeding" and self.energy > self.max_energy * 0.9:
            self.state = "wandering"

        # Impatient rest: Max duration for resting
        if (self.state == "resting" and
            self.state_duration >= self.max_resting_turns and
            self.energy > self.max_energy * self.min_energy_force_exit_rest_ratio):
            self.state = "wandering"
            self.state_duration = 0 # Reset duration as state is changing
            
        if self.state == "hunting":
            self.strength = int(self.base_strength * 1.2)
            self.vision = int(self.base_vision * 1.5)
        elif self.state == "resting":
            self.energy = min(self.max_energy, self.energy + 2)

    def apply_environmental_effects(self):
        """
        Apply environmental effects to the unit.
        Placeholder for future implementation.
        """
        pass

    def set_board(self, board):
        """Set the board reference and calculate quarter height."""
        self.board = board
        self.board_height = board.height
        self.quarter_height = board.height // 4
        
    def _get_next_exploration_direction(self):
        """Get the next exploration direction based on current position and board height."""
        if self.board_height is None:
            return (1, 0)  # Default to right if board not set
            
        # Calculate which quarter of the board we're in
        current_quarter = (self.y // self.quarter_height) % 4
        
        # Define directions for each quarter (clockwise)
        quarter_directions = [
            (1, 0),   # Right
            (0, 1),   # Down
            (-1, 0),  # Left
            (0, -1)   # Up
        ]
        
        return quarter_directions[current_quarter]
        
    def _get_exploration_move(self) -> Optional[Tuple[int, int]]:
        """Get the next exploration move based on the current direction and distance."""
        if self.exploration_distance >= self.quarter_height:
            # Time to change direction
            self.exploration_direction = self._get_next_exploration_direction()
            self.exploration_distance = 0
            
        # Calculate the next position
        next_x = self.x + self.exploration_direction[0]
        next_y = self.y + self.exploration_direction[1]
        
        # Check if the move is valid
        if self.board.is_valid_position(next_x, next_y):
            self.exploration_distance += 1
            return (next_x, next_y)
            
        # If the move is invalid, try to find a valid alternative
        # Try perpendicular directions first
        perpendicular_directions = [
            (self.exploration_direction[1], -self.exploration_direction[0]),  # 90 degrees
            (-self.exploration_direction[1], self.exploration_direction[0])   # -90 degrees
        ]
        
        for direction in perpendicular_directions:
            alt_x = self.x + direction[0]
            alt_y = self.y + direction[1]
            if self.board.is_valid_position(alt_x, alt_y):
                self.exploration_direction = direction
                self.exploration_distance = 0
                return (alt_x, alt_y)
                
        return None
    
    def _explore_territory(self, board):
        """Explore territory by moving in the current exploration direction."""
        possible_moves, _ = self.get_potential_moves_in_vision_range(board)
        
        if not possible_moves:
            # Completely blocked - try to rest or wait
            self.state = "resting"
            return
            
        exploration_move = self._get_exploration_move()
        if exploration_move and exploration_move in possible_moves:
            dx = exploration_move[0] - self.x
            dy = exploration_move[1] - self.y
            if self.move(dx, dy, board):
                self.energy -= self.energy_cost_move
        elif possible_moves:
            # If planned exploration move isn't possible, try any available move
            move_x, move_y = possible_moves[0]
            dx = move_x - self.x
            dy = move_y - self.y
            if self.move(dx, dy, board):
                self.energy -= self.energy_cost_move
