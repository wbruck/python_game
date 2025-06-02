"""
Visualization module for the ecosystem simulation game.

This module provides text-based visualization capabilities using ASCII characters
and ANSI colors to represent the game state in the terminal.
"""

import os
from typing import Dict, List, Optional
from enum import Enum

from .board import Board, Position
from .units.base_unit import Unit
from .plants.base_plant import Plant

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    ORANGE = "\033[38;5;208m"  # Using 256-color code for orange

class Visualization:
    """
    Handles the text-based visualization of the game state.
    
    This class provides both real-time visualization capabilities and
    snapshot reporting of the game state using ASCII characters and ANSI colors.
    """
    
    def __init_symbols(self):
        """Initialize symbols with proper color codes."""
        c = Colors  # Shorthand reference
        
        self.UNIT_SYMBOLS = {
            "predator": {
                "idle": c.RED + "P" + c.RESET,
                "hunting": c.RED + c.BOLD + "P" + c.RESET,
                "fleeing": c.RED + "p" + c.RESET,
                "feeding": c.RED + "F" + c.RESET,
                "wandering": c.RED + "w" + c.RESET,
                "resting": c.RED + "r" + c.RESET,
                "dead": c.RED + "x" + c.RESET,
                "decaying": c.RED + "%" + c.RESET,
            },
            "scavenger": {
                "idle": c.BLUE + "S" + c.RESET,
                "hunting": c.BLUE + c.BOLD + "S" + c.RESET,
                "fleeing": c.BLUE + "s" + c.RESET,
                "feeding": c.BLUE + "F" + c.RESET,
                "wandering": c.BLUE + "w" + c.RESET,
                "resting": c.BLUE + "r" + c.RESET,
                "dead": c.BLUE + "x" + c.RESET,
                "decaying": c.BLUE + "%" + c.RESET,
            },
            "grazer": {
                "idle": c.GREEN + "G" + c.RESET,
                "hunting": c.GREEN + c.BOLD + "G" + c.RESET,
                "fleeing": c.GREEN + "g" + c.RESET,
                "feeding": c.GREEN + "F" + c.RESET,
                "wandering": c.GREEN + "w" + c.RESET,
                "resting": c.GREEN + "r" + c.RESET,
                "dead": c.GREEN + "x" + c.RESET,
                "decaying": c.GREEN + "%" + c.RESET,
            }
        }
        
        self.PLANT_SYMBOLS = {
            "alive": c.GREEN + "*" + c.RESET,
            "growing": c.GREEN + "," + c.RESET,
            "consumed": c.GREEN + "." + c.RESET
        }
    
    def __init__(self, board: Board, enabled: bool = True):
        """
        Initialize the visualization system.
        
        Args:
            board: The game board to visualize
            enabled: Whether visualization is initially enabled
        """
        self.board = board
        self.enabled = enabled
        self.frame_count = 0
        self._last_stats = {}
        self.__init_symbols()
    
    def toggle(self) -> None:
        """Toggle visualization on/off."""
        self.enabled = not self.enabled
    
    def _get_unit_symbol(self, unit: Unit) -> str:
        """Get the appropriate symbol for a unit based on its type and state."""
        if hasattr(unit, "unit_type") and hasattr(unit, "state"):
            unit_symbols = self.UNIT_SYMBOLS.get(unit.unit_type, {})
            return unit_symbols.get(unit.state, Colors.ORANGE + "?" + Colors.RESET)
        return Colors.ORANGE + "?" + Colors.RESET
    
    def _get_plant_symbol(self, plant: Plant) -> str:
        """Get the appropriate symbol for a plant based on its state."""
        if not plant.state.is_alive:
            return self.PLANT_SYMBOLS["consumed"]
        elif plant.state.growth_stage < 1.0:
            return self.PLANT_SYMBOLS["growing"]
        return self.PLANT_SYMBOLS["alive"]
    
    def _collect_stats(self) -> Dict:
        """Collect current game statistics."""
        stats = {
            "turn": self.frame_count,
            "units": {
                "total": 0,
                "predator": 0,
                "scavenger": 0,
                "grazer": 0,
                "dead": 0
            },
            "plants": {
                "total": 0,
                "alive": 0,
                "growing": 0,
                "consumed": 0
            }
        }
        
        # Count units and plants
        for y in range(self.board.height):
            for x in range(self.board.width):
                obj = self.board.grid[y][x]
                if isinstance(obj, Unit):
                    stats["units"]["total"] += 1
                    if hasattr(obj, "unit_type"):
                        stats["units"][obj.unit_type] += 1
                    if not obj.alive:
                        stats["units"]["dead"] += 1
                elif isinstance(obj, Plant):
                    stats["plants"]["total"] += 1
                    if obj.state.is_alive:
                        if obj.state.growth_stage >= 1.0:
                            stats["plants"]["alive"] += 1
                        else:
                            stats["plants"]["growing"] += 1
                    else:
                        stats["plants"]["consumed"] += 1
        
        self._last_stats = stats
        return stats
        
    def _format_stats(self, stats: Dict) -> str:
        """Format statistics for display."""
        return (
            f"Turn: {stats['turn']}\n"
            f"Units: {stats['units']['total']} "
            f"(P:{stats['units']['predator']} "
            f"S:{stats['units']['scavenger']} "
            f"G:{stats['units']['grazer']} "
            f"D:{stats['units']['dead']})\n"
            f"Plants: {stats['plants']['total']} "
            f"(A:{stats['plants']['alive']} "
            f"G:{stats['plants']['growing']} "
            f"C:{stats['plants']['consumed']})"
        )
    
    def render(self) -> None:
        """
        Render the current game state to the terminal if visualization is enabled.
        """
        if not self.enabled:
            return
            
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Collect and display stats
        stats = self._collect_stats()
        print(self._format_stats(stats))
        print()
        
        # Draw board border
        print("+" + "-" * (self.board.width * 2 - 1) + "+")
        
        # Draw board contents
        for y in range(self.board.height):
            print("|", end="")
            for x in range(self.board.width):
                obj = self.board.grid[y][x]
                if isinstance(obj, Unit):
                    print(self._get_unit_symbol(obj), end=" ")
                elif isinstance(obj, Plant):
                    print(self._get_plant_symbol(obj), end=" ")
                else:
                    print(" ", end=" ")
            print("|")
        
        # Draw board border
        print("+" + "-" * (self.board.width * 2 - 1) + "+")
        print()
        
        self.frame_count += 1
    
    def generate_snapshot(self) -> str:
        """
        Generate a text snapshot of the current game state.
        
        Returns:
            str: A formatted string containing the game state snapshot
        """
        stats = self._collect_stats()
        lines = [
            "=== Game State Snapshot ===",
            self._format_stats(stats),
            "",
            "Board State:",
            "+" + "-" * (self.board.width * 2 - 1) + "+"
        ]
        
        for y in range(self.board.height):
            row = ["|"]
            for x in range(self.board.width):
                obj = self.board.grid[y][x]
                if isinstance(obj, Unit):
                    row.append(self._get_unit_symbol(obj))
                elif isinstance(obj, Plant):
                    row.append(self._get_plant_symbol(obj))
                else:
                    row.append(" ")
                row.append(" ")
            row.append("|")
            lines.append("".join(row))
        
        lines.extend([
            "+" + "-" * (self.board.width * 2 - 1) + "+",
            "",
            "Legend:",
            "Units:",
            "  P/p - Predator (uppercase=active, lowercase=passive)",
            "  S/s - Scavenger",
            "  G/g - Grazer",
            "  F - Feeding",
            "  w - Wandering",
            "  r - Resting",
            "  x - Dead",
            "  % - Decaying",
            "",
            "Plants:",
            "  * - Alive",
            "  , - Growing",
            "  . - Consumed",
            "",
            "=== End Snapshot ==="
        ])
        
        return "\n".join(lines)
