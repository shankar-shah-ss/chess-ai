#!/usr/bin/env python3
"""
Diagnostic script to identify gameplay issues
"""
import sys
import os
sys.path.append('src')

import pygame
from const import *
from game import Game
from square import Square
from move import Move

def test_mouse_interaction():
    """Test mouse click detection and piece movement"""
    print("🔍 Testing mouse interaction...")
    
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game = Game()
    board = game.board
    dragger = game.dragger
    
    print(f"✓ Board size: {WIDTH}x{HEIGHT}")
    print(f"✓ Square size: {SQSIZE}")
    print(f"✓ Game mode: {game.game_mode}")
    print(f"✓ Next player: {game.next_player}")
    
    # Test initial board state
    print("\n📋 Testing initial board state:")
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col].piece
            if piece and row in [0, 1, 6, 7]:
                print(f"  {piece.name} at ({row},{col})")
    
    # Test piece selection
    print("\n🎯 Testing piece selection:")
    test_positions = [(6, 4), (1, 4), (7, 4)]  # White pawn, black pawn, white king
    
    for row, col in test_positions:
        piece = board.squares[row][col].piece
        if piece:
            print(f"  Position ({row},{col}): {piece.color} {piece.name}")
            # Test move calculation
            board.calc_moves(piece, row, col, bool=True)
            print(f"    Valid moves: {len(piece.moves)}")
            if piece.moves:
                for move in piece.moves[:3]:  # Show first 3 moves
                    print(f"      -> ({move.final.row},{move.final.col})")
        else:
            print(f"  Position ({row},{col}): Empty")
    
    pygame.quit()
    return True

def test_move_validation():
    """Test move validation system"""
    print("\n⚖️ Testing move validation...")
    
    game = Game()
    board = game.board
    
    # Test a simple pawn move
    pawn = board.squares[6][4].piece  # White pawn at e2
    if pawn:
        print(f"✓ Found white pawn at e2: {pawn.name}")
        
        # Calculate valid moves
        board.calc_moves(pawn, 6, 4, bool=True)
        print(f"✓ Pawn has {len(pawn.moves)} valid moves")
        
        if pawn.moves:
            # Test first move
            move = pawn.moves[0]
            print(f"✓ Testing move to ({move.final.row},{move.final.col})")
            
            # Check if move is valid
            is_valid = board.valid_move(pawn, move)
            print(f"✓ Move validation result: {is_valid}")
            
            if is_valid:
                print("✓ Move validation working correctly")
                return True
            else:
                print("✗ Move validation failed")
                return False
    
    print("✗ Could not find test piece")
    return False

def test_game_state():
    """Test game state management"""
    print("\n🎮 Testing game state...")
    
    game = Game()
    
    print(f"✓ Game over: {game.game_over}")
    print(f"✓ Next player: {game.next_player}")
    print(f"✓ Game mode: {game.game_mode}")
    print(f"✓ Engine white: {game.engine_white}")
    print(f"✓ Engine black: {game.engine_black}")
    
    # Test mode switching
    print("\n🔄 Testing mode switching:")
    for mode in [0, 1, 2]:
        game.set_game_mode(mode)
        print(f"  Mode {mode}: white_engine={game.engine_white}, black_engine={game.engine_black}")
    
    return True

def test_event_handling():
    """Test event handling system"""
    print("\n🖱️ Testing event handling...")
    
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    # Simulate mouse click on e2 pawn
    click_x = 4 * SQSIZE + SQSIZE // 2  # e file
    click_y = 6 * SQSIZE + SQSIZE // 2  # 2nd rank
    
    clicked_row = click_y // SQSIZE
    clicked_col = click_x // SQSIZE
    
    print(f"✓ Simulated click at pixel ({click_x},{click_y})")
    print(f"✓ Converted to square ({clicked_row},{clicked_col})")
    print(f"✓ Expected: (6,4) for e2")
    
    if clicked_row == 6 and clicked_col == 4:
        print("✓ Mouse coordinate conversion working")
        pygame.quit()
        return True
    else:
        print("✗ Mouse coordinate conversion failed")
        pygame.quit()
        return False

def main():
    print("🚀 Chess AI Diagnostic Tool")
    print("=" * 40)
    
    tests = [
        ("Mouse Interaction", test_mouse_interaction),
        ("Move Validation", test_move_validation),
        ("Game State", test_game_state),
        ("Event Handling", test_event_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 40)
    print("📊 DIAGNOSTIC SUMMARY:")
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    failed_tests = [name for name, result in results if not result]
    if failed_tests:
        print(f"\n🔧 ISSUES FOUND:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\nThe game may not be playable due to these issues.")
    else:
        print("\n🎉 All tests passed! The game should be playable.")

if __name__ == '__main__':
    main()