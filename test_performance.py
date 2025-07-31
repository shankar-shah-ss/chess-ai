#!/usr/bin/env python3
"""
Performance test for chess game responsiveness
"""
import sys
import os
import time
sys.path.append('src')

import pygame
from main import Main

def test_responsiveness():
    print("🚀 Testing game responsiveness...")
    
    # Initialize game
    main = Main()
    game = main.game
    
    # Test piece selection speed
    start_time = time.time()
    
    # Simulate selecting a piece
    piece = game.board.squares[6][4].piece  # White pawn
    if piece:
        game.board.calc_moves(piece, 6, 4, bool=True)
        
    selection_time = time.time() - start_time
    print(f"✓ Piece selection time: {selection_time*1000:.1f}ms")
    
    # Test move validation speed
    start_time = time.time()
    
    if piece and piece.moves:
        move = piece.moves[0]
        is_valid = game.board.valid_move(piece, move)
        
    validation_time = time.time() - start_time
    print(f"✓ Move validation time: {validation_time*1000:.1f}ms")
    
    # Performance assessment
    total_time = selection_time + validation_time
    if total_time < 0.05:  # 50ms
        print("🎉 Game should be very responsive!")
    elif total_time < 0.1:  # 100ms
        print("✅ Game should be responsive")
    else:
        print("⚠️  Game may feel sluggish")
    
    print(f"📊 Total interaction time: {total_time*1000:.1f}ms")

if __name__ == '__main__':
    test_responsiveness()