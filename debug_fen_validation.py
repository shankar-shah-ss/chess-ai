#!/usr/bin/env python3
"""
Debug FEN validation specifically
"""
import sys
sys.path.append('src')

def test_game_fen_validation():
    """Test the exact FEN validation method used in the game"""
    print("🔍 Testing Game FEN Validation Method")
    print("=" * 50)
    
    from game import Game
    import pygame
    
    # Initialize pygame
    pygame.init()
    
    # Create game
    game = Game()
    
    # Test initial position FEN
    fen = game.board.to_fen(game.next_player)
    print(f"Generated FEN: {fen}")
    
    # Test the exact validation method used in the game
    is_valid = game._validate_fen(fen)
    print(f"Game validation result: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test with python-chess directly
    try:
        import chess
        chess_board = chess.Board(fen)
        direct_valid = chess_board.is_valid()
        print(f"Direct chess validation: {'✅ Valid' if direct_valid else '❌ Invalid'}")
        
        # Check if there's a difference
        if is_valid != direct_valid:
            print("⚠️ Validation methods disagree!")
        else:
            print("✅ Validation methods agree")
            
    except Exception as e:
        print(f"❌ Direct validation error: {e}")
    
    # Test after making some moves
    print(f"\n🔍 Testing After Engine vs Engine Moves")
    print("=" * 40)
    
    # Simulate some moves that might happen in engine vs engine
    try:
        # Make a few moves to see if FEN becomes invalid
        for i in range(5):
            fen = game.board.to_fen(game.next_player)
            is_valid = game._validate_fen(fen)
            print(f"Move {i}: FEN valid = {'✅' if is_valid else '❌'}")
            
            if not is_valid:
                print(f"❌ Invalid FEN detected: {fen}")
                break
            
            # Try to make a simple move
            # Find a piece that can move
            piece_found = False
            for row in range(8):
                for col in range(8):
                    square = game.board.squares[row][col]
                    if square.has_piece() and square.piece.color == game.next_player:
                        piece = square.piece
                        # Get valid moves for this piece
                        game.board.calc_moves(piece, row, col, bool=False)
                        if piece.moves:
                            move = piece.moves[0]  # Take first valid move
                            game.make_move(piece, move)
                            piece_found = True
                            break
                if piece_found:
                    break
            
            if not piece_found:
                print("No valid moves found")
                break
                
    except Exception as e:
        print(f"❌ Error during move simulation: {e}")
    
    pygame.quit()
    return True

def test_problematic_positions():
    """Test some positions that might cause FEN issues"""
    print(f"\n🔍 Testing Potentially Problematic Positions")
    print("=" * 50)
    
    from board import Board
    
    # Test various positions
    test_positions = [
        # Standard starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        # After e4
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        # After e4 e5
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
        # Position with castling rights lost
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w - - 0 2",
        # Position with en passant
        "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3",
    ]
    
    for i, fen in enumerate(test_positions):
        print(f"\nTesting position {i+1}: {fen}")
        
        try:
            import chess
            chess_board = chess.Board(fen)
            is_valid = chess_board.is_valid()
            print(f"  Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
            if not is_valid:
                print(f"  ❌ This position is invalid!")
                
        except Exception as e:
            print(f"  ❌ Validation error: {e}")
    
    return True

def test_fen_edge_cases():
    """Test edge cases that might cause FEN validation to fail"""
    print(f"\n🔍 Testing FEN Edge Cases")
    print("=" * 40)
    
    # Test cases that might cause issues
    edge_cases = [
        ("Empty string", ""),
        ("None", None),
        ("Incomplete FEN", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"),
        ("Extra spaces", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 "),
        ("Invalid piece", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKXNR w KQkq - 0 1"),
    ]
    
    for name, fen in edge_cases:
        print(f"\nTesting {name}: '{fen}'")
        
        try:
            if fen is None:
                print("  ❌ None value")
                continue
                
            if not fen or len(fen.strip()) == 0:
                print("  ❌ Empty or whitespace-only")
                continue
            
            import chess
            chess_board = chess.Board(fen)
            is_valid = chess_board.is_valid()
            print(f"  Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    return True

def main():
    """Run FEN validation debugging"""
    print("🔍 FEN Validation Debug Suite")
    print("Investigating why FEN validation fails in engine vs engine")
    print("=" * 60)
    
    tests = [
        ("Game FEN Validation", test_game_fen_validation),
        ("Problematic Positions", test_problematic_positions),
        ("FEN Edge Cases", test_fen_edge_cases),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
    
    print(f"\n💡 Debugging Complete")
    print("If FEN generation is working but validation fails,")
    print("the issue might be in the game state or timing.")

if __name__ == "__main__":
    main()