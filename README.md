# Ecosystem Simulation Game

A simple RPG-style ecosystem simulation game where different unit types interact with each other and their environment.

## Project Description

This project implements a turn-based ecosystem simulation with different unit types that move around on a 2D grid, interact with each other, and compete for resources. The simulation features:

- Different unit types with specialized behaviors (predators, scavengers, grazers)
- A 2D game board with plants and obstacles
- Turn-based game loop
- Configurable game parameters
- Unit states and decision-making

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pipenv (for dependency management)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/wbruck/python_game.git
   cd python_game
   ```

2. Set up the Python environment using pipenv:
   ```
   pipenv install --dev
   ```

3. Activate the virtual environment:
   ```
   pipenv shell
   ```

### Running the Game

Run the game using the main script:
```
python main.py
```

### Command Line Options

- `-c`, `--config`: Path to config file (default: config.json)
- `--no-display`: Disable visual display
- `--turns`: Override number of turns
- `--seed`: Random seed for reproducibility

### Running Tests

Run the tests using pytest:
```
pipenv run test
```

Or check code coverage:
```
pipenv run coverage
```

## Project Structure

```
./
├── game/                   # Main package containing all game logic
│   ├── __init__.py         # Package initialization
│   ├── board.py            # Implementation of the 2D game board
│   ├── units/              # Subpackage for all unit-related classes
│   │   ├── __init__.py     # Package initialization
│   │   ├── base_unit.py    # Base Unit class with fundamental stats
│   │   └── unit_types.py   # Specialized unit types
│   ├── game_loop.py        # Implementation of the main game loop
│   └── config.py           # Game configuration settings
├── tests/                  # Directory for all unit tests
│   ├── __init__.py         # Package initialization
│   ├── test_board.py       # Tests for the board module
│   ├── test_units.py       # Tests for the units package
│   └── test_game_loop.py   # Tests for the game_loop module
├── main.py                 # Entry point to run the game
├── Pipfile                 # Pipenv dependency management
└── Pipfile.lock            # Locked dependencies
```

Created with [**Solver**](https://solverai.com)
