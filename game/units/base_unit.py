"""
Base Unit module for the ecosystem simulation game.

This module implements the base Unit class with fundamental RPG-style stats and behaviors.
All other unit types will inherit from this base class.
"""

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
        self._state = "idle"  # Use private attribute for state
        self.alive = True
        self.decay_stage = 0  # 0 means not decaying (alive)
        self.decay_energy = energy  # Energy available when consumed as food
        self.last_state = None  # For tracking state transitions
        self.state_duration = 0  # Turns spent in current state
        
    @property
    def state(self):
        """Get the current state."""
        return self._state
        
    @state.setter
    def state(self, new_state):
        """Set state and update stats accordingly."""
        self.last_state = self._state
        self._state = new_state
        self._update_stats_for_state()
        
    def _update_stats_for_state(self):
        """Update unit stats based on current state."""
        # Reset to base stats first
        self.speed = self.base_speed
        self.strength = self.base_strength
        self.vision = self.base_vision
        
        # Apply state-specific modifiers
        if self._state == "fleeing":
            self.speed = int(self.base_speed * 1.5) + 1  # Speed boost when fleeing
            self.strength = int(self.base_strength * 0.5)  # Weaker while fleeing
        elif self._state == "hunting":
            self.vision = int(self.base_vision * 1.2) + 1  # Vision boost when hunting
            self.strength = int(self.base_strength * 1.2)  # Stronger while hunting
        elif self._state == "resting":
            self.speed = 0  # Cannot move while resting
            # Recover energy while resting
            self.energy = min(self.max_energy, self.energy + 5)
        elif self._state == "feeding":
            self.speed = 0  # Cannot move while feeding
            self.vision = int(self.base_vision * 0.5)  # Limited awareness while feeding
        elif self._state == "dead":
            self.alive = False
            self.speed = 0
            self.vision = 0
            self.strength = 0
        
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
        

    def _consume(self, target) -> float:
        """
        Consume another unit or plant for energy.
        
        Args:
            target: The unit or plant to consume
            
        Returns:
            float: Amount of energy gained from consumption
        """
        if hasattr(target, 'decay_energy'):
            # Consume dead units
            energy_gained = target.decay_energy
            target.decay_energy = 0
            self.energy += energy_gained
            return energy_gained
        elif hasattr(target, 'consume'):
            # Consume plants using their consume method
            energy_needed = self.max_energy - self.energy
            energy_gained = target.consume(energy_needed)
            self.energy += energy_gained
            return energy_gained
        elif hasattr(target, 'energy'):
            # Fallback for other energy-containing objects
            energy_gained = target.energy
            target.energy = 0
            self.energy += energy_gained
            return energy_gained
        return 0.0

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

    def move(self, new_x, new_y, board):
        """
        Move the unit to a specific position if possible.
        
        Args:
            new_x (int): The target x-coordinate.
            new_y (int): The target y-coordinate.
            board (Board): The game board.
            
        Returns:
            bool: True if the move was successful, False otherwise.
        """
        if not self.alive or self.state in ["dead", "decaying", "resting", "feeding"]:
            return False
            
        # Calculate distance to move
        dx = abs(new_x - self.x)
        dy = abs(new_y - self.y)
        
        # Calculate total distance
        total_dist = abs(dx) + abs(dy)
        
        # Calculate base energy cost (1 per step, minimum 1)
        base_cost = max(1, total_dist)
        
        # Modify cost based on state
        # Verify we have minimum energy to attempt movement
        min_energy = 2  # Minimum energy required to attempt any movement
        if self.energy < min_energy:
            return False

        # Calculate base energy cost
        energy_cost = base_cost * {
            "fleeing": 2.0,    # Double cost when fleeing
            "hunting": 1.5,    # 50% more when hunting
            "resting": 0.5,    # Half cost when resting
            "feeding": 2.0,    # Double cost when feeding
        }.get(self.state, 1.0)

        # Additional cost for diagonal movement
        if dx != 0 and dy != 0:
            energy_cost *= 1.4  # 40% more for diagonal

        # Ensure minimum cost and convert to integer
        energy_cost = int(max(min_energy, energy_cost))
        
        # Attempt the move
        if board.move_object(self.x, self.y, new_x, new_y):
            # Always consume at least min_energy, but no more than we have
            actual_cost = min(self.energy, energy_cost)
            self.energy -= actual_cost
            return True

        # Failed moves cost half energy (minimum 1)
        failed_cost = max(1, energy_cost // 2)
        self.energy = max(0, self.energy - failed_cost)
        return False
    
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

        # Get base vision range and adjust for state
        vision_range = self.vision
        if self.state == "hunting":
            vision_range = int(self.vision * 1.5)
        elif self.state == "fleeing":
            vision_range = int(self.vision * 1.2)
        elif self.state == "feeding":
            vision_range = int(self.vision * 0.5)  # Limited awareness while feeding
            
        # Use board's line of sight calculations for better accuracy
        visible_units = board.get_units_in_range(self.x, self.y, vision_range)
        
        # Convert to list of tuples with positions for compatibility
        result = []
        for unit in visible_units:
            if unit is not self:  # Exclude self from results
                result.append((unit, unit.x, unit.y))
                
        # Sort by distance for priority assessment
        return sorted(result, key=lambda x: abs(x[1] - self.x) + abs(x[2] - self.y))
    
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

        # Check food type and conditions
        valid_food = False
        if hasattr(food, "energy_value"):
            valid_food = True
        elif isinstance(food, Unit) and not food.alive:
            # Initialize decay properties if needed
            if not hasattr(food, 'decay_stage'):
                food.decay_stage = 0
            if not hasattr(food, 'decay_energy') or food.decay_energy is None:
                food.decay_energy = food.energy
            if food.decay_energy > 0:
                valid_food = True
                # Ensure food is marked as dead
                food.state = "dead"
            
        if not valid_food:
            return False
            
        # Check energy capacity
        if self.energy >= self.max_energy:
            return False
            
        # Calculate energy gain
        if isinstance(food, Unit) and not food.alive:
            if food.decay_energy <= 0:
                return False
            energy_available = food.decay_energy
            absorption_rate = 0.8  # 80% efficiency for consuming dead units
            gained_energy = min(
                energy_available,
                self.max_energy - self.energy
            ) * absorption_rate
            food.decay_energy = 0  # Consume all decay energy
        else:
            energy_available = food.energy_value
            absorption_rate = 1.0  # 100% efficiency for plants
            gained_energy = min(
                energy_available,
                self.max_energy - self.energy
            ) * absorption_rate
            
        self.energy += gained_energy
        
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
    
    def update(self, board):
        """
        Update the unit's state based on its surroundings and internal state.
        Implements a sophisticated state machine for decision making.
        
        Args:
            board (Board): The game board.
        """
        # Check for death first
        if self.hp <= 0:  # Handle death state
            if self.alive:  # Only initialize decay on new death
                self.state = "dead"  # This will trigger _update_stats_for_state
                self.decay_stage = 0
                self.decay_energy = max(self.energy, 20)  # Ensure minimum energy content for scavenging
            elif self.state == "dead" and self.decay_stage < 3:  # Progress through decay stages
                self.decay_stage += 1
                self.decay_energy = max(0, self.decay_energy - 10)  # Reduce available energy over time
            return
            
        if not self.alive:  # Skip updates if dead
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
