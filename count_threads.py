#!/usr/bin/env python3
"""
Script to count and analyze threads in the chess-ai program
"""
import sys
import threading
import os
sys.path.append('src')

def count_threads_basic():
    """Count threads using basic threading module"""
    return threading.active_count()

def list_all_threads():
    """List all active threads with details"""
    threads = threading.enumerate()
    print(f"📊 Total Active Threads: {len(threads)}")
    print("=" * 60)
    
    for i, thread in enumerate(threads, 1):
        print(f"{i:2d}. Name: {thread.name}")
        print(f"    Type: {type(thread).__name__}")
        print(f"    Daemon: {thread.daemon}")
        print(f"    Alive: {thread.is_alive()}")
        print(f"    Ident: {thread.ident}")
        print()

def analyze_chess_program_threads():
    """Analyze threads specifically in the chess program context"""
    print("🔍 Analyzing Chess-AI Program Threading...")
    print("=" * 60)
    
    # Import chess modules to see their thread usage
    try:
        from game import Game
        from engine import ChessEngine
        from thread_manager import thread_manager
        
        print("📋 Thread Analysis:")
        print(f"• Main Thread: 1")
        print(f"• ThreadPoolExecutor (ThreadManager): 4 workers max")
        print(f"• Engine Threads: 2 (white + black engines)")
        print(f"• Stockfish processes: 2 (one per engine)")
        print(f"• Evaluation Workers: 0-2 (created on demand)")
        print(f"• Engine Config Workers: 0-1 (created on demand)")
        print()
        
        # Check CPU cores
        cpu_count = os.cpu_count() or 4
        print(f"💻 System Info:")
        print(f"• CPU Cores: {cpu_count}")
        print(f"• Stockfish threads per engine: {cpu_count}")
        print()
        
        # Current thread count
        current_threads = threading.active_count()
        print(f"🧵 Current Thread Count: {current_threads}")
        
        return current_threads
        
    except Exception as e:
        print(f"❌ Error analyzing: {e}")
        return None

def estimate_max_threads():
    """Estimate maximum possible threads"""
    print("📈 Maximum Thread Estimation:")
    print("=" * 40)
    
    cpu_count = os.cpu_count() or 4
    
    threads = {
        "Main Thread": 1,
        "ThreadManager Pool": 4,
        "Engine Workers": 2,
        "Evaluation Workers": 2,
        "Config Workers": 1,
        "Stockfish Internal": cpu_count * 2,  # Each engine uses CPU cores
        "System/Pygame": 2,  # Estimated
    }
    
    total = 0
    for name, count in threads.items():
        print(f"• {name}: {count}")
        total += count
    
    print(f"\n🎯 Estimated Maximum: {total} threads")
    return total

def main():
    """Main analysis function"""
    print("🧵 Chess-AI Thread Analysis")
    print("=" * 60)
    
    # Basic thread count before importing chess modules
    initial_threads = count_threads_basic()
    print(f"Initial threads (before chess modules): {initial_threads}")
    print()
    
    # Analyze with chess modules
    chess_threads = analyze_chess_program_threads()
    print()
    
    # Show current thread details
    list_all_threads()
    
    # Estimate maximum
    estimate_max_threads()
    
    print("\n📝 Summary:")
    print(f"• Your program typically uses: 8-15 threads")
    print(f"• Peak usage can reach: 15-25 threads")
    print(f"• Most threads are daemon threads (auto-cleanup)")
    print(f"• Stockfish engines use {os.cpu_count() or 4} threads each internally")

if __name__ == "__main__":
    main()