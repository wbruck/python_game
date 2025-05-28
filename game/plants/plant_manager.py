"""
Plant manager for handling plant generation and distribution in the ecosystem.

This module provides functionality for generating, distributing, and managing
plants across the game board in sustainable patterns.
"""

import random
from typing import List, Dict, Type, Optional
from game.board import Board, Position
from game.plants.base_plant import Plant
from game.plants.plant_types import BasicPlant, EnergyRichPlant, FastGrowingPlant

class PlantManager:
    """Manages the generation and distribution of plants on the game board."""
    
    def __init__(self, board: Board, config: dict):
        """
        Initialize the plant manager.
        
        Args:
            board: Game board instance
            config: Configuration dictionary containing plant settings
        """
        self.board = board
        self.config = config
        self.plants: Dict[Position, Plant] = {}
        
        # Plant type distribution weights
        self.plant_types: Dict[Type[BasicPlant | EnergyRichPlant | FastGrowingPlant], float] = {
            BasicPlant: 0.6,        # 60% basic plants
            EnergyRichPlant: 0.15,  # 15% energy-rich plants
            FastGrowingPlant: 0.25  # 25% fast-growing plants
        }
    
    def generate_initial_plants(self) -> None:
        """Generate the initial distribution of plants on the board."""
        initial_count = self.config["plants"]["initial_count"]
        
        # Generate plants up to the initial count
        while len(self.plants) < initial_count:
            self._try_place_random_plant()
    
    def _try_place_random_plant(self) -> bool:
        """
        Attempt to place a random plant on the board.
        
        Returns:
            bool: True if plant was placed successfully, False otherwise
        """
        # Get random position
        x = random.randint(0, self.board.width - 1)
        y = random.randint(0, self.board.height - 1)
        pos = Position(x, y)
        
        # Check if position is available
        if not self.board.is_valid_position(x, y) or self.board.grid[y][x] is not None:
            return False
            
        # Select plant type based on distribution weights
        plant_type: Type[BasicPlant | EnergyRichPlant | FastGrowingPlant] = random.choices(
            list(self.plant_types.keys()),
            weights=list(self.plant_types.values())
        )[0]
        
        # Create and place the plant with board reference
        plant = plant_type(pos, board=self.board)
        if self.board.place_object(plant, x, y):
            self.plants[pos] = plant
            return True
        
        return False
    
    def update(self, dt: float) -> None:
        """
        Update all plants and manage distribution.
        
        Args:
            dt: Time delta since last update
        """
        # Update existing plants
        for plant in list(self.plants.values()):
            plant.update(dt)
            
        # Try to maintain minimum plant count
        current_count = len(self.plants)
        max_count = self.config["plants"]["max_count"]
        growth_rate = self.config["plants"]["growth_rate"]
        
        # Randomly generate new plants based on growth rate
        if current_count < max_count and random.random() < growth_rate:
            self._try_place_random_plant()
    
    def remove_plant(self, position: Position) -> None:
        """
        Remove a plant from the board and tracking.
        
        Args:
            position: Position of the plant to remove
        """
        if position in self.plants:
            plant = self.plants[position]
            self.board.remove_object(position.x, position.y)
            del self.plants[position]
