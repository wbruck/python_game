"""
Unit Types module for the ecosystem simulation game.

This module implements various unit types that inherit from the base Unit class,
each with specialized behaviors and characteristics.
"""

import random # Ensure random is imported for Scavenger fallback
from game.units.base_unit import Unit
from game.plants.base_plant import Plant # For Scavenger._find_food

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
        super().__init__(x, y, unit_type="predator", hp=hp, energy=80, strength=15, speed=2, vision=6, config=config)
        self.target = None
    
    def update(self, board):
        """
        Update the predator's state based on its surroundings.
        Predators prioritize hunting over other activities.
        Args:
            board (Board): The game board.
        """
        super().update(board)
        if not self.alive or self.state == "resting":
            return

        if self.state == "wandering" and \
           not (self.energy <= self.max_energy * 0.2) and \
           not (self.hp < self.max_hp * 0.3):
            return

        if self.energy <= self.max_energy * 0.2:
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
        visible_objects_data = self.look(board)

        visible_units = []
        for item in visible_objects_data:
            obj = item[0]
            if hasattr(obj, 'alive'):
                visible_units.append(obj)

        # print(f"Visible units for predator at ({self.x}, {self.y}) via self.look(): {len(visible_units)}") # DEBUG
        # for unit in visible_units: # DEBUG
        #     if hasattr(unit, 'x') and hasattr(unit, 'y'): # DEBUG
        #          print(f"- Found unit at ({unit.x}, {unit.y}): {type(unit).__name__}, alive: {unit.alive}") # DEBUG
        #     else: # DEBUG
        #          print(f"- Found non-unit object or unit missing x/y: {type(unit).__name__}") # DEBUG

        potential_prey = [u for u in visible_units if isinstance(u, (Grazer, Scavenger)) and u.alive]
        # print(f"Potential prey found: {len(potential_prey)}") # DEBUG
        
        if potential_prey:
            target = min(potential_prey, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            dx = 0 if target.x == self.x else (1 if target.x > self.x else -1)
            dy = 0 if target.y == self.y else (1 if target.y > self.y else -1)
            
            if abs(dx) + abs(dy) > self.speed:
                if abs(target.x - self.x) > abs(target.y - self.y): dy = 0
                else: dx = 0
            
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                energy_before_attack = self.energy
                self.attack(target)
                if self.energy < energy_before_attack:
                    self.state = "combat"
                    self.gain_experience("combat")
                    if not target.alive:
                        self.gain_experience("hunting")
                        self.eat(target)
            else:
                # print(f"DEBUG Predator._hunt_prey: id={id(self)} attempting to move towards prey at ({target.x},{target.y}) with preferred dx={dx}, dy={dy}") #DEBUG
                moved = self.move(dx, dy, board)
                if not moved and (dx != 0 or dy != 0):
                    # print(f"DEBUG Predator._hunt_prey: id={id(self)} initial move dx={dx}, dy={dy} failed. Trying cardinal components.") #DEBUG
                    cardinal_dx = 0 if target.x == self.x else (1 if target.x > self.x else -1)
                    cardinal_dy = 0 if target.y == self.y else (1 if target.y > self.y else -1)
                    if cardinal_dx != 0 and self.move(cardinal_dx, 0, board):
                        moved = True
                        # print(f"DEBUG Predator._hunt_prey: id={id(self)} cardinal move dx={cardinal_dx}, dy=0 succeeded.") #DEBUG
                    elif cardinal_dy != 0 and self.move(0, cardinal_dy, board):
                        moved = True
                        # print(f"DEBUG Predator._hunt_prey: id={id(self)} cardinal move dx=0, dy={cardinal_dy} succeeded.") #DEBUG

                if moved:
                    hunt_move_cost = 2
                    if self.config:
                        temp_cost = self.config.get("units", "energy_consumption.move_hunt")
                        if temp_cost is not None: hunt_move_cost = temp_cost
                    self.energy -= hunt_move_cost
                    self.gain_experience("hunting", 0.5)
                # else: # DEBUG
                    # print(f"DEBUG Predator._hunt_prey: id={id(self)} failed to make any move towards prey.") #DEBUG

    def _find_closest_food(self, board):
        """Find and move toward the closest food source (typically dead units for Predator)."""
        # print(f"DEBUG Predator._find_closest_food: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, state={self.state}") #DEBUG
        visible_objects_data = self.look(board)
        food_sources = [item[0] for item in visible_objects_data if hasattr(item[0], 'alive') and not item[0].alive and hasattr(item[0], 'decay_stage') and item[0].decay_stage < 3]

        if food_sources:
            target = min(food_sources, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self.eat(target)
            else:
                move_dx = 1 if target.x > self.x else (-1 if target.x < self.x else 0)
                move_dy = 1 if target.y > self.y else (-1 if target.y < self.y else 0)
                # print(f"DEBUG Predator._find_closest_food: id={id(self)} attempting move towards food with dx={move_dx}, dy={move_dy}") #DEBUG
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    # print(f"DEBUG Predator._find_closest_food: id={id(self)} initial move dx={move_dx}, dy={move_dy} failed. Trying cardinal.") #DEBUG
                    if move_dx != 0 and self.move(move_dx, 0, board): moved = True
                    elif move_dy != 0 and self.move(0, move_dy, board): moved = True

                if moved:
                    move_cost = 1
                    if self.config:
                        temp_cost = self.config.get("units", "energy_consumption.move")
                        if temp_cost is not None: move_cost = temp_cost
                    self.energy -= move_cost

    def _flee_from_threats(self, board):
        """Predator flees from other (presumably stronger) Predators."""
        # print(f"DEBUG Predator._flee_from_threats: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, state={self.state}") #DEBUG
        visible_units = self.look(board)
        threats = [item[0] for item in visible_units if isinstance(item[0], Predator) and item[0] != self and item[0].alive]
        
        if threats:
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            flee_dx = 0
            if self.x < threat.x: flee_dx = -1
            elif self.x > threat.x: flee_dx = 1
            flee_dy = 0
            if self.y < threat.y: flee_dy = -1
            elif self.y > threat.y: flee_dy = 1
            
            if flee_dx == 0 and flee_dy == 0:
                 flee_dx = random.choice([-1,1]) if board.is_valid_position(self.x-1, self.y) or board.is_valid_position(self.x+1, self.y) else 0
                 flee_dy = random.choice([-1,1]) if board.is_valid_position(self.x, self.y-1) or board.is_valid_position(self.x, self.y+1) else 0
                 if flee_dx == 0 and flee_dy == 0:
                     available = board.get_available_moves(self.x, self.y)
                     if available:
                         panic_pos = random.choice(available)
                         flee_dx = panic_pos.x - self.x
                         flee_dy = panic_pos.y - self.y

            # print(f"DEBUG Predator._flee_from_threats: id={id(self)} attempting to move with dx={flee_dx}, dy={flee_dy}") #DEBUG
            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                # print(f"DEBUG Predator._flee_from_threats: id={id(self)} initial flee dx={flee_dx}, dy={flee_dy} failed. Trying cardinal.") #DEBUG
                if flee_dx != 0 and self.move(flee_dx, 0, board): moved = True
                elif flee_dy != 0 and self.move(0, flee_dy, board): moved = True

            if moved:
                flee_cost = 3
                if self.config:
                    temp_cost = self.config.get("units", "energy_consumption.move_flee")
                    if temp_cost is not None: flee_cost = temp_cost
                self.energy -= flee_cost
                self.gain_experience("fleeing")
            # else: # DEBUG
                # print(f"DEBUG Predator._flee_from_threats: id={id(self)} failed to make any flee move.") #DEBUG

class Scavenger(Unit):
    """
    A scavenger unit that specializes in finding and consuming dead units.
    Scavengers have enhanced vision and can detect dead units from farther away.
    They're not as strong as predators but are more efficient at extracting energy from corpses.
    """
    def __init__(self, x, y, hp=None, config=None):
        super().__init__(x, y, unit_type="scavenger", hp=hp, energy=110, strength=8, speed=1, vision=8, config=config)
    
    def update(self, board):
        super().update(board)
        if not self.alive or self.state == "resting": return

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
        # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, base_speed={self.base_speed}, state={self.state}") #DEBUG
        visible_objects_data = self.look(board)
        corpses = [item[0] for item in visible_objects_data if hasattr(item[0], 'alive') and not item[0].alive and hasattr(item[0], 'decay_stage') and item[0].decay_stage < 4]
        
        if corpses:
            target = min(corpses, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self.eat(target)
            else:
                move_dx = 1 if target.x > self.x else (-1 if target.x < self.x else 0)
                move_dy = 1 if target.y > self.y else (-1 if target.y < self.y else 0)
                # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} attempting move towards corpse (dx={move_dx}, dy={move_dy})") #DEBUG
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} initial move (dx={move_dx}, dy={move_dy}) failed. Trying cardinal.") #DEBUG
                    if move_dx != 0:
                        # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} Trying horizontal (dx={move_dx}, dy=0)") #DEBUG
                        if self.move(move_dx, 0, board):
                            moved = True
                            # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} Horizontal move succeeded.") #DEBUG
                    if not moved and move_dy != 0:
                        # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} Trying vertical (dx=0, dy={move_dy})") #DEBUG
                        if self.move(0, move_dy, board):
                            moved = True
                            # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} Vertical move succeeded.") #DEBUG

                if moved:
                    move_cost = 1
                    if self.config:
                        temp_cost = self.config.get("units", "energy_consumption.move")
                        if temp_cost is not None: move_cost = temp_cost
                    self.energy -= move_cost
                    self.gain_experience("hunting", 0.2)
                # else: # DEBUG
                    # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} failed to move toward corpse.") #DEBUG
        # else: # DEBUG
            # print(f"DEBUG Scavenger._search_for_corpses: id={id(self)} no corpses found.") #DEBUG

    def _find_food(self, board):
        """Find any food source when hungry."""
        # print(f"DEBUG Scavenger._find_food: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, base_speed={self.base_speed}, state={self.state}") #DEBUG
        visible_objects_data = self.look(board)
        food_sources = []
        for item in visible_objects_data:
            obj = item[0]
            if (hasattr(obj, 'alive') and not obj.alive and hasattr(obj, 'decay_stage')) or isinstance(obj, Plant):
                food_sources.append(obj)
        
        if food_sources:
            target = min(food_sources, key=lambda u: ((u.x - self.x if hasattr(u, 'x') else u.position.x - self.x)**2 +
                                                      (u.y - self.y if hasattr(u, 'y') else u.position.y - self.y)**2)**0.5)
            target_x = target.x if hasattr(target, 'x') else target.position.x
            target_y = target.y if hasattr(target, 'y') else target.position.y

            if abs(target_x - self.x) <= 1 and abs(target_y - self.y) <= 1:
                self.eat(target)
            else:
                move_dx = 1 if target_x > self.x else (-1 if target_x < self.x else 0)
                move_dy = 1 if target_y > self.y else (-1 if target_y < self.y else 0)
                # print(f"DEBUG Scavenger._find_food: id={id(self)} attempting move towards food (dx={move_dx}, dy={move_dy})") #DEBUG
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    # print(f"DEBUG Scavenger._find_food: id={id(self)} initial move (dx={move_dx}, dy={move_dy}) failed. Trying cardinal.") #DEBUG
                    if move_dx != 0:
                        # print(f"DEBUG Scavenger._find_food: id={id(self)} Trying horizontal (dx={move_dx}, dy=0)") #DEBUG
                        if self.move(move_dx, 0, board):
                            moved = True
                            # print(f"DEBUG Scavenger._find_food: id={id(self)} Horizontal move succeeded.") #DEBUG
                    if not moved and move_dy != 0:
                        # print(f"DEBUG Scavenger._find_food: id={id(self)} Trying vertical (dx=0, dy={move_dy})") #DEBUG
                        if self.move(0, move_dy, board):
                            moved = True
                            # print(f"DEBUG Scavenger._find_food: id={id(self)} Vertical move succeeded.") #DEBUG

                if moved:
                    move_cost = 1
                    if self.config:
                        temp_cost = self.config.get("units", "energy_consumption.move")
                        if temp_cost is not None: move_cost = temp_cost
                    self.energy -= move_cost
        # else: # DEBUG
            # print(f"DEBUG Scavenger._find_food: id={id(self)} no food found.") #DEBUG

    def _flee_from_threats(self, board):
        """Scavenger flees from Predators."""
        # print(f"DEBUG Scavenger._flee_from_threats: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, state={self.state}") #DEBUG
        visible_units = self.look(board)
        threats = [item[0] for item in visible_units if isinstance(item[0], Predator) and item[0].alive]
        
        if threats:
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            flee_dx = 0
            if self.x < threat.x: flee_dx = -1
            elif self.x > threat.x: flee_dx = 1
            flee_dy = 0
            if self.y < threat.y: flee_dy = -1
            elif self.y > threat.y: flee_dy = 1

            if flee_dx == 0 and flee_dy == 0:
                 flee_dx = random.choice([-1,1]) if board.is_valid_position(self.x-1, self.y) or board.is_valid_position(self.x+1, self.y) else 0
                 flee_dy = random.choice([-1,1]) if board.is_valid_position(self.x, self.y-1) or board.is_valid_position(self.x, self.y+1) else 0
                 if flee_dx == 0 and flee_dy == 0:
                     available = board.get_available_moves(self.x, self.y)
                     if available:
                         panic_pos = random.choice(available)
                         flee_dx = panic_pos.x - self.x
                         flee_dy = panic_pos.y - self.y

            # print(f"DEBUG Scavenger._flee_from_threats: id={id(self)} attempting to move with dx={flee_dx}, dy={flee_dy}") #DEBUG
            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                # print(f"DEBUG Scavenger._flee_from_threats: id={id(self)} initial flee dx={flee_dx}, dy={flee_dy} failed. Trying cardinal.") #DEBUG
                if flee_dx != 0 and self.move(flee_dx, 0, board): moved = True
                elif flee_dy != 0 and self.move(0, flee_dy, board): moved = True
            
            if moved:
                flee_cost = 2
                if self.config:
                    temp_cost = self.config.get("units", "energy_consumption.move_flee")
                    if temp_cost is not None: flee_cost = temp_cost
                self.energy -= flee_cost
                self.gain_experience("fleeing")
            # else: # DEBUG
                # print(f"DEBUG Scavenger._flee_from_threats: id={id(self)} failed to make any flee move.") #DEBUG

class Grazer(Unit):
    """
    A grazer unit that primarily consumes plants.
    Grazers are peaceful units with high energy capacity but low strength.
    They avoid combat and focus on finding and consuming plants.
    """
    def __init__(self, x, y, hp=None, config=None):
        super().__init__(x, y, unit_type="grazer", hp=hp, energy=130, strength=5, speed=1, vision=5, config=config)
        self.exploration_moves = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        self.next_exploration_move_index = 0
    
    def update(self, board):
        super().update(board)
        if not self.alive:
            return
        
        visible_units_data = self.look(board) # Use self.look()
        threats = [item[0] for item in visible_units_data if isinstance(item[0], Predator) and item[0].alive]
        
        if threats:
            self.state = "fleeing"
            # print(f"DEBUG Grazer.update: id={id(self)} state changed to fleeing due to threats.") #DEBUG
            self._flee_from_threats(board, threats) # Pass threats to avoid re-calculating
        elif self.energy < self.max_energy * 0.4: # Adjusted threshold for consistency
            self.state = "hungry"
            # print(f"DEBUG Grazer.update: id={id(self)} state changed to hungry.") #DEBUG
            self._find_food(board)
        else:
            self.state = "grazing" # Default state if not fleeing or hungry
            self._graze(board)

    def _graze(self, board):
        """Wander to find and consume plants."""
        # print(f"DEBUG Grazer._graze: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, base_speed={self.base_speed}, state={self.state}") #DEBUG
        visible_plants_data = self.look(board) # self.look() returns list of (obj,x,y)
        plants = [item[0] for item in visible_plants_data if isinstance(item[0], Plant)]

        if plants:
            target = min(plants, key=lambda p: ((p.position.x - self.x)**2 + (p.position.y - self.y)**2)**0.5)
            if abs(target.position.x - self.x) <= 1 and abs(target.position.y - self.y) <= 1:
                if self.eat(target):
                    self.gain_experience("feeding")
            else:
                move_dx = 1 if target.position.x > self.x else (-1 if target.position.x < self.x else 0)
                move_dy = 1 if target.position.y > self.y else (-1 if target.position.y < self.y else 0)
                # print(f"DEBUG Grazer._graze: id={id(self)} attempting move towards plant with dx={move_dx}, dy={move_dy}") #DEBUG
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    # print(f"DEBUG Grazer._graze: id={id(self)} initial move dx={move_dx}, dy={move_dy} failed. Trying cardinal components.") #DEBUG
                    if move_dx != 0 and self.move(move_dx, 0, board):
                        moved = True
                        # print(f"DEBUG Grazer._graze: id={id(self)} cardinal move dx={move_dx}, dy=0 succeeded.") #DEBUG
                    elif move_dy != 0 and self.move(0, move_dy, board):
                        moved = True
                        # print(f"DEBUG Grazer._graze: id={id(self)} cardinal move dx=0, dy={move_dy} succeeded.") #DEBUG
                if moved:
                    self.energy -= 1
                    self.gain_experience("feeding", 0.2)
        else:
            explore_dx, explore_dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            # print(f"DEBUG Grazer._graze: id={id(self)} attempting random exploration move dx={explore_dx}, dy={explore_dy}") #DEBUG
            if self.move(explore_dx, explore_dy, board):
                self.energy -= 1

    def _find_food(self, board):
        """Find closest plant when hungry."""
        # print(f"DEBUG Grazer._find_food: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, base_speed={self.base_speed}, state={self.state}") #DEBUG
        visible_plants_data = self.look(board)
        plants = [item[0] for item in visible_plants_data if isinstance(item[0], Plant)]
        
        if plants:
            target = min(plants, key=lambda p: ((p.position.x - self.x)**2 + (p.position.y - self.y)**2)**0.5)
            if abs(target.position.x - self.x) <= 1 and abs(target.position.y - self.y) <= 1:
                if self.eat(target):
                    self.gain_experience("feeding")
            else:
                move_dx = 1 if target.position.x > self.x else (-1 if target.position.x < self.x else 0)
                move_dy = 1 if target.position.y > self.y else (-1 if target.position.y < self.y else 0)
                # print(f"DEBUG Grazer._find_food: id={id(self)} attempting move towards plant with dx={move_dx}, dy={move_dy}") #DEBUG
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    # print(f"DEBUG Grazer._find_food: id={id(self)} initial move dx={move_dx}, dy={move_dy} failed. Trying cardinal components.") #DEBUG
                    if move_dx != 0 and self.move(move_dx, 0, board):
                        moved = True
                        # print(f"DEBUG Grazer._find_food: id={id(self)} cardinal move dx={move_dx}, dy=0 succeeded.") #DEBUG
                    elif move_dy != 0 and self.move(0, move_dy, board):
                        moved = True
                        # print(f"DEBUG Grazer._find_food: id={id(self)} cardinal move dx=0, dy={move_dy} succeeded.") #DEBUG
                if moved:
                    self.energy -= 1
        # No random move here, default to wandering/grazing if no specific food found by this targeted method

    def _flee_from_threats(self, board, threats): # Accept threats to avoid re-calculating
        """Move away from predators."""
        # print(f"DEBUG Grazer._flee_from_threats: id={id(self)}, x={self.x}, y={self.y}, speed={self.speed}, base_speed={self.base_speed}, state={self.state}") #DEBUG
        if threats: # threats is now passed in
            threat = min(threats, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            flee_dx = 0
            if self.x < threat.x: flee_dx = -1
            elif self.x > threat.x: flee_dx = 1
            flee_dy = 0
            if self.y < threat.y: flee_dy = -1
            elif self.y > threat.y: flee_dy = 1
            
            if flee_dx == 0 and flee_dy == 0: # Fallback if on same spot or calculation error
                 flee_dx = random.choice([-1,1]) if board.is_valid_position(self.x-1, self.y) or board.is_valid_position(self.x+1, self.y) else 0
                 flee_dy = random.choice([-1,1]) if board.is_valid_position(self.x, self.y-1) or board.is_valid_position(self.x, self.y+1) else 0
                 if flee_dx == 0 and flee_dy == 0:
                     available = board.get_available_moves(self.x, self.y)
                     if available:
                         panic_pos = random.choice(available)
                         flee_dx = panic_pos.x - self.x
                         flee_dy = panic_pos.y - self.y
            
            # print(f"DEBUG Grazer._flee_from_threats: id={id(self)} attempting to move with dx={flee_dx}, dy={flee_dy}") #DEBUG
            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                # print(f"DEBUG Grazer._flee_from_threats: id={id(self)} diagonal flee dx={flee_dx}, dy={flee_dy} failed. Trying cardinal.") #DEBUG
                if flee_dx != 0 and self.move(flee_dx, 0, board):
                    moved = True
                    # print(f"DEBUG Grazer._flee_from_threats: id={id(self)} cardinal flee dx={flee_dx}, dy=0 succeeded.") #DEBUG
                elif flee_dy != 0 and self.move(0, flee_dy, board): # Use elif to avoid second move if first cardinal succeeded
                    moved = True
                    # print(f"DEBUG Grazer._flee_from_threats: id={id(self)} cardinal flee dx=0, dy={flee_dy} succeeded.") #DEBUG
            
            if moved:
                self.energy -= 2
                self.gain_experience("fleeing")
            # else: # DEBUG
                # print(f"DEBUG Grazer._flee_from_threats: id={id(self)} failed to make any flee move.") #DEBUG
                pass
