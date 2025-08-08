#!/usr/bin/env python3
"""
Check Queen's Gambit position
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_book import get_opening_book, cleanup_opening_book

def check_qg():
    book = get_opening_book()
    
    # Test FEN from the test
    test_fen = "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2"
    
    print(f"Testing Queen's Gambit FEN:")
    print(f"FEN: {test_fen}")
    print(f"In book: {test_fen in book.json_book}")
    
    move = book.get_book_move(test_fen, 1)
    print(f"Book move: {move}")
    
    # Check what similar positions we have
    print(f"\nSimilar positions in book:")
    for fen in book.json_book.keys():
        if "2PP4" in fen and "3p4" in fen:
            print(f"  {fen}")
            print(f"    Moves: {[m.move for m in book.json_book[fen]]}")
    
    cleanup_opening_book()

if __name__ == "__main__":
    check_qg()