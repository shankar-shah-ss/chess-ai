#!/usr/bin/env python3
"""
Monitor threads during actual game execution
"""
import sys
import threading
import time
import os
sys.path.append('src')

def monitor_threads_during_game():
    """Monitor threads while game components are active"""
    print("🎮 Monitoring Threads During Game Execution")
    print("=" * 60)
    
    # Import and initialize game components
    from game import Game
    from main import Main
    
    print(f"After imports: {threading.active_count()} threads")
    
    # Create game instance
    game = Game()
    print(f"After Game creation: {threading.active_count()} threads")
    
    # List current threads
    threads = threading.enumerate()
    print(f"\n📊 Active Threads ({len(threads)}):")
    for i, thread in enumerate(threads, 1):
        print(f"{i:2d}. {thread.name} ({type(thread).__name__}) - Daemon: {thread.daemon}")
    
    # Test engine thread creation
    print(f"\n🤖 Testing Engine Thread Creation...")
    if game.engine_white_instance and game.engine_black_instance:
        print("✅ Both engines initialized")
        
        # Enable engines to see thread creation
        game.engine_white = True
        game.engine_black = True
        print(f"After enabling engines: {threading.active_count()} threads")
        
        # Try to schedule an engine move to see worker threads
        try:
            game.schedule_engine_move()
            time.sleep(0.1)  # Give time for thread creation
            print(f"After scheduling engine move: {threading.active_count()} threads")
        except Exception as e:
            print(f"Engine scheduling: {e}")
    
    # List final threads
    final_threads = threading.enumerate()
    print(f"\n📊 Final Active Threads ({len(final_threads)}):")
    for i, thread in enumerate(final_threads, 1):
        print(f"{i:2d}. {thread.name} ({type(thread).__name__}) - Daemon: {thread.daemon}")
    
    return len(final_threads)

def analyze_thread_types():
    """Analyze different types of threads in the program"""
    print("\n🔍 Thread Type Analysis:")
    print("=" * 40)
    
    thread_info = {
        "Python Threads": {
            "MainThread": "Main program execution",
            "EngineWorker": "Chess engine move calculation",
            "EvaluationWorker": "Position evaluation",
            "EngineConfigWorker": "Engine configuration changes",
            "ThreadPoolExecutor": "Managed thread pool workers"
        },
        "External Processes": {
            "Stockfish": "Chess engine processes (2 instances)",
            "Stockfish Internal": "Each Stockfish uses 8 threads internally"
        },
        "System Threads": {
            "Pygame": "Graphics and event handling",
            "Python GC": "Garbage collection",
            "System": "OS-level threads"
        }
    }
    
    for category, threads in thread_info.items():
        print(f"\n📂 {category}:")
        for name, description in threads.items():
            print(f"  • {name}: {description}")

def main():
    """Main monitoring function"""
    print("🧵 Chess-AI Thread Monitor")
    print("=" * 60)
    
    initial_count = threading.active_count()
    print(f"Starting threads: {initial_count}")
    
    try:
        final_count = monitor_threads_during_game()
        
        analyze_thread_types()
        
        print(f"\n📊 Thread Summary:")
        print(f"• Starting threads: {initial_count}")
        print(f"• Peak threads during execution: {final_count}")
        print(f"• Your system has {os.cpu_count()} CPU cores")
        print(f"• Each Stockfish engine can use up to {os.cpu_count()} threads")
        
        print(f"\n🎯 Answer: Your program uses approximately {final_count}-{final_count + 16} threads")
        print(f"   • Python threads: {final_count}")
        print(f"   • Stockfish internal threads: up to 16 (8 per engine)")
        print(f"   • Total system impact: {final_count + 16} threads maximum")
        
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()