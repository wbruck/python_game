#!/usr/bin/env python3
"""
Save system for the ecosystem simulation game.

This module provides basic save/load functionality.
"""

import json
import random
from pathlib import Path

from .board import Board, MovementType
from .game_loop import GameLoop, TimeOfDay, Season
from .config import Config

def save_game(game_loop, config, filename):
    """Save current game state to a file."""
    save_dir = Path("saves")
    save_dir.mkdir(exist_ok=True)
    save_path = save_dir / filename

    data = {
        "version": "1.0.0",
        "config": config.config,
        "game_state": {
            "current_turn": game_loop.current_turn,
            "time_of_day": game_loop.time_of_day.value,
            "season": game_loop.season.value,
            "random_state": random.getstate()
        },
        "board": {
            "width": game_loop.board.width,
            "height": game_loop.board.height,
            "movement_type": game_loop.board.movement_type.value
        },
        "units": [],
        "plants": []
    }

    # Save units
    for unit in game_loop.units:
        pos = game_loop.board._object_positions.get(unit)
        if pos:
            unit_data = {
                "type": unit.__class__.__name__,
                "position": {"x": pos.x, "y": pos.y},
                "stats": {
                    "hp": unit.hp,
                    "energy": unit.energy,
                    "strength": unit.strength,
                    "speed": unit.speed,
                    "vision": unit.vision,
                    "alive": unit.alive,
                    "state": unit.state,
                    "decay_stage": unit.decay_stage
                }
            }
            data["units"].append(unit_data)

    # Save plants
    for plant in game_loop.plants:
        pos = game_loop.board._object_positions.get(plant)
        if pos:
            plant_data = {
                "type": plant.__class__.__name__,
                "position": {"x": pos.x, "y": pos.y},
                "state": {
                    "growth_stage": plant.state.growth_stage,
                    "energy_content": plant.state.energy_content,
                    "is_alive": plant.state.is_alive
                }
            }
            data["plants"].append(plant_data)

    with open(save_path, "w") as f:
        json.dump(data, f, indent=2)

    return str(save_path)

def load_game(save_path):
    """Load game state from a file."""
    with open(save_path, "r") as f:
        data = json.load(f)

    config = Config()
    config.config = data["config"]
    
    board = Board(
        width=data["board"]["width"],
        height=data["board"]["height"],
        movement_type=MovementType(data["board"]["movement_type"])
    )
    
    game_loop = GameLoop(board, config=config)
    game_loop.current_turn = data["game_state"]["current_turn"]
    game_loop.time_of_day = TimeOfDay(data["game_state"]["time_of_day"])
    game_loop.season = Season(data["game_state"]["season"])
    random.setstate(data["game_state"]["random_state"])

    # Restore units
    from .units.unit_types import Predator, Scavenger, Grazer
    unit_types = {
        "Predator": Predator,
        "Scavenger": Scavenger,
        "Grazer": Grazer
    }

    for unit_data in data.get("units", []):
        unit_class = unit_types.get(unit_data["type"])
        if unit_class:
            pos = unit_data["position"]
            unit = unit_class(pos["x"], pos["y"])
            for key, value in unit_data["stats"].items():
                setattr(unit, key, value)
            game_loop.add_unit(unit)
            board.place_object(unit, pos["x"], pos["y"])

    # Restore plants
    from .plants.plant_types import BasicPlant, EnergyRichPlant, FastGrowingPlant
    plant_types = {
        "BasicPlant": BasicPlant,
        "EnergyRichPlant": EnergyRichPlant,
        "FastGrowingPlant": FastGrowingPlant
    }

    for plant_data in data.get("plants", []):
        plant_class = plant_types.get(plant_data["type"])
        if plant_class:
            pos = plant_data["position"]
            plant = plant_class(Position(pos["x"], pos["y"]))
            for key, value in plant_data["state"].items():
                setattr(plant.state, key, value)
            game_loop.add_plant(plant)
            board.place_object(plant, pos["x"], pos["y"])
    
    return game_loop, config

def list_saves():
    """List all available save files."""
    save_dir = Path("saves")
    saves = {}
    if save_dir.exists():
        for save_file in save_dir.glob("*.json"):
            saves[save_file.stem] = str(save_file)
    return saves
