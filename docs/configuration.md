# Configuration Guide

## Overview

The game uses a JSON-based configuration system that allows customizing various aspects of gameplay. The configuration can be modified at runtime and automatically reloads when changes are detected.

## Configuration File Location

The default configuration file is `config.json` in the root directory. You can specify a different file using the `-c` or `--config` command line option:

```bash
python main.py --config custom_config.json
```

## Configuration Options

### Board Settings
```json
{
    "board": {
        "width": 20,        // Board width (5-100)
        "height": 20,       // Board height (5-100)
        "allow_diagonal_movement": true  // Enable 8-direction movement
    }
}
```

### Game Settings
```json
{
    "game": {
        "max_turns": 1000,    // Maximum turns before game ends (1-10000)
        "turn_delay": 0.1     // Delay between turns in seconds (0.0-5.0)
    }
}
```

### Unit Settings
```json
{
    "units": {
        "initial_count": {
            "predator": 3,    // Starting predator count (0-50)
            "scavenger": 5,   // Starting scavenger count (0-50)
            "grazer": 8       // Starting grazer count (0-50)
        },
        "energy_consumption": {
            "move": 1,        // Energy cost per move (0-10)
            "attack": 2,      // Energy cost per attack (0-10)
            "look": 0         // Energy cost for looking around (0-10)
        },
        "decay_rate": 0.1     // Dead unit decay speed (0.0-1.0)
    }
}
```

### Plant Settings
```json
{
    "plants": {
        "initial_count": 15,    // Starting plant count (0-100)
        "growth_rate": 0.05,    // New plant chance per turn (0.0-1.0)
        "max_count": 30         // Maximum plants on board (1-200)
    }
}
```

### Environment Settings
```json
{
    "environment": {
        "day_night_cycle": true,  // Enable day/night cycle
        "cycle_length": 20        // Turns per day/night cycle (1-100)
    }
}
```

## Effects of Settings

### Board Size
- Larger boards (width/height) allow more space for units but may impact performance
- Recommended to balance board size with unit counts for optimal performance

### Movement Type
- `allow_diagonal_movement: true` enables 8-direction movement (including diagonals)
- `allow_diagonal_movement: false` restricts to 4-direction movement (cardinal only)

### Unit Balance
- Initial counts affect ecosystem balance
- Higher predator counts create more aggressive environments
- Higher grazer counts support larger predator populations
- Scavengers help clean up dead units and maintain energy flow

### Energy System
- Energy consumption rates affect unit survival strategies
- Higher costs force more careful resource management
- Lower costs allow more aggressive actions

### Plant System
- Growth rate affects food availability
- Max count prevents overwhelming plant growth
- Initial count sets starting food availability

### Environmental Effects
- Day/night cycle affects visibility and behavior
- Cycle length determines adaptation periods
- Environmental changes influence unit decision-making

## Runtime Configuration

The configuration system supports runtime changes:
1. Modify the JSON file while the game is running
2. Changes are automatically detected and validated
3. If valid, new settings are applied immediately
4. Invalid changes are logged and ignored

## Validation Rules

All configuration values are validated against these rules:
- Board dimensions must be between 5 and 100
- Unit counts must be between 0 and 50
- Energy costs must be between 0 and 10
- Rates and probabilities must be between 0.0 and 1.0
- Cycle lengths must be between 1 and 100

## Best Practices

1. Start with default values and adjust gradually
2. Monitor performance with larger board sizes
3. Balance unit populations for sustainable ecosystems
4. Test configuration changes in small increments
5. Back up working configurations before major changes
