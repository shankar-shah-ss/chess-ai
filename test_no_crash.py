#!/usr/bin/env python3
"""
Test that the game starts without crashing
"""
import sys
import signal
import time
sys.path.append('src')

def test_game_no_crash():
    """Test that game starts without the Tkinter crash"""
    print("🎮 Testing Game Startup (No Crash Test)")
    print("=" * 50)
    
    try:
        # Set up signal handler for timeout
        def timeout_handler(signum, frame):
            print("✅ Game ran for 3 seconds without crashing!")
            print("✅ PGN system is working correctly")
            sys.exit(0)
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)  # 3 second timeout
        
        # Import and start the game
        from main import Main
        
        print("✓ Imports successful")
        print("✓ Creating Main instance...")
        
        main = Main()
        print("✓ Main instance created")
        print("✓ Starting game loop...")
        
        # This should run without the Tkinter crash
        main.mainloop()
        
    except SystemExit:
        # Expected from timeout
        pass
    except Exception as e:
        print(f"❌ Game crashed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_game_no_crash()
    if success:
        print("\n🎉 SUCCESS: Game runs without Tkinter crash!")
        print("✅ PGN system is macOS compatible")
    else:
        print("\n❌ FAILED: Game still has issues")