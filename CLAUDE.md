# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Development Environment
- `pipenv install --dev` - Install dependencies
- `pipenv shell` - Activate virtual environment

### Testing
- `pipenv run test` - Run all tests
- `pipenv run pytest -m integration` - Run only integration tests  
- `pipenv run pytest -m "not integration"` - Run only unit tests
- `pipenv run coverage` - Run tests with coverage report

### Code Quality
- `pipenv run lint` - Run flake8 linter

### Running the Application
- `python main.py` - Run CLI simulation
- `python main.py --no-display` - Run without visualization
- `python main.py --turns 100 --seed 42` - Run with specific parameters
- `uvicorn api_server:app --reload --port 8000` - Start web API server

## Architecture Overview

This is a turn-based ecosystem simulation with three main components:

### Core Game Architecture
- **Board**: 2D grid-based world using Position dataclass for coordinates
- **GameLoop**: Turn-based processor managing units, plants, and environmental cycles (day/night, seasons)
- **Units**: Inheritance hierarchy with BaseUnit providing RPG-style stats (HP, energy, strength, speed, vision) and state machine (idle, hunting, fleeing, feeding, wandering, resting)
- **Plants**: Growth/decay lifecycle managed through PlantManager

### Unit System
Units follow a centralized movement and vision system with template-based initialization:
- **Predators**: High strength, medium speed, lower vision
- **Scavengers**: Medium stats, highest vision for finding corpses
- **Grazers**: Low strength, high energy, focused on plant consumption

### API Architecture
FastAPI server provides REST endpoints for web-based interaction:
- Game instances by ID with board state retrieval
- Turn advancement via POST requests  
- Individual entity statistics access

### Configuration System
JSON-based configuration in `config.json` with hierarchical access via Config class. Auto-generates defaults if missing.

### Testing Strategy
- Unit tests for individual components
- Integration tests marked with `@pytest.mark.integration`
- Comprehensive coverage including edge cases and lifecycle testing

## Key Implementation Notes

- All units maintain board reference for centralized collision detection
- Position validation occurs at board level, not unit level
- Plant placement uses factory pattern with position placeholders
- Game state persists through GameLoop, not individual entities
- Web interface accesses game state via read-only API endpoints