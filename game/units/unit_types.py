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
    
    def __init__(self, x, y, hp=None, config=None): # Added hp, default from template if None
        """
        Initialize a new predator unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
            hp (int, optional): Health points. Defaults to template value.
        """
        # Pass unit_type to super for template lookup if hp is not specified
        # Values provided here (energy, strength etc.) will override template if hp is also None,
        # or be used if hp is specified (template won't be fully reapplied in Unit.__init__)
        super().__init__(x, y, unit_type="predator", hp=hp, energy=80, strength=15, speed=2, vision=6, config=config)
        self.target = None
    
    def update(self, board):
        """
        Update the predator's state based on its surroundings.
        
        Predators prioritize hunting over other activities.
        
        Args:
            board (Board): The game board.
        """
        super().update(board) # Call base class update for general state transitions / decay
        if not self.alive or self.state == "resting": # If base class decided unit should rest or unit is dead, respect it.
            return

        # If base class set state to "wandering", and predator isn't critically hungry/injured, let it wander.
        # This helps test_state_transitions see the "wandering" state.
        if self.state == "wandering" and \
           not (self.energy <= self.max_energy * 0.2) and \
           not (self.hp < self.max_hp * 0.3):
            # self._wander_action(board) # Placeholder for actual wandering behavior if any
            return # Keep state as wandering for this turn

        # State machine for predator behavior
        # Update state based on conditions (potentially overriding base states if needed)
        if self.energy <= self.max_energy * 0.2: # Changed to <= for consistency
            self.state = "hungry"
            self._find_closest_food(board)
        elif self.hp < self.max_hp * 0.3:
            self.state = "fleeing"
            self._flee_from_threats(board)
        else: # Default Predator action, could also be set if not hungry, not fleeing, not wandering
            self.state = "hunting"
            self._hunt_prey(board)

    def _hunt_prey(self, board):
        """Hunt for prey within vision range."""
        # Use self.look(board) which returns a list of (object, x, y) tuples
        # and correctly filters out self.
        # Note: self.look() in base_unit.py already adjusts vision based on state (e.g. hunting).
        visible_objects_data = self.look(board) # self.look() is in base_unit.py

        # Filter for units from the visible objects
        visible_units = []
        for item in visible_objects_data:
            obj = item[0] # The object itself
            if hasattr(obj, 'alive'): # Check if it's a unit (has 'alive' attribute)
                visible_units.append(obj)

        print(f"Visible units for predator at ({self.x}, {self.y}) via self.look(): {len(visible_units)}")
        for unit in visible_units:
            # Ensure unit has x and y attributes for the print, which it should if it's a Unit
            if hasattr(unit, 'x') and hasattr(unit, 'y'):
                 print(f"- Found unit at ({unit.x}, {unit.y}): {type(unit).__name__}, alive: {unit.alive}")
            else:
                 print(f"- Found non-unit object or unit missing x/y: {type(unit).__name__}")

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
                energy_before_attack = self.energy
                damage_dealt = self.attack(target) # attack() returns damage

                if self.energy < energy_before_attack: # Confirms attack occurred (cost energy)
                    self.state = "combat"
                    self.gain_experience("combat")
                    if not target.alive: # If target died
                        self.gain_experience("hunting") # For successful kill
                        # Attempt to eat the killed prey.
                        # The eat() method in base_unit handles setting state to "feeding"
                        self.eat(target)
            else:
                # Move toward prey
                print(f"Attempting to move: dx={dx}, dy={dy}")
                original_dx, original_dy = dx, dy
                move_success = board.move_unit(self, original_dx, original_dy)
                print(f"Move success (initial attempt): {move_success}")

                if not move_success and original_dx != 0 and original_dy != 0:
                    print(f"Initial diagonal move ({original_dx},{original_dy}) failed. Trying cardinal alternatives.")
                    # Try moving horizontally
                    move_success_h = board.move_unit(self, original_dx, 0)
                    print(f"Move success (horizontal attempt): {move_success_h}")
                    if move_success_h:
                        move_success = True
                    else:
                        # Try moving vertically if horizontal failed
                        move_success_v = board.move_unit(self, 0, original_dy)
                        print(f"Move success (vertical attempt): {move_success_v}")
                        if move_success_v:
                            move_success = True

                if move_success:
                    print("Reducing energy by 2 due to hunting movement.")
                    self.energy -= 2  # Higher energy cost for hunting movement
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
    
    def __init__(self, x, y, hp=None, config=None): # Added hp, default from template if None
        """
        Initialize a new scavenger unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
            hp (int, optional): Health points. Defaults to template value.
        """
        # Pass unit_type to super for template lookup
        super().__init__(x, y, unit_type="scavenger", hp=hp, energy=110, strength=8, speed=1, vision=8, config=config)
    
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

    def _search_for_corpses(self, board):
        """Search for dead units to consume."""
        # Scavengers have enhanced detection of dead units
        visible_units = board.get_units_in_range(self.x, self.y, self.vision + 2)
        print(f"Scavenger at ({self.x}, {self.y}) found {len(visible_units)} visible units:")
        for unit in visible_units:
            print(f"- Found unit at ({unit.x}, {unit.y}): {type(unit).__name__}, alive={unit.alive}")
        
        corpses = [u for u in visible_units if not u.alive and u.decay_stage < 4]  # Can eat more decayed corpses
        print(f"Found {len(corpses)} corpses to scavenge")
        
        if corpses:
            target = min(corpses, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            print(f"Scavenger at ({self.x}, {self.y}) found corpse at ({target.x}, {target.y})")
            
            # Calculate direction to move toward corpse
            dx = -1 if self.x > target.x else (1 if self.x < target.x else 0)
            dy = -1 if self.y > target.y else (1 if self.y < target.y else 0)
            print(f"Moving toward corpse with dx={dx}, dy={dy}")
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                energy_gained = self._consume(target)
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
            dx = max(min(self.x - threat.x, self.speed), -self.speed)
            dy = max(min(self.y - threat.y, self.speed), -self.speed)
            
            if board.move_unit(self, dx, dy):
                self.energy -= 2
                self.gain_experience("fleeing")


class Grazer(Unit):
    """
    A grazer unit that primarily consumes plants.
    
    Grazers are peaceful units with high energy capacity but low strength.
    They avoid combat and focus on finding and consuming plants.
    """
    
    def __init__(self, x, y, hp=None, config=None): # Added hp, default from template if None
        """
        Initialize a new grazer unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
            hp (int, optional): Health points. Defaults to template value.
        """
        # Pass unit_type to super for template lookup
        super().__init__(x, y, unit_type="grazer", hp=hp, energy=130, strength=5, speed=1, vision=5, config=config)
        self.exploration_moves = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        self.next_exploration_move_index = 0
    
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
        plants = board.get_plants_in_range(self.x, self.y, self.vision)
        
        if plants:
            target = min(plants, key=lambda p: ((p.position.x - self.x)**2 + (p.position.y - self.y)**2)**0.5)
            dx = max(min(target.position.x - self.x, self.speed), -self.speed)
            dy = max(min(target.position.y - self.y, self.speed), -self.speed)
            
            if abs(target.position.x - self.x) <= 1 and abs(target.position.y - self.y) <= 1:
                # Call self.eat() which handles interaction with Plant.consume and energy update
                if self.eat(target): # self.eat will update energy and state
                    # Grazer specific bonus was: self.energy += int(energy_gained * 0.3)
                    # This bonus logic needs to be integrated into Unit.eat or handled differently
                    # For now, relying on Unit.eat to correctly provide energy.
                    self.gain_experience("feeding") # Experience gain is fine here
            else:
                original_dx, original_dy = dx, dy
                move_success = board.move_unit(self, original_dx, original_dy)
                if not move_success and original_dx != 0 and original_dy != 0:
                    # Try cardinal alternatives
                    if board.move_unit(self, original_dx, 0):
                        move_success = True
                    elif board.move_unit(self, 0, original_dy):
                        move_success = True

                if move_success:
                    self.energy -= 1
                    self.gain_experience("feeding", 0.2)  # Small exp gain for finding food
        else:
            # If no plants visible, explore deterministically
            dx, dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            if board.move_unit(self, dx, dy):
                self.energy -= 1

    def _find_food(self, board):
        """Find closest plant when hungry."""
        plants = board.get_plants_in_range(self.x, self.y, self.vision)
        
        if plants:
            target = min(plants, key=lambda p: ((p.position.x - self.x)**2 + (p.position.y - self.y)**2)**0.5)
            dx = max(min(target.position.x - self.x, self.speed), -self.speed)
            dy = max(min(target.position.y - self.y, self.speed), -self.speed)
            
            if abs(target.position.x - self.x) <= 1 and abs(target.position.y - self.y) <= 1:
                # Call self.eat() which handles interaction with Plant.consume and energy update
                if self.eat(target): # self.eat will update energy and state
                    self.gain_experience("feeding") # Experience gain is fine here
            else:
                original_dx, original_dy = dx, dy
                move_success = board.move_unit(self, original_dx, original_dy)
                if not move_success and original_dx != 0 and original_dy != 0:
                    # Try cardinal alternatives
                    if board.move_unit(self, original_dx, 0):
                        move_success = True
                    elif board.move_unit(self, 0, original_dy):
                        move_success = True

                if move_success:
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
