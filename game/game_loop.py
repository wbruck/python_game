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
        while self.is_running and self.current_turn < self.max_turns:
            self.process_turn()
            
    def process_turn(self):
        """
        Process a single turn of the game, including environmental cycles and all entity updates.
        """
        self.current_turn += 1
        
        # Update environmental cycles
        self._update_environmental_cycles()
        
        # Apply environmental effects
        self._apply_environmental_effects()
        
        # Randomize unit order for fair processing
        random.shuffle(self.units)
        
        # Process each unit's turn
        for unit in self.units:
            if unit.alive:
                # Update unit based on current environmental conditions
                vision_modifier = 0.5 if self.time_of_day == TimeOfDay.NIGHT else 1.0
                energy_cost_modifier = 1.5 if self.time_of_day == TimeOfDay.NIGHT else 1.0
                
                # Update unit with current conditions
                unit.vision = int(unit.base_vision * vision_modifier)
                unit.update(self.board)
                
                # Apply energy costs based on time of day
                unit.energy = max(0, unit.energy - (1 * energy_cost_modifier))
        
        # Process dead units (decay)
        dead_units = [unit for unit in self.units if not unit.alive]
        for dead_unit in dead_units:
            if dead_unit.state == "dead":
                dead_unit.state = "decaying"
            # Only update if in decaying state
            if dead_unit.state == "decaying":
                dead_unit.update(self.board)
        
        # Process plants based on season and time of day
        growth_modifiers = {
            Season.SPRING: 1.2,
            Season.SUMMER: 1.5,
            Season.AUTUMN: 0.8,
            Season.WINTER: 0.3
        }
        
        for plant in self.plants:
            plant.growth_rate = plant.base_growth_rate * growth_modifiers[self.season]
            plant.update()
            
            # Night time slightly reduces plant energy content
            if self.time_of_day == TimeOfDay.NIGHT:
                plant.energy = max(plant.energy * 0.95, plant.min_energy)
        
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
        # Update day/night cycle
        day_night_phase = self.current_turn % self.day_night_cycle_length
        if day_night_phase == 0:
            # Toggle between day and night
            self.time_of_day = TimeOfDay.NIGHT if self.time_of_day == TimeOfDay.DAY else TimeOfDay.DAY
        
        # Update seasons
        season_phase = self.current_turn % self.season_length
        if season_phase == 0:
            # Cycle through seasons
            season_order = list(Season)
            current_index = season_order.index(self.season)
            self.season = season_order[(current_index + 1) % len(season_order)]

    def _apply_environmental_effects(self):
        """
        Apply global environmental effects based on current conditions.
        """
        # This method can be extended to apply additional environmental effects
        # Currently, the effects are applied directly in process_turn
        pass

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
            "turn": self.current_turn,
            "max_turns": self.max_turns,
            "alive_units": alive_units,
            "dead_units": dead_units,
            "plants": len(self.plants),  # Just return the count as expected by tests
            "units": {
                "decaying": decaying_units
            },
            "environment": {
                "time_of_day": self.time_of_day.value,
                "season": self.season.value,
                "day_night_cycle_length": self.day_night_cycle_length,
                "season_length": self.season_length,
                "next_cycle_change": self.day_night_cycle_length - (self.current_turn % self.day_night_cycle_length),
                "next_season_change": self.season_length - (self.current_turn % self.season_length)
            },
            "units": {
                "total": len(self.units),
                "alive": alive_units,
                "dead": dead_units,
                "decaying": decaying_units
            },
            "plants": len(self.plants)  # Return just the count as expected by tests
        }
        
        return stats
