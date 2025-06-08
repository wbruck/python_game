#!/usr/bin/env python3
"""
Main entry point for the ecosystem simulation game.

This script initializes and runs the ecosystem simulation game.
"""

import random
import time
import argparse
# Removed: import threading
from game.board import Board, Position
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import Predator, Scavenger, Grazer
from game.plants.plant_types import BasicPlant # Import BasicPlant
from game.plants.plant_manager import PlantManager
from game.visualization import Visualization
# Removed: from web_server import set_game_board
import sys # Import sys for isatty()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ecosystem Simulation Game")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config file")
    parser.add_argument("--no-display", action="store_true", help="Disable visual display")
    parser.add_argument("--turns", type=int, help="Override number of turns")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    # Removed: parser.add_argument("--serve-web", ...)
    # Removed: parser.add_argument("--port", ...)
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
            unit = unit_class(x=x, y=y, board=board)
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
    
    # Initialize plant manager and generate initial plants
    plant_manager = PlantManager(board, config.config)
    plant_manager.generate_initial_plants()
    
    # Add plants to game loop
    for plant in plant_manager.plants.values():
        game_loop.add_plant(plant)
        
    # Store plant manager reference in game loop for updates
    game_loop.plant_manager = plant_manager

    visualizer = Visualization(board)
    return game_loop, visualizer

def display_game(game_loop):
    """Display the current state of the game."""
    # Simple placeholder for visualization
    # Will be replaced with proper visualization later
    # stats = game_loop.get_stats()
    # print(f"Turn: {stats['turn']}/{stats['max_turns']}")
    # print(f"Units: {stats['alive_units']} alive, {stats['dead_units']} dead")
    # print(f"Plants: {stats['plants']}")
    # print("-" * 40)
    pass # Contents commented out as per instructions

def print_unit_stats(game_loop, current_turn):
    """Prints statistics for each unit."""
    print(f"--- Unit Stats (Turn {current_turn}) [FIXED VERSION] ---")
    
    # Helper function to check if unit is still on the board
    def is_unit_on_board(unit):
        if not game_loop.board.is_valid_position(unit.x, unit.y):
            return False
        return game_loop.board.grid[unit.y][unit.x] == unit
    
    # Get units that are still relevant to the game (alive or still on board)
    relevant_units = [unit for unit in game_loop.units if unit.alive or is_unit_on_board(unit)]
    
    # Categorize relevant units
    alive_units = [unit for unit in relevant_units if unit.alive]
    dead_units = [unit for unit in relevant_units if not unit.alive]
    
    if alive_units:
        print("\nAlive Units:")
        for unit in alive_units:
            print(f"  - [{unit.uuid}] Type: {unit.unit_type}, Pos: ({unit.x}, {unit.y}), "
                  f"Energy: {unit.energy}, State: {unit.state}")
    
    if dead_units:
        print("\nDead Units (still on board):")
        for unit in dead_units:
            decay_info = f", Decay: {getattr(unit, 'decay_stage', 'N/A')}" if hasattr(unit, 'decay_stage') else ""
            print(f"  - [{unit.uuid}] Type: {unit.unit_type}, Pos: ({unit.x}, {unit.y}), "
                  f"State: {unit.state}{decay_info}")
    
    # Show total counts for clarity
    total_in_game = len(game_loop.units)
    total_shown = len(relevant_units)
    fully_decayed = total_in_game - total_shown
    
    if fully_decayed > 0:
        print(f"\nNote: {fully_decayed} fully decayed unit(s) not shown (removed from board)")
    
    print(f"\n--- End Unit Stats ---")
    if sys.stdin.isatty(): # Check if running in an interactive terminal
        input("Press Enter to continue...")
    else:
        print("Non-interactive mode, continuing without pause...")

def main():
    """Main function to run the game."""
    args = parse_args()

    # Load configuration first
    config = Config(args.config)

    # Removed the entire 'if args.serve_web:' block
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Config already loaded above
    
    # Override config with command line arguments
    if args.turns is not None:
        config.set("game", "max_turns", args.turns)
    
    # Set up the game
    game_loop, visualizer = setup_game(config)
    
    # Run the game loop with display
    game_loop.is_running = True
    
    visualization_update_frequency = config.get("game", "visualization_update_frequency")
    unit_stats_print_frequency = config.get("game", "unit_stats_print_frequency")

    while game_loop.is_running and game_loop.current_turn < game_loop.max_turns:
        game_loop.process_turn()
        
        if not args.no_display:
            if visualization_update_frequency > 0 and \
               game_loop.current_turn % visualization_update_frequency == 0:
                visualizer.render()

            if unit_stats_print_frequency > 0 and \
               game_loop.current_turn % unit_stats_print_frequency == 0:
                print_unit_stats(game_loop, game_loop.current_turn)

            # Only sleep if something was displayed
            time.sleep(config.get("game", "turn_delay"))

    # Display final state
    print("\nGame finished!")
    if not args.no_display:
        visualizer.render() # Final render

if __name__ == "__main__":
    main()
