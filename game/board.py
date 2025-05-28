"""
Board module that implements the 2D game board for the ecosystem simulation.

This module provides the core functionality for the game board where units move around,
interact with each other, and interact with plants and obstacles.
"""

from enum import Enum
import random
from typing import List, Tuple, Optional, Set, Dict
from dataclasses import dataclass

class MovementType(Enum):
    """Defines allowed movement directions on the board."""
    CARDINAL = 4  # North, South, East, West
    DIAGONAL = 8  # Cardinal + Diagonals

@dataclass(frozen=True)  # Makes the class immutable and hashable
class Position:
    """Represents a position on the board."""
    x: int
    y: int

    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __hash__(self):
        return hash((self.x, self.y))
class Board:
    """
    Represents the 2D game board where all game elements are placed and interact.
    
    The board is implemented as a 2D grid (matrix) that can contain units, plants,
    and obstacles. It manages movement, collision detection, and visibility.
    """
    
    def __init__(self, width: int, height: int, allow_diagonal: bool = False):
        """
        Initialize a new game board with the specified dimensions.
        
        Args:
            width (int): The width of the board.
            height (int): The height of the board.
            allow_diagonal (bool): Whether diagonal movement is allowed.
        """
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.movement_type = MovementType.DIAGONAL if allow_diagonal else MovementType.CARDINAL
        self._object_positions: Dict[object, Position] = {}  # Track object positions
        self._plants: Set[object] = set()  # Track plants separately
        self.random = random.Random()  # Create a dedicated random number generator
        
        # Define movement vectors based on movement type
        self.movement_vectors = [
            (0, 1),   # North
            (0, -1),  # South
            (1, 0),   # East
            (-1, 0),  # West
        ]
        if allow_diagonal:
            self.movement_vectors.extend([
                (1, 1),    # Northeast
                (-1, 1),   # Northwest
                (1, -1),   # Southeast
                (-1, -1),  # Southwest
            ])
    def is_valid_position(self, x, y):
        """
        Check if the given coordinates are within the board boundaries.
        
        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.
            
        Returns:
            bool: True if the position is valid, False otherwise.
        """
        return 0 <= x < self.width and 0 <= y < self.height
    

    def get_object(self, x: int, y: int) -> Optional[object]:
        """
        Get the object at the specified position.
        
        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            
        Returns:
            Optional[object]: The object at the position, or None if empty.
        """
        if not self.is_valid_position(x, y):
            return None
        return self.grid[y][x]

    def place_object(self, obj: object, x: int, y: int) -> bool:
        """
        Place an object on the board at the specified position.
        
        Args:
            obj: The object to place (unit, plant, or obstacle).
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            
        Returns:
            bool: True if the object was placed successfully, False otherwise.
        """
        if not self.is_valid_position(x, y) or self.grid[y][x] is not None:
            return False
        
        self.grid[y][x] = obj
        self._object_positions[obj] = Position(x, y)
        # Add to plants set if it's a plant
        if hasattr(obj, 'consume') and hasattr(obj, 'state'):
            self._plants.add(obj)
        return True
    
    def get_units_in_range(self, x: int, y: int, range_: int) -> List[object]:
        """
        Get all units within a specified range of a position.
        Uses Manhattan distance for consistent game mechanics.
        
        Args:
            x (int): Center x-coordinate
            y (int): Center y-coordinate
            range_ (int): Vision range to check
            
        Returns:
            List[object]: List of units found within range and line of sight
        """
        units = []
        # Expand search area slightly to ensure edge cases
        search_range = range_ + 1
        center = Position(x, y)
        
        # Search expanded area for units
        for dy in range(-search_range, search_range + 1):
            for dx in range(-search_range, search_range + 1):
                check_x = x + dx
                check_y = y + dy
                
                # Skip invalid positions
                if not self.is_valid_position(check_x, check_y):
                    continue
                
                # Use Manhattan distance for game consistency
                if abs(dx) + abs(dy) > range_:
                    continue
                
                # Get object at position
                obj = self.get_object(check_x, check_y)
                if obj is None or not hasattr(obj, 'alive'):
                    continue
                    
                # Skip self and duplicates
                if hasattr(obj, 'x') and hasattr(obj, 'y'):
                    if obj.x == x and obj.y == y:
                        continue
                if obj in units:
                    continue
                    
                # Check line of sight
                target = Position(check_x, check_y)
                if self._has_line_of_sight(center, target):
                    units.append(obj)
                    
        return units

    def remove_object(self, x: int, y: int) -> Optional[object]:
        """
        Remove an object from the specified position.
        
        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            
        Returns:
            The object that was removed, or None if there was no object.
        """
        if not self.is_valid_position(x, y):
            return None
        
        obj = self.grid[y][x]
        if obj is not None:
            self.grid[y][x] = None
            del self._object_positions[obj]
            if obj in self._plants:
                self._plants.remove(obj)
        return obj

    def get_object_position(self, obj: object) -> Optional[Position]:
        """
        Get the current position of an object on the board.
        
        Args:
            obj: The object to locate.
            
        Returns:
            Position: The object's position, or None if not found.
        """
        return self._object_positions.get(obj)

    def calculate_field_of_view(self, x: int, y: int, vision_range: int) -> Set[Position]:
        """
        Calculate visible positions from a given point within vision range.
        Uses ray casting for line of sight calculations.
        
        Args:
            x (int): The x-coordinate of the viewing position.
            y (int): The y-coordinate of the viewing position.
            vision_range (int): Maximum distance that can be seen.
            
        Returns:
            Set[Position]: Set of visible positions.
        """
        if not self.is_valid_position(x, y):
            return set()

        visible = set()
        center = Position(x, y)
        visible.add(center)  # Always include center position
        
        # Cast rays in all directions
        for angle in range(0, 360, 15):  # Cast a ray every 15 degrees
            rad = angle * 3.14159 / 180.0
            dx = int(vision_range * 0.71 * (-1 if angle > 180 else 1))  # Scale for better coverage
            dy = int(vision_range * 0.71 * (-1 if 90 < angle < 270 else 1))
            
            curr_x, curr_y = x, y
            for step in range(vision_range):
                curr_x += dx // vision_range
                curr_y += dy // vision_range
                
                if not self.is_valid_position(curr_x, curr_y):
                    break
                    
                pos = Position(curr_x, curr_y)
                if center.distance_to(pos) > vision_range:
                    break
                    
                visible.add(pos)
                
                # Stop at vision-blocking objects
                obj = self.get_object(curr_x, curr_y)
                if obj is not None and hasattr(obj, 'blocks_vision') and obj.blocks_vision:
                    break
        
        return visible

    def _has_line_of_sight(self, start: Position, end: Position) -> bool:
        """
        Check if there is a clear line of sight between two positions.
        Uses Bresenham's line algorithm for ray casting.
        
        Args:
            start (Position): Starting position.
            end (Position): Target position.
            
        Returns:
            bool: True if there is clear line of sight.
        """
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y
        
        # Immediately return True if checking the same position
        if x0 == x1 and y0 == y1:
            return True
            
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            # Move to next position
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
                
            # Check if we've reached the target
            if x == x1 and y == y1:
                return True
                
            # Check for vision-blocking obstacles
            obj = self.grid[y][x]
            if obj is not None and hasattr(obj, 'blocks_vision') and obj.blocks_vision:
                return False
        
        return False  # Return False if we never reached the target
    
    def move_object(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """
        Move an object from one position to another.
        
        Args:
            from_x (int): The source x-coordinate.
            from_y (int): The source y-coordinate.
            to_x (int): The destination x-coordinate.
            to_y (int): The destination y-coordinate.
            
        Returns:
            bool: True if the move was successful, False otherwise.
        """
        # Validate positions and get moving object
        if not self.is_valid_position(from_x, from_y) or not self.is_valid_position(to_x, to_y):
            return False
        
        obj = self.grid[from_y][from_x]
        if obj is None or self.grid[to_y][to_x] is not None:
            return False
            
        # Calculate distances
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        manhattan_dist = dx + dy
        diagonal_dist = max(dx, dy)  # For diagonal movement
        
        # Get the unit's speed if it has one
        max_distance = 1  # Default to 1 step
        if hasattr(obj, 'speed'):
            max_distance = obj.speed
        
        # No movement case
        if dx == 0 and dy == 0:
            return False
            
        # Get maximum allowed distance based on unit speed
        max_speed = max_distance if hasattr(obj, 'speed') else 1
        
        # Calculate movement constraints based on type
        if self.movement_type == MovementType.DIAGONAL:
            # For diagonal movement, allow any move within speed range
            if manhattan_dist > max_speed * 2:  # Diagonal moves count as 2 steps
                return False
        else:  # CARDINAL movement
            # For cardinal movement, one direction must be 0
            if dx > 0 and dy > 0:  # No diagonal movement allowed
                return False
            if manhattan_dist > max_speed:  # Check total distance
                return False
                
        # For multi-step moves, ensure path is clear
        if manhattan_dist > 1:
            # Calculate step sizes
            dx_step = (to_x - from_x) // manhattan_dist
            dy_step = (to_y - from_y) // manhattan_dist
            
            # Check each intermediate position
            for i in range(1, manhattan_dist):
                check_x = from_x + (dx_step * i)
                check_y = from_y + (dy_step * i)
                if self.grid[check_y][check_x] is not None:
                    return False
                
        # Path must be clear for multi-step moves
        if manhattan_dist > 1:
            # Check intermediate positions
            step_x = 1 if to_x > from_x else (-1 if to_x < from_x else 0)
            step_y = 1 if to_y > from_y else (-1 if to_y < from_y else 0)
            curr_x, curr_y = from_x, from_y
            
            while curr_x != to_x or curr_y != to_y:
                next_x = curr_x + (step_x if curr_x != to_x else 0)
                next_y = curr_y + (step_y if curr_y != to_y else 0)
                if self.grid[next_y][next_x] is not None:
                    return False
                curr_x, curr_y = next_x, next_y
        
        self.grid[to_y][to_x] = obj
        self.grid[from_y][from_x] = None
        self._object_positions[obj] = Position(to_x, to_y)
        
        # Update the object's own coordinates if it has them
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            obj.x = to_x
            obj.y = to_y
        
        return True

    def get_available_moves(self, x: int, y: int) -> List[Position]:
        """
        Get all valid moves from a given position based on movement type.
        
        Args:
            x (int): The x-coordinate of the starting position.
            y (int): The y-coordinate of the starting position.
            
        Returns:
            List[Position]: List of valid positions that can be moved to.
        """
        if not self.is_valid_position(x, y) or self.grid[y][x] is None:
            return []
            
        valid_moves = []
        for dx, dy in self.movement_vectors:
            new_x, new_y = x + dx, y + dy
            if self.is_valid_position(new_x, new_y) and self.grid[new_y][new_x] is None:
                valid_moves.append(Position(new_x, new_y))
        return valid_moves

    def move_unit(self, unit: object, dx: int, dy: int) -> bool:
        """
        Move a unit by the given delta if possible.
        
        Args:
            unit: The unit to move
            dx (int): Relative x movement (-1, 0, or 1)
            dy (int): Relative y movement (-1, 0, or 1)
            
        Returns:
            bool: True if the move was successful, False otherwise.
        """
        current_pos = self.get_object_position(unit)
        if current_pos is None:
            return False
            
        # Calculate target position
        new_x = current_pos.x + dx
        new_y = current_pos.y + dy
        
        # Verify valid movement
        if not self.is_valid_position(new_x, new_y):
            return False
            
        # Move using the unit's own move method if available
        if hasattr(unit, 'move'):
            return unit.move(new_x, new_y, self)
            
        # Fallback to direct movement if unit doesn't have move method
        return self.move_object(current_pos.x, current_pos.y, new_x, new_y)

    def get_plants_in_range(self, x: int, y: int, range_: int) -> List[object]:
        """
        Get all plants within a specified range of a position.
        
        Args:
            x (int): Center x-coordinate
            y (int): Center y-coordinate
            range_ (int): Range to check
            
        Returns:
            List[object]: List of plants found within range
        """
        plants = []
        for dy in range(-range_, range_ + 1):
            for dx in range(-range_, range_ + 1):
                check_x, check_y = x + dx, y + dy
                if self.is_valid_position(check_x, check_y):
                    obj = self.get_object(check_x, check_y)
                    if obj is not None and hasattr(obj, 'growth_rate'):  # Check if object is a plant
                        plants.append(obj)
        return plants

    def place_random_plants(self, num_plants: int, plant_factory) -> List[Position]:
        """
        Place a specified number of plants randomly on empty board positions.
        
        Args:
            num_plants (int): Number of plants to place.
            plant_factory: Function that creates a new plant instance.
            
        Returns:
            List[Position]: Positions where plants were placed.
        """
        empty_positions = [
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x] is None
        ]
        
        if len(empty_positions) < num_plants:
            num_plants = len(empty_positions)
            
        selected_positions = random.sample(empty_positions, num_plants)
        placed_positions = []
        
        for pos in selected_positions:
            plant = plant_factory()
            if self.place_object(plant, pos.x, pos.y):
                placed_positions.append(pos)
                
        return placed_positions
    
    def add_plant(self, plant) -> bool:
        """
        Add a plant to the board at its current position.
        
        Args:
            plant: The plant object to add
            
        Returns:
            bool: True if plant was added successfully, False otherwise
        """
        pos = getattr(plant, 'position', None)
        if pos is None:
            return False
        
        success = self.place_object(plant, pos.x, pos.y)
        if success:
            self._plants = self._plants | {plant}  # Use union to avoid set initialization issue
        return success

    def remove_plant(self, plant) -> bool:
        """
        Remove a plant from the board.
        
        Args:
            plant: The plant object to remove
            
        Returns:
            bool: True if plant was removed successfully, False otherwise
        """
        pos = self._object_positions.get(plant)
        if pos is None or plant not in self._plants:
            return False
            
        self.remove_object(pos.x, pos.y)
        self._plants.remove(plant)
        return True

