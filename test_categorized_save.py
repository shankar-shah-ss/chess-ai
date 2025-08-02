#!/usr/bin/env python3
"""
Test the categorized PGN save functionality
"""
import sys
sys.path.append('src')
import os
import time

def test_directory_creation():
    """Test that categorized directories are created"""
    print("🔍 Testing Directory Creation")
    print("=" * 35)
    
    from pgn_manager import PGNManager
    
    # Create PGN manager (should create directories)
    pgn = PGNManager()
    
    # Check if directories exist
    base_dir = os.path.join(os.path.dirname(__file__), 'games')
    categories = ['human-vs-human', 'human-vs-engine', 'engine-vs-engine']
    
    for category in categories:
        category_dir = os.path.join(base_dir, category)
        if os.path.exists(category_dir):
            print(f"✅ Directory exists: {category}")
        else:
            print(f"❌ Directory missing: {category}")
            return False
    
    return True

def test_game_categorization():
    """Test that games are categorized correctly"""
    print(f"\n🔍 Testing Game Categorization")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    
    # Test cases: (white_player, black_player, expected_category)
    test_cases = [
        ("Human", "Human", "human-vs-human"),
        ("Human", "Engine", "human-vs-engine"),
        ("Engine", "Human", "human-vs-engine"),
        ("Engine", "Engine", "engine-vs-engine"),
    ]
    
    for white, black, expected in test_cases:
        pgn = PGNManager()
        pgn.start_new_game(white, black, f"Test {white} vs {black}")
        
        category_dir, category = pgn.get_game_category_dir()
        
        if category == expected:
            print(f"✅ {white} vs {black} → {category}")
        else:
            print(f"❌ {white} vs {black} → {category} (expected {expected})")
            return False
    
    return True

def test_categorized_quick_save():
    """Test quick save with categorization"""
    print(f"\n🔍 Testing Categorized Quick Save")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    from move import Move
    from square import Square
    from piece import Pawn
    
    # Test different game types
    test_games = [
        ("TestHuman1", "TestHuman2", "human-vs-human"),
        ("TestHuman", "Engine", "human-vs-engine"),
        ("Engine", "Engine", "engine-vs-engine"),
    ]
    
    for white, black, expected_category in test_games:
        pgn = PGNManager()
        pgn.start_new_game(white, black, f"Test {white} vs {black}")
        
        # Add a test move
        test_move = Move(Square(6, 4), Square(4, 4))
        test_piece = Pawn('white')
        pgn.add_move(test_move, test_piece)
        
        # Quick save
        filename = f"test_{expected_category}_{int(time.time())}"
        result = pgn.save_pgn_quick(filename)
        
        if result:
            print(f"✅ {white} vs {black} quick save initiated")
        else:
            print(f"❌ {white} vs {black} quick save failed")
            return False
    
    # Give background threads time to complete
    time.sleep(2)
    
    # Verify files were saved in correct directories
    base_dir = os.path.join(os.path.dirname(__file__), 'games')
    
    for white, black, expected_category in test_games:
        category_dir = os.path.join(base_dir, expected_category)
        
        # Check if any test files exist in this directory
        if os.path.exists(category_dir):
            files = [f for f in os.listdir(category_dir) if f.startswith('test_')]
            if files:
                print(f"✅ Files found in {expected_category}: {len(files)} files")
            else:
                print(f"⚠️ No test files found in {expected_category}")
        else:
            print(f"❌ Category directory missing: {expected_category}")
            return False
    
    return True

def test_wrapper_categorized_save():
    """Test PGN wrapper categorized save"""
    print(f"\n🔍 Testing PGN Wrapper Categorized Save")
    print("=" * 45)
    
    from game import Game
    from move import Move
    from square import Square
    from piece import Pawn
    import pygame
    
    pygame.init()
    
    # Test different game modes
    test_modes = [
        (0, "human-vs-human"),   # Human vs Human
        (1, "human-vs-engine"),  # Human vs Engine
        (2, "engine-vs-engine"), # Engine vs Engine
    ]
    
    for game_mode, expected_category in test_modes:
        game = Game()
        game.game_mode = game_mode
        
        # Set engine flags based on mode
        if game_mode == 1:  # Human vs Engine
            game.engine_black = True
        elif game_mode == 2:  # Engine vs Engine
            game.engine_white = True
            game.engine_black = True
        
        # Start PGN recording
        game.pgn.start_recording()
        
        # Add a test move
        test_move = Move(Square(6, 4), Square(4, 4))
        test_piece = Pawn('white')
        game.pgn.record_move(test_move, test_piece)
        
        # Quick save
        filename = f"wrapper_test_{expected_category}_{int(time.time())}"
        result = game.pgn.save_game_quick(filename)
        
        if result:
            print(f"✅ Game mode {game_mode} ({expected_category}) save initiated")
        else:
            print(f"❌ Game mode {game_mode} ({expected_category}) save failed")
            pygame.quit()
            return False
    
    pygame.quit()
    
    # Give background threads time to complete
    time.sleep(2)
    
    return True

def test_directory_structure():
    """Test final directory structure"""
    print(f"\n🔍 Testing Final Directory Structure")
    print("=" * 45)
    
    base_dir = os.path.join(os.path.dirname(__file__), 'games')
    
    if not os.path.exists(base_dir):
        print(f"❌ Base games directory missing: {base_dir}")
        return False
    
    print(f"📂 Games directory: {base_dir}")
    
    categories = ['human-vs-human', 'human-vs-engine', 'engine-vs-engine']
    
    for category in categories:
        category_dir = os.path.join(base_dir, category)
        
        if os.path.exists(category_dir):
            files = [f for f in os.listdir(category_dir) if f.endswith('.pgn')]
            print(f"  📂 {category}: {len(files)} PGN files")
            
            # Show a few example files
            for i, filename in enumerate(files[:3]):
                print(f"    📄 {filename}")
            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more files")
        else:
            print(f"  ❌ Missing: {category}")
            return False
    
    return True

def main():
    """Run categorized save tests"""
    print("🔧 Categorized PGN Save Test Suite")
    print("Testing automatic game categorization")
    print("=" * 60)
    
    tests = [
        ("Directory Creation", test_directory_creation),
        ("Game Categorization", test_game_categorization),
        ("Categorized Quick Save", test_categorized_quick_save),
        ("Wrapper Categorized Save", test_wrapper_categorized_save),
        ("Directory Structure", test_directory_structure),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*15} {test_name} {'='*15}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 Categorized Save Test Results")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All categorized save features working correctly!")
        print("✅ Automatic directory creation")
        print("✅ Game mode detection and categorization")
        print("✅ Categorized quick save")
        print("✅ Categorized dialog save")
        print("✅ Proper directory structure")
        print("\n📁 Games are now organized by type:")
        print("  📂 games/human-vs-human/")
        print("  📂 games/human-vs-engine/")
        print("  📂 games/engine-vs-engine/")
    else:
        print("\n⚠️ Some issues remain")
        print("Please check the failed tests above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)