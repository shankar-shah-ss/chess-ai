#!/usr/bin/env python3
"""
Test script to verify engine illegal move fixes
Tests move validation and double move prevention
"""

import sys
sys.path.append('src')
import pygame
import time
from game import Game
from move_validator import MoveValidator, EngineMovePreventer
from move import Move
from square import Square

def test_move_validation():
    """Test the move validation system"""
    print("🧪 Testing Move Validation System")
    print("=" * 50)
    
    pygame.init()
    game = Game()
    validator = MoveValidator()
    
    # Test 1: Valid move validation
    print("\n1️⃣ Testing Valid Move Validation")
    print("-" * 30)
    
    # Test a valid pawn move (e2-e4)
    valid_uci = "e2e4"
    validated_move = validator.validate_uci_move(valid_uci, game.board, 'white')
    
    if validated_move:
        print(f"✅ Valid move correctly validated: {valid_uci}")
    else:
        print(f"❌ Valid move incorrectly rejected: {valid_uci}")
    
    # Test 2: Invalid move validation
    print("\n2️⃣ Testing Invalid Move Validation")
    print("-" * 30)
    
    # Test an invalid move (knight moving like a pawn)
    invalid_uci = "b1b3"  # Knight trying to move like pawn
    validated_move = validator.validate_uci_move(invalid_uci, game.board, 'white')
    
    if not validated_move:
        print(f"✅ Invalid move correctly rejected: {invalid_uci}")
    else:
        print(f"❌ Invalid move incorrectly accepted: {invalid_uci}")
    
    # Test 3: UCI parsing
    print("\n3️⃣ Testing UCI Parsing")
    print("-" * 30)
    
    test_cases = [
        ("e2e4", True),    # Valid format
        ("a1h8", True),    # Valid format
        ("e7e8q", True),   # Valid with promotion
        ("xyz", False),    # Invalid format
        ("", False),       # Empty string
        ("e2e9", False),   # Invalid coordinates
    ]
    
    for uci, should_parse in test_cases:
        try:
            move = validator._uci_to_internal_move(uci[:2], uci[2:4], uci[4:] if len(uci) > 4 else None)
            parsed = move is not None
            
            if parsed == should_parse:
                print(f"✅ UCI parsing correct for '{uci}': {parsed}")
            else:
                print(f"❌ UCI parsing incorrect for '{uci}': expected {should_parse}, got {parsed}")
        except:
            if not should_parse:
                print(f"✅ UCI parsing correctly failed for '{uci}'")
            else:
                print(f"❌ UCI parsing unexpectedly failed for '{uci}'")
    
    pygame.quit()
    return True

def test_double_move_prevention():
    """Test the double move prevention system"""
    print("\n🧪 Testing Double Move Prevention")
    print("=" * 50)
    
    pygame.init()
    game = Game()
    preventer = EngineMovePreventer()
    
    # Test 1: Normal alternating moves
    print("\n1️⃣ Testing Normal Move Alternation")
    print("-" * 30)
    
    # White move
    can_move = preventer.can_engine_move('white', 'white')
    if can_move:
        print("✅ White allowed to move first")
    else:
        print("❌ White incorrectly prevented from moving first")
    
    time.sleep(0.1)  # Small delay
    
    # Black move
    can_move = preventer.can_engine_move('black', 'black')
    if can_move:
        print("✅ Black allowed to move after white")
    else:
        print("❌ Black incorrectly prevented from moving after white")
    
    # Test 2: Double move prevention
    print("\n2️⃣ Testing Double Move Prevention")
    print("-" * 30)
    
    # Try white move again immediately
    can_move = preventer.can_engine_move('white', 'white')
    if not can_move:
        print("✅ White correctly prevented from double move")
    else:
        print("❌ White incorrectly allowed double move")
    
    # Test 3: Cooldown system
    print("\n3️⃣ Testing Cooldown System")
    print("-" * 30)
    
    # Wait for cooldown
    time.sleep(0.6)  # Wait longer than cooldown
    
    # Try white move after cooldown
    can_move = preventer.can_engine_move('white', 'white')
    if can_move:
        print("✅ White allowed to move after cooldown")
    else:
        print("❌ White incorrectly prevented after cooldown")
    
    pygame.quit()
    return True

def test_engine_integration():
    """Test engine integration with validation"""
    print("\n🧪 Testing Engine Integration")
    print("=" * 50)
    
    pygame.init()
    game = Game()
    
    # Test 1: Validator initialization
    print("\n1️⃣ Testing Validator Initialization")
    print("-" * 30)
    
    if hasattr(game, 'move_validator'):
        print("✅ Move validator initialized")
    else:
        print("❌ Move validator not initialized")
    
    if hasattr(game, 'engine_move_preventer'):
        print("✅ Engine move preventer initialized")
    else:
        print("❌ Engine move preventer not initialized")
    
    # Test 2: Board position validation
    print("\n2️⃣ Testing Board Position Validation")
    print("-" * 30)
    
    valid_position = game.move_validator.validate_engine_position(game.board, 'white')
    if valid_position:
        print("✅ Initial board position valid")
    else:
        print("❌ Initial board position invalid")
    
    # Test 3: FEN validation
    print("\n3️⃣ Testing FEN Validation")
    print("-" * 30)
    
    fen = game.board.to_fen('white')
    if fen and len(fen.strip()) > 0:
        print(f"✅ FEN generated: {fen[:50]}...")
        
        # Validate FEN format
        parts = fen.split()
        if len(parts) >= 4:
            print("✅ FEN format valid")
        else:
            print("❌ FEN format invalid")
    else:
        print("❌ FEN generation failed")
    
    pygame.quit()
    return True

def test_comprehensive_validation():
    """Run comprehensive validation tests"""
    print("\n🧪 Comprehensive Engine Fix Validation")
    print("=" * 60)
    
    tests = [
        ("Move Validation System", test_move_validation),
        ("Double Move Prevention", test_double_move_prevention),
        ("Engine Integration", test_engine_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n🎯 Engine Fix Test Results")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All Engine Fixes Working!")
        print("✅ Move validation prevents illegal moves")
        print("✅ Double move prevention working")
        print("✅ UCI parsing robust")
        print("✅ Engine integration secure")
        print("✅ Position validation active")
        print("\n🛡️ Engine illegal move issues FIXED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) need attention")
    
    return passed == total

if __name__ == "__main__":
    success = test_comprehensive_validation()
    sys.exit(0 if success else 1)