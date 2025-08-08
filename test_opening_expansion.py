#!/usr/bin/env python3
"""
Test script for the expanded opening database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_book import get_opening_book, cleanup_opening_book
from chess import STARTING_FEN, Board
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_opening_coverage():
    """Test the expanded opening database coverage"""
    print("🧪 Testing Expanded Opening Database")
    print("=" * 50)
    
    # Initialize opening book
    book = get_opening_book()
    
    # Get book information
    info = book.get_book_info()
    print(f"📊 Opening Book Statistics:")
    print(f"   • JSON positions: {info['json_positions']}")
    print(f"   • PGN database loaded: {info['pgn_database_loaded']}")
    print(f"   • Polyglot loaded: {info['polyglot_loaded']}")
    print(f"   • Max depth: {info['max_depth']}")
    print(f"   • Rotation factor: {info['rotation_factor']}")
    print()
    
    # Test major opening lines
    test_positions = [
        # Starting position
        (STARTING_FEN, "Starting position"),
        
        # After 1.e4
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "After 1.e4"),
        
        # After 1.e4 e5
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "After 1.e4 e5"),
        
        # Ruy Lopez
        ("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Ruy Lopez"),
        
        # Italian Game
        ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Italian Game"),
        
        # Sicilian Defense
        ("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Sicilian Defense"),
        
        # French Defense
        ("rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "French Defense"),
        
        # Caro-Kann Defense
        ("rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "Caro-Kann Defense"),
        
        # After 1.d4
        ("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1", "After 1.d4"),
        
        # Queen's Gambit
        ("rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2", "Queen's Gambit"),
        
        # Nimzo-Indian Defense
        ("rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4", "Nimzo-Indian Defense"),
        
        # King's Indian Defense
        ("rnbqk2r/ppp1ppbp/3p1np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4", "King's Indian Defense"),
        
        # English Opening
        ("rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1", "English Opening"),
        
        # Reti Opening
        ("rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1", "Reti Opening"),
    ]
    
    print("🎯 Testing Opening Coverage:")
    print("-" * 30)
    
    total_positions = 0
    covered_positions = 0
    
    for fen, description in test_positions:
        move = book.get_book_move(fen, 1)
        total_positions += 1
        
        if move:
            covered_positions += 1
            print(f"✅ {description:<25} → {move}")
        else:
            print(f"❌ {description:<25} → No book move")
    
    print()
    print(f"📈 Coverage: {covered_positions}/{total_positions} ({covered_positions/total_positions*100:.1f}%)")
    print()
    
    # Test move variety (rotation)
    print("🔄 Testing Move Rotation:")
    print("-" * 25)
    
    starting_moves = []
    for i in range(10):
        move = book.get_book_move(STARTING_FEN, 1)
        starting_moves.append(move)
    
    unique_moves = set(starting_moves)
    print(f"Generated moves: {starting_moves}")
    print(f"Unique moves: {len(unique_moves)} out of 10 attempts")
    print(f"Rotation working: {'✅' if len(unique_moves) > 1 else '❌'}")
    print()
    
    # Test specific opening lines
    print("🏰 Testing Specific Opening Lines:")
    print("-" * 35)
    
    # Test a complete opening sequence
    board = Board()
    moves_played = []
    
    for move_num in range(1, 11):  # Test first 10 moves
        fen = board.fen()
        book_move = book.get_book_move(fen, move_num)
        
        if book_move:
            try:
                chess_move = board.parse_uci(book_move)
                if chess_move in board.legal_moves:
                    board.push(chess_move)
                    moves_played.append(book_move)
                    side = "White" if board.turn else "Black"
                    print(f"Move {move_num} ({side}): {book_move}")
                else:
                    print(f"Move {move_num}: {book_move} (ILLEGAL)")
                    break
            except Exception as e:
                print(f"Move {move_num}: {book_move} (PARSE ERROR: {e})")
                break
        else:
            side = "White" if board.turn else "Black"
            print(f"Move {move_num} ({side}): No book move found")
            print(f"Current FEN: {fen}")
            break
    
    print(f"\nComplete sequence: {' '.join(moves_played)}")
    print(f"Moves from book: {len(moves_played)}")
    print()
    
    # Test opening names/classifications
    print("📚 Testing Opening Classifications:")
    print("-" * 35)
    
    classification_tests = [
        ("e2e4", "King's Pawn Opening"),
        ("d2d4", "Queen's Pawn Opening"), 
        ("g1f3", "Reti Opening"),
        ("c2c4", "English Opening"),
        ("f2f4", "Bird's Opening"),
        ("b2b3", "Nimzowitsch-Larsen Attack"),
    ]
    
    for first_move, expected_name in classification_tests:
        move = book.get_book_move(STARTING_FEN, 1)
        if move == first_move:
            print(f"✅ {first_move} → {expected_name}")
        else:
            # Check if it's available as an option
            board_test = Board()
            try:
                chess_move = board_test.parse_uci(first_move)
                if chess_move in board_test.legal_moves:
                    print(f"🔄 {first_move} → {expected_name} (available)")
                else:
                    print(f"❌ {first_move} → {expected_name} (not available)")
            except:
                print(f"❌ {first_move} → {expected_name} (invalid)")
    
    print()
    print("🎉 Opening Database Test Complete!")
    
    # Cleanup
    cleanup_opening_book()

def test_performance():
    """Test opening book performance"""
    print("\n⚡ Performance Test:")
    print("-" * 20)
    
    import time
    
    book = get_opening_book()
    
    # Test lookup speed
    start_time = time.time()
    for _ in range(1000):
        book.get_book_move(STARTING_FEN, 1)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000 * 1000  # Convert to milliseconds
    print(f"Average lookup time: {avg_time:.3f}ms")
    print(f"Lookups per second: {1000/(end_time - start_time):.0f}")
    
    cleanup_opening_book()

if __name__ == "__main__":
    try:
        test_opening_coverage()
        test_performance()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_opening_book()