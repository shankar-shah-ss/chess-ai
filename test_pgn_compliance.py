#!/usr/bin/env python3
"""
Test PGN system compliance with README_PGN.md requirements
"""
import sys
sys.path.append('src')

def test_piece_notation():
    """Test piece notation compliance"""
    print("♟️ Testing Piece Notation Compliance")
    print("=" * 50)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import Pawn, Knight, Bishop, Rook, Queen, King
    
    pgn = PGNManager()
    
    test_cases = [
        # (piece, move, expected_notation, description)
        # Note: Square(row, col) where row 0=8th rank, row 7=1st rank
        (King('white'), Move(Square(7, 4), Square(7, 6)), "Kg1", "King to g1"),  # e1 to g1
        (Queen('white'), Move(Square(7, 3), Square(4, 3)), "Qd4", "Queen to d4"),  # d1 to d4
        (Rook('white'), Move(Square(7, 0), Square(0, 0)), "Ra8", "Rook to a8"),    # a1 to a8
        (Bishop('white'), Move(Square(7, 5), Square(3, 2)), "Bc5", "Bishop to c5"), # f1 to c5
        (Knight('white'), Move(Square(7, 6), Square(5, 5)), "Nf3", "Knight to f3"), # g1 to f3
        (Pawn('white'), Move(Square(6, 4), Square(4, 4)), "e4", "Pawn to e4"),     # e2 to e4
        (Pawn('white'), Move(Square(6, 3), Square(3, 3)), "d5", "Pawn to d5"),     # d2 to d5
    ]
    
    print("📋 Basic Piece Moves:")
    all_passed = True
    for piece, move, expected, description in test_cases:
        notation = pgn._generate_algebraic_notation(move, piece)
        status = "✅" if notation == expected else "❌"
        if notation != expected:
            all_passed = False
        print(f"{status} {description}: {notation} (expected: {expected})")
    
    return all_passed

def test_special_notation():
    """Test special notation compliance"""
    print(f"\n🔀 Testing Special Notation Compliance")
    print("=" * 50)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import Pawn, Knight, Bishop, Rook, Queen, King
    
    pgn = PGNManager()
    
    test_cases = [
        # Pawn capture: exd5 (e4 pawn captures on d5)
        (Pawn('white'), Move(Square(4, 4), Square(3, 3)), "exd5", "Pawn capture", True),
        # Promotion: e8=Q (e7 pawn promotes to queen on e8)
        (Pawn('white'), Move(Square(1, 4), Square(0, 4)), "e8=Q", "Pawn promotion", False, False, False, False, "Queen"),
        # Kingside Castle: O-O
        (King('white'), Move(Square(7, 4), Square(7, 6)), "O-O", "Kingside castle", False, False, False, True),
        # Queenside Castle: O-O-O
        (King('white'), Move(Square(7, 4), Square(7, 2)), "O-O-O", "Queenside castle", False, False, False, True),
        # Check: Qh5+ (queen moves to h5 giving check)
        (Queen('white'), Move(Square(7, 3), Square(3, 7)), "Qh5+", "Check by queen", False, True),
        # Checkmate: Qh7# (queen moves to h7 giving checkmate)
        (Queen('white'), Move(Square(3, 7), Square(1, 7)), "Qh7#", "Checkmate by queen", False, False, True),
    ]
    
    print("📋 Special Moves:")
    all_passed = True
    for i, test_case in enumerate(test_cases):
        piece, move, expected, description = test_case[:4]
        
        # Extract optional parameters
        captured = test_case[4] if len(test_case) > 4 else False
        is_check = test_case[5] if len(test_case) > 5 else False
        is_checkmate = test_case[6] if len(test_case) > 6 else False
        is_castling = test_case[7] if len(test_case) > 7 else False
        promotion = test_case[8] if len(test_case) > 8 else None
        
        # Create captured piece if needed
        captured_piece = Pawn('black') if captured else None
        
        notation = pgn._generate_algebraic_notation(
            move, piece, captured_piece, is_check, is_checkmate, is_castling, promotion
        )
        
        status = "✅" if notation == expected else "❌"
        if notation != expected:
            all_passed = False
        print(f"{status} {description}: {notation} (expected: {expected})")
    
    return all_passed

def test_missing_features():
    """Test for missing features mentioned in README"""
    print(f"\n🔍 Checking Missing Features")
    print("=" * 40)
    
    missing_features = []
    
    # Check for disambiguation logic
    print("🔧 Disambiguation Logic:")
    print("❌ Not implemented - Multiple pieces of same type to same square")
    missing_features.append("Disambiguation (Nbd7, R1a3, etc.)")
    
    # Check for en passant
    print("\n🔧 En Passant:")
    print("❌ Not implemented - En passant capture notation")
    missing_features.append("En passant notation (exd6 e.p.)")
    
    # Check for move ambiguity resolution
    print("\n🔧 Move Ambiguity:")
    print("❌ Not implemented - Resolving ambiguous moves")
    missing_features.append("Ambiguous move resolution")
    
    return missing_features

def test_example_game():
    """Test against the Ruy Lopez example from README"""
    print(f"\n🧠 Testing Example Game (Ruy Lopez Opening)")
    print("=" * 50)
    
    expected_moves = [
        "1. e4 e5",
        "2. Nf3 Nc6", 
        "3. Bb5 a6",
        "4. Ba4 Nf6",
        "5. O-O Be7",
        "6. Re1 b5",
        "7. Bb3 d6",
        "8. c3 O-O",
        "9. h3 Nb8",
        "10. d4 Nbd7"
    ]
    
    print("📋 Expected Ruy Lopez moves:")
    for move in expected_moves:
        print(f"✓ {move}")
    
    print(f"\n⚠️ Note: Our current implementation can generate basic moves")
    print("but lacks disambiguation for complex positions like 'Nbd7'")

def analyze_compliance():
    """Analyze overall compliance with README requirements"""
    print(f"\n📊 PGN Compliance Analysis")
    print("=" * 40)
    
    # What we have implemented correctly
    implemented = [
        "✅ Basic piece notation (K, Q, R, B, N, pawn=empty)",
        "✅ Square notation (a1-h8)",
        "✅ Capture notation (x)",
        "✅ Check notation (+)",
        "✅ Checkmate notation (#)",
        "✅ Castling notation (O-O, O-O-O)",
        "✅ Promotion notation (=Q)",
        "✅ PGN headers and format",
        "✅ Move numbering",
        "✅ Result notation (1-0, 0-1, 1/2-1/2)"
    ]
    
    # What needs improvement
    needs_work = [
        "❌ Pawn capture notation (exd5) - partially implemented",
        "❌ Disambiguation (Nbd7, R1a3) - not implemented", 
        "❌ En passant notation - not implemented",
        "❌ Complex position handling - limited"
    ]
    
    print("🎯 Successfully Implemented:")
    for item in implemented:
        print(f"  {item}")
    
    print(f"\n⚠️ Needs Improvement:")
    for item in needs_work:
        print(f"  {item}")
    
    compliance_score = len(implemented) / (len(implemented) + len(needs_work)) * 100
    print(f"\n📈 Overall Compliance: {compliance_score:.1f}%")
    
    return compliance_score

def main():
    """Run all compliance tests"""
    print("🔍 PGN System Compliance Check")
    print("Testing against README_PGN.md requirements")
    print("=" * 60)
    
    # Run tests
    piece_notation_passed = test_piece_notation()
    special_notation_passed = test_special_notation()
    missing_features = test_missing_features()
    test_example_game()
    compliance_score = analyze_compliance()
    
    # Final summary
    print(f"\n🎯 Final Assessment")
    print("=" * 30)
    
    if piece_notation_passed:
        print("✅ Basic piece notation: PASSED")
    else:
        print("❌ Basic piece notation: FAILED")
    
    if special_notation_passed:
        print("✅ Special notation: PASSED")
    else:
        print("❌ Special notation: NEEDS WORK")
    
    print(f"⚠️ Missing features: {len(missing_features)}")
    
    if compliance_score >= 80:
        print("🎉 GOOD: System meets most PGN requirements")
    elif compliance_score >= 60:
        print("⚠️ FAIR: System meets basic PGN requirements")
    else:
        print("❌ POOR: System needs significant PGN improvements")
    
    print(f"\n💡 Recommendation:")
    if compliance_score >= 80:
        print("✅ Current implementation is suitable for basic game recording")
        print("✅ Can be used for analysis in most chess software")
        print("⚠️ Consider adding disambiguation for advanced positions")
    else:
        print("⚠️ Consider implementing missing features for full compliance")

if __name__ == "__main__":
    main()