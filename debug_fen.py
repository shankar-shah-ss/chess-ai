#!/usr/bin/env python3
"""
Debug FEN generation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chess import Board, STARTING_FEN

def debug_fens():
    board = Board()
    print(f"Starting FEN: {board.fen()}")
    
    # Play 1.d4
    move = board.parse_uci("d2d4")
    board.push(move)
    print(f"After 1.d4: {board.fen()}")
    
    # Play 1...d5
    move = board.parse_uci("d7d5")
    board.push(move)
    print(f"After 1.d4 d5: {board.fen()}")
    
    # Play 2.c4
    move = board.parse_uci("c2c4")
    board.push(move)
    print(f"After 1.d4 d5 2.c4: {board.fen()}")

if __name__ == "__main__":
    debug_fens()