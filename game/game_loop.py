"""
Game Loop module for the ecosystem simulation game.

This module implements the main game loop that manages turn-based progression
and orchestrates unit actions, plant growth, environmental cycles, and other game mechanics.
"""

import random
import time
from enum import Enum
from typing import List, Optional

class TimeOfDay(Enum):
    """Represents different times of day that affect gameplay."""
    DAY = "day"
    NIGHT = "night"

class Season(Enum):
    """Represents seasons that affect plant growth and unit behavior."""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"
class GameLoop:
    """
    Main game loop that controls the flow of the game.
    
    This class manages turns, allowing each unit to evaluate the board,
    make decisions, and perform actions. It also handles plant growth and decay.
    """
    
    def __init__(self, board, max_turns=1000, config=None):
        """
        Initialize a new game loop.
        
        Args:
            board: The game board.
            max_turns (int): Maximum number of turns before the game ends.
            config: Configuration object for game settings.
        """
        self.board = board
        self.max_turns = max_turns
        self.current_turn = 0
        self.units = []
        self.plants = []
        self.is_running = False
        self.config = config
        
        # Environmental cycles
        self.time_of_day = TimeOfDay.DAY
        self.season = Season.SPRING
        self.day_night_cycle_length = config.config["environment"]["cycle_length"] if config else 20
        self.season_length = self.day_night_cycle_length * 4  # One season lasts 4 day/night cycles
        
        # Gameplay speed control
        self.turn_delay = config.config["game"]["turn_delay"] if config else 0.1
    def add_unit(self, unit):
        """
        Add a unit to the game.
        
        Args:
            unit: The unit to add.
        """
        self.units.append(unit)
        
    def add_plant(self, plant):
        """
        Add a plant to the game.
        
        Args:
            plant: The plant to add.
        """
        self.plants.append(plant)
        
    def start(self):
        """
        Start the game loop.
        """
        self.is_running = True
        self.run()
        
    def stop(self):
        """
        Stop the game loop.
        """
        self.is_running = False
        
    def run(self):
        """
        Run the game loop until it completes or is stopped.
        """
        self.is_running = True  # Ensure is_running is set
        while self.is_running and self.current_turn < self.max_turns:
            self.process_turn()
        self.is_running = False
            
    def process_turn(self):
        """
        Process a single turn of the game, following the exact required order:
        1. Increment turn
        2. Update environmental cycles
        3. Apply environmental effects
        4. Shuffle units
        5. Update living units
        6. Update plants
        7. Update vision based on time of day
        """
        # 1. Increment turn counter
        self.current_turn += 1
        
        # 2. Update environmental cycles and time of day
        old_time_of_day = self.time_of_day
        self._update_environmental_cycles()

        # 3. Apply environmental effects
        self._apply_environmental_effects()

        # 4. Shuffle units
        random.shuffle(self.units) # Added shuffle
        
        # 5. Update units
        for unit in self.units:
            if hasattr(unit, 'update') and callable(getattr(unit, 'update')):
                unit.update(self.board) # Call update for ALL units (living or dead for decay)

            # Apply general energy costs (e.g. for existing) only to living units after their update
            if unit.alive:
                energy_cost_modifier = 1.5 if self.time_of_day == TimeOfDay.NIGHT else 1.0
                if hasattr(unit, 'energy'): # Check if unit has energy attribute
                    # Assuming a base passive energy cost of 1 per turn for living units
                    unit.energy = max(0, unit.energy - (1 * energy_cost_modifier))
        
        # 6. Update plants
        growth_modifiers = {
            Season.SPRING: 1.2,
            Season.SUMMER: 1.5,
            Season.AUTUMN: 0.8,
            Season.WINTER: 0.3
        }
        
        for plant in self.plants:
            # Apply seasonal growth rate modifier
            if hasattr(plant, 'base_growth_rate'):
                plant.growth_rate = plant.base_growth_rate * growth_modifiers[self.season]
            
            # Update plant
            # Ensure plant.update exists and is callable
            if hasattr(plant, 'update') and callable(getattr(plant, 'update')):
                plant.update() # Assuming plant.update takes no arguments like dt from original file
            else:
                # Fallback or error if update method is missing
                pass # Or log a warning: print(f"Warning: Plant {plant} missing update method.")
            
            # Apply nighttime energy reduction
            if self.time_of_day == TimeOfDay.NIGHT and hasattr(plant, 'energy'):
                plant.energy = max(plant.energy * 0.95, plant.min_energy if hasattr(plant, 'min_energy') else 0)

        # 7. Update vision based on time of day (Moved to the end of step list)
        if old_time_of_day != self.time_of_day or self.current_turn == 1:
            self._update_unit_vision()

        # Handle state transitions for newly dead units (This can be part of unit updates or a separate phase)
        # For now, keeping it after main updates as in original structure before this change.
        # The logic for dead_units changing state to "decaying" is now handled within Unit.update(),
        # so the following block can be removed or commented out:
        # dead_units = [unit for unit in self.units if not unit.alive and unit.state == "dead"]
        # for dead_unit in dead_units:
        #     if hasattr(dead_unit, 'state'): # Check if unit has state before changing
        #          dead_unit.state = "decaying"
        
        # Add delay between turns if configured
        if self.turn_delay > 0:
            time.sleep(self.turn_delay)
        
        # Check if the game should end
        if self.current_turn >= self.max_turns:
            self.is_running = False
            
    def _update_environmental_cycles(self):
        """
        Update the day/night cycle and seasons based on turn count.
        """
        # Day/night cycle changes every 10 turns
        if self.current_turn % 10 == 0 and self.current_turn > 0:
            self.time_of_day = TimeOfDay.NIGHT if self.time_of_day == TimeOfDay.DAY else TimeOfDay.DAY
            
        # Update seasons every 40 turns (4 day/night cycles)
        if self.current_turn % 40 == 0 and self.current_turn > 0:
            season_order = list(Season)
            current_index = season_order.index(self.season)
            self.season = season_order[(current_index + 1) % len(season_order)]

    def _apply_environmental_effects(self):
        """
        Apply global environmental effects based on current conditions.
        """
        # Apply effects to all living units first
        for unit in self.units:
            if unit.alive and hasattr(unit, 'apply_environmental_effects'):
                unit.apply_environmental_effects()
        
        # Apply effects to all plants
        for plant in self.plants:
            if hasattr(plant, 'apply_environmental_effects'):
                plant.apply_environmental_effects()

    def _update_unit_vision(self):
        """
        Update vision for all living units based on time of day.
        """
        for unit in self.units:
            if unit.alive and hasattr(unit, 'base_vision'):
                unit.vision = unit.base_vision // 2 if self.time_of_day == TimeOfDay.NIGHT else unit.base_vision

    def get_stats(self):
        """
        Get current game statistics and environmental conditions.
        
        Returns:
            dict: A dictionary containing game statistics and environmental state.
        """
        alive_units = len([unit for unit in self.units if unit.alive])
        dead_units = len([unit for unit in self.units if not unit.alive])
        decaying_units = len([unit for unit in self.units if not unit.alive and unit.state == "decaying"])
        
        stats = {
            "current_turn": self.current_turn,
            "turn": self.current_turn,  # Backward compatibility
            "max_turns": self.max_turns,
            "alive_units": alive_units,
            "living_units": alive_units,  # Test requirement
            "dead_units": dead_units,
            "units": {
                "total": len(self.units),
                "alive": alive_units,
                "dead": dead_units,
                "decaying": decaying_units
            },
            "plants": len(self.plants),
            "plant_count": len(self.plants),
            "time_of_day": self.time_of_day.value,
            "season": self.season.value,
            "environment": {
                "time_of_day": self.time_of_day.value,
                "season": self.season.value,
                "day_night_cycle_length": self.day_night_cycle_length,
                "season_length": self.season_length,
                "next_cycle_change": self.day_night_cycle_length - (self.current_turn % self.day_night_cycle_length),
                "next_season_change": self.season_length - (self.current_turn % self.season_length)
            }
        }
        
        return stats
