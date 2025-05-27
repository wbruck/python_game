# Game Architecture Documentation

## Overview

The ecosystem simulation game is built using a modular architecture that separates different game components into distinct modules. The game implements a turn-based ecosystem where different unit types interact with each other and their environment on a 2D grid board.

## Core Components

### 1. Game Board (`game/board.py`)
- Implements a 2D grid system using the `Board` class
- Manages unit positions and movement
- Handles collision detection and visibility calculations
- Supports both cardinal (4-direction) and diagonal (8-direction) movement
- Uses efficient position tracking with the `Position` dataclass

### 2. Unit System (`game/units/`)
The unit system is built around a base `Unit` class that implements core RPG-style attributes and behaviors:

#### Base Unit (`base_unit.py`)
- Core stats: HP, energy, strength, speed, vision
- State machine for decision-making
- Movement and interaction capabilities
- Evolution and experience tracking

#### Unit Types (`unit_types.py`)
Specialized unit behaviors for:
- Predators: Hunt other units actively
- Scavengers: Seek and consume dead units
- Grazers: Focus on plant consumption

### 3. Plant System (`game/plants/`)
- Manages food resources on the board
- Implements growth and regeneration mechanics
- Different plant types with varying energy values
- Balanced distribution algorithms

### 4. Game Loop (`game/game_loop.py`)
- Manages turn-based progression
- Orchestrates unit actions and board updates
- Handles environmental cycles (day/night)
- Controls game flow and win conditions

### 5. Configuration System (`game/config.py`)
- JSON-based configuration
- Runtime reloading capability
- Validation and default values
- Event notifications for config changes

### 6. Visualization (`game/visualization.py`)
- Text-based board rendering
- Unit and object representation
- Game state display
- Support for both real-time and snapshot views

## Data Flow

1. The game loop manages the overall flow:
   - Initializes board and units
   - Processes each turn
   - Updates unit states and positions
   - Manages plant growth
   - Handles visualization updates

2. Each turn involves:
   - Random unit action order
   - State evaluation for each unit
   - Action execution (movement, combat, feeding)
   - Environment updates
   - Plant system updates
   - Decay processing

3. Configuration changes can occur at runtime:
   - JSON file modifications
   - Validation checks
   - Event notifications
   - System updates

## Extension Points

The game is designed to be easily extensible in several ways:

1. New Unit Types:
   - Inherit from `base_unit.Unit`
   - Implement custom behavior patterns
   - Add specialized attributes

2. Plant Variations:
   - Create new plant types
   - Modify growth patterns
   - Adjust energy values

3. Board Mechanics:
   - Add new movement patterns
   - Implement special terrain effects
   - Create custom visibility rules

4. Game Rules:
   - Modify turn mechanics
   - Add new win conditions
   - Implement special events

## Performance Considerations

- Efficient position tracking using dictionaries
- Optimized visibility calculations
- Configurable board sizes
- Memory management for large simulations
