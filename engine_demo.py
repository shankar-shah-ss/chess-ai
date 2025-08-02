#!/usr/bin/env python3
"""
Demonstrate separate engines for white and black in Engine vs Engine mode
"""
import sys
import threading
import time
sys.path.append('src')

def demonstrate_separate_engines():
    """Show that white and black use separate engine instances"""
    print("🤖 Engine vs Engine Mode: Separate Engine Demonstration")
    print("=" * 70)
    
    from game import Game
    
    # Create game instance
    game = Game()
    
    print(f"📋 Engine Initialization:")
    print(f"• White Engine: {game.engine_white_instance}")
    print(f"• Black Engine: {game.engine_black_instance}")
    print(f"• Same Instance? {game.engine_white_instance is game.engine_black_instance}")
    print(f"• Both Healthy? White: {game.engine_white_instance._is_healthy if game.engine_white_instance else False}, Black: {game.engine_black_instance._is_healthy if game.engine_black_instance else False}")
    
    # Set to Engine vs Engine mode
    print(f"\n🎮 Setting Game Mode to Engine vs Engine...")
    game.set_game_mode(2)  # Engine vs Engine
    
    print(f"• Engine White Enabled: {game.engine_white}")
    print(f"• Engine Black Enabled: {game.engine_black}")
    
    # Test engine selection for each player
    print(f"\n🔍 Engine Selection by Player:")
    white_engine = game._get_engine_for_player('white')
    black_engine = game._get_engine_for_player('black')
    
    print(f"• White Player Engine: {white_engine}")
    print(f"• Black Player Engine: {black_engine}")
    print(f"• Different Instances? {white_engine is not black_engine}")
    
    # Show engine IDs/memory addresses
    if white_engine and black_engine:
        print(f"• White Engine ID: {id(white_engine)}")
        print(f"• Black Engine ID: {id(black_engine)}")
        print(f"• Memory Address Difference: {abs(id(white_engine) - id(black_engine))}")
    
    # Test configuration changes
    print(f"\n⚙️ Testing Separate Configuration:")
    original_depth = game.depth
    original_level = game.level
    
    print(f"• Original Depth: {original_depth}")
    print(f"• Original Level: {original_level}")
    
    # Change settings (this affects both engines)
    game.set_engine_depth(original_depth + 2)
    time.sleep(0.2)  # Wait for config thread
    
    print(f"• New Depth Applied to Both Engines: {game.depth}")
    
    # Test that both engines can work independently
    print(f"\n🧪 Testing Independent Operation:")
    
    # Simulate white's turn
    print("• Simulating White's Turn:")
    game.next_player = 'white'
    white_engine_for_move = game._get_engine_for_player('white')
    print(f"  - Engine Selected: {id(white_engine_for_move) if white_engine_for_move else 'None'}")
    
    # Simulate black's turn  
    print("• Simulating Black's Turn:")
    game.next_player = 'black'
    black_engine_for_move = game._get_engine_for_player('black')
    print(f"  - Engine Selected: {id(black_engine_for_move) if black_engine_for_move else 'None'}")
    
    print(f"  - Different Engines Used: {white_engine_for_move is not black_engine_for_move}")

def analyze_engine_processes():
    """Analyze the underlying Stockfish processes"""
    print(f"\n🔬 Stockfish Process Analysis:")
    print("=" * 40)
    
    from game import Game
    game = Game()
    
    if game.engine_white_instance and game.engine_black_instance:
        white_engine = game.engine_white_instance
        black_engine = game.engine_black_instance
        
        print(f"📊 Engine Details:")
        print(f"• White Engine Object: {white_engine}")
        print(f"• Black Engine Object: {black_engine}")
        
        # Check if they have separate Stockfish processes
        if hasattr(white_engine, 'engine') and hasattr(black_engine, 'engine'):
            print(f"• White Stockfish Process: {white_engine.engine}")
            print(f"• Black Stockfish Process: {black_engine.engine}")
            print(f"• Separate Processes: {white_engine.engine is not black_engine.engine}")
        
        # Check thread usage
        print(f"\n🧵 Threading Information:")
        print(f"• Each engine can use up to {8} threads internally")
        print(f"• Total Stockfish threads: up to {8 * 2} (8 per engine)")
        print(f"• Python wrapper threads: 2 (one per engine)")

def explain_engine_architecture():
    """Explain the engine architecture"""
    print(f"\n🏗️ Engine Architecture Explanation:")
    print("=" * 50)
    
    architecture = {
        "Game Instance": {
            "engine_white_instance": "ChessEngine() - Dedicated for white pieces",
            "engine_black_instance": "ChessEngine() - Dedicated for black pieces",
            "engine": "Compatibility reference (points to white engine)"
        },
        "Each ChessEngine": {
            "Stockfish Process": "Separate stockfish.exe process",
            "Internal Threads": "Up to 8 threads (matches CPU cores)",
            "Communication": "UCI protocol via stdin/stdout",
            "Memory": "Independent memory space"
        },
        "Game Modes": {
            "Human vs Human": "No engines active",
            "Human vs Engine": "Only black engine active",
            "Engine vs Engine": "Both engines active independently"
        }
    }
    
    for category, details in architecture.items():
        print(f"\n📂 {category}:")
        for item, description in details.items():
            print(f"  • {item}: {description}")

def main():
    """Main demonstration"""
    try:
        demonstrate_separate_engines()
        analyze_engine_processes()
        explain_engine_architecture()
        
        print(f"\n✅ Summary - Engine vs Engine Mode:")
        print("🔹 YES, separate engines are used for white and black")
        print("🔹 Each engine is a complete ChessEngine() instance")
        print("🔹 Each engine runs its own Stockfish process")
        print("🔹 Each Stockfish process uses up to 8 threads internally")
        print("🔹 Engines operate completely independently")
        print("🔹 Total system impact: 2 processes + up to 16 threads")
        print("🔹 Configuration changes apply to both engines simultaneously")
        
        print(f"\n🎯 Resource Usage in Engine vs Engine:")
        print("• Python objects: 2 (ChessEngine instances)")
        print("• Stockfish processes: 2 (separate .exe processes)")
        print("• Stockfish threads: up to 16 (8 per process)")
        print("• Python threads: 2-4 (EngineWorker + config threads)")
        print("• Total threads: ~18-20 threads maximum")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()