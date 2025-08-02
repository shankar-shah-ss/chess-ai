#!/usr/bin/env python3
"""
Debug PGN file generation issue
"""
import sys
sys.path.append('src')

from pgn_manager import PGNManager
from move import Move
from square import Square
from piece import Pawn, Knight

# Create a test PGN
pgn = PGNManager()
pgn.start_new_game("Test Tournament", "Test Location")

print("Headers after start_new_game:")
for key, value in pgn.headers.items():
    if value:
        print(f"  {key}: {value}")

# Add some moves
pawn = Pawn('white')
knight = Knight('black')

move1 = Move(Square(6, 4), Square(4, 4))  # e4
move2 = Move(Square(0, 1), Square(2, 2))  # Nc6

pgn.add_move(move1, pawn)
pgn.add_move(move2, knight)

# Add annotations
pgn.add_comment(0, "King's pawn opening")
pgn.add_nag(1, 1)  # Good move

pgn.set_result("1-0", "Test game")

# Generate PGN
pgn_text = pgn.generate_pgn()
print("\nGenerated PGN:")
print("=" * 40)
print(pgn_text)
print("=" * 40)

# Check what we're looking for
expected_content = [
    "[Event \"Test Tournament\"]",
    "[Site \"Test Location\"]",
    "1. e4 {King's pawn opening} Nc6!",
    "1-0"
]

print("\nChecking expected content:")
for expected in expected_content:
    found = expected in pgn_text
    print(f"  '{expected}': {'✅' if found else '❌'}")