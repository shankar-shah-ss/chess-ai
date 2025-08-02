#!/usr/bin/env python3
"""
Debug FEN generation issues
"""
import sys
sys.path.append('src')

def test_fen_generation():
    """Test FEN generation from initial position"""
    print("🔍 Testing FEN Generation")
    print("=" * 40)
    
    from board import Board
    
    # Create a new board
    board = Board()
    
    # Generate FEN for initial position
    fen = board.to_fen('white')
    print(f"Generated FEN: {fen}")
    
    # Expected initial FEN
    expected_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"Expected FEN:  {expected_fen}")
    
    # Check if they match
    match = fen == expected_fen
    print(f"FEN Match: {'✅' if match else '❌'}")
    
    # Test FEN validation
    try:
        import chess
        chess_board = chess.Board(fen)
        is_valid = chess_board.is_valid()
        print(f"FEN Valid: {'✅' if is_valid else '❌'}")
        
        if not is_valid:
            print("❌ FEN validation failed!")
            print("Analyzing FEN components...")
            
            parts = fen.split()
            if len(parts) != 6:
                print(f"❌ Wrong number of FEN parts: {len(parts)} (expected 6)")
            else:
                print(f"✅ Correct number of FEN parts: {len(parts)}")
                print(f"  1. Piece placement: {parts[0]}")
                print(f"  2. Active color: {parts[1]}")
                print(f"  3. Castling rights: {parts[2]}")
                print(f"  4. En passant: {parts[3]}")
                print(f"  5. Halfmove clock: {parts[4]}")
                print(f"  6. Fullmove number: {parts[5]}")
        
    except ImportError:
        print("⚠️ python-chess not available, cannot validate FEN")
        # Basic validation
        parts = fen.split()
        if len(parts) == 6:
            print("✅ FEN has correct number of parts")
        else:
            print(f"❌ FEN has wrong number of parts: {len(parts)}")
    except Exception as e:
        print(f"❌ FEN validation error: {e}")
    
    return fen

def test_fen_after_moves():
    """Test FEN generation after some moves"""
    print(f"\n🔍 Testing FEN After Moves")
    print("=" * 40)
    
    from board import Board
    from move import Move
    from square import Square
    
    board = Board()
    
    # Make a simple move: e2-e4
    piece = board.squares[6][4].piece  # White pawn on e2
    if piece:
        move = Move(Square(6, 4), Square(4, 4))  # e2 to e4
        board.move(piece, move)
        
        fen = board.to_fen('black')
        print(f"FEN after e4: {fen}")
        
        # Test validation
        try:
            import chess
            chess_board = chess.Board(fen)
            is_valid = chess_board.is_valid()
            print(f"FEN Valid: {'✅' if is_valid else '❌'}")
            
            if not is_valid:
                print("❌ FEN validation failed after move!")
                
        except Exception as e:
            print(f"❌ FEN validation error: {e}")
    
    return True

def test_piece_symbols():
    """Test piece symbol generation"""
    print(f"\n🔍 Testing Piece Symbols")
    print("=" * 40)
    
    from piece import Pawn, Knight, Bishop, Rook, Queen, King
    
    pieces = [
        (Pawn('white'), 'P'),
        (Pawn('black'), 'p'),
        (Knight('white'), 'N'),
        (Knight('black'), 'n'),
        (Bishop('white'), 'B'),
        (Bishop('black'), 'b'),
        (Rook('white'), 'R'),
        (Rook('black'), 'r'),
        (Queen('white'), 'Q'),
        (Queen('black'), 'q'),
        (King('white'), 'K'),
        (King('black'), 'k'),
    ]
    
    all_correct = True
    for piece, expected in pieces:
        symbol = piece.symbol()
        fen_symbol = symbol.upper() if piece.color == 'white' else symbol.lower()
        correct = fen_symbol == expected
        status = "✅" if correct else "❌"
        print(f"{status} {piece.color} {piece.name}: '{fen_symbol}' (expected: '{expected}')")
        if not correct:
            all_correct = False
    
    return all_correct

def debug_board_state():
    """Debug the board state to see what might be wrong"""
    print(f"\n🔍 Debugging Board State")
    print("=" * 40)
    
    from board import Board
    
    board = Board()
    
    print("Board squares content:")
    for row in range(8):
        row_str = ""
        for col in range(8):
            square = board.squares[row][col]
            if square.isempty():
                row_str += "."
            else:
                piece = square.piece
                symbol = piece.symbol()
                fen_char = symbol.upper() if piece.color == 'white' else symbol.lower()
                row_str += fen_char
        print(f"Row {row}: {row_str}")
    
    print(f"\nCastling rights: {board.castling_rights}")
    print(f"En passant target: {board.en_passant_target}")
    print(f"Halfmove clock: {board.halfmove_clock}")
    print(f"Fullmove number: {board.fullmove_number}")
    
    return True

def main():
    """Run FEN debugging tests"""
    print("🔍 FEN Generation Debug Suite")
    print("Testing FEN generation and validation")
    print("=" * 50)
    
    tests = [
        ("Initial Position FEN", test_fen_generation),
        ("FEN After Moves", test_fen_after_moves),
        ("Piece Symbols", test_piece_symbols),
        ("Board State Debug", debug_board_state),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*15} {test_name} {'='*15}")
            result = test_func()
            results[test_name] = result is not False
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 Debug Results Summary")
    print("=" * 30)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n💡 Recommendations:")
    print("1. Check if python-chess is installed for FEN validation")
    print("2. Verify piece symbol generation is correct")
    print("3. Check board state initialization")
    print("4. Ensure FEN format matches standard")

if __name__ == "__main__":
    main()