#!/usr/bin/env python3
"""
Main entry point for the ecosystem simulation game.

This script initializes and runs the ecosystem simulation game.
"""

import random
import time
import argparse
import threading # Added threading
from game.board import Board, Position
from game.game_loop import GameLoop
from game.config import Config
from game.units.unit_types import Predator, Scavenger, Grazer
from game.plants.plant_types import BasicPlant # Import BasicPlant
from game.visualization import Visualization
from web_server import set_game_board # Added set_game_board

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ecosystem Simulation Game")
    parser.add_argument("-c", "--config", default="config.json", help="Path to config file")
    parser.add_argument("--no-display", action="store_true", help="Disable visual display")
    parser.add_argument("--turns", type=int, help="Override number of turns")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--serve-web", action="store_true", help="Start the FastAPI web server for the game interface")
    parser.add_argument("--port", type=int, default=8099, help="Port number for the web server (default: 8099)")
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
    print(f"--- Unit Stats (Turn {current_turn}) ---")
    for unit in game_loop.units:
        print(f"  - Type: {unit.unit_type}, Pos: ({unit.position.x}, {unit.position.y}), "
              f"Energy: {unit.energy}, State: {unit.state}, Alive: {unit.alive}")
    print(f"--- End Unit Stats ---")

def main():
    """Main function to run the game."""
    args = parse_args()

    # Load configuration first, as it's needed by both paths
    config = Config(args.config)

    if args.serve_web:
        try:
            import uvicorn
            from web_server import app  # Assuming web_server.py and app object exist

            # Set up the game to get the board
            game_loop, _ = setup_game(config) # Visualizer not used in web mode
            set_game_board(game_loop.board) # Pass the board to the web server

            # Define the game loop runner function
            def run_game_loop(game_loop_instance):
                game_loop_instance.is_running = True # Ensure it's set to run
                turn_delay = config.get("game", "turn_delay", 0.1) # Get turn_delay, default if not found
                while game_loop_instance.is_running and \
                      game_loop_instance.current_turn < game_loop_instance.max_turns:
                    game_loop_instance.process_turn()
                    # print(f"Web server background game turn: {game_loop_instance.current_turn}") # Optional: for debugging
                    time.sleep(turn_delay) # Use configured turn delay

            # Create and start the game thread
            game_thread = threading.Thread(target=run_game_loop, args=(game_loop,), daemon=True)
            game_thread.start()

            print(f"Starting web server on http://0.0.0.0:{args.port}")
            print(f"Access the game interface at http://0.0.0.0:{args.port}/static/index.html")
            uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
        except ImportError as e:
            print(f"Error importing modules for web server: {e}")
            print("Please ensure 'uvicorn' and 'fastapi' are installed and web_server.py is correctly set up.")
        except Exception as e:
            print(f"Failed to start web server or run game thread: {e}")
        return  # Exit after attempting to start/starting the server
    
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
