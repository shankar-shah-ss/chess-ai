#!/usr/bin/env python3
"""
Diagnose opening book prioritization - check if book moves are properly prioritized over engine moves
"""

import sys
import os
import time
from typing import Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from engine import ChessEngine
    from opening_book import OpeningBook
    from chess import STARTING_FEN, Board
    import chess
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

def test_book_prioritization():
    """Test if book moves are properly prioritized over engine calculation"""
    print("🔍 Diagnosing Opening Book Prioritization")
    print("=" * 50)
    
    # Test positions where book should have moves
    test_positions = [
        {
            'name': 'Starting Position',
            'fen': STARTING_FEN,
            'move_number': 1,
            'expected_book_moves': ['e2e4', 'd2d4', 'g1f3', 'c2c4']
        },
        {
            'name': 'After 1.e4',
            'fen': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
            'move_number': 2,
            'expected_book_moves': ['e7e5', 'c7c5', 'e7e6', 'c7c6']
        },
        {
            'name': 'After 1.e4 e5',
            'fen': 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2',
            'move_number': 3,
            'expected_book_moves': ['g1f3', 'f1c4', 'b1c3', 'd2d3']
        }
    ]
    
    print("🎯 Testing Book Move Availability")
    print("-" * 35)
    
    # First, test the opening book directly
    try:
        book = OpeningBook()
        
        for pos in test_positions:
            print(f"\n📍 {pos['name']}:")
            print(f"   FEN: {pos['fen']}")
            print(f"   Move number: {pos['move_number']}")
            
            # Check what book returns
            book_move = book.get_book_move(pos['fen'], pos['move_number'])
            
            if book_move:
                print(f"   ✅ Book has move: {book_move}")
                
                # Check if it's one of the expected moves
                if book_move in pos['expected_book_moves']:
                    print(f"   ✅ Move is expected: {book_move} in {pos['expected_book_moves']}")
                else:
                    print(f"   ⚠️ Unexpected move: {book_move}, expected one of {pos['expected_book_moves']}")
            else:
                print(f"   ❌ No book move found")
                print(f"   Expected one of: {pos['expected_book_moves']}")
        
    except Exception as e:
        print(f"❌ Error testing book directly: {e}")
    
    print(f"\n🎯 Testing Engine Book Integration")
    print("-" * 40)
    
    # Test with different engine configurations
    configs = [
        (10, 12, "Intermediate"),
        (20, 20, "Maximum")
    ]
    
    for skill, depth, label in configs:
        print(f"\n🔧 Testing {label} (Skill {skill}, Depth {depth})")
        print("-" * 30)
        
        try:
            engine = ChessEngine(skill_level=skill, depth=depth, use_opening_book=True)
            
            for pos in test_positions:
                print(f"\n   📍 {pos['name']}:")
                
                # Set position
                engine.set_position(pos['fen'])
                engine.move_count = pos['move_number'] - 1
                
                # Time the move selection
                start_time = time.time()
                chosen_move = engine.get_best_move()
                end_time = time.time()
                
                move_time_ms = (end_time - start_time) * 1000
                
                print(f"      Chosen move: {chosen_move}")
                print(f"      Time taken: {move_time_ms:.1f}ms")
                
                # Determine source
                if move_time_ms < 100:  # Very fast = likely book
                    source = "📖 Book (fast)"
                    print(f"      Source: {source}")
                    
                    # Verify it's actually from book
                    if engine.opening_book:
                        book_move = engine.opening_book.get_book_move(pos['fen'], pos['move_number'])
                        if book_move == chosen_move:
                            print(f"      ✅ Confirmed: Move matches book suggestion")
                        else:
                            print(f"      ⚠️ Warning: Fast move but doesn't match book ({book_move})")
                    
                else:  # Slow = engine calculation
                    source = "🤖 Engine (slow)"
                    print(f"      Source: {source}")
                    
                    # Check if book had a move available
                    if engine.opening_book:
                        book_move = engine.opening_book.get_book_move(pos['fen'], pos['move_number'])
                        if book_move:
                            print(f"      ❌ ISSUE: Book had move ({book_move}) but engine calculated instead!")
                            print(f"      This suggests book prioritization may not be working correctly")
                        else:
                            print(f"      ✅ Correct: No book move available, engine calculation expected")
                
                # Check if move is reasonable
                if chosen_move in pos['expected_book_moves']:
                    print(f"      ✅ Move quality: Good (matches expected book moves)")
                else:
                    print(f"      ⚠️ Move quality: Unexpected (not in {pos['expected_book_moves']})")
            
            engine.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error testing {label}: {e}")

def test_book_vs_engine_preference():
    """Test specific scenarios where book and engine might choose different moves"""
    print(f"\n🤔 Testing Book vs Engine Preference")
    print("=" * 40)
    
    print("This test checks if the engine properly prioritizes book moves")
    print("even when the engine might calculate a different 'best' move.")
    print()
    
    # Test position where book and engine might differ
    test_fen = STARTING_FEN
    
    try:
        # Test with book enabled
        print("🔧 Test 1: Engine WITH opening book")
        engine_with_book = ChessEngine(skill_level=20, depth=20, use_opening_book=True)
        engine_with_book.set_position(test_fen)
        
        start_time = time.time()
        move_with_book = engine_with_book.get_best_move()
        time_with_book = (time.time() - start_time) * 1000
        
        print(f"   Move chosen: {move_with_book}")
        print(f"   Time taken: {time_with_book:.1f}ms")
        print(f"   Source: {'📖 Book' if time_with_book < 100 else '🤖 Engine'}")
        
        engine_with_book.cleanup()
        
        # Test with book disabled
        print(f"\n🔧 Test 2: Engine WITHOUT opening book")
        engine_without_book = ChessEngine(skill_level=20, depth=20, use_opening_book=False)
        engine_without_book.set_position(test_fen)
        
        start_time = time.time()
        move_without_book = engine_without_book.get_best_move()
        time_without_book = (time.time() - start_time) * 1000
        
        print(f"   Move chosen: {move_without_book}")
        print(f"   Time taken: {time_without_book:.1f}ms")
        print(f"   Source: 🤖 Engine (book disabled)")
        
        engine_without_book.cleanup()
        
        # Compare results
        print(f"\n📊 Comparison:")
        print(f"   With book:    {move_with_book} ({time_with_book:.1f}ms)")
        print(f"   Without book: {move_without_book} ({time_without_book:.1f}ms)")
        
        if move_with_book == move_without_book:
            print(f"   ✅ Same move chosen - book and engine agree")
        else:
            print(f"   ⚠️ Different moves - book vs engine preference")
            
            if time_with_book < 100:
                print(f"   ✅ Book move was used (fast response)")
                print(f"   This is CORRECT behavior - book should be prioritized")
            else:
                print(f"   ❌ Engine calculation was used despite book availability")
                print(f"   This suggests a problem with book prioritization")
        
        # Speed comparison
        if time_with_book < time_without_book / 10:
            print(f"   ✅ Significant speed advantage with book ({time_without_book/time_with_book:.0f}x faster)")
        else:
            print(f"   ❌ No significant speed advantage - book may not be working")
        
    except Exception as e:
        print(f"❌ Error in preference test: {e}")

def analyze_book_configuration():
    """Analyze the current book configuration"""
    print(f"\n⚙️ Analyzing Book Configuration")
    print("=" * 35)
    
    try:
        engine = ChessEngine(skill_level=20, depth=20, use_opening_book=True)
        
        print(f"📚 Opening Book Status:")
        print(f"   Book enabled: {engine.use_opening_book}")
        
        if engine.opening_book:
            print(f"   Book object: ✅ Created")
            
            # Check book statistics
            if hasattr(engine.opening_book, 'json_book'):
                json_positions = len(engine.opening_book.json_book)
                print(f"   JSON positions: {json_positions}")
            
            if hasattr(engine.opening_book, 'max_book_depth'):
                print(f"   Max book depth: {engine.opening_book.max_book_depth}")
            
            # Test a simple position
            test_move = engine.opening_book.get_book_move(STARTING_FEN, 1)
            print(f"   Test move from start: {test_move}")
            
        else:
            print(f"   Book object: ❌ Not created")
        
        engine.cleanup()
        
    except Exception as e:
        print(f"❌ Error analyzing configuration: {e}")

def main():
    """Main diagnostic function"""
    try:
        print("🚀 Opening Book Prioritization Diagnostic")
        print("Testing if book moves are properly prioritized over engine moves")
        print()
        
        test_book_prioritization()
        test_book_vs_engine_preference()
        analyze_book_configuration()
        
        print(f"\n🎯 Summary & Recommendations:")
        print("=" * 30)
        print("✅ Expected behavior:")
        print("   • Book moves should be used when available (< 100ms)")
        print("   • Engine calculation only when no book move exists (15+ seconds)")
        print("   • Book moves should be prioritized regardless of engine strength")
        print()
        print("❌ Problem indicators:")
        print("   • Slow moves (15+ seconds) when book should have the position")
        print("   • Engine calculating moves that exist in opening book")
        print("   • No speed advantage when book is enabled vs disabled")
        
        print(f"\n🎉 Diagnostic Complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()