#!/usr/bin/env python3
"""
Demonstrate thread creation when changing engine depth/level
"""
import sys
import threading
import time
sys.path.append('src')

def monitor_thread_changes():
    """Monitor thread creation during depth/level changes"""
    print("🧵 Thread Creation Demo: Depth/Level Changes")
    print("=" * 60)
    
    from game import Game
    
    # Create game and enable engines
    game = Game()
    game.engine_white = True
    game.engine_black = True
    
    def show_threads(label):
        threads = threading.enumerate()
        print(f"\n📊 {label}: {len(threads)} threads")
        for i, thread in enumerate(threads, 1):
            print(f"  {i}. {thread.name} ({type(thread).__name__}) - Alive: {thread.is_alive()}")
    
    show_threads("Initial state")
    
    print(f"\n🔧 Changing engine depth from {game.depth} to {game.depth + 1}...")
    game.set_engine_depth(game.depth + 1)
    time.sleep(0.05)  # Give thread time to start
    show_threads("After depth change")
    
    time.sleep(0.2)  # Wait for config thread to complete
    show_threads("After config thread completes")
    
    print(f"\n🎯 Changing engine level from {game.level} to {game.level - 1}...")
    game.set_engine_level(game.level - 1)
    time.sleep(0.05)  # Give thread time to start
    show_threads("After level change")
    
    time.sleep(0.2)  # Wait for config thread to complete
    show_threads("After config thread completes")
    
    print(f"\n⚡ Rapid changes (simulating fast key presses)...")
    for i in range(3):
        print(f"  Change {i+1}: Depth {game.depth + 1}")
        game.set_engine_depth(game.depth + 1)
        time.sleep(0.02)  # Very short delay
        threads = threading.enumerate()
        print(f"    Threads: {len(threads)}")
    
    time.sleep(0.3)  # Wait for all to complete
    show_threads("After rapid changes")

def explain_threading_behavior():
    """Explain the threading behavior"""
    print(f"\n📚 How Thread Creation Works:")
    print("=" * 40)
    print("🔹 When you press +/- (level) or ↑/↓ (depth):")
    print("  1. A new EngineConfigWorker thread is created")
    print("  2. Any existing config thread is stopped")
    print("  3. The new thread configures both engines")
    print("  4. Thread automatically terminates when done")
    print()
    print("🔹 Thread lifecycle:")
    print("  • Created: Immediately when key is pressed")
    print("  • Duration: ~100-200ms (includes 100ms delay)")
    print("  • Cleanup: Automatic (daemon thread)")
    print()
    print("🔹 Why use threads?")
    print("  • Prevents UI freezing during engine configuration")
    print("  • Allows cancellation of slow operations")
    print("  • Handles rapid key presses gracefully")
    print()
    print("🔹 Key bindings:")
    print("  • +/= : Increase engine level")
    print("  • - : Decrease engine level") 
    print("  • ↑ : Increase engine depth")
    print("  • ↓ : Decrease engine depth")

def main():
    """Main demonstration"""
    try:
        monitor_thread_changes()
        explain_threading_behavior()
        
        print(f"\n✅ Summary:")
        print("• YES, each depth/level change creates a new thread")
        print("• Thread is short-lived (~100-200ms)")
        print("• Old threads are stopped before new ones start")
        print("• Maximum 1 config thread active at any time")
        print("• Threads are daemon threads (auto-cleanup)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()