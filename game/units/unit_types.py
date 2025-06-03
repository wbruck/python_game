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
        if self.config:
            self.energy_cost_move_hunt = self.config.get("units", "energy_consumption.move_hunt")
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_hunt') or self.energy_cost_move_hunt is None:
            # Fallback to general move cost if specific hunt cost is not found or if config is None
            self.energy_cost_move_hunt = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            # Fallback for flee cost, potentially higher than normal move
            self.energy_cost_move_flee = self.energy_cost_move + 1

        self.exploration_moves = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        self.next_exploration_move_index = 0

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

        potential_prey = [u for u in visible_units if isinstance(u, (Grazer, Scavenger)) and u.alive]
        
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
                moved = self.move(dx, dy, board)
                if not moved and (dx != 0 or dy != 0):
                    cardinal_dx = 0 if target.x == self.x else (1 if target.x > self.x else -1)
                    cardinal_dy = 0 if target.y == self.y else (1 if target.y > self.y else -1)
                    if cardinal_dx != 0 and self.move(cardinal_dx, 0, board):
                        moved = True
                    elif cardinal_dy != 0 and self.move(0, cardinal_dy, board):
                        moved = True

                if moved:
                    self.energy -= self.energy_cost_move_hunt
                    self.gain_experience("hunting", 0.5)

    def _find_closest_food(self, board):
        """Find and move toward the closest food source (typically dead units for Predator)."""
        visible_objects_data = self.look(board)
        food_sources = [item[0] for item in visible_objects_data if hasattr(item[0], 'alive') and not item[0].alive and hasattr(item[0], 'decay_stage') and item[0].decay_stage < 3]

        if food_sources:
            target = min(food_sources, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self.eat(target)
            else:
                move_dx = 1 if target.x > self.x else (-1 if target.x < self.x else 0)
                move_dy = 1 if target.y > self.y else (-1 if target.y < self.y else 0)
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    if move_dx != 0 and self.move(move_dx, 0, board): moved = True
                    elif move_dy != 0 and self.move(0, move_dy, board): moved = True

                if moved:
                    # Foraging for food when hungry might use the base move cost or a specific graze/scavenge cost
                    # For Predator, it's likely still a general move or a less intensive hunt move
                    self.energy -= self.energy_cost_move
        else:
            # No dead units visible, perform an exploration move
            explore_dx, explore_dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            if self.move(explore_dx, explore_dy, board):
                self.energy -= self.energy_cost_move # Use general move cost for exploration

    def _flee_from_threats(self, board):
        """Predator flees from other (presumably stronger) Predators."""
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

            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                if flee_dx != 0 and self.move(flee_dx, 0, board): moved = True
                elif flee_dy != 0 and self.move(0, flee_dy, board): moved = True

            if moved:
                self.energy -= self.energy_cost_move_flee
                self.gain_experience("fleeing")

class Scavenger(Unit):
    """
    A scavenger unit that specializes in finding and consuming dead units.
    Scavengers have enhanced vision and can detect dead units from farther away.
    They're not as strong as predators but are more efficient at extracting energy from corpses.
    """
    def __init__(self, x, y, hp=None, config=None):
        super().__init__(x, y, unit_type="scavenger", hp=hp, energy=110, strength=8, speed=1, vision=8, config=config)
        if self.config:
            # Scavengers might have specific costs for scavenging movement or fleeing
            self.energy_cost_move_scavenge = self.config.get("units", "energy_consumption.move_graze") # Using move_graze as a proxy
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_scavenge') or self.energy_cost_move_scavenge is None:
            self.energy_cost_move_scavenge = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            self.energy_cost_move_flee = self.energy_cost_move + 1

        self.exploration_moves = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
        self.next_exploration_move_index = 0

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
        visible_objects_data = self.look(board)
        corpses = [item[0] for item in visible_objects_data if hasattr(item[0], 'alive') and not item[0].alive and hasattr(item[0], 'decay_stage') and item[0].decay_stage < 4]
        
        if corpses:
            target = min(corpses, key=lambda u: ((u.x - self.x)**2 + (u.y - self.y)**2)**0.5)
            if abs(target.x - self.x) <= 1 and abs(target.y - self.y) <= 1:
                self.eat(target)
            else:
                move_dx = 1 if target.x > self.x else (-1 if target.x < self.x else 0)
                move_dy = 1 if target.y > self.y else (-1 if target.y < self.y else 0)
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    if move_dx != 0:
                        if self.move(move_dx, 0, board):
                            moved = True
                    if not moved and move_dy != 0:
                        if self.move(0, move_dy, board):
                            moved = True

                if moved:
                    self.energy -= self.energy_cost_move_scavenge
                    self.gain_experience("hunting", 0.2)

    def _find_food(self, board):
        """Find any food source when hungry."""
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
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    if move_dx != 0:
                        if self.move(move_dx, 0, board):
                            moved = True
                    if not moved and move_dy != 0:
                        if self.move(0, move_dy, board):
                            moved = True

                if moved:
                    self.energy -= self.energy_cost_move_scavenge
        else:
            # No food sources visible, perform an exploration move
            explore_dx, explore_dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            if self.move(explore_dx, explore_dy, board):
                # energy_cost_move_scavenge has a fallback to energy_cost_move in __init__
                self.energy -= self.energy_cost_move_scavenge

    def _flee_from_threats(self, board):
        """Scavenger flees from Predators."""
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

            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                if flee_dx != 0 and self.move(flee_dx, 0, board): moved = True
                elif flee_dy != 0 and self.move(0, flee_dy, board): moved = True
            
            if moved:
                self.energy -= self.energy_cost_move_flee
                self.gain_experience("fleeing")

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
        if self.config:
            self.energy_cost_move_graze = self.config.get("units", "energy_consumption.move_graze")
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_graze') or self.energy_cost_move_graze is None:
            self.energy_cost_move_graze = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            self.energy_cost_move_flee = self.energy_cost_move + 1 # Default flee cost

    def update(self, board):
        super().update(board)
        if not self.alive:
            return
        
        visible_units_data = self.look(board) # Use self.look()
        threats = [item[0] for item in visible_units_data if isinstance(item[0], Predator) and item[0].alive]
        
        if threats:
            self.state = "fleeing"
            self._flee_from_threats(board, threats) # Pass threats to avoid re-calculating
        elif self.energy < self.max_energy * 0.4: # Adjusted threshold for consistency
            self.state = "hungry"
            self._find_food(board)
        else:
            self.state = "grazing" # Default state if not fleeing or hungry
            self._graze(board)

    def _graze(self, board):
        """Wander to find and consume plants."""
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
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    if move_dx != 0 and self.move(move_dx, 0, board):
                        moved = True
                    elif move_dy != 0 and self.move(0, move_dy, board):
                        moved = True
                if moved:
                    self.energy -= self.energy_cost_move_graze
                    self.gain_experience("feeding", 0.2)
        else:
            explore_dx, explore_dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            if self.move(explore_dx, explore_dy, board):
                self.energy -= self.energy_cost_move_graze # Use graze cost for exploration

    def _find_food(self, board):
        """Find closest plant when hungry."""
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
                moved = self.move(move_dx, move_dy, board)
                if not moved and (move_dx != 0 or move_dy != 0):
                    if move_dx != 0 and self.move(move_dx, 0, board):
                        moved = True
                    elif move_dy != 0 and self.move(0, move_dy, board):
                        moved = True

                if moved:
                    self.energy -= self.energy_cost_move_graze # Use graze cost when actively finding food
        else:
            # No plants visible, perform an exploration move
            explore_dx, explore_dy = self.exploration_moves[self.next_exploration_move_index]
            self.next_exploration_move_index = (self.next_exploration_move_index + 1) % len(self.exploration_moves)
            if self.move(explore_dx, explore_dy, board):
                self.energy -= self.energy_cost_move_graze # Use graze cost for exploration

    def _flee_from_threats(self, board, threats): # Accept threats to avoid re-calculating
        """Move away from predators."""
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
            
            moved = self.move(flee_dx, flee_dy, board)
            if not moved and (flee_dx != 0 or flee_dy != 0):
                if flee_dx != 0 and self.move(flee_dx, 0, board):
                    moved = True
                elif flee_dy != 0 and self.move(0, flee_dy, board): # Use elif to avoid second move if first cardinal succeeded
                    moved = True
            
            if moved:
                self.energy -= self.energy_cost_move_flee
                self.gain_experience("fleeing")
                pass

# Dictionary mapping unit type names to their classes
UNIT_TYPES = {
    "predator": Predator,
    "scavenger": Scavenger,
    "grazer": Grazer
}
