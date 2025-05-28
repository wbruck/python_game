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
    
    def __init__(self, width: int, height: int, movement_type: MovementType = MovementType.CARDINAL):
        """
        Initialize a new game board with the specified dimensions.
        
        Args:
            width (int): The width of the board.
            height (int): The height of the board.
            movement_type (MovementType): Type of movement allowed on the board.
        """
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.movement_type = movement_type
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
        if movement_type == MovementType.DIAGONAL:
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
        Uses Euclidean distance for more natural vision mechanics.
        
        Args:
            x (int): Center x-coordinate
            y (int): Center y-coordinate
            range_ (int): Vision range to check
            
        Returns:
            List[object]: List of units found within range and line of sight
        """
        print(f"Checking vision from ({x}, {y}) with range {range_}")
        units = []
        # Expand search area to cover diagonal vision
        search_range = int(range_ * 1.5)  # Expanded to ensure catching diagonal cases
        center = Position(x, y)
        
        # Search expanded area for units
        for dy in range(-search_range, search_range + 1):
            for dx in range(-search_range, search_range + 1):
                check_x = x + dx
                check_y = y + dy
                
                # Skip invalid positions
                if not self.is_valid_position(check_x, check_y):
                    continue
                
                # Use Euclidean distance for more natural vision
                distance = ((dx * dx) + (dy * dy)) ** 0.5
                if distance > range_:
                    continue
                
                # Get object at position
                obj = self.get_object(check_x, check_y)
                if obj is None:
                    continue
                    
                print(f"Found object at ({check_x}, {check_y}): {obj}")
                
                # Only consider units (objects with 'alive' attribute)
                if not hasattr(obj, 'alive'):
                    print(f"Object is not a unit (no 'alive' attribute)")
                    continue
                    
                # Skip self and duplicates
                if hasattr(obj, 'x') and hasattr(obj, 'y'):
                    if obj.x == x and obj.y == y:
                        print(f"Skipping self at ({x}, {y})")
                        continue
                if obj in units:
                    print(f"Skipping duplicate unit")
                    continue
                    
                # Check line of sight
                target = Position(check_x, check_y)
                has_los = self._has_line_of_sight(center, target)
                print(f"Line of sight check to ({check_x}, {check_y}): {has_los}")
                if has_los:
                    print(f"Adding unit to visible list: {obj}")
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
        # Check each position within a square of size vision_range
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                # Calculate target position
                target_x, target_y = x + dx, y + dy
                
                # Skip if out of bounds
                if not self.is_valid_position(target_x, target_y):
                    continue
                
                # Skip if beyond vision range (use Manhattan distance for simplicity)
                if abs(dx) + abs(dy) > vision_range:
                    continue
                
                # Add position if we have line of sight
                start_pos = Position(x, y)
                target_pos = Position(target_x, target_y)
                if self._has_line_of_sight(start_pos, target_pos):
                    visible.add(target_pos)
        
        return visible

    def _has_line_of_sight(self, start: Position, end: Position) -> bool:
        """
        Check if there is a clear line of sight between two positions.
        Uses a simplified direct path check with obstacle detection.
        
        Args:
            start (Position): Starting position.
            end (Position): Target position.
            
        Returns:
            bool: True if there is clear line of sight.
        """
        # Early exit for same position
        if start.x == end.x and start.y == end.y:
            return True
            
        # Get relative coordinates
        dx = end.x - start.x
        dy = end.y - start.y
        distance = max(abs(dx), abs(dy))
        
        if distance == 0:
            return True
            
        # Check points along the line
        for step in range(1, distance):
            # Calculate intermediate point
            x = start.x + int(dx * step / distance)
            y = start.y + int(dy * step / distance)
            
            # Check for vision-blocking obstacles
            obj = self.grid[y][x]
            if obj is not None and hasattr(obj, 'blocks_vision') and obj.blocks_vision:
                return False
                
        return True
    
    def move_object(self, from_x: int, from_y: int, to_x: int, to_y: int, ignore_constraints: bool = False) -> bool:
        """
        Move an object from one position to another.
        
        Args:
            from_x (int): The source x-coordinate.
            from_y (int): The source y-coordinate.
            to_x (int): The destination x-coordinate.
            to_y (int): The destination y-coordinate.
            ignore_constraints (bool): If True, ignores movement type and speed constraints (for testing)
            
        Returns:
            bool: True if the move was successful, False otherwise.
        """
        print(f"Moving object from ({from_x}, {from_y}) to ({to_x}, {to_y})")
        
        # Validate positions
        if not self.is_valid_position(from_x, from_y) or not self.is_valid_position(to_x, to_y):
            print("Invalid position in move_object")
            return False
            
        # Get and validate object
        obj = self.grid[from_y][from_x]
        if obj is None:
            print(f"No object found at source position ({from_x}, {from_y})")
            return False
            
        # Check if destination is clear
        if self.grid[to_y][to_x] is not None:
            print(f"Destination position ({to_x}, {to_y}) is occupied")
            return False
            
        # Calculate movement distance
        dx = abs(to_x - from_x)
        dy = abs(to_y - from_y)
        manhattan_dist = dx + dy
        
        if not ignore_constraints:
            # Get unit's speed limit
            max_speed = getattr(obj, 'speed', 1)  # Default to 1 if no speed attribute
            
            # Check movement constraints
            if manhattan_dist > max_speed:
                print(f"Movement distance {manhattan_dist} exceeds speed limit {max_speed}")
                return False
                
            # Check diagonal movement
            is_diagonal = dx > 0 and dy > 0
            if is_diagonal and self.movement_type != MovementType.DIAGONAL:
                print("Diagonal movement not allowed")
                return False
                
            # Check speed limit
            if manhattan_dist > max_speed:
                print(f"Movement distance {manhattan_dist} exceeds speed limit {max_speed}")
                return False
                
            # Check for occupied space
            if self.grid[to_y][to_x] is not None:
                print(f"Destination position ({to_x}, {to_y}) is occupied")
                return False
            
        # Move object
        self.grid[from_y][from_x] = None
        self.grid[to_y][to_x] = obj
        self._object_positions[obj] = Position(to_x, to_y)
        
        # Update object's own position
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            print(f"Updating object position from ({obj.x}, {obj.y}) to ({to_x}, {to_y})")
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

