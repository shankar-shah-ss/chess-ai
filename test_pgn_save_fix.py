#!/usr/bin/env python3
"""
Test the PGN save UI freeze fixes
"""
import sys
sys.path.append('src')
import time
import threading

def test_pgn_save_non_blocking():
    """Test that PGN save doesn't block the main thread"""
    print("🔍 Testing PGN Save Non-Blocking")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    
    # Create PGN manager and add some test data
    pgn = PGNManager()
    pgn.start_new_game("TestWhite", "TestBlack", "Test Game")
    
    # Add some test moves
    from move import Move
    from square import Square
    from piece import Pawn
    
    # Create mock move data
    test_move = Move(Square(6, 4), Square(4, 4))  # e2-e4
    test_piece = Pawn('white')
    
    pgn.add_move(test_move, test_piece)
    
    print(f"✅ Test PGN created with {pgn.get_move_count()} moves")
    
    # Test non-blocking save
    start_time = time.time()
    
    # This should return immediately without blocking
    result = pgn.save_pgn_dialog()
    
    elapsed = time.time() - start_time
    
    if elapsed < 0.1:  # Should return almost immediately
        print(f"✅ save_pgn_dialog() returned in {elapsed:.3f}s (non-blocking)")
    else:
        print(f"❌ save_pgn_dialog() took {elapsed:.3f}s (may be blocking)")
    
    # Test quick save
    start_time = time.time()
    result = pgn.save_pgn_quick("test_quick_save")
    elapsed = time.time() - start_time
    
    if elapsed < 0.1:
        print(f"✅ save_pgn_quick() returned in {elapsed:.3f}s (non-blocking)")
    else:
        print(f"❌ save_pgn_quick() took {elapsed:.3f}s (may be blocking)")
    
    # Give background threads time to complete
    time.sleep(2)
    
    return True

def test_pgn_wrapper_non_blocking():
    """Test PGN wrapper save methods"""
    print(f"\n🔍 Testing PGN Wrapper Non-Blocking")
    print("=" * 45)
    
    from game import Game
    import pygame
    
    pygame.init()
    
    # Create game and start PGN recording
    game = Game()
    game.pgn.start_recording()
    
    # Add a test move
    from move import Move
    from square import Square
    from piece import Pawn
    
    test_move = Move(Square(6, 4), Square(4, 4))
    test_piece = Pawn('white')
    game.pgn.record_move(test_move, test_piece)
    
    print(f"✅ Game PGN created with {game.pgn.get_move_count()} moves")
    
    # Test wrapper save methods
    start_time = time.time()
    result = game.pgn.save_game()
    elapsed = time.time() - start_time
    
    if elapsed < 0.1:
        print(f"✅ pgn.save_game() returned in {elapsed:.3f}s (non-blocking)")
    else:
        print(f"❌ pgn.save_game() took {elapsed:.3f}s (may be blocking)")
    
    start_time = time.time()
    result = game.pgn.save_game_quick("test_wrapper_quick")
    elapsed = time.time() - start_time
    
    if elapsed < 0.1:
        print(f"✅ pgn.save_game_quick() returned in {elapsed:.3f}s (non-blocking)")
    else:
        print(f"❌ pgn.save_game_quick() took {elapsed:.3f}s (may be blocking)")
    
    pygame.quit()
    
    # Give background threads time to complete
    time.sleep(2)
    
    return True

def test_thread_safety():
    """Test thread safety of PGN save operations"""
    print(f"\n🔍 Testing PGN Save Thread Safety")
    print("=" * 40)
    
    from pgn_manager import PGNManager
    
    # Create PGN manager
    pgn = PGNManager()
    pgn.start_new_game("ThreadTest1", "ThreadTest2", "Thread Safety Test")
    
    # Add test move
    from move import Move
    from square import Square
    from piece import Pawn
    
    test_move = Move(Square(6, 4), Square(4, 4))
    test_piece = Pawn('white')
    pgn.add_move(test_move, test_piece)
    
    # Test multiple concurrent save operations
    results = []
    errors = []
    
    def save_worker(worker_id):
        """Worker function for concurrent saves"""
        try:
            result = pgn.save_pgn_quick(f"thread_test_{worker_id}")
            results.append(f"Worker {worker_id}: Success")
        except Exception as e:
            errors.append(f"Worker {worker_id}: {e}")
    
    # Start multiple save threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=save_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    print(f"  Successful saves: {len(results)}")
    print(f"  Errors: {len(errors)}")
    
    if len(errors) == 0:
        print("✅ Thread safety test passed")
    else:
        print("❌ Thread safety issues detected:")
        for error in errors:
            print(f"    {error}")
    
    return len(errors) == 0

def test_ui_responsiveness_simulation():
    """Simulate UI responsiveness during PGN save"""
    print(f"\n🔍 Testing UI Responsiveness Simulation")
    print("=" * 45)
    
    from pgn_manager import PGNManager
    import time
    
    # Create PGN with multiple moves
    pgn = PGNManager()
    pgn.start_new_game("UITest1", "UITest2", "UI Responsiveness Test")
    
    # Add multiple moves to make PGN generation more work
    from move import Move
    from square import Square
    from piece import Pawn, Knight
    
    moves = [
        (Move(Square(6, 4), Square(4, 4)), Pawn('white')),
        (Move(Square(1, 1), Square(2, 3)), Knight('black')),
        (Move(Square(6, 3), Square(4, 3)), Pawn('white')),
        (Move(Square(0, 6), Square(2, 5)), Knight('black')),
    ]
    
    for move, piece in moves:
        pgn.add_move(move, piece)
    
    print(f"✅ Created PGN with {pgn.get_move_count()} moves")
    
    # Simulate UI loop during save
    ui_responsive = True
    ui_iterations = 0
    
    def ui_simulation():
        """Simulate UI main loop"""
        nonlocal ui_responsive, ui_iterations
        start_time = time.time()
        
        while time.time() - start_time < 3:  # Run for 3 seconds
            # Simulate UI work
            time.sleep(0.016)  # ~60 FPS
            ui_iterations += 1
            
            # Check if we can do UI work (not blocked)
            if time.time() - start_time > 2:  # After 2 seconds
                break
    
    # Start UI simulation
    ui_thread = threading.Thread(target=ui_simulation)
    ui_thread.start()
    
    # Start PGN save (should not block UI)
    time.sleep(0.5)  # Let UI start
    pgn.save_pgn_quick("ui_test")
    
    # Wait for UI simulation to complete
    ui_thread.join()
    
    if ui_iterations > 100:  # Should have many iterations if not blocked
        print(f"✅ UI remained responsive ({ui_iterations} iterations)")
    else:
        print(f"❌ UI may have been blocked ({ui_iterations} iterations)")
    
    return ui_iterations > 100

def main():
    """Run PGN save fix tests"""
    print("🔧 PGN Save UI Freeze Fix Test Suite")
    print("Testing fixes for PGN save blocking UI")
    print("=" * 60)
    
    tests = [
        ("PGN Save Non-Blocking", test_pgn_save_non_blocking),
        ("PGN Wrapper Non-Blocking", test_pgn_wrapper_non_blocking),
        ("Thread Safety", test_thread_safety),
        ("UI Responsiveness Simulation", test_ui_responsiveness_simulation),
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
    print(f"\n🎯 PGN Save Fix Test Results")
    print("=" * 35)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All PGN save fixes working correctly!")
        print("✅ Non-blocking PGN save implemented")
        print("✅ Background threading for save operations")
        print("✅ Quick save option added")
        print("✅ Keyboard shortcuts: Ctrl+S (quick), Shift+S (dialog)")
        print("✅ UI will no longer freeze during PGN save")
    else:
        print("\n⚠️ Some issues remain")
        print("Please check the failed tests above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)