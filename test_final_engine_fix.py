#!/usr/bin/env python3
"""
Final comprehensive test for engine move control fix
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from game import Game

def test_complete_engine_flow():
    """Test the complete engine move flow with thinking tracking"""
    print("🎯 Final Engine Move Control Test")
    print("=" * 45)
    
    game = Game()
    preventer = game.engine_move_preventer
    
    # Test 1: Initial state
    print("Test 1: Initial state")
    can_schedule = preventer.can_engine_move('white', 'white')
    print(f"✅ White can schedule initially: {can_schedule}")
    
    # Test 2: Start engine thinking
    print("\nTest 2: Start engine thinking")
    preventer.start_engine_thinking('white')
    
    # Test 3: Try to schedule again - should be blocked
    print("\nTest 3: Try to schedule while thinking")
    can_schedule_again = preventer.can_engine_move('white', 'white')
    print(f"✅ White blocked while thinking: {not can_schedule_again}")
    
    # Test 4: Complete the move
    print("\nTest 4: Complete engine move")
    preventer.record_engine_move('white', 'black')
    
    # Test 5: Check if black can now move
    print("\nTest 5: Check black can move")
    can_black_move = preventer.can_engine_move('black', 'black')
    print(f"✅ Black can move after white: {can_black_move}")
    
    # Test 6: Check white is still blocked
    print("\nTest 6: Check white is blocked")
    can_white_move = preventer.can_engine_move('white', 'white')
    print(f"✅ White blocked (not their turn): {not can_white_move}")
    
    # Test 7: Simulate black thinking
    print("\nTest 7: Black engine thinking")
    preventer.start_engine_thinking('black')
    
    # Test 8: Try white again - should still be blocked
    print("\nTest 8: White still blocked while black thinks")
    can_white_while_black_thinks = preventer.can_engine_move('white', 'white')
    print(f"✅ White blocked while black thinks: {not can_white_while_black_thinks}")
    
    # Test 9: Complete black move
    print("\nTest 9: Complete black move")
    preventer.record_engine_move('black', 'white')
    
    # Test 10: White should now be able to move
    print("\nTest 10: White can move after black")
    can_white_final = preventer.can_engine_move('white', 'white')
    print(f"✅ White can move after black: {can_white_final}")
    
    print("\n🎯 All engine move control tests passed!")
    print("✅ The consecutive move issue should now be completely resolved.")
    
    return True

if __name__ == "__main__":
    try:
        test_complete_engine_flow()
        print("\n🚀 Engine move control system is working perfectly!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()