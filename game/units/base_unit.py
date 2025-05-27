"""
Base Unit module for the ecosystem simulation game.

This module implements the base Unit class with fundamental RPG-style stats and behaviors.
All other unit types will inherit from this base class.
"""

import random
# Predefined unit templates for different roles
UNIT_TEMPLATES = {
    "predator": {
        "hp": 100,
        "energy": 120,
        "strength": 15,
        "speed": 2,
        "vision": 8,  # Increased vision range for better hunting
        "unit_type": "predator"  # Ensure unit_type is set
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
        self.unit_type = unit_type  # Set unit_type first
        
        # Use template if unit_type is provided
        if unit_type and unit_type in UNIT_TEMPLATES:
            template = UNIT_TEMPLATES[unit_type]
            hp = template["hp"]
            energy = template["energy"]
            strength = template["strength"]
            speed = template["speed"]
            vision = template["vision"]
            self.unit_type = template.get("unit_type", unit_type)  # Use template unit_type if provided

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
        if not board.is_valid_position(new_x, new_y):
            print(f"Invalid position: ({new_x},{new_y})")
            return False
            
        if board.get_object(new_x, new_y) is not None:
            print(f"Position occupied: ({new_x},{new_y})")
            return False
        
        # Calculate energy cost based on state and movement
        energy_cost = 1  # Base cost of 1 per move regardless of distance
        if self.state == "fleeing":
            energy_cost = 2  # Double cost when fleeing
            
        # Minimum energy requirement to move at all
        min_energy = 2
        if self.energy < min_energy:
            print(f"Insufficient minimum energy: {self.energy} < {min_energy}")
            return False
            
        # Check for sufficient energy for movement cost
        if self.energy < energy_cost:
            print(f"Insufficient energy for movement: {self.energy} < {energy_cost}")
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
        # Process movement and actions first if alive
        if self.alive and self.state not in ["dead", "decaying", "resting", "feeding"]:
            moved = False
            # First scan for prey if we're a predator
            print(f"\nUnit at ({self.x},{self.y}) - Type: {self.unit_type}, Vision: {self.vision}, State: {self.state}")
            if self.unit_type == "predator":
                print(f"Predator scanning for prey...")
                for dx in range(-self.vision, self.vision + 1):
                    for dy in range(-self.vision, self.vision + 1):
                        check_x, check_y = self.x + dx, self.y + dy
                        if board.is_valid_position(check_x, check_y):
                            obj = board.get_object(check_x, check_y)
                            if obj and hasattr(obj, 'unit_type'):
                                print(f"Found object at ({check_x},{check_y}) - Type: {obj.unit_type}")
                                if obj.unit_type == "grazer" and obj.alive:
                                    print(f"Found live prey at ({check_x},{check_y})")
                            if obj and hasattr(obj, 'unit_type') and obj.unit_type == "grazer":
                                # Attack if adjacent
                                if abs(dx) <= 1 and abs(dy) <= 1:
                                    print(f"Predator attacking grazer at ({check_x},{check_y})")
                                    self.state = "combat"  # Set combat state before attack
                                    damage = self.attack(obj)
                                    if damage > 0:
                                        print(f"Predator dealt {damage} damage to grazer")
                                        self.state = "combat"  # Ensure combat state is maintained
                                        if not obj.alive:  # If prey died from attack
                                            self.state = "feeding"
                                            self.energy += 30  # Gain energy from successful hunt
                                            print(f"Predator gained energy from prey")
                                        moved = True
                                        return  # Exit the update to maintain state
                                else:  # Move toward prey
                                    self.state = "hunting"
                                    # Allow diagonal movement
                                    move_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
                                    move_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
                                    print(f"Predator at ({self.x},{self.y}) spotted prey at ({check_x},{check_y})")
                                    if abs(dx) > abs(dy):  # Try moving horizontally first
                                        if not self.move(move_x, 0, board):
                                            moved = self.move(0, move_y, board)
                                        else:
                                            moved = True
                                    else:  # Try moving vertically first
                                        if not self.move(0, move_y, board):
                                            moved = self.move(move_x, 0, board)
                                        else:
                                            moved = True
                                    print(f"Predator moving toward prey: ({move_x},{move_y}) - Success: {moved}")
                                break

            # Then scan for food (plants) if we haven't moved
            if not moved:
                print(f"Scanning for food...")
                for dx in range(-self.vision, self.vision + 1):
                    for dy in range(-self.vision, self.vision + 1):
                        check_x, check_y = self.x + dx, self.y + dy
                        if board.is_valid_position(check_x, check_y):
                            obj = board.get_object(check_x, check_y)
                            if obj:
                                has_energy = hasattr(obj, 'state') and hasattr(obj.state, 'energy_content')
                                print(f"Found object at ({check_x},{check_y}) - Has energy: {has_energy}")
                            if obj and hasattr(obj, 'state') and hasattr(obj.state, 'energy_content'):  # Found plant
                                self.state = "hunting"
                                # Feed if adjacent
                                if abs(dx) <= 1 and abs(dy) <= 1:
                                    self.state = "feeding"
                                    if hasattr(self, 'unit_type') and self.unit_type == "grazer":
                                        # Grazer consuming plant
                                        consumed = obj.consume(20)  # Consume some energy
                                        if consumed > 0:
                                            self.energy += consumed
                                            print(f"Grazer consumed {consumed} energy from plant at ({check_x},{check_y})")
                                            self.state = "feeding"  # Set feeding state when successful
                                            return  # Exit update to maintain feeding state
                                    moved = True
                                else:  # Move toward food
                                    # Allow diagonal movement
                                    move_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
                                    move_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
                                    print(f"Unit at ({self.x},{self.y}) spotted food at ({check_x},{check_y})")
                                    if abs(dx) > abs(dy):  # Try moving horizontally first
                                        if not self.move(move_x, 0, board):
                                            moved = self.move(0, move_y, board)
                                        else:
                                            moved = True
                                    else:  # Try moving vertically first
                                        if not self.move(0, move_y, board):
                                            moved = self.move(move_x, 0, board)
                                        else:
                                            moved = True
                                    print(f"Moving toward food: ({move_x},{move_y}) - Success: {moved}")
                                break
            
            # If no food found or couldn't move toward it, implement wandering behavior
            if not moved and self.state == "wandering":
                # Choose a random direction to move
                directions = [(1,0), (-1,0), (0,1), (0,-1)]
                move_x, move_y = random.choice(directions)
                success = self.move(move_x, move_y, board)
                print(f"Wandering move attempt: ({move_x},{move_y}) from ({self.x},{self.y}) - Success: {success}")

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

        # State transitions based on conditions and current state
        if self.hp <= 0:
            self.state = "dead"
        elif self.energy < self.max_energy * 0.2:
            self.state = "resting"
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self.speed = int(self.base_speed * 1.5) + 1  # Speed boost when fleeing
        elif self.state == "resting" and self.energy > self.max_energy * 0.8:
            self.state = "wandering"
        elif self.state == "feeding" and self.energy > self.max_energy * 0.9:
            self.state = "wandering"
        elif self.state == "combat":
            if self.energy > self.max_energy * 0.6:
                self.state = "hunting"  # Return to hunting after combat if energy permits
            else:
                self.state = "feeding"  # Need to recover energy after combat
        elif self.state == "hunting" and self.energy < self.max_energy * 0.4:
            self.state = "feeding"  # Need to recover energy from hunting
        elif self.state in ["idle", "wandering"]:
            if random.random() < 0.3:  # 30% chance to start hunting
                self.state = "hunting"
            else:
                self.state = "wandering"
            
        # Apply state-specific effects
        if self.state == "hunting":
            self.strength = int(self.base_strength * 1.2)
            self.vision = int(self.base_vision * 1.5)
        elif self.state == "resting":
            self.energy = min(self.max_energy, self.energy + 2)  # Recover energy while resting
