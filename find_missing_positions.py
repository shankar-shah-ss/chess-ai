#!/usr/bin/env python3
"""
Find missing positions in opening database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from opening_book import get_opening_book, cleanup_opening_book
from chess import STARTING_FEN, Board

def find_missing():
    book = get_opening_book()
    
    # Test positions from the failing test
    test_positions = [
        # Starting position
        (STARTING_FEN, "Starting position"),
        
        # After 1.e4
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1", "After 1.e4 (with e3)"),
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1", "After 1.e4 (no e3)"),
        
        # After 1.e4 e5
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2", "After 1.e4 e5 (with e6)"),
        ("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2", "After 1.e4 e5 (no e6)"),
        
        # After 1.d4
        ("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1", "After 1.d4 (with d3)"),
        ("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1", "After 1.d4 (no d3)"),
        
        # After 1.c4
        ("rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3 0 1", "After 1.c4 (with c3)"),
        ("rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1", "After 1.c4 (no c3)"),
    ]
    
    print("🔍 Checking specific positions:")
    print("-" * 40)
    
    for fen, description in test_positions:
        move = book.get_book_move(fen, 1)
        in_book = fen in book.json_book
        
        if move:
            print(f"✅ {description}")
            print(f"   FEN: {fen}")
            print(f"   Move: {move}")
        else:
            print(f"❌ {description}")
            print(f"   FEN: {fen}")
            print(f"   In book: {in_book}")
        print()
    
    # Generate actual FENs from moves
    print("🎯 Generating actual FENs:")
    print("-" * 30)
    
    moves_to_test = ["e2e4", "d2d4", "c2c4", "g1f3"]
    
    for move in moves_to_test:
        board = Board()
        chess_move = board.parse_uci(move)
        board.push(chess_move)
        fen = board.fen()
        
        book_move = book.get_book_move(fen, 1)
        in_book = fen in book.json_book
        
        print(f"After {move}:")
        print(f"  FEN: {fen}")
        print(f"  In book: {in_book}")
        print(f"  Book move: {book_move}")
        print()
    
    cleanup_opening_book()

if __name__ == "__main__":
    find_missing()