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

### API Usage

The simulation can also be controlled and viewed via a FastAPI web server and a simple web UI.

**Starting the API Server:**

To start the API server, run the following command from the project root (where `api_server.py` is located), ensuring your `pipenv shell` is active:

```bash
uvicorn api_server:app --reload --port 8000
```
*   `--reload`: Enables auto-reloading when code changes (for development).
*   `--port 8000`: Specifies the port number (default is 8000). You can change this if needed.

**Accessing the Web UI:**

Once the server is running, you can access the basic web interface by navigating to:
`http://localhost:8000/static/index.html` in your web browser.

**API Endpoints:**

The server provides the following main API endpoints. A default game instance with ID `default_game` is created when the server starts.

*   **`GET /game/{game_id}/board`**
    *   Description: Retrieves the current state of the game board for the specified `game_id`. This includes the board dimensions, current turn number, and a list of all entities (units and plants) with their positions and basic details.
    *   Example: `GET /game/default_game/board`

*   **`POST /game/{game_id}/update`**
    *   Description: Advances the game simulation by one turn for the specified `game_id`. The request body is empty. The response contains the updated board state, similar to the `/board` endpoint.
    *   Example: `POST /game/default_game/update`

*   **`GET /game/{game_id}/entity/{entity_id}`**
    *   Description: Retrieves detailed statistics for a specific entity (unit or plant) identified by `entity_id` within the given `game_id`. The `entity_id` can be obtained from the responses of the `/board` or `/update` endpoints.
    *   Example: `GET /game/default_game/entity/default_game_Predator_162530120` (Note: actual entity IDs will vary)

### Running Tests

Run the tests using pytest:
```
pipenv run test
```

Or check code coverage:
```
pipenv run coverage
```

#### Running or Excluding Integration Tests

Integration tests are marked with `@pytest.mark.integration`.

- To run only integration tests:
  ```
  pipenv run pytest -m integration
  ```
- To run only unit tests (exclude integration tests):
  ```
  pipenv run pytest -m "not integration"
  ```

## Project Structure

```
./
├── Pipfile                 # Pipenv dependency management file
├── Pipfile.lock            # Pipenv lock file for reproducible builds
├── README.md               # This README file
├── config.json             # User-configurable game settings (auto-generated if not present)
├── pytest.ini              # Configuration file for pytest
├── main.py                 # Main entry point to run the game
├── game/                   # Core package containing all game logic
│   ├── __init__.py         # Package initialization
│   ├── board.py            # Game board implementation (grid, positions)
│   ├── config.py           # Configuration loading and management
│   ├── game_loop.py        # Main game loop and turn processing
│   ├── visualization.py    # Text-based display logic (optional)
│   ├── units/              # Subpackage for unit-related classes
│   │   ├── __init__.py     # Package initialization
│   │   ├── base_unit.py    # Base class for all unit types
│   │   └── unit_types.py   # Specific unit implementations (Predator, Grazer, etc.)
│   └── plants/             # Subpackage for plant-related classes
│       ├── __init__.py     # Package initialization
│       ├── base_plant.py   # Base class for all plant types
│       ├── plant_types.py  # Specific plant implementations (BasicPlant, etc.)
│       └── plant_manager.py # Manages plant lifecycle (not fully implemented/used yet)
├── tests/                  # Directory for all automated tests
│   ├── __init__.py         # Package initialization
│   ├── conftest.py         # Pytest fixtures and configuration
│   ├── test_board.py       # Tests for the game board
│   ├── test_config.py      # Tests for configuration handling
│   ├── test_game_loop.py   # Tests for the main game loop
│   ├── test_units.py       # Tests for general unit behaviors (combines base_unit and unit_types)
│   ├── test_base_unit.py   # Specific tests for base_unit functionalities
│   ├── test_unit_types.py  # Specific tests for individual unit type behaviors
│   ├── test_plants.py      # Tests for plant functionalities
│   ├── test_visualization.py # Tests for the visualization module
│   └── test_integration.py # Integration tests for overall game mechanics (and other test_integration_*.py files)
└── docs/                   # Project documentation
    ├── README.md           # Overview of the documentation
    ├── architecture.md     # High-level architecture details
    ├── configuration.md    # Details on config.json settings
    └── ...                 # Other documentation files (API, tutorials)
```

## Features

*   Turn-based ecosystem simulation.
*   Multiple unit types with unique behaviors (Predators, Scavengers, Grazers).
*   Variety of plant types (e.g., BasicPlant) serving as food sources.
*   2D grid-based game board with configurable dimensions.
*   Day/night cycle and seasonal changes affecting gameplay (though effects might be basic currently).
*   Units possess stats (HP, energy, strength, speed, vision) and can level up based on actions.
*   Configuration-driven game parameters via `config.json`, with defaults provided.
*   Line-of-sight visibility for units.
*   Basic text-based display with an option for no-display mode for faster simulations.
*   Comprehensive test suite using pytest, including unit and integration tests.
*   Dependency management using Pipenv.

Created with [**Solver**](https://solverai.com)
