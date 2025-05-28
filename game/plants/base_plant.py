"""
Base plant class for the ecosystem simulation.

This module defines the core functionality for all plant types in the game,
including growth, energy content, and consumption mechanics.
"""

from dataclasses import dataclass
from typing import Optional
from game.board import Position

@dataclass
class PlantState:
    """Represents the current state of a plant."""
    growth_stage: float  # 0.0 to 1.0, where 1.0 is fully grown
    energy_content: float  # Current energy content available for consumption
    is_alive: bool  # Whether the plant is alive or consumed

class Plant:
    """Base class for all plant types in the ecosystem."""
    
    def __init__(self, 
                 position: Position,
                 base_energy: float,
                 growth_rate: float,
                 regrowth_time: float):
        """
        Initialize a new plant.
        
        Args:
            position: The plant's position on the board
            base_energy: Maximum energy content when fully grown
            growth_rate: How quickly the plant grows (0.0 to 1.0)
            regrowth_time: Time required to fully regrow after consumption
        """
        self.position = position
        self.base_energy = base_energy
        self.growth_rate = growth_rate
        self.regrowth_time = regrowth_time
        self.state = PlantState(
            growth_stage=1.0,  # Start fully grown
            energy_content=base_energy,
            is_alive=True
        )
    
    def update(self, dt: float) -> None:
        """
        Update the plant's state for this time step.
        
        Args:
            dt: Time delta since last update
        """
        if not self.state.is_alive and self.state.growth_stage < 1.0:
            # Regrow if consumed
            self.state.growth_stage = min(1.0, 
                self.state.growth_stage + (self.growth_rate * dt))
            
            # Once fully regrown, restore energy and mark as alive
            if self.state.growth_stage >= 1.0:
                self.state.energy_content = self.base_energy
                self.state.is_alive = True
    
    def consume(self, amount: float) -> float:
        """
        Consume energy from this plant.
        
        Args:
            amount: Amount of energy requested
            
        Returns:
            float: Actual amount of energy provided
        """
        if not self.state.is_alive:
            return 0.0
        
        available = self.state.energy_content
        consumed = min(amount, available)
        self.state.energy_content -= consumed
        
        # If all energy is consumed, mark as consumed and start regrowth
        if self.state.energy_content <= 0:
            self.state.is_alive = False
            self.state.growth_stage = 0.0
        
        return consumed
    
    @property
    def energy_content(self) -> float:
        """Get the current energy content of the plant."""
        return self.state.energy_content

    @property
    def symbol(self) -> str:
        """Return the symbol used to represent this plant on the game board."""
        if not self.state.is_alive:
            return "."  # Consumed plant
        return "*"  # Basic plant symbol, subclasses should override
