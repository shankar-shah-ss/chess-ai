#!/usr/bin/env python3
"""
Debug coordinate system
"""
import sys
sys.path.append('src')

def debug_coordinates():
    """Debug the coordinate system"""
    print("🔍 Debugging Coordinate System")
    print("=" * 40)
    
    # Test coordinate mapping
    col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    
    print("📋 Row/Col to Square mapping:")
    for row in range(8):
        for col in range(8):
            file_letter = col_map[col]
            rank_number = str(8 - row)
            square_name = file_letter + rank_number
            print(f"Row {row}, Col {col} = {square_name}")
        print()
    
    print("🎯 Key squares:")
    print("g1 should be: Row 7, Col 6")
    print("e1 should be: Row 7, Col 4") 
    print("a8 should be: Row 0, Col 0")
    print("h8 should be: Row 0, Col 7")
    print("a1 should be: Row 7, Col 0")
    print("h1 should be: Row 7, Col 7")

if __name__ == "__main__":
    debug_coordinates()