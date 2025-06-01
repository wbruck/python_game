#!/usr/bin/env python3
"""
Main entry point for the ecosystem simulation game.

This script initializes and runs the ecosystem simulation game.
"""

import random
import time
import argparse
from game.board import Board, Position
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import Predator, Scavenger, Grazer
from game.plants.plant_types import BasicPlant # Import BasicPlant

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ecosystem Simulation Game")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config file")
    parser.add_argument("--no-display", action="store_true", help="Disable visual display")
    parser.add_argument("--turns", type=int, help="Override number of turns")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    return parser.parse_args()

def setup_game(config):
    """Set up the game with the given configuration."""
    # Create board
    board_width = config.get("board", "width")
    board_height = config.get("board", "height")
    board = Board(board_width, board_height)
    
    # Create game loop
    max_turns = config.get("game", "max_turns")
    game_loop = GameLoop(board, max_turns=max_turns)
    
    # Create and place units
    unit_counts = config.get("units", "initial_count")
    
    # Helper function to place a unit at a random empty position
    def place_unit_randomly(unit_class):
        """Place a unit at a random empty position using place_object."""
        while True:
            x = random.randint(0, board_width - 1)
            y = random.randint(0, board_height - 1)
            unit = unit_class(x=x, y=y)
            if board.place_object(unit, x, y):
                game_loop.add_unit(unit)
                return unit
    # Place predators
    for _ in range(unit_counts.get("predator", 0)):
        place_unit_randomly(Predator)
    
    # Place scavengers
    for _ in range(unit_counts.get("scavenger", 0)):
        place_unit_randomly(Scavenger)
    
    # Place grazers
    for _ in range(unit_counts.get("grazer", 0)):
        place_unit_randomly(Grazer)
    
    # Place initial plants
    num_plants = config.get("plants", "initial_count")
    
    # Define a simple plant factory. BasePlant requires a position.
    # place_random_plants will handle the actual random position.
    # The board's place_object method updates its internal tracking
    # but does not update the plant's own `position` attribute if it's a complex object.
    # This is a known limitation for now.
    def plant_factory():
        # BasicPlant(position, base_energy, growth_rate, regrowth_time)
        # Using default values from BasicPlant or arbitrary valid ones for now.
        # The key is that `place_random_plants` needs a callable that returns a plant instance.
        # The position passed here is a placeholder.
        return BasicPlant(position=Position(0,0))

    placed_plant_positions = board.place_random_plants(num_plants, plant_factory)

    # Add placed plants to the game loop
    for pos in placed_plant_positions:
        plant_object = board.get_object(pos.x, pos.y)
        if plant_object: # Ensure a plant was actually placed and retrieved
            game_loop.add_plant(plant_object)

    return game_loop

def display_game(game_loop):
    """Display the current state of the game."""
    # Simple placeholder for visualization
    # Will be replaced with proper visualization later
    stats = game_loop.get_stats()
    print(f"Turn: {stats['turn']}/{stats['max_turns']}")
    print(f"Units: {stats['alive_units']} alive, {stats['dead_units']} dead")
    print(f"Plants: {stats['plants']}")
    print("-" * 40)

def main():
    """Main function to run the game."""
    args = parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Load configuration
    config = Config(args.config)
    
    # Override config with command line arguments
    if args.turns is not None:
        config.set("game", "max_turns", args.turns)
    
    # Set up the game
    game_loop = setup_game(config)
    
    # Run the game loop with display
    game_loop.is_running = True
    
    while game_loop.is_running and game_loop.current_turn < game_loop.max_turns:
        game_loop.process_turn()
        
        if not args.no_display:
            display_game(game_loop)
            time.sleep(config.get("game", "turn_delay"))
    
    # Display final state
    print("\nGame finished!")
    display_game(game_loop)

if __name__ == "__main__":
    main()
