#!/usr/bin/env python3
"""
Debug opening book lookups
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_book import get_opening_book, cleanup_opening_book
from chess import Board, STARTING_FEN

def debug_book():
    book = get_opening_book()
    
    # Check what positions are in the book
    print("📚 Positions in opening book:")
    for i, (fen, moves) in enumerate(book.json_book.items(), 1):
        if i <= 10:  # Show first 10
            print(f"  {i}. {fen}")
            print(f"     Moves: {[m.move for m in moves]}")
        elif i == 11:
            print(f"  ... and {len(book.json_book) - 10} more positions")
            break
    
    print(f"\nTotal positions: {len(book.json_book)}")
    
    # Test specific lookups
    test_fens = [
        STARTING_FEN,
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1",  # After 1.d4
        "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2",  # After 1.d4 d5
    ]
    
    print("\n🔍 Testing specific lookups:")
    for i, fen in enumerate(test_fens, 1):
        move = book.get_book_move(fen, 1)
        print(f"  {i}. FEN: {fen}")
        print(f"     Move: {move}")
        print(f"     In book: {fen in book.json_book}")
        print()
    
    cleanup_opening_book()

if __name__ == "__main__":
    debug_book()