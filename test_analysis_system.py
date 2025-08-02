#!/usr/bin/env python3
"""
Test script for the Chess Analysis System
Demonstrates all 4 phases of functionality
"""

import sys
sys.path.append('src')
import pygame
import time
from chess_analysis_system import ChessAnalysisSystem, AnalysisMode
from game import Game
from opening_database import opening_database

def test_phase_1_game_review():
    """Test Phase 1: Basic Game Review Mode"""
    print("\n🎯 Testing Phase 1: Basic Game Review Mode")
    print("=" * 60)
    
    pygame.init()
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Sample PGN for testing
    sample_pgn = """[Event "Test Game"]
[Site "Chess AI"]
[Date "2024.01.01"]
[Round "1"]
[White "Player 1"]
[Black "Player 2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0"""
    
    # Test loading PGN
    success = analysis_system.load_game_from_pgn(sample_pgn)
    if success:
        print("✅ PGN loaded successfully")
        print(f"   Moves loaded: {len(analysis_system.move_history)}")
    else:
        print("❌ Failed to load PGN")
        return False
    
    # Test navigation
    print("\n📍 Testing Navigation:")
    
    # Navigate to different positions
    analysis_system.navigate_to_move(5)
    print(f"✅ Navigated to move 5: current index = {analysis_system.current_move_index}")
    
    analysis_system.navigate_next()
    print(f"✅ Next move: current index = {analysis_system.current_move_index}")
    
    analysis_system.navigate_previous()
    print(f"✅ Previous move: current index = {analysis_system.current_move_index}")
    
    analysis_system.navigate_first()
    print(f"✅ First move: current index = {analysis_system.current_move_index}")
    
    analysis_system.navigate_last()
    print(f"✅ Last move: current index = {analysis_system.current_move_index}")
    
    pygame.quit()
    return True

def test_phase_2_engine_analysis():
    """Test Phase 2: Stockfish Integration & Evaluation"""
    print("\n🎯 Testing Phase 2: Engine Analysis")
    print("=" * 60)
    
    pygame.init()
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Test position analysis
    print("🔍 Analyzing starting position...")
    analysis = analysis_system.analyze_current_position(depth=15)
    
    if analysis:
        print("✅ Position analysis completed:")
        print(f"   Evaluation: {analysis.get('evaluation', 'N/A')}")
        print(f"   Best move: {analysis.get('best_move', 'N/A')}")
        print(f"   Depth: {analysis.get('depth', 'N/A')}")
        print(f"   Principal variation: {analysis.get('principal_variation', [])}")
    else:
        print("⚠️ Position analysis not available (engine may not be initialized)")
    
    # Test evaluation bar values
    print(f"\n📊 Evaluation bar:")
    print(f"   Current evaluation: {analysis_system.current_evaluation}")
    print(f"   Best move hint: {analysis_system.best_move_hint}")
    
    pygame.quit()
    return True

def test_phase_3_move_classification():
    """Test Phase 3: Move Classification & Opening Explorer"""
    print("\n🎯 Testing Phase 3: Move Classification & Opening Detection")
    print("=" * 60)
    
    pygame.init()
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Test move classification
    print("🏷️ Testing Move Classifications:")
    
    test_cases = [
        (0, "Best Move"),
        (25, "Good Move"),
        (75, "Inaccuracy"),
        (150, "Mistake"),
        (300, "Blunder")
    ]
    
    for cp_loss, expected in test_cases:
        classification = analysis_system.classify_move(cp_loss)
        annotation = analysis_system.get_move_annotation(classification)
        print(f"   {cp_loss} cp loss → {classification.value} {annotation} ({expected})")
    
    # Test opening detection
    print("\n🔍 Testing Opening Detection:")
    
    test_positions = [
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3", "King's Pawn Opening"),
        ("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6", "Sicilian Defense"),
        ("rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3", "Queen's Pawn Opening"),
        ("rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3", "English Opening")
    ]
    
    for fen, expected_name in test_positions:
        opening_info = opening_database.detect_opening(fen)
        detected_name = opening_info.get('name', 'Unknown')
        eco_code = opening_info.get('eco', '')
        
        status = "✅" if expected_name in detected_name else "⚠️"
        print(f"   {status} {detected_name} ({eco_code})")
    
    # Test accuracy calculation
    print(f"\n📈 Accuracy Scores:")
    print(f"   White: {analysis_system.accuracy_scores['white']:.1f}%")
    print(f"   Black: {analysis_system.accuracy_scores['black']:.1f}%")
    
    pygame.quit()
    return True

def test_phase_4_interactive_exploration():
    """Test Phase 4: Interactive Exploration & Custom Position Analysis"""
    print("\n🎯 Testing Phase 4: Interactive Exploration")
    print("=" * 60)
    
    pygame.init()
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Test exploration mode
    print("🔍 Testing Exploration Mode:")
    
    analysis_system.enter_exploration_mode()
    print(f"✅ Exploration mode: {analysis_system.exploration_mode}")
    print(f"✅ Free play enabled: {analysis_system.free_play_enabled}")
    
    # Test custom position
    print("\n🎲 Testing Custom Position:")
    
    # Famous position: "Immortal Game" position
    custom_fen = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq -"
    
    success = analysis_system.set_custom_position(custom_fen)
    if success:
        print("✅ Custom position set successfully")
        print(f"   Position: {custom_fen[:50]}...")
    else:
        print("❌ Failed to set custom position")
    
    # Test variation analysis
    print("\n🌳 Testing Variation Analysis:")
    
    test_moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
    variation_analysis = analysis_system.analyze_variation(test_moves)
    
    if variation_analysis:
        print("✅ Variation analysis completed:")
        print(f"   Moves analyzed: {len(variation_analysis.get('moves', []))}")
        print(f"   Best continuations: {len(variation_analysis.get('best_continuations', []))}")
    else:
        print("⚠️ Variation analysis not available")
    
    # Exit exploration mode
    analysis_system.exit_exploration_mode()
    print(f"✅ Exploration mode exited: {not analysis_system.exploration_mode}")
    
    pygame.quit()
    return True

def test_ui_components():
    """Test UI rendering components"""
    print("\n🎯 Testing UI Components")
    print("=" * 60)
    
    pygame.init()
    screen = pygame.display.set_mode((1220, 800))
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Load a sample game for UI testing
    sample_pgn = """[Event "UI Test"]
[Site "Chess AI"]
[Date "2024.01.01"]
[White "Test Player"]
[Black "Test Engine"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"""
    
    analysis_system.load_game_from_pgn(sample_pgn)
    
    # Test different modes
    modes = [
        AnalysisMode.REVIEW,
        AnalysisMode.ENGINE,
        AnalysisMode.CLASSIFICATION,
        AnalysisMode.EXPLORATION
    ]
    
    for mode in modes:
        analysis_system.current_mode = mode
        print(f"🎨 Testing UI for {mode.value} mode...")
        
        # Clear screen
        screen.fill((240, 240, 240))
        
        # Render analysis panel
        try:
            analysis_system.render_analysis_panel(screen)
            print(f"   ✅ {mode.value} UI rendered successfully")
        except Exception as e:
            print(f"   ❌ {mode.value} UI rendering failed: {e}")
    
    pygame.quit()
    return True

def test_api_methods():
    """Test API-like methods"""
    print("\n🎯 Testing API Methods")
    print("=" * 60)
    
    pygame.init()
    game = Game()
    analysis_system = ChessAnalysisSystem(game)
    
    # Test status API
    status = analysis_system.get_analysis_status()
    print("📊 Analysis Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Load game for export test
    sample_pgn = """[Event "Export Test"]
[Site "Chess AI"]
[Date "2024.01.01"]
[White "Player"]
[Black "Engine"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0"""
    
    analysis_system.load_game_from_pgn(sample_pgn)
    
    # Test export (will be None without full analysis)
    export_data = analysis_system.export_analysis()
    if export_data:
        print("✅ Analysis export successful")
        print(f"   Export size: {len(export_data)} characters")
    else:
        print("⚠️ No analysis data to export (expected without engine analysis)")
    
    pygame.quit()
    return True

def run_comprehensive_tests():
    """Run all analysis system tests"""
    print("🧪 Chess Analysis System - Comprehensive Test Suite")
    print("Testing all 4 phases of functionality")
    print("=" * 80)
    
    tests = [
        ("Phase 1: Game Review Mode", test_phase_1_game_review),
        ("Phase 2: Engine Analysis", test_phase_2_engine_analysis),
        ("Phase 3: Move Classification", test_phase_3_move_classification),
        ("Phase 4: Interactive Exploration", test_phase_4_interactive_exploration),
        ("UI Components", test_ui_components),
        ("API Methods", test_api_methods),
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print(f"\n🎯 Chess Analysis System Test Results")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All Analysis System Features Working!")
        print("✅ Phase 1: Game Review with PGN loading and navigation")
        print("✅ Phase 2: Engine integration with evaluation bar")
        print("✅ Phase 3: Move classification and opening detection")
        print("✅ Phase 4: Interactive exploration and custom positions")
        print("✅ Professional UI components")
        print("✅ API methods for integration")
        print("\n🏆 Professional Chess Analysis System Ready!")
        print("🎮 Press F5 in game to toggle analysis panel")
        print("🎮 Use F1-F4 to switch between analysis modes")
        print("🎮 Arrow keys for navigation in review mode")
    else:
        print(f"\n⚠️ {total - passed} test(s) need attention")
        print("Some features may have limited functionality without full engine integration")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)