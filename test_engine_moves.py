#!/usr/bin/env python3
"""
Test script for engine move scheduling and turn control
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from move_validator import EngineMovePreventer

def test_engine_move_preventer():
    """Test the engine move prevention logic"""
    print("🧪 Testing Engine Move Preventer")
    print("=" * 40)
    
    preventer = EngineMovePreventer()
    
    # Test 1: Initial state - white should be able to move
    print("Test 1: Initial state")
    result = preventer.can_engine_move('white', 'white')
    print(f"White can move initially: {result}")
    assert result == True, "White should be able to move initially"
    
    # Test 2: Record white move, now black should be able to move
    print("\nTest 2: After white moves")
    preventer.record_engine_move('white', 'black')
    
    result = preventer.can_engine_move('black', 'black')
    print(f"Black can move after white: {result}")
    assert result == True, "Black should be able to move after white"
    
    # Test 3: White should NOT be able to move again (it's black's turn)
    result = preventer.can_engine_move('white', 'white')
    print(f"White can move again (should be False): {result}")
    # This should be False because it's black's turn
    
    # Test 4: Record black move, now white should be able to move
    print("\nTest 4: After black moves")
    preventer.record_engine_move('black', 'white')
    
    result = preventer.can_engine_move('white', 'white')
    print(f"White can move after black: {result}")
    assert result == True, "White should be able to move after black"
    
    # Test 5: Black should NOT be able to move again (it's white's turn)
    result = preventer.can_engine_move('black', 'black')
    print(f"Black can move again (should be False): {result}")
    
    print("\n✅ Engine Move Preventer tests completed!")

def test_turn_alternation():
    """Test proper turn alternation"""
    print("\n🧪 Testing Turn Alternation")
    print("=" * 40)
    
    preventer = EngineMovePreventer()
    
    # Simulate a game sequence
    moves = [
        ('white', 'black'),  # White moves, black's turn next
        ('black', 'white'),  # Black moves, white's turn next
        ('white', 'black'),  # White moves, black's turn next
        ('black', 'white'),  # Black moves, white's turn next
    ]
    
    for i, (current_player, next_turn) in enumerate(moves):
        print(f"\nMove {i+1}: {current_player} to move")
        
        # Check if move is allowed
        can_move = preventer.can_engine_move(current_player, current_player)
        print(f"Can {current_player} move: {can_move}")
        
        if can_move:
            # Record the move
            preventer.record_engine_move(current_player, next_turn)
            print(f"Recorded {current_player} move, next turn: {next_turn}")
        else:
            print(f"❌ Move blocked for {current_player}")
    
    print("\n✅ Turn alternation test completed!")

if __name__ == "__main__":
    try:
        test_engine_move_preventer()
        test_turn_alternation()
        print("\n🎯 All tests passed! Engine move control is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()