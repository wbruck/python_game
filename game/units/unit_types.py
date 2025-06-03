"""
Unit Types module for the ecosystem simulation game.

This module implements various unit types that inherit from the base Unit class,
each with specialized behaviors and characteristics.
"""

import random # Ensure random is imported for Scavenger fallback
from game.units.base_unit import Unit
from game.plants.base_plant import Plant # For Scavenger._find_food
from typing import Optional, Tuple

class Predator(Unit):
    """
    A predator unit that actively hunts other units.
    
    Predators have high strength and speed, making them effective hunters.
    They primarily target other units for food rather than plants.
    """
    
    def __init__(self, x, y, hp=None, config=None, board=None):
        """
        Initialize a new predator unit.
        
        Args:
            x (int): Initial x-coordinate on the board.
            y (int): Initial y-coordinate on the board.
            hp (int, optional): Health points. Defaults to template value.
        """
        super().__init__(x, y, unit_type="predator", hp=hp, energy=80, strength=15, speed=2, vision=6, config=config, board=board)
        self.target = None
        if self.config:
            self.energy_cost_move_hunt = self.config.get("units", "energy_consumption.move_hunt")
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_hunt') or self.energy_cost_move_hunt is None:
            self.energy_cost_move_hunt = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            self.energy_cost_move_flee = self.energy_cost_move + 1

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
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)
        
        potential_prey = [obj for obj, x, y in visible_objects if isinstance(obj, (Grazer, Scavenger)) and obj.alive]

        # 1. Immediate Action: Attack adjacent prey
        if potential_prey:
            for prey in potential_prey:
                if abs(prey.x - self.x) <= 1 and abs(prey.y - self.y) <= 1: # Adjacent
                    energy_before_attack = self.energy
                    damage_dealt = self.attack(prey)
                    if damage_dealt > 0 : # Successful attack
                        self.state = "combat"
                        self.gain_experience("combat")
                        if not prey.alive:
                            self.gain_experience("hunting")
                            self.eat(prey) # Attempt to eat immediately
                        return # Action taken (attacked)

        # 2. Score moves to hunt prey if no immediate attack was made
        if potential_prey and possible_moves:
            closest_prey = min(potential_prey, key=lambda p: abs(p.x - self.x) + abs(p.y - self.y))
            
            scored_moves = []
            current_dist_to_prey = abs(closest_prey.x - self.x) + abs(closest_prey.y - self.y)

            for move_x, move_y in possible_moves:
                dist_after_move = abs(closest_prey.x - move_x) + abs(closest_prey.y - move_y)
                score = current_dist_to_prey - dist_after_move # Higher score if move reduces distance
                scored_moves.append((score, (move_x, move_y)))
            
            if scored_moves:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
                if scored_moves[0][0] > 0: # Only move if it's beneficial
                    best_move_coords = scored_moves[0][1]
                    dx = best_move_coords[0] - self.x
                    dy = best_move_coords[1] - self.y
                    if self.move(dx, dy, board):
                        self.energy -= self.energy_cost_move_hunt
                        self.gain_experience("hunting", 0.5)
                    return # Action taken (moved to hunt)

        # 3. Fallback: Exploration if no prey to hunt or no good move
        exploration_move = self._get_exploration_move()
        if exploration_move:
            explore_target_x, explore_target_y = exploration_move
            # Check if this exploration target is in our possible_moves
            if (explore_target_x, explore_target_y) in possible_moves:
                dx = explore_target_x - self.x
                dy = explore_target_y - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move # Standard move cost for exploration
            # If exploration target is not an immediate move, try to find a move towards it
            elif possible_moves: # Try to move towards exploration target
                scored_exploration_moves = []
                current_dist_to_explore_target = abs(explore_target_x - self.x) + abs(explore_target_y - self.y)
                for move_x, move_y in possible_moves:
                    dist_after_move = abs(explore_target_x - move_x) + abs(explore_target_y - move_y)
                    score = current_dist_to_explore_target - dist_after_move
                    scored_exploration_moves.append((score, (move_x, move_y)))

                if scored_exploration_moves:
                    scored_exploration_moves.sort(key=lambda x: x[0], reverse=True)
                    if scored_exploration_moves[0][0] >= 0: # Allow neutral moves for exploration
                        best_move_coords = scored_exploration_moves[0][1]
                        dx = best_move_coords[0] - self.x
                        dy = best_move_coords[1] - self.y
                        if self.move(dx, dy, board):
                            self.energy -= self.energy_cost_move


    def _find_closest_food(self, board):
        """Find and move toward the closest food source (typically dead units for Predator)."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)

        food_sources = [obj for obj, x, y in visible_objects if not obj.alive and hasattr(obj, 'decay_stage') and obj.decay_stage < 3]

        # 1. Immediate Action: Eat adjacent food
        if food_sources:
            for food in food_sources:
                if abs(food.x - self.x) <= 1 and abs(food.y - self.y) <= 1: # Adjacent
                    if self.eat(food):
                        self.gain_experience("feeding")
                    return # Action taken (ate or tried to eat)

        # 2. Score moves to reach food
        if food_sources and possible_moves:
            closest_food = min(food_sources, key=lambda f: abs(f.x - self.x) + abs(f.y - self.y))
            scored_moves = []
            current_dist_to_food = abs(closest_food.x - self.x) + abs(closest_food.y - self.y)

            for move_x, move_y in possible_moves:
                dist_after_move = abs(closest_food.x - move_x) + abs(closest_food.y - move_y)
                score = current_dist_to_food - dist_after_move
                scored_moves.append((score, (move_x, move_y)))

            if scored_moves:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
                if scored_moves[0][0] > 0:
                    best_move_coords = scored_moves[0][1]
                    dx = best_move_coords[0] - self.x
                    dy = best_move_coords[1] - self.y
                    if self.move(dx, dy, board):
                        self.energy -= self.energy_cost_move # Standard move cost
                    return # Action taken (moved to food)

        # 3. Fallback: Exploration if no food or no good move
        exploration_move = self._get_exploration_move()
        if exploration_move:
            explore_target_x, explore_target_y = exploration_move
            if (explore_target_x, explore_target_y) in possible_moves:
                dx = explore_target_x - self.x
                dy = explore_target_y - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move
            elif possible_moves: # Try to move towards exploration target
                scored_exploration_moves = []
                current_dist_to_explore_target = abs(explore_target_x - self.x) + abs(explore_target_y - self.y)
                for move_x, move_y in possible_moves:
                    dist_after_move = abs(explore_target_x - move_x) + abs(explore_target_y - move_y)
                    score = current_dist_to_explore_target - dist_after_move
                    scored_exploration_moves.append((score, (move_x, move_y)))

                if scored_exploration_moves:
                    scored_exploration_moves.sort(key=lambda x: x[0], reverse=True)
                    if scored_exploration_moves[0][0] >= 0:
                        best_move_coords = scored_exploration_moves[0][1]
                        dx = best_move_coords[0] - self.x
                        dy = best_move_coords[1] - self.y
                        if self.move(dx, dy, board):
                            self.energy -= self.energy_cost_move

    def _flee_from_threats(self, board):
        """Predator flees from other (presumably stronger) Predators."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)
        
        threats = [obj for obj, x, y in visible_objects if isinstance(obj, Predator) and obj != self and obj.alive]

        if not threats:
            return # No threats to flee from

        if not possible_moves:
            return # Nowhere to flee

        closest_threat = min(threats, key=lambda t: abs(t.x - self.x) + abs(t.y - self.y))
        scored_moves = []
        current_dist_to_threat = abs(closest_threat.x - self.x) + abs(closest_threat.y - self.y)

        for move_x, move_y in possible_moves:
            dist_after_move = abs(closest_threat.x - move_x) + abs(closest_threat.y - move_y)
            # Score is how much distance is increased. Negative score means closer to threat.
            score = dist_after_move - current_dist_to_threat
            scored_moves.append((score, (move_x, move_y)))

        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            # Prefer any move that increases distance, or at least doesn't decrease it if cornered
            if scored_moves[0][0] >= 0:
                best_move_coords = scored_moves[0][1]
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")
            else: # If all moves lead closer or are neutral but bad, pick the "least bad" or random
                # For now, pick the one that gets us "least closer" or a random one if multiple equally bad.
                # Or, if all scores are negative, could pick a random move from possible_moves.
                # Let's just pick the top one from sorted list, even if score is negative.
                best_move_coords = scored_moves[0][1]
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")
        # If no scored_moves (e.g. possible_moves was empty, though checked above), do nothing.

class Scavenger(Unit):
    """
    A scavenger unit that specializes in finding and consuming dead units.
    Scavengers have enhanced vision and can detect dead units from farther away.
    They're not as strong as predators but are more efficient at extracting energy from corpses.
    """
    def __init__(self, x, y, hp=None, config=None, board=None):
        super().__init__(x, y, unit_type="scavenger", hp=hp, energy=110, strength=8, speed=1, vision=8, config=config, board=board)
        if self.config:
            self.energy_cost_move_scavenge = self.config.get("units", "energy_consumption.move_graze")
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_scavenge') or self.energy_cost_move_scavenge is None:
            self.energy_cost_move_scavenge = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            self.energy_cost_move_flee = self.energy_cost_move + 1

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
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)
        
        corpses = [obj for obj, x, y in visible_objects if not obj.alive and hasattr(obj, 'decay_stage') and obj.decay_stage < 4]

        # 1. Immediate Action: Eat adjacent corpse
        if corpses:
            for corpse in corpses:
                if abs(corpse.x - self.x) <= 1 and abs(corpse.y - self.y) <= 1:
                    if self.eat(corpse):
                        self.gain_experience("feeding") # Scavengers gain exp for eating corpses
                    return # Action taken

        # 2. Score moves to reach corpses
        if corpses and possible_moves:
            target_corpse = min(corpses, key=lambda c: abs(c.x - self.x) + abs(c.y - self.y))
            scored_moves = []
            current_dist_to_corpse = abs(target_corpse.x - self.x) + abs(target_corpse.y - self.y)

            for move_x, move_y in possible_moves:
                dist_after_move = abs(target_corpse.x - move_x) + abs(target_corpse.y - move_y)
                score = current_dist_to_corpse - dist_after_move
                scored_moves.append((score, (move_x, move_y)))

            if scored_moves:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
                if scored_moves[0][0] > 0:
                    best_move_coords = scored_moves[0][1]
                    dx = best_move_coords[0] - self.x
                    dy = best_move_coords[1] - self.y
                    if self.move(dx, dy, board):
                        self.energy -= self.energy_cost_move_scavenge
                        self.gain_experience("hunting", 0.2) # Keep original exp gain for scavenging move
                    return

        # 3. Fallback: Exploration
        exploration_move = self._get_exploration_move()
        if exploration_move:
            explore_target_x, explore_target_y = exploration_move
            if (explore_target_x, explore_target_y) in possible_moves:
                dx = explore_target_x - self.x
                dy = explore_target_y - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_scavenge
            elif possible_moves: # Try to move towards exploration target
                scored_exploration_moves = []
                current_dist_to_explore_target = abs(explore_target_x - self.x) + abs(explore_target_y - self.y)
                for move_x, move_y in possible_moves:
                    dist_after_move = abs(explore_target_x - move_x) + abs(explore_target_y - move_y)
                    score = current_dist_to_explore_target - dist_after_move
                    scored_exploration_moves.append((score, (move_x, move_y)))

                if scored_exploration_moves:
                    scored_exploration_moves.sort(key=lambda x: x[0], reverse=True)
                    if scored_exploration_moves[0][0] >= 0:
                        best_move_coords = scored_exploration_moves[0][1]
                        dx = best_move_coords[0] - self.x
                        dy = best_move_coords[1] - self.y
                        if self.move(dx, dy, board):
                            self.energy -= self.energy_cost_move_scavenge


    def _find_food(self, board):
        """Find any food source when hungry (corpses or plants for Scavenger)."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)
        
        food_sources = [obj for obj, x, y in visible_objects if (not obj.alive and hasattr(obj, 'decay_stage')) or isinstance(obj, Plant)]

        # 1. Immediate Action: Eat adjacent food
        if food_sources:
            for food in food_sources:
                food_x = food.x if not isinstance(food, Plant) else food.position.x
                food_y = food.y if not isinstance(food, Plant) else food.position.y
                if abs(food_x - self.x) <= 1 and abs(food_y - self.y) <= 1:
                    if self.eat(food):
                        self.gain_experience("feeding")
                    return # Action taken

        # 2. Score moves to reach food
        if food_sources and possible_moves:
            target_food = min(food_sources, key=lambda f: abs((f.x if not isinstance(f, Plant) else f.position.x) - self.x) + \
                                                         abs((f.y if not isinstance(f, Plant) else f.position.y) - self.y))
            target_x = target_food.x if not isinstance(target_food, Plant) else target_food.position.x
            target_y = target_food.y if not isinstance(target_food, Plant) else target_food.position.y

            scored_moves = []
            current_dist_to_food = abs(target_x - self.x) + abs(target_y - self.y)

            for move_x, move_y in possible_moves:
                dist_after_move = abs(target_x - move_x) + abs(target_y - move_y)
                score = current_dist_to_food - dist_after_move
                scored_moves.append((score, (move_x, move_y)))

            if scored_moves:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
                if scored_moves[0][0] > 0:
                    best_move_coords = scored_moves[0][1]
                    dx = best_move_coords[0] - self.x
                    dy = best_move_coords[1] - self.y
                    if self.move(dx, dy, board):
                        self.energy -= self.energy_cost_move_scavenge
                    return

        # 3. Fallback: Exploration
        exploration_move = self._get_exploration_move()
        if exploration_move:
            explore_target_x, explore_target_y = exploration_move
            if (explore_target_x, explore_target_y) in possible_moves:
                dx = explore_target_x - self.x
                dy = explore_target_y - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_scavenge
            elif possible_moves:
                scored_exploration_moves = []
                current_dist_to_explore_target = abs(explore_target_x - self.x) + abs(explore_target_y - self.y)
                for move_x, move_y in possible_moves:
                    dist_after_move = abs(explore_target_x - move_x) + abs(explore_target_y - move_y)
                    score = current_dist_to_explore_target - dist_after_move
                    scored_exploration_moves.append((score, (move_x, move_y)))

                if scored_exploration_moves:
                    scored_exploration_moves.sort(key=lambda x: x[0], reverse=True)
                    if scored_exploration_moves[0][0] >= 0:
                        best_move_coords = scored_exploration_moves[0][1]
                        dx = best_move_coords[0] - self.x
                        dy = best_move_coords[1] - self.y
                        if self.move(dx, dy, board):
                            self.energy -= self.energy_cost_move_scavenge


    def _flee_from_threats(self, board):
        """Scavenger flees from Predators."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)
        
        threats = [obj for obj, x, y in visible_objects if isinstance(obj, Predator) and obj.alive] # Scavenger flees any live Predator

        if not threats:
            return

        if not possible_moves:
            return

        closest_threat = min(threats, key=lambda t: abs(t.x - self.x) + abs(t.y - self.y))
        scored_moves = []
        current_dist_to_threat = abs(closest_threat.x - self.x) + abs(closest_threat.y - self.y)

        for move_x, move_y in possible_moves:
            dist_after_move = abs(closest_threat.x - move_x) + abs(closest_threat.y - move_y)
            score = dist_after_move - current_dist_to_threat
            scored_moves.append((score, (move_x, move_y)))
            
        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            if scored_moves[0][0] >= 0 : # Prioritize moves that increase or maintain distance
                best_move_coords = scored_moves[0][1]
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")
            else: # All moves lead closer, pick the one that leads "least closer" or a random one
                # Fallback to random valid move if all scores are negative (truly cornered)
                # For now, using the "least bad" move.
                best_move_coords = scored_moves[0][1] # Best of the bad options
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")
        # If no scored_moves (e.g. possible_moves was empty), do nothing.

class Grazer(Unit):
    """
    A grazer unit that primarily consumes plants.
    Grazers are peaceful units with high energy capacity but low strength.
    They avoid combat and focus on finding and consuming plants.
    """
    def __init__(self, x, y, hp=None, config=None, board=None):
        super().__init__(x, y, unit_type="grazer", hp=hp, energy=130, strength=5, speed=1, vision=5, config=config, board=board)
        if self.config:
            self.energy_cost_move_graze = self.config.get("units", "energy_consumption.move_graze")
            self.energy_cost_move_flee = self.config.get("units", "energy_consumption.move_flee")

        if not hasattr(self, 'energy_cost_move_graze') or self.energy_cost_move_graze is None:
            self.energy_cost_move_graze = self.energy_cost_move
        if not hasattr(self, 'energy_cost_move_flee') or self.energy_cost_move_flee is None:
            self.energy_cost_move_flee = self.energy_cost_move + 1 # Default flee cost
            
    def update(self, board):
        super().update(board)
        if not self.alive or self.state == "resting": # Added resting check from Predator
            return

        # Grazer's primary concern is threats. Get visible objects once.
        # No, get_potential_moves_in_vision_range should be called by specific action methods
        # because vision range might change based on state (e.g. hunting, fleeing)
        # For Grazer, fleeing is top priority.

        # Check for threats first.
        # To do this efficiently, we need visible objects.
        # We can call get_potential_moves_in_vision_range once here if vision doesn't change for fleeing vs grazing.
        # Or, _flee_from_threats handles its own vision scan.
        # Let's assume _flee_from_threats will get its own scan for now.
        
        # The original Grazer logic called self.look() then decided state.
        # We need to adapt this. Let's get visible objects once for state decisions.
        _, visible_objects_for_state_decision = self.get_potential_moves_in_vision_range(board)
        threats_for_state_decision = [obj for obj, x, y in visible_objects_for_state_decision if isinstance(obj, Predator) and obj.alive]

        if threats_for_state_decision:
            self.state = "fleeing"
            self._flee_from_threats(board, threats_for_state_decision) # Pass identified threats
        elif self.energy < self.max_energy * 0.4:
            self.state = "hungry" # Or searching_food
            self._find_food(board) # This method will find plants
        else:
            self.state = "grazing"
            self._graze(board) # This method will find plants


    def _graze(self, board): # Similar to _find_food but for non-hungry state
        """Wander to find and consume plants."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)

        plants = [obj for obj, x, y in visible_objects if isinstance(obj, Plant) and obj.state.is_alive and obj.state.energy_content > 0]

        # 1. Immediate Action: Eat adjacent plant
        if plants:
            for plant in plants:
                if abs(plant.position.x - self.x) <= 1 and abs(plant.position.y - self.y) <= 1:
                    if self.eat(plant):
                        self.gain_experience("feeding")
                    return # Action taken

        # 2. Score moves to reach plants
        if plants and possible_moves:
            target_plant = min(plants, key=lambda p: abs(p.position.x - self.x) + abs(p.position.y - self.y))
            scored_moves = []
            current_dist_to_plant = abs(target_plant.position.x - self.x) + abs(target_plant.position.y - self.y)

            for move_x, move_y in possible_moves:
                dist_after_move = abs(target_plant.position.x - move_x) + abs(target_plant.position.y - move_y)
                score = current_dist_to_plant - dist_after_move
                scored_moves.append((score, (move_x, move_y)))

            if scored_moves:
                scored_moves.sort(key=lambda x: x[0], reverse=True)
                if scored_moves[0][0] > 0:
                    best_move_coords = scored_moves[0][1]
                    dx = best_move_coords[0] - self.x
                    dy = best_move_coords[1] - self.y
                    if self.move(dx, dy, board):
                        self.energy -= self.energy_cost_move_graze
                        self.gain_experience("feeding", 0.2) # Original exp for moving to graze
                    return

        # 3. Fallback: Exploration
        exploration_move = self._get_exploration_move()
        if exploration_move:
            explore_target_x, explore_target_y = exploration_move
            if (explore_target_x, explore_target_y) in possible_moves:
                dx = explore_target_x - self.x
                dy = explore_target_y - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_graze
            elif possible_moves:
                scored_exploration_moves = []
                current_dist_to_explore_target = abs(explore_target_x - self.x) + abs(explore_target_y - self.y)
                for move_x, move_y in possible_moves:
                    dist_after_move = abs(explore_target_x - move_x) + abs(explore_target_y - move_y)
                    score = current_dist_to_explore_target - dist_after_move
                    scored_exploration_moves.append((score, (move_x, move_y)))

                if scored_exploration_moves:
                    scored_exploration_moves.sort(key=lambda x: x[0], reverse=True)
                    if scored_exploration_moves[0][0] >= 0:
                        best_move_coords = scored_exploration_moves[0][1]
                        dx = best_move_coords[0] - self.x
                        dy = best_move_coords[1] - self.y
                        if self.move(dx, dy, board):
                            self.energy -= self.energy_cost_move_graze


    def _find_food(self, board): # Specifically for when hungry
        """Find closest plant when hungry."""
        # This is essentially the same logic as _graze for Grazer
        self._graze(board)


    def _flee_from_threats(self, board, threats_identified_in_update):
        """Move away from predators. Threats are passed from update() method."""
        possible_moves, visible_objects = self.get_potential_moves_in_vision_range(board)

        # Use threats passed from update method if available and still relevant,
        # otherwise, can re-scan from visible_objects if needed (e.g. if state changed vision)
        # For now, directly use threats_identified_in_update
        threats = threats_identified_in_update

        if not threats:
             # As a fallback, if threats_identified_in_update is empty (e.g. called directly), re-scan
            threats = [obj for obj, x, y in visible_objects if isinstance(obj, Predator) and obj.alive]
            if not threats:
                return # No threats to flee from

        if not possible_moves:
            return # Nowhere to flee

        closest_threat = min(threats, key=lambda t: abs(t.x - self.x) + abs(t.y - self.y))
        scored_moves = []
        current_dist_to_threat = abs(closest_threat.x - self.x) + abs(closest_threat.y - self.y)

        for move_x, move_y in possible_moves:
            dist_after_move = abs(closest_threat.x - move_x) + abs(closest_threat.y - move_y)
            score = dist_after_move - current_dist_to_threat
            scored_moves.append((score, (move_x, move_y)))
            
        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            if scored_moves[0][0] >= 0:
                best_move_coords = scored_moves[0][1]
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")
            else: # All moves are bad, pick the "least bad"
                best_move_coords = scored_moves[0][1]
                dx = best_move_coords[0] - self.x
                dy = best_move_coords[1] - self.y
                if self.move(dx, dy, board):
                    self.energy -= self.energy_cost_move_flee
                    self.gain_experience("fleeing")

# Dictionary mapping unit type names to their classes
UNIT_TYPES = {
    "predator": Predator,
    "scavenger": Scavenger,
    "grazer": Grazer
}
