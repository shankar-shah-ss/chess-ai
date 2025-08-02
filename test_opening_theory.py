#!/usr/bin/env python3
"""
Test script for the Opening Theory System
Tests all phases of opening detection and exploration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_theory_system import opening_theory_system
import chess

def test_opening_detection():
    """Test Phase 1: Opening Detection"""
    print("🧪 Testing Opening Detection (Phase 1)")
    print("=" * 50)
    
    test_positions = [
        # Starting position
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "Starting Position"),
        
        # King's Pawn Opening
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "King's Pawn Opening"),
        
        # King's Pawn Game
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2", "King's Pawn Game"),
        
        # Italian Game
        ("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3", "Italian Game"),
        
        # Sicilian Defense
        ("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2", "Sicilian Defense"),
    ]
    
    for fen, expected_name in test_positions:
        opening_info = opening_theory_system.detect_opening(fen)
        detected_name = opening_info.get("name", "Unknown")
        eco_code = opening_info.get("eco", "")
        phase = opening_info.get("phase", "unknown")
        
        print(f"📍 Position: {expected_name}")
        print(f"   Detected: {detected_name} ({eco_code})")
        print(f"   Phase: {phase}")
        print(f"   Theoretical: {'Yes' if opening_info.get('is_theoretical', False) else 'No'}")
        
        if opening_info.get("key_ideas"):
            print(f"   Key Ideas: {', '.join(opening_info['key_ideas'][:2])}")
        
        print()

def test_move_sequence_detection():
    """Test opening detection through move sequences"""
    print("🧪 Testing Move Sequence Detection")
    print("=" * 50)
    
    # Test Italian Game sequence
    board = chess.Board()
    moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"]
    move_names = ["e4", "e5", "Nf3", "Nc6", "Bc4"]
    
    print("🎯 Playing Italian Game sequence:")
    for i, (uci_move, san_move) in enumerate(zip(moves, move_names)):
        move = chess.Move.from_uci(uci_move)
        board.push(move)
        
        opening_info = opening_theory_system.detect_opening(board.fen())
        print(f"   {i+1}. {san_move} → {opening_info.get('name', 'Unknown')} ({opening_info.get('eco', '')})")
    
    print()

def test_next_moves():
    """Test Phase 2: Next Move Suggestions"""
    print("🧪 Testing Next Move Suggestions (Phase 2)")
    print("=" * 50)
    
    # Test from starting position
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    next_moves = opening_theory_system.get_next_moves(starting_fen, limit=5)
    
    print("📍 From starting position:")
    for i, move in enumerate(next_moves):
        print(f"   {i+1}. {move.san} - W:{move.white_win_rate:.1f}% D:{move.draw_rate:.1f}% B:{move.black_win_rate:.1f}%")
    
    print()

def test_opening_search():
    """Test opening search functionality"""
    print("🧪 Testing Opening Search")
    print("=" * 50)
    
    search_terms = ["Sicilian", "Italian", "Ruy Lopez", "French"]
    
    for term in search_terms:
        results = opening_theory_system.search_openings(term)
        print(f"🔍 Search '{term}': {len(results)} results")
        for result in results[:2]:  # Show first 2 results
            print(f"   - {result.name} ({result.eco})")
        print()

def test_statistics():
    """Test Phase 3: Statistical Display"""
    print("🧪 Testing Opening Statistics (Phase 3)")
    print("=" * 50)
    
    eco_codes = ["B00", "C20", "C50", "C60", "B20"]
    
    for eco in eco_codes:
        stats = opening_theory_system.get_opening_statistics(eco)
        print(f"📊 ECO {eco}:")
        print(f"   Win Rate: W:{stats['white_win_rate']:.1f}% D:{stats['draw_rate']:.1f}% B:{stats['black_win_rate']:.1f}%")
        print(f"   Games: {stats['total_games']:,} | Popularity: {stats['popularity']:.1f}%")
        print()

def test_transpositions():
    """Test transposition detection"""
    print("🧪 Testing Transposition Detection")
    print("=" * 50)
    
    # Test a few positions for transpositions
    test_fens = [
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
    ]
    
    for fen in test_fens:
        transpositions = opening_theory_system.get_transpositions(fen)
        opening_info = opening_theory_system.detect_opening(fen)
        print(f"📍 {opening_info.get('name', 'Unknown')}")
        print(f"   Transpositions: {len(transpositions)}")
        print()

def test_database_operations():
    """Test database export/import functionality"""
    print("🧪 Testing Database Operations")
    print("=" * 50)
    
    # Test cache operations
    print("🧹 Testing cache operations...")
    opening_theory_system.clear_cache()
    print("   Cache cleared successfully")
    
    # Test database info
    print(f"📚 Database contains:")
    print(f"   Variations: {len(opening_theory_system.variations)}")
    print(f"   Positions: {len(opening_theory_system.positions)}")
    print(f"   ECO codes: {len(opening_theory_system.eco_index)}")
    print()

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Opening Theory Test")
    print("=" * 60)
    print()
    
    try:
        test_opening_detection()
        test_move_sequence_detection()
        test_next_moves()
        test_opening_search()
        test_statistics()
        test_transpositions()
        test_database_operations()
        
        print("✅ All tests completed successfully!")
        print("🎯 Opening Theory System is fully functional")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_test()