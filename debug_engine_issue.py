#!/usr/bin/env python3
"""
Debug script to identify the engine move issue
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from game import Game

def debug_engine_state():
    """Debug the engine move state"""
    print("🔍 Debugging Engine Move State")
    print("=" * 40)
    
    game = Game()
    
    # Enable both engines for testing
    game.engine_white = True
    game.engine_black = True
    
    print(f"Initial state:")
    print(f"  Next player: {game.next_player}")
    print(f"  White engine: {game.engine_white}")
    print(f"  Black engine: {game.engine_black}")
    
    # Check initial scheduling ability
    can_schedule = game.engine_move_preventer.can_engine_move(game.next_player, game.next_player)
    print(f"  Can schedule for {game.next_player}: {can_schedule}")
    
    # Simulate the main loop condition
    should_schedule = (game.next_player == 'white' and game.engine_white) or \
                     (game.next_player == 'black' and game.engine_black)
    print(f"  Should schedule (main loop condition): {should_schedule}")
    
    # Test what happens when we try to schedule multiple times
    print(f"\nTesting multiple scheduling attempts:")
    for i in range(5):
        can_schedule = game.engine_move_preventer.can_engine_move(game.next_player, game.next_player)
        print(f"  Attempt {i+1}: Can schedule {game.next_player}: {can_schedule}")
        if not can_schedule:
            break
        time.sleep(0.05)  # Small delay
    
    print(f"\n🔍 Debug completed")

if __name__ == "__main__":
    debug_engine_state()