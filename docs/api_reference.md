# API Reference

## Board Module

### class Board
```python
Board(width: int, height: int, movement_type: MovementType = MovementType.CARDINAL)
```

Core class representing the game board and managing all object positions and interactions.

#### Methods

##### Place and Remove Objects
- `place_object(obj: object, x: int, y: int) -> bool`
  - Places an object at the specified coordinates
  - Returns True if successful, False if position is invalid or occupied

- `remove_object(x: int, y: int) -> Optional[object]`
  - Removes and returns the object at specified coordinates
  - Returns None if position is empty

##### Position and Movement
- `is_valid_position(x: int, y: int) -> bool`
  - Checks if coordinates are within board boundaries

- `get_valid_moves(unit: Unit) -> List[Tuple[int, int]]`
  - Returns list of valid movement coordinates for a unit
  - Considers unit speed and board obstacles

##### Visibility and Search
- `get_visible_positions(x: int, y: int, range: int) -> Set[Position]`
  - Returns set of positions visible from given coordinates
  - Considers obstacles and vision range

- `get_nearby_units(x: int, y: int, range: int) -> List[Unit]`
  - Returns list of units within specified range
  - Excludes obstacles and plants

## Unit Module

### class Unit
```python
Unit(x: int, y: int, unit_type: Optional[str] = None, hp: int = 100, energy: int = 100, 
     strength: int = 10, speed: int = 1, vision: int = 5)
```

Base class for all game units with RPG-style stats and behaviors.

#### Properties
- `alive: bool` - Unit's living status
- `state: str` - Current behavior state
- `position: Position` - Current board position
- `stats: Dict[str, int]` - Dictionary of current stat values

#### Methods

##### Core Behaviors
- `move(direction: Tuple[int, int]) -> bool`
  - Attempts to move in specified direction
  - Returns True if successful

- `attack(target: Unit) -> bool`
  - Attempts to attack target unit
  - Returns True if attack was successful

- `consume(target: Union[Unit, Plant]) -> int`
  - Consumes target for energy
  - Returns amount of energy gained

##### State Management
- `update_state(board: Board) -> None`
  - Updates unit's state based on current conditions
  - Triggers state-specific behaviors

- `check_energy() -> bool`
  - Verifies if unit has sufficient energy
  - Returns False if unit should die from energy loss

##### Evolution System
- `gain_experience(amount: int) -> None`
  - Adds experience points to the unit
  - May trigger evolution when thresholds are met

- `evolve() -> None`
  - Attempts to evolve the unit based on experience
  - Adds new traits or improves existing ones

## Plant Module

### class BasePlant
```python
BasePlant(x: int, y: int, energy_value: int = 10, growth_rate: float = 0.05)
```

Base class for all plant types in the game.

#### Methods
- `grow() -> bool`
  - Attempts to grow or spread
  - Returns True if successful

- `get_energy_value() -> int`
  - Returns current energy value when consumed

## Configuration Module

### class Config
```python
Config(config_path: str = "config.json")
```

Manages game configuration with runtime reloading capability.

#### Methods
- `load_config() -> None`
  - Loads configuration from file
  - Validates all values against schema

- `get_value(key: str, default: Any = None) -> Any`
  - Returns configuration value for key
  - Falls back to default if not found

- `add_change_listener(callback: Callable[[str, Any], None]) -> None`
  - Registers callback for configuration changes

## Game Loop Module

### class GameLoop
```python
GameLoop(board: Board, config: Config)
```

Manages the main game loop and turn progression.

#### Methods
- `run() -> None`
  - Starts the main game loop
  - Continues until max turns or win condition

- `process_turn() -> None`
  - Processes a single game turn
  - Updates all units and board state

- `add_observer(observer: Observer) -> None`
  - Adds an observer for game events

## Visualization Module

### class BaseVisualizer
```python
BaseVisualizer(use_colors: bool = True)
```

Base class for game state visualization.

#### Methods
- `render(board: Board) -> str`
  - Renders current board state
  - Returns string representation

- `render_stats(game_stats: GameStats) -> str`
  - Renders current game statistics
  - Returns string representation

## Statistics Module

### class GameStats
```python
GameStats()
```

Collects and analyzes game statistics.

#### Methods
- `update(game_state: GameState) -> None`
  - Updates statistics with current game state

- `get_population_trends() -> Dict[str, List[int]]`
  - Returns population history for each unit type

- `export_to_csv(filename: str) -> None`
  - Exports collected statistics to CSV file

## Extensions and Customization

### Creating New Unit Types
```python
class CustomUnit(Unit):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, unit_type="custom")
        # Add custom attributes
        
    def decide_action(self, board: Board) -> Optional[Action]:
        # Implement custom decision logic
        pass
```

### Creating New Plant Types
```python
class CustomPlant(BasePlant):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.energy_value = 20
        self.growth_rate = 0.1
```

### Adding Custom Observers
```python
class CustomObserver(Observer):
    def on_turn_complete(self, game_state: GameState) -> None:
        # Process turn completion
        pass
        
    def on_unit_action(self, unit: Unit, action: Action) -> None:
        # Process unit actions
        pass
```
