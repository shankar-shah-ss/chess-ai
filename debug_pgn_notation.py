#!/usr/bin/env python3
"""
Debug PGN notation generation
"""
import sys
sys.path.append('src')

def debug_notation():
    """Debug notation generation"""
    print("🔍 Debugging PGN Notation Generation")
    print("=" * 50)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import King
    
    pgn = PGNManager()
    
    # Test the exact move that's failing
    king = King('white')
    move = Move(Square(7, 4), Square(7, 6))  # e1 to g1
    
    print(f"Move: e1 to g1")
    print(f"From: Row {move.initial.row}, Col {move.initial.col}")
    print(f"To: Row {move.final.row}, Col {move.final.col}")
    
    # Check coordinate mapping
    col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    from_file = col_map[move.initial.col]
    from_rank = str(8 - move.initial.row)
    to_file = col_map[move.final.col]
    to_rank = str(8 - move.final.row)
    
    print(f"From square: {from_file}{from_rank}")
    print(f"To square: {to_file}{to_rank}")
    
    # Generate notation
    notation = pgn._generate_algebraic_notation(move, king)
    print(f"Generated notation: {notation}")
    print(f"Expected: Kg1")

if __name__ == "__main__":
    debug_notation()