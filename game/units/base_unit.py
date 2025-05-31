"""
Base Unit module for the ecosystem simulation game.

This module implements the base Unit class with fundamental RPG-style stats and behaviors.
All other unit types will inherit from this base class.
"""

from game.plants.base_plant import Plant # Added import

# Predefined unit templates for different roles
UNIT_TEMPLATES = {
    "predator": {
        "hp": 100,
        "energy": 120,
        "strength": 15,
        "speed": 2,
        "vision": 6
    },
    "scavenger": {
        "hp": 80,
        "energy": 100,
        "strength": 8,
        "speed": 3,
        "vision": 8
    },
    "grazer": {
        "hp": 120,
        "energy": 150,
        "strength": 5,
        "speed": 1,
        "vision": 4
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
    
    def __init__(self, x, y, unit_type=None, hp=100, energy=100, strength=10, speed=1, vision=5):
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
        """
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
        
        # Validate movement based on speed
        if abs(dx) + abs(dy) > self.speed:
            return False
        
        # Check if movement is possible
        if not board.is_valid_position(new_x, new_y) or board.get_object(new_x, new_y) is not None:
            return False
        
        # Calculate energy cost based on state and movement (fixed cost of 1 per space)
        energy_cost = 1  # Base cost of 1 per move regardless of distance
        if self.state == "fleeing":
            energy_cost = 2  # Double cost when fleeing
        
        # Check for sufficient energy - need at least 2 energy to move
        if self.energy < 2:  # Minimum energy requirement
            return False
        
        # Check if we can afford the movement cost
        if self.energy < energy_cost:
            return False
            
        # Check if movement is possible
        if not board.move_object(self.x, self.y, new_x, new_y):
            return False
            
        # Apply movement and energy cost
        self.x = new_x
        self.y = new_y
        self.energy -= energy_cost
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
                # Let Plant.consume handle how much energy it can give
                # Assuming 100% absorption efficiency for plants for now
                energy_gained = food.consume(needed_energy)
            else:
                return False # Plant is not consumable
        elif isinstance(food, Unit) and not food.alive:
            # Initialize decay properties if needed (though should be set on death)
            if not hasattr(food, 'decay_stage'): food.decay_stage = 0
            if not hasattr(food, 'decay_energy') or food.decay_energy is None: food.decay_energy = food.max_energy # or current energy at time of death

            if food.decay_energy > 0:
                energy_available = food.decay_energy
                absorption_rate = 0.8  # 80% efficiency for consuming dead units

                # How much energy the unit can actually take
                can_take = self.max_energy - self.energy
                # How much to attempt to take from corpse considering absorption
                attempt_to_gain = min(energy_available, can_take / absorption_rate if absorption_rate > 0 else float('inf'))

                energy_gained = attempt_to_gain * absorption_rate
                food.decay_energy -= attempt_to_gain # Reduce corpse energy by amount before absorption
                food.decay_energy = max(0, food.decay_energy) # Ensure not negative
            else:
                return False # Dead unit has no energy
        else:
            return False # Not a valid food type

        if energy_gained <= 0: # If no energy was gained (e.g. plant had none, or unit already full after calc)
            return False
            
        self.energy += energy_gained
        self.energy = min(self.energy, self.max_energy) # Ensure not over max_energy

        # Only change state if we're alive and not in a restricted state
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
            
        # Calculate base damage
        damage = max(1, self.strength)
        
        # Apply state modifiers
        if self.state == "hunting":
            damage *= 1.5
        elif self.state == "fleeing":
            damage *= 0.5
            
        # Energy cost for attacking
        energy_cost = 2
        if self.energy < energy_cost:
            return 0
            
        self.energy -= energy_cost
        
        # Apply damage
        target.hp -= damage
        
        # Check if target died
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            target.state = "dead"
            target.decay_stage = 0
            target.decay_energy = target.energy  # Initialize decay energy
            
        return damage
    
    def act(self, board):
        """
        Update the unit's state based on its surroundings and internal state.
        Implements a sophisticated state machine for decision making.
        
        Args:
            board (Board): The game board.
        """
        # Check for death first
        if self.hp <= 0 and self.alive:  # Only initialize decay on new death
            self.hp = 0
            self.alive = False
            self.state = "dead"
            self.decay_stage = 0
            self.decay_energy = self.energy
            return
            
        if not self.alive:
            decay_rate = 0.1  # 10% decay per turn
            # Always increment decay stage for dead units
            self.decay_stage += 1
            self.decay_energy *= (1 - decay_rate)
            
            # After 5 turns of being dead, transition to decaying
            if self.decay_stage > 5 and self.state == "dead":
                self.state = "decaying"
            return
            
        # Reset stat modifiers
        self.strength = self.base_strength
        self.speed = self.base_speed
        self.vision = self.base_vision
        
        # Handle state duration limits before anything else
        if (self.state_duration > 10 and 
            self.state not in ["dead", "decaying", "resting", "wandering"] and 
            self.energy > self.max_energy * 0.4 and 
            self.hp > self.max_hp * 0.3):
            self.state = "wandering"
            self.state_duration = 0
            return

        # Track state duration
        if self.state == self.last_state:
            self.state_duration += 1
        else:
            self.state_duration = 0
            self.last_state = self.state

        # State transitions based on conditions
        if self.energy < self.max_energy * 0.2:
            self.state = "resting"
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self.speed = int(self.base_speed * 1.5) + 1  # Speed boost when fleeing, ensure at least +1
        elif self.energy < self.max_energy * 0.4:
            self.state = "feeding"
        elif self.state == "resting" and self.energy > self.max_energy * 0.8:
            self.state = "wandering"
        elif self.state == "feeding" and self.energy > self.max_energy * 0.9:
            self.state = "wandering"
            
        # Apply state-specific effects
        if self.state == "hunting":
            self.strength = int(self.base_strength * 1.2)
            self.vision = int(self.base_vision * 1.5)
        elif self.state == "resting":
            self.energy = min(self.max_energy, self.energy + 2)  # Recover energy while resting
