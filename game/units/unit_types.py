"""
Unit Types module for the ecosystem simulation game.

This module implements various unit types that inherit from the base Unit class,
each with specialized behaviors and characteristics.
"""

from game.units.base_unit import Unit

class Predator(Unit):
    """
    A predator unit that actively hunts other units.
    
    Predators have high strength and speed, making them effective hunters.
    They primarily target other units for food rather than plants.
    """
    
    def __init__(self, x, y):
        """
        Initialize a new predator unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
        """
        from game.config import Config
        config = Config()
        
        # Get predator-specific attributes from config
        base_energy = config.get("units", "predator.base_energy")
        vision_range = config.get("units", "predator.vision_range")
        attack_strength = config.get("units", "predator.attack_strength")
        
        super().__init__(
            x=x, 
            y=y, 
            hp=120,  # Base HP is standard
            energy=base_energy,
            strength=attack_strength,
            speed=2,  # Base speed is standard
            vision=vision_range
        )
        self.target = None
    
    def update(self, board):
        """
        Update the predator's state based on its surroundings.
        
        Predators prioritize hunting over other activities.
        
        Args:
            board (Board): The game board.
        """
        if not self.alive:
            # Handle decay for dead units
            self.decay_stage += 1
            return
        
        # State machine for predator behavior
        # Update state based on conditions
        if self.energy < self.max_energy * 0.2:
            self.state = "hungry"
            self._find_closest_food(board)
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self._flee_from_threats(board)
        else:
            self.state = "hunting"
            self._hunt_prey(board)

    def _hunt_prey(self, board):
        """Hunt for prey within vision range."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        print(f"Visible units for predator at ({self.x}, {self.y}): {len(visible_units)}")
        for unit in visible_units:
            print(f"- Found unit at ({unit.x}, {unit.y}): {type(unit).__name__}")
            
        potential_prey = [u for u in visible_units if isinstance(u, (Grazer, Scavenger)) and u.alive]
        print(f"Potential prey found: {len(potential_prey)}")
        
        if potential_prey:
            target = min(potential_prey, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            dx = 0 if target.x == self.x else (1 if target.x > self.x else -1)
            dy = 0 if target.y == self.y else (1 if target.y > self.y else -1)
            
            # Limit by speed
            if abs(dx) + abs(dy) > self.speed:
                if abs(target.x - self.x) > abs(target.y - self.y):
                    dy = 0
                else:
                    dx = 0
            
            # If adjacent to prey, attack
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                damage = self._attack(target)
                if damage > 0:
                    self.gain_experience("combat")
                    if not target.alive:
                        self.gain_experience("hunting")
            else:
                # Move toward prey
                print(f"Attempting to move: dx={dx}, dy={dy}")
                move_success = board.move_unit(self, dx, dy)
                print(f"Move success: {move_success}")
                if move_success:
                    move_cost = Config().get("units", "energy_consumption.move")
                    self.energy -= move_cost * (1.5 if self.state == "hunting" else 1.0)  # Higher cost when hunting
                    self.gain_experience("hunting", 0.5)

    def _find_closest_food(self, board):
        """Find and move toward the closest food source."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        food_sources = [u for u in visible_units if not u.alive and u.decay_stage < 3]
        
        if food_sources:
            target = min(food_sources, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            dx = max(min(target.x - self.x, self.speed), -self.speed)
            dy = max(min(target.y - self.y, self.speed), -self.speed)
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self._consume(target)
                self.gain_experience("feeding")
            else:
                board.move_unit(self, dx, dy)
                self.energy -= 1

    def _flee_from_threats(self, board):
        """Move away from threats."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        threats = [u for u in visible_units if isinstance(u, Predator) and u != self and u.alive]
        
        if threats:
            # Move away from the closest threat
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            dx = max(min(self.x - threat.x, self.speed), -self.speed)
            dy = max(min(self.y - threat.y, self.speed), -self.speed)
            
            if board.move_unit(self, dx, dy):
                self.energy -= 3  # Highest energy cost for fleeing
                self.gain_experience("fleeing")


class Scavenger(Unit):
    """
    A scavenger unit that specializes in finding and consuming dead units.
    
    Scavengers have enhanced vision and can detect dead units from farther away.
    They're not as strong as predators but are more efficient at extracting energy from corpses.
    """
    
    def __init__(self, x, y):
        """
        Initialize a new scavenger unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
        """
        # Scavengers have better vision and moderate stats
        super().__init__(
            x=x, 
            y=y, 
            hp=90,           # Lower HP than others
            energy=80,       # Start with less energy to encourage feeding
            strength=8, 
            speed=2,         # Good speed for finding food
            vision=8         # Enhanced vision for finding corpses
        )
    
    def update(self, board):
        """
        Update the scavenger's state based on its surroundings.
        
        Scavengers prioritize finding dead units to consume.
        
        Args:
            board (Board): The game board.
        """
        if not self.alive:
            # Handle decay for dead units
            self.decay_stage += 1
            return
        
        # State machine for scavenger behavior
        if self.energy < self.max_energy * 0.3:
            self.state = "hungry"
            self._find_food(board)
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self._flee_from_threats(board)
        else:
            self.state = "scavenging"
            self._search_for_corpses(board)

    def feed(self, target):
        """
        Feed on a dead unit, gaining energy based on its decay state.
        
        Args:
            target: The dead unit to feed on
            
        Returns:
            int: Amount of energy gained
        """
        if target.alive or not hasattr(target, 'decay_energy'):
            return 0
            
        # Ensure target has valid decay properties
        if not hasattr(target, 'decay_stage'):
            target.decay_stage = 0
        if not hasattr(target, 'decay_energy'):
            target.decay_energy = target.energy
            
        # Ensure target has proper decay properties
        if not hasattr(target, 'decay_stage'):
            target.decay_stage = 0
        if not hasattr(target, 'decay_energy'):
            target.decay_energy = target.max_energy
            
        # Calculate base energy available (more from fresher corpses)
        base_energy = target.decay_energy * (1.0 - (target.decay_stage * 0.2))
        
        # Scavengers are extremely efficient at extracting energy
        efficiency = 3.0 if self.state == "hungry" else 2.0
        potential_gain = int(base_energy * efficiency)
        
        # Ensure significant energy gain
        minimum_gain = 35
        energy_gain = max(minimum_gain, min(potential_gain, self.max_energy - self.energy))
        
        # Apply the energy gain
        self.energy = min(self.max_energy, self.energy + energy_gain)
        
        # Reduce corpse's energy and advance decay
        target.decay_energy = max(0, target.decay_energy - (energy_gain / efficiency))
        target.decay_stage += 1
        
        # Update decay state if fully consumed
        if target.decay_energy <= 0:
            target.decay_stage = 4  # Fully consumed
            target.decay_energy = 0
            target.state = "decaying"
            
        return energy_gain
        
    def _search_for_corpses(self, board):
        """Search for dead units to consume."""
        # Scavengers have enhanced detection of dead units
        visible_units = board.get_units_in_range(self.x, self.y, self.vision + 2)
        corpses = [u for u in visible_units if not u.alive and u.decay_stage < 4]  # Can eat more decayed corpses
        
        if corpses:
            target = min(corpses, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            
            # Calculate direction to move toward corpse
            dx = -1 if self.x > target.x else (1 if self.x < target.x else 0)
            dy = -1 if self.y > target.y else (1 if self.y < target.y else 0)
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                energy_gained = self.feed(target)
                if energy_gained > 0:
                    # Scavengers get more energy from corpses
                    self.energy += int(energy_gained * 0.5)
                    self.gain_experience("feeding")
            # Try diagonal move first, then try horizontal or vertical if that fails
            print(f"Attempting diagonal move toward corpse: dx={dx}, dy={dy}")
            if board.move_unit(self, dx, dy):
                print(f"Successfully moved toward corpse diagonally")
                self.energy -= 1
                self.gain_experience("hunting", 0.2)
            elif board.move_unit(self, dx, 0):  # Try horizontal
                print(f"Successfully moved toward corpse horizontally")
                self.energy -= 1
                self.gain_experience("hunting", 0.2)
            elif board.move_unit(self, 0, dy):  # Try vertical
                print(f"Successfully moved toward corpse vertically")
                self.energy -= 1
                self.gain_experience("hunting", 0.2)
            else:
                print("Failed to move toward corpse in any direction")

    def _find_food(self, board):
        """Find any food source when hungry."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        food_sources = ([u for u in visible_units if not u.alive] + 
                       [p for p in board.get_plants_in_range(self.x, self.y, self.vision)])
        
        if food_sources:
            target = min(food_sources, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            dx = max(min(target.x - self.x, self.speed), -self.speed)
            dy = max(min(target.y - self.y, self.speed), -self.speed)
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self._consume(target)
                self.gain_experience("feeding")
            else:
                board.move_unit(self, dx, dy)
                self.energy -= 1

    def _flee_from_threats(self, board):
        """Move away from threats."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        threats = [u for u in visible_units if isinstance(u, Predator) and u.alive]
        
        if threats:
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            # Move in opposite direction of threat
            # Use increased speed when fleeing
            dx = max(min(self.x - threat.x, self.flee_speed), -self.flee_speed)
            dy = max(min(self.y - threat.y, self.flee_speed), -self.flee_speed)
            
            if board.move_unit(self, dx, dy):
                move_cost = Config().get("units", "energy_consumption.move")
                self.energy -= move_cost * 1.5  # Higher energy cost when fleeing
                self.gain_experience("fleeing")


class Grazer(Unit):
    """
    A grazer unit that primarily consumes plants.
    
    Grazers are peaceful units with high energy capacity but low strength.
    They avoid combat and focus on finding and consuming plants.
    """
    
    def __init__(self, x, y):
        """
        Initialize a new grazer unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
        """
        from game.config import Config
        config = Config()
        
        # Get grazer-specific attributes from config
        base_energy = config.get("units", "grazer.base_energy")
        vision_range = config.get("units", "grazer.vision_range")
        flee_speed = config.get("units", "grazer.flee_speed")
        
        super().__init__(
            x=x,
            y=y,
            hp=90,  # Base HP is standard
            energy=base_energy,
            strength=5,  # Base strength is standard
            speed=1,  # Base speed, increases when fleeing
            vision=vision_range
        )
        self.flee_speed = flee_speed  # Store flee speed for state changes
    
    def update(self, board):
        """
        Update the grazer's state based on its surroundings.
        
        Grazers prioritize finding plants and avoiding predators.
        
        Args:
            board (Board): The game board.
        """
        if not self.alive:
            # Handle decay for dead units
            self.decay_stage += 1
            return
        
        # First check for predators
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        threats = [u for u in visible_units if isinstance(u, Predator) and u.alive]
        
        # State machine for grazer behavior
        if threats:
            self.state = "fleeing"
            self._flee_from_threats(board)
        elif self.energy < self.max_energy * 0.3:
            self.state = "hungry"
            self._find_food(board)
        else:
            self.state = "grazing"
            self._graze(board)

    def _graze(self, board):
        """Find and consume plants efficiently."""
        # Use the Unit's _consume method directly to consume plants
        plants = board.get_plants_in_range(self.x, self.y, self.vision)
        for plant in plants:
            if (abs(plant.x - self.x) <= 1 and abs(plant.y - self.y) <= 1):
                energy_gained = self._consume(plant)
                if energy_gained > 0:
                    self.gain_experience("feeding")
                    break
        
        if plants:
            target = min(plants, key=lambda p: ((p.x - self.x)**2 + (p.y - self.y)**2)**0.5)
            dx = max(min(target.x - self.x, self.speed), -self.speed)
            dy = max(min(target.y - self.y, self.speed), -self.speed)
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                energy_gained = self._consume(target)  # _consume already adds energy
                if energy_gained > 0:
                    self.gain_experience("feeding")
            else:
                if board.move_unit(self, dx, dy):
                    move_cost = Config().get("units", "energy_consumption.move")
                    self.energy -= move_cost
                    self.gain_experience("feeding", 0.2)  # Small exp gain for finding food
        else:
            # If no plants visible, explore randomly
            dx = board.random.randint(-self.speed, self.speed)
            dy = board.random.randint(-self.speed, self.speed)
            if board.move_unit(self, dx, dy):
                self.energy -= 1

    def _find_food(self, board):
        """Find closest plant when hungry."""
        plants = board.get_plants_in_range(self.x, self.y, self.vision)
        
        if plants:
            target = min(plants, key=lambda p: ((p.x - self.x)**2 + (p.y - self.y)**2)**0.5)
            dx = max(min(target.x - self.x, self.speed), -self.speed)
            dy = max(min(target.y - self.y, self.speed), -self.speed)
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                energy_gained = self._consume(target)
                if energy_gained > 0:
                    self.gain_experience("feeding")
            else:
                board.move_unit(self, dx, dy)
                self.energy -= 1

    def _flee_from_threats(self, board):
        """Move away from predators, using enhanced threat detection."""
        visible_units = board.get_units_in_range(self.x, self.y, self.vision)
        threats = [u for u in visible_units if isinstance(u, Predator) and u.alive]
        
        if threats:
            # Find the closest threat and move directly away from it
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            print(f"Grazer at ({self.x}, {self.y}) fleeing from threat at ({threat.x}, {threat.y})")
            
            # Try to move away from threat while staying on board
            dx = -1 if threat.x > self.x else 1
            dy = -1 if threat.y > self.y else 1
            
            # Adjust if we're at board edges
            if self.x + dx < 0 or self.x + dx >= board.width:
                dx = -dx
            if self.y + dy < 0 or self.y + dy >= board.height:
                dy = -dy
                
            print(f"Attempting move with edge correction: dx={dx}, dy={dy}")
            
            if board.move_unit(self, dx, dy):
                print("Diagonal move succeeded")
                self.energy -= 2
                self.gain_experience("fleeing")
            elif board.move_unit(self, dx, 0):  # Try horizontal
                print("Horizontal move succeeded")
                self.energy -= 2
                self.gain_experience("fleeing")
            elif board.move_unit(self, 0, dy):  # Try vertical
                print("Vertical move succeeded")
                self.energy -= 2
                self.gain_experience("fleeing")
