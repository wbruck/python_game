"""
Specific plant type implementations for the ecosystem simulation.

This module defines different plant types with varying energy values,
growth rates, and regrowth times to create a diverse ecosystem.
"""

from game.board import Position
from game.plants.base_plant import Plant

class BasicPlant(Plant):
    """
    Standard plant with balanced energy and growth characteristics.
    Serves as the primary food source in the ecosystem.
    """
    
    def __init__(self, position: Position):
        super().__init__(
            position=position,
            base_energy=50.0,      # Standard energy content
            growth_rate=0.08,      # Standard growth rate
            regrowth_time=12.0     # Standard regrowth time
        )
    
    @property
    def symbol(self) -> str:
        return "*" if self.state.is_alive else "."

class EnergyRichPlant(Plant):
    """
    High-energy plant that provides more sustenance but grows slower.
    Creates strategic food source locations in the ecosystem.
    """
    
    def __init__(self, position: Position):
        super().__init__(
            position=position,
            base_energy=100.0,     # High energy content
            growth_rate=0.04,      # Slower growth rate
            regrowth_time=20.0     # Longer regrowth time
        )
    
    @property
    def symbol(self) -> str:
        return "%" if self.state.is_alive else "."

class FastGrowingPlant(Plant):
    """
    Rapidly regenerating plant with lower energy content.
    Provides reliable but less nutritious food sources.
    """
    
    def __init__(self, position: Position):
        super().__init__(
            position=position,
            base_energy=25.0,      # Lower energy content
            growth_rate=0.16,      # Fast growth rate
            regrowth_time=6.0      # Short regrowth time
        )
    
    @property
    def symbol(self) -> str:
        return "+" if self.state.is_alive else "."

# Dictionary of available plant types for easy reference and instantiation
PLANT_TYPES = {
    "basic": BasicPlant,
    "energy_rich": EnergyRichPlant,
    "fast_growing": FastGrowingPlant
}
