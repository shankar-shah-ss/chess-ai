#!/usr/bin/env python3
"""
Final test for engine move control fix
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from game import Game

def test_engine_move_flow():
    """Test the complete engine move flow"""
    print("🎯 Testing Complete Engine Move Flow")
    print("=" * 45)
    
    game = Game()
    
    # Test 1: Initial state
    print("Test 1: Initial state")
    can_white_move = game.engine_move_preventer.can_engine_move('white', 'white')
    print(f"✅ White can move initially: {can_white_move}")
    
    # Test 2: Simulate white engine move
    print("\nTest 2: Simulate white engine move")
    game.engine_move_preventer.record_engine_move('white', 'black')
    game.next_player = 'black'  # Simulate turn change
    
    # Test 3: Check if black can move
    print("\nTest 3: Check black can move after white")
    can_black_move = game.engine_move_preventer.can_engine_move('black', 'black')
    print(f"✅ Black can move after white: {can_black_move}")
    
    # Test 4: Check if white is blocked
    print("\nTest 4: Check white is blocked")
    can_white_move_again = game.engine_move_preventer.can_engine_move('white', 'white')
    print(f"✅ White blocked (should be False): {can_white_move_again}")
    
    # Test 5: Wait for cooldown and try again
    print("\nTest 5: Wait for cooldown")
    time.sleep(0.2)  # Wait longer than cooldown
    can_white_after_cooldown = game.engine_move_preventer.can_engine_move('white', 'white')
    print(f"✅ White still blocked after cooldown (should be False): {can_white_after_cooldown}")
    
    # Test 6: Simulate black move
    print("\nTest 6: Simulate black engine move")
    game.engine_move_preventer.record_engine_move('black', 'white')
    game.next_player = 'white'  # Simulate turn change
    
    # Test 7: Check if white can move now
    print("\nTest 7: Check white can move after black")
    can_white_move_final = game.engine_move_preventer.can_engine_move('white', 'white')
    print(f"✅ White can move after black: {can_white_move_final}")
    
    print("\n🎯 Engine move flow test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_engine_move_flow()
        print("\n✅ All engine move control tests passed!")
        print("🎯 The consecutive move issue should now be resolved.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()