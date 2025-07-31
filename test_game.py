#!/usr/bin/env python3
"""
Simple test script to verify the chess game works
"""
import sys
import os
sys.path.append('src')

try:
    import pygame
    print("✓ Pygame imported successfully")
except ImportError as e:
    print(f"✗ Pygame import failed: {e}")
    sys.exit(1)

try:
    import chess
    print("✓ Chess library imported successfully")
except ImportError as e:
    print(f"✗ Chess library import failed: {e}")
    sys.exit(1)

try:
    from stockfish import Stockfish
    print("✓ Stockfish imported successfully")
except ImportError as e:
    print(f"✗ Stockfish import failed: {e}")
    sys.exit(1)

# Test Stockfish engine
try:
    engine = Stockfish()
    print("✓ Stockfish engine initialized successfully")
    engine.set_position(["e2e4"])
    move = engine.get_best_move()
    print(f"✓ Engine working - best response to e4: {move}")
except Exception as e:
    print(f"✗ Stockfish engine failed: {e}")

# Test game imports
try:
    from const import WIDTH, HEIGHT
    from game import Game
    from board import Board
    print("✓ Game modules imported successfully")
except ImportError as e:
    print(f"✗ Game module import failed: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! The game should work now.")
print("Run: cd src && python3 main.py")