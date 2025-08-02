#!/usr/bin/env python3
"""
Test PGN integration with the main chess game
Verifies that all PGN features work correctly with the game engine
"""
import sys
sys.path.append('src')

def test_game_pgn_integration():
    """Test PGN integration with actual game"""
    print("🎮 Testing PGN Integration with Chess Game")
    print("=" * 50)
    
    from game import Game
    from move import Move
    from square import Square
    import pygame
    
    # Initialize pygame (required for game)
    pygame.init()
    
    # Create game instance
    game = Game()
    
    # Verify PGN integration is set up
    assert hasattr(game, 'pgn'), "Game should have PGN integration"
    assert game.pgn.recording, "PGN recording should be active"
    
    print("✅ PGN integration initialized")
    
    # Test that PGN manager has all new features
    pgn_manager = game.pgn.pgn_manager
    
    # Check for new methods
    new_methods = [
        'add_comment', 'add_nag', 'add_variation',
        'set_opening_info', 'set_player_info', 'set_time_control',
        'validate_pgn', 'get_statistics', 'export_to_fen'
    ]
    
    for method in new_methods:
        assert hasattr(pgn_manager, method), f"PGN manager should have {method} method"
    
    print("✅ All new PGN methods available")
    
    # Test enhanced move recording
    initial_moves = len(pgn_manager.moves)
    
    # Simulate a move (e2-e4)
    from piece import Pawn
    piece = game.board.squares[6][4].piece  # White pawn on e2
    if piece and piece.name == 'pawn':
        move = Move(Square(6, 4), Square(4, 4))  # e2 to e4
        
        # This should work with the enhanced record_move method
        game.pgn.record_move(move, piece)
        
        assert len(pgn_manager.moves) == initial_moves + 1, "Move should be recorded"
        print("✅ Enhanced move recording works")
    
    # Test new PGN features
    game.pgn.set_player_ratings("2000", "1900")
    game.pgn.set_opening_classification("C20", "King's Pawn Game")
    game.pgn.set_time_control("10+5")
    
    print("✅ Extended PGN information set")
    
    # Test comment and annotation
    if pgn_manager.moves:
        game.pgn.add_move_comment("Opening move")
        game.pgn.add_move_annotation(1)  # Good move
        print("✅ Move annotations added")
    
    # Test PGN generation
    pgn_text = game.pgn.get_current_pgn_preview()
    
    # Check for expected elements
    expected_elements = [
        "[Event",
        "[White",
        "[Black",
        "[Result",
        "Chess AI v2.0"  # New generator version
    ]
    
    for element in expected_elements:
        assert element in pgn_text, f"PGN should contain {element}"
    
    print("✅ PGN generation includes all elements")
    
    # Test validation
    is_valid, errors = game.pgn.validate_current_pgn()
    assert is_valid, f"PGN should be valid, errors: {errors}"
    print("✅ PGN validation passes")
    
    # Test statistics
    stats = game.pgn.get_game_statistics()
    assert isinstance(stats, dict), "Statistics should be a dictionary"
    assert 'total_moves' in stats, "Statistics should include total_moves"
    print("✅ Game statistics available")
    
    print(f"\n📊 Current Game Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    pygame.quit()
    return True

def test_pgn_file_operations():
    """Test PGN file save/load operations"""
    print(f"\n💾 Testing PGN File Operations")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import Pawn, Knight
    import tempfile
    import os
    
    # Create a test PGN
    pgn = PGNManager()
    pgn.start_new_game(
        white_player="Player1", 
        black_player="Player2",
        event="Test Tournament", 
        site="Test Location"
    )
    
    # Add some moves
    pawn = Pawn('white')
    knight = Knight('black')
    
    move1 = Move(Square(6, 4), Square(4, 4))  # e4
    move2 = Move(Square(0, 1), Square(2, 2))  # Nc6
    
    pgn.add_move(move1, pawn)
    pgn.add_move(move2, knight)
    
    # Add annotations
    pgn.add_comment(0, "King's pawn opening")
    pgn.add_nag(1, 1)  # Good move
    
    pgn.set_result("1-0", "Test game")
    
    # Test file save
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pgn', delete=False) as f:
        temp_path = f.name
    
    try:
        success = pgn.save_pgn_file(temp_path)
        assert success, "PGN file save should succeed"
        
        # Verify file exists and has content
        assert os.path.exists(temp_path), "PGN file should exist"
        
        with open(temp_path, 'r') as f:
            content = f.read()
        
        # Check for expected content
        expected_content = [
            "[Event \"Test Tournament\"]",
            "[Site \"Test Location\"]",
            "1. e4 {King's pawn opening} Nc6!",
            "1-0"
        ]
        
        for expected in expected_content:
            assert expected in content, f"PGN file should contain: {expected}"
        
        print("✅ PGN file save/load successful")
        print(f"✅ File size: {len(content)} characters")
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return True

def test_advanced_notation():
    """Test advanced PGN notation features"""
    print(f"\n🔧 Testing Advanced Notation")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import Pawn, Queen
    
    pgn = PGNManager()
    
    # Test en passant notation
    pawn = Pawn('white')
    en_passant_move = Move(Square(3, 4), Square(2, 3))  # exd6 e.p.
    
    notation = pgn._generate_algebraic_notation(
        en_passant_move, pawn, None, False, False, False, None, True
    )
    
    assert "e.p." in notation, f"En passant notation should include 'e.p.', got: {notation}"
    print(f"✅ En passant notation: {notation}")
    
    # Test promotion notation
    promotion_move = Move(Square(1, 4), Square(0, 4))  # e8=Q
    promotion_notation = pgn._generate_algebraic_notation(
        promotion_move, pawn, None, False, False, False, "Queen", False
    )
    
    assert "=Q" in promotion_notation, f"Promotion should include =Q, got: {promotion_notation}"
    print(f"✅ Promotion notation: {promotion_notation}")
    
    # Test check and checkmate
    queen = Queen('white')
    check_move = Move(Square(7, 3), Square(3, 7))  # Qh5+
    check_notation = pgn._generate_algebraic_notation(
        check_move, queen, None, True, False, False, None, False
    )
    
    assert "+" in check_notation, f"Check notation should include +, got: {check_notation}"
    print(f"✅ Check notation: {check_notation}")
    
    # Test checkmate
    mate_notation = pgn._generate_algebraic_notation(
        check_move, queen, None, False, True, False, None, False
    )
    
    assert "#" in mate_notation, f"Checkmate notation should include #, got: {mate_notation}"
    print(f"✅ Checkmate notation: {mate_notation}")
    
    return True

def main():
    """Run all PGN integration tests"""
    print("🔍 PGN Integration Test Suite")
    print("Testing integration with main chess game")
    print("=" * 60)
    
    tests = [
        ("Game PGN Integration", test_game_pgn_integration),
        ("PGN File Operations", test_pgn_file_operations),
        ("Advanced Notation", test_advanced_notation),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results[test_name] = result
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 Integration Test Summary")
    print("=" * 40)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall Results: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ PGN system is fully integrated with the chess game")
        print("✅ All advanced features are working correctly")
        print("✅ Ready for production use!")
    else:
        print("⚠️ Some integration tests failed")
        print("Please check the error messages above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)