# Tutorials and Examples

## Getting Started

### Basic Setup

1. Install the required dependencies:
```bash
# Clone the repository
git clone https://github.com/wbruck/python_game.git
cd python_game

# Set up Python environment
pipenv install --dev
pipenv shell
```

2. Run your first simulation:
```bash
python main.py
```

This will start the game with default settings, showing a text-based visualization of the ecosystem.

### Understanding the Display

The game uses ASCII characters to represent different elements:
- `P` - Predator units
- `S` - Scavenger units
- `G` - Grazer units
- `*` - Plants
- `#` - Obstacles
- `.` - Empty space
- `X` - Dead units

## Common Usage Scenarios

### 1. Creating a Balanced Ecosystem

This configuration creates a stable ecosystem with balanced unit populations:

```json
{
    "board": {
        "width": 30,
        "height": 30
    },
    "units": {
        "initial_count": {
            "predator": 5,
            "scavenger": 8,
            "grazer": 15
        }
    },
    "plants": {
        "initial_count": 25,
        "growth_rate": 0.08
    }
}
```

Save this as `balanced_config.json` and run:
```bash
python main.py -c balanced_config.json
```

### 2. Survival Challenge Scenario

This configuration creates a challenging environment with scarce resources:

```json
{
    "board": {
        "width": 20,
        "height": 20
    },
    "units": {
        "initial_count": {
            "predator": 8,
            "scavenger": 3,
            "grazer": 10
        },
        "energy_consumption": {
            "move": 2,
            "attack": 3
        }
    },
    "plants": {
        "initial_count": 10,
        "growth_rate": 0.03
    }
}
```

### 3. Observing Evolution

To better observe unit evolution, use this long-running configuration:

```json
{
    "game": {
        "max_turns": 5000,
        "turn_delay": 0.2
    },
    "units": {
        "initial_count": {
            "predator": 3,
            "scavenger": 5,
            "grazer": 12
        }
    }
}
```

## Extending the Game

### 1. Creating a New Unit Type

To create a new unit type, extend the base Unit class:

```python
# game/units/unit_types.py

class Ambusher(Unit):
    """A unit that hides and ambushes passing prey."""
    
    def __init__(self, x, y):
        super().__init__(x, y, unit_type="ambusher")
        self.hidden = False
    
    def decide_action(self, board):
        if self.energy < self.max_energy * 0.3:
            # Low energy - seek food
            self.state = "hunting"
            return self.hunt_nearest_prey(board)
            
        if not self.hidden and self.energy > self.max_energy * 0.7:
            # Hide when energy is high
            self.state = "idle"
            self.hidden = True
            return None
            
        if self.hidden:
            # Check for nearby prey while hidden
            nearby = board.get_nearby_units(self.x, self.y, 2)
            prey = [u for u in nearby if isinstance(u, Grazer)]
            if prey:
                self.hidden = False
                self.state = "hunting"
                return self.attack(prey[0])
        
        return None
```

### 2. Adding Custom Plant Types

Create a new plant type with special properties:

```python
# game/plants/plant_types.py

class EnergyRichPlant(BasePlant):
    """A plant that provides more energy but grows slowly."""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.energy_value = 50  # Higher energy value
        self.growth_rate = 0.03  # Slower growth
```

### 3. Implementing Custom Board Features

Add special terrain features to the board:

```python
# game/board.py

class Board:
    def add_water_feature(self, x, y, size):
        """Add a water feature that affects movement."""
        for dx in range(-size, size + 1):
            for dy in range(-size, size + 1):
                if self.is_valid_position(x + dx, y + dy):
                    self.grid[y + dy][x + dx] = Water()
```

## Advanced Topics

### 1. Performance Optimization

For larger simulations, consider these settings:

```json
{
    "board": {
        "width": 50,
        "height": 50
    },
    "game": {
        "turn_delay": 0.05
    },
    "units": {
        "initial_count": {
            "predator": 10,
            "scavenger": 15,
            "grazer": 25
        }
    }
}
```

### 2. Data Collection

To analyze ecosystem behavior, use the built-in stats collection:

```python
from game.stats import GameStats

stats = GameStats()
game.add_observer(stats)

# After running the simulation
stats.plot_population_trends()
stats.export_to_csv("simulation_data.csv")
```

### 3. Custom Visualization

Example of implementing a custom visualization:

```python
from game.visualization import BaseVisualizer

class ColorVisualizer(BaseVisualizer):
    def __init__(self):
        super().__init__()
        self.colors = {
            'predator': '\033[91m',  # Red
            'scavenger': '\033[93m',  # Yellow
            'grazer': '\033[92m',     # Green
            'plant': '\033[32m',      # Dark Green
        }
    
    def render_unit(self, unit):
        unit_type = unit.__class__.__name__.lower()
        color = self.colors.get(unit_type, '')
        return f"{color}{unit_type[0].upper()}\033[0m"
```

## Troubleshooting

### Common Issues

1. **Performance Problems**
   - Reduce board size
   - Decrease unit counts
   - Increase turn delay
   - Disable diagonal movement

2. **Unbalanced Ecosystem**
   - Adjust initial unit counts
   - Modify energy consumption rates
   - Change plant growth settings
   - Balance predator/prey ratios

3. **Visualization Issues**
   - Check terminal size matches board dimensions
   - Verify terminal supports ASCII characters
   - Try alternate visualization mode
