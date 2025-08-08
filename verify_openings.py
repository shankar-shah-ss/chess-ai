#!/usr/bin/env python3
"""
Quick verification of opening database coverage
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_book import get_opening_book, cleanup_opening_book
from chess import STARTING_FEN, Board

def verify_coverage():
    book = get_opening_book()
    
    # Test specific sequences
    sequences = [
        # Queen's Pawn Game
        ["d2d4", "d7d5", "c2c4"],
        # King's Pawn Game  
        ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
        # Sicilian Defense
        ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4"],
        # English Opening
        ["c2c4", "e7e5", "b1c3"],
        # Reti Opening
        ["g1f3", "d7d5", "c2c4"],
    ]
    
    for i, sequence in enumerate(sequences, 1):
        print(f"\n🧪 Testing Sequence {i}: {' '.join(sequence)}")
        board = Board()
        moves_found = 0
        
        for move_num, expected_move in enumerate(sequence, 1):
            fen = board.fen()
            book_move = book.get_book_move(fen, move_num)
            
            if book_move:
                if book_move == expected_move:
                    print(f"  ✅ Move {move_num}: {book_move} (expected)")
                    moves_found += 1
                else:
                    print(f"  🔄 Move {move_num}: {book_move} (got {book_move}, expected {expected_move})")
                    moves_found += 1
                
                # Make the expected move to continue sequence
                try:
                    chess_move = board.parse_uci(expected_move)
                    board.push(chess_move)
                except:
                    print(f"  ❌ Invalid move: {expected_move}")
                    break
            else:
                print(f"  ❌ Move {move_num}: No book move found")
                break
        
        print(f"  📊 Coverage: {moves_found}/{len(sequence)} moves")
    
    cleanup_opening_book()

if __name__ == "__main__":
    verify_coverage()