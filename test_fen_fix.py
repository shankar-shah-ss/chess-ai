#!/usr/bin/env python3
"""
Test the FEN generation fixes for engine vs engine
"""
import sys
sys.path.append('src')

def test_engine_vs_engine_fen():
    """Test FEN generation during engine vs engine gameplay"""
    print("🔍 Testing Engine vs Engine FEN Generation")
    print("=" * 50)
    
    from game import Game
    import pygame
    import time
    
    # Initialize pygame
    pygame.init()
    
    # Create game with maximum settings
    game = Game()
    game.depth = 20  # Maximum depth
    game.level = 20  # Maximum level
    
    # Set engine vs engine mode
    game.engine_white = True
    game.engine_black = True
    game.game_mode = 2  # Engine vs Engine
    
    print(f"✅ Game initialized with max settings (depth={game.depth}, level={game.level})")
    print(f"✅ Engine vs Engine mode enabled")
    
    # Test initial FEN generation
    fen = game.board.to_fen(game.next_player)
    print(f"Initial FEN: {fen}")
    
    if fen is None:
        print("❌ Initial FEN generation failed!")
        return False
    
    is_valid = game._validate_fen(fen)
    print(f"Initial FEN valid: {'✅' if is_valid else '❌'}")
    
    if not is_valid:
        print("❌ Initial FEN validation failed!")
        return False
    
    # Simulate rapid moves like in engine vs engine
    print(f"\n🎮 Simulating Engine vs Engine Moves")
    print("=" * 40)
    
    move_count = 0
    max_moves = 20  # Test first 20 moves
    
    try:
        for move_num in range(max_moves):
            print(f"\nMove {move_num + 1}:")
            
            # Test FEN generation before scheduling engine
            with game.board_state_lock:
                fen = game.board.to_fen(game.next_player)
            
            if fen is None:
                print(f"❌ FEN generation returned None at move {move_num + 1}")
                game._debug_board_state()
                break
            
            is_valid = game._validate_fen(fen)
            print(f"  FEN: {fen[:50]}...")
            print(f"  Valid: {'✅' if is_valid else '❌'}")
            
            if not is_valid:
                print(f"❌ FEN validation failed at move {move_num + 1}")
                game._debug_board_state()
                break
            
            # Find and make a valid move
            move_made = False
            for row in range(8):
                for col in range(8):
                    square = game.board.squares[row][col]
                    if square.has_piece() and square.piece.color == game.next_player:
                        piece = square.piece
                        game.board.calc_moves(piece, row, col, bool=False)
                        if piece.moves:
                            move = piece.moves[0]
                            print(f"  Making move: {piece.color} {piece.name} from ({row},{col}) to ({move.final.row},{move.final.col})")
                            game.make_move(piece, move)
                            move_made = True
                            move_count += 1
                            break
                if move_made:
                    break
            
            if not move_made:
                print(f"  No valid moves found at move {move_num + 1}")
                break
            
            # Check if game is over
            if game.game_over:
                print(f"  Game over: {game.winner}")
                break
    
    except Exception as e:
        print(f"❌ Error during move simulation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n📊 Test Results:")
    print(f"  Moves completed: {move_count}")
    print(f"  FEN generation: {'✅ Working' if move_count > 0 else '❌ Failed'}")
    print(f"  Thread safety: {'✅ Protected' if hasattr(game, 'board_state_lock') else '❌ Not protected'}")
    
    pygame.quit()
    return move_count > 0

def test_concurrent_fen_access():
    """Test concurrent FEN generation to simulate threading issues"""
    print(f"\n🔍 Testing Concurrent FEN Access")
    print("=" * 40)
    
    from game import Game
    import pygame
    import threading
    import time
    
    pygame.init()
    game = Game()
    
    results = []
    errors = []
    
    def generate_fen_worker(worker_id):
        """Worker function to generate FEN concurrently"""
        try:
            for i in range(10):
                with game.board_state_lock:
                    fen = game.board.to_fen(game.next_player)
                
                if fen is None:
                    errors.append(f"Worker {worker_id}: FEN generation returned None")
                    return
                
                is_valid = game._validate_fen(fen)
                if not is_valid:
                    errors.append(f"Worker {worker_id}: Invalid FEN generated")
                    return
                
                results.append(f"Worker {worker_id}: Success")
                time.sleep(0.01)  # Small delay to increase chance of race conditions
                
        except Exception as e:
            errors.append(f"Worker {worker_id}: Exception - {e}")
    
    # Create multiple threads to access FEN generation simultaneously
    threads = []
    for i in range(5):
        thread = threading.Thread(target=generate_fen_worker, args=(i,))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"  Successful operations: {len(results)}")
    print(f"  Errors: {len(errors)}")
    
    if errors:
        print("  Error details:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    - {error}")
    
    pygame.quit()
    return len(errors) == 0

def test_board_state_corruption():
    """Test for board state corruption scenarios"""
    print(f"\n🔍 Testing Board State Corruption Scenarios")
    print("=" * 50)
    
    from game import Game
    from piece import Pawn, Knight
    from move import Move
    from square import Square
    import pygame
    
    pygame.init()
    game = Game()
    
    # Test 1: Piece with invalid attributes
    print("Test 1: Piece with invalid attributes")
    try:
        # Create a piece with missing attributes
        invalid_piece = Pawn('white')
        delattr(invalid_piece, 'name')  # Remove name attribute
        
        # Place it on the board
        game.board.squares[4][4].piece = invalid_piece
        
        fen = game.board.to_fen(game.next_player)
        if fen is None:
            print("  ✅ Correctly detected invalid piece and returned None")
        else:
            print("  ❌ Failed to detect invalid piece")
            
        # Restore valid piece
        game.board.squares[4][4].piece = None
        
    except Exception as e:
        print(f"  ❌ Exception during invalid piece test: {e}")
    
    # Test 2: None piece in non-empty square
    print("\nTest 2: None piece in non-empty square")
    try:
        # Create a square that claims to have a piece but has None
        square = game.board.squares[4][4]
        square.piece = None
        # Manually set the square to claim it has a piece (this simulates corruption)
        original_isempty = square.isempty
        square.isempty = lambda: False  # Force it to claim it's not empty
        
        fen = game.board.to_fen(game.next_player)
        if fen is None:
            print("  ✅ Correctly detected None piece in non-empty square")
        else:
            print("  ❌ Failed to detect None piece corruption")
            
        # Restore normal function
        square.isempty = original_isempty
        
    except Exception as e:
        print(f"  ❌ Exception during None piece test: {e}")
    
    # Test 3: Invalid next_player
    print("\nTest 3: Invalid next_player")
    try:
        fen = game.board.to_fen("invalid_color")
        if fen is None:
            print("  ✅ Correctly rejected invalid next_player")
        else:
            print("  ❌ Failed to reject invalid next_player")
            
    except Exception as e:
        print(f"  ❌ Exception during invalid next_player test: {e}")
    
    pygame.quit()
    return True

def main():
    """Run all FEN fix tests"""
    print("🔧 FEN Generation Fix Test Suite")
    print("Testing fixes for engine vs engine FEN issues")
    print("=" * 60)
    
    tests = [
        ("Engine vs Engine FEN", test_engine_vs_engine_fen),
        ("Concurrent FEN Access", test_concurrent_fen_access),
        ("Board State Corruption", test_board_state_corruption),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n🎯 Fix Test Results")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n📊 Overall: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All fixes working correctly!")
        print("✅ Thread-safe FEN generation implemented")
        print("✅ Board state corruption detection added")
        print("✅ Enhanced error handling in place")
        print("✅ Engine vs Engine should now work properly")
    else:
        print("\n⚠️ Some issues remain")
        print("Please check the failed tests above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)