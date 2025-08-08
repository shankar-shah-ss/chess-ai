#!/usr/bin/env python3
"""
Analyze and display engine timeouts at different skill levels and depths
"""

import sys
import os
import time
import json
from typing import Dict, List, Tuple, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from engine import ChessEngine
    from chess import STARTING_FEN, Board
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running from the chess-ai directory")
    sys.exit(1)

def load_config() -> Dict:
    """Load configuration from chess_ai_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'chess_ai_config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ Config file not found, using defaults")
        return {
            "engine": {
                "timeout_seconds": 30,
                "default_depth": 15,
                "default_skill_level": 10,
                "max_depth": 20,
                "max_skill_level": 20
            }
        }

def get_timeout_for_level(skill_level: int, depth: int) -> int:
    """Get timeout in milliseconds based on skill level and depth"""
    # This mirrors the logic from engine.py
    if skill_level >= 20 and depth >= 20:
        return 5000   # 5 seconds for maximum strength
    elif skill_level >= 18 or depth >= 18:
        return 4000   # 4 seconds for very high strength
    elif skill_level >= 15 or depth >= 15:
        return 3000   # 3 seconds for high strength
    else:
        return 2000   # 2 seconds for normal play

def analyze_timeout_matrix():
    """Analyze timeout matrix for different skill levels and depths"""
    print("🕐 Chess Engine Timeout Analysis")
    print("=" * 60)
    
    config = load_config()
    engine_config = config.get('engine', {})
    
    print(f"📋 Configuration:")
    print(f"   • Config timeout: {engine_config.get('timeout_seconds', 30)} seconds")
    print(f"   • Max depth: {engine_config.get('max_depth', 20)}")
    print(f"   • Max skill level: {engine_config.get('max_skill_level', 20)}")
    print()
    
    # Define test ranges
    skill_levels = [1, 5, 10, 15, 18, 20]
    depths = [5, 10, 15, 18, 20]
    
    print("🎯 Timeout Matrix (milliseconds):")
    print("-" * 50)
    
    # Header
    print(f"{'Skill/Depth':<12}", end="")
    for depth in depths:
        print(f"{depth:>8}", end="")
    print()
    print("-" * 50)
    
    # Matrix
    for skill in skill_levels:
        print(f"Level {skill:<6}", end="")
        for depth in depths:
            timeout = get_timeout_for_level(skill, depth)
            print(f"{timeout:>8}", end="")
        print()
    
    print()
    
    # Categorize timeouts
    print("📊 Timeout Categories:")
    print("-" * 25)
    
    categories = {
        "Fast (≤2s)": [],
        "Medium (3s)": [],
        "Slow (4s)": [],
        "Maximum (5s)": []
    }
    
    for skill in skill_levels:
        for depth in depths:
            timeout = get_timeout_for_level(skill, depth)
            config_str = f"S{skill}/D{depth}"
            
            if timeout <= 2000:
                categories["Fast (≤2s)"].append(config_str)
            elif timeout == 3000:
                categories["Medium (3s)"].append(config_str)
            elif timeout == 4000:
                categories["Slow (4s)"].append(config_str)
            elif timeout >= 5000:
                categories["Maximum (5s)"].append(config_str)
    
    for category, configs in categories.items():
        if configs:
            print(f"{category:<15}: {', '.join(configs)}")
    
    print()

def test_actual_timeouts():
    """Test actual engine response times"""
    print("⏱️ Actual Engine Performance Test")
    print("=" * 40)
    
    test_positions = [
        (STARTING_FEN, "Starting position"),
        ("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", "Italian Game"),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 5", "Complex middlegame"),
    ]
    
    test_configs = [
        (5, 8, "Beginner"),
        (10, 12, "Intermediate"),
        (15, 15, "Advanced"),
        (18, 18, "Expert"),
        (20, 20, "Maximum"),
    ]
    
    print("Testing engine response times...")
    print()
    
    for skill, depth, label in test_configs:
        print(f"🎯 {label} (Skill: {skill}, Depth: {depth})")
        expected_timeout = get_timeout_for_level(skill, depth)
        print(f"   Expected timeout: {expected_timeout}ms ({expected_timeout/1000:.1f}s)")
        
        try:
            engine = ChessEngine(skill_level=skill, depth=depth, use_opening_book=False)
            
            total_time = 0
            successful_moves = 0
            
            for fen, pos_name in test_positions:
                engine.set_position(fen)
                
                start_time = time.time()
                move = engine.get_best_move()
                end_time = time.time()
                
                actual_time = (end_time - start_time) * 1000  # Convert to ms
                
                if move:
                    total_time += actual_time
                    successful_moves += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"   {status} {pos_name}: {actual_time:.0f}ms")
            
            if successful_moves > 0:
                avg_time = total_time / successful_moves
                print(f"   📊 Average: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
                
                # Compare with expected
                efficiency = (expected_timeout / avg_time) * 100 if avg_time > 0 else 0
                if avg_time <= expected_timeout:
                    print(f"   ✅ Within timeout limit ({efficiency:.0f}% efficient)")
                else:
                    print(f"   ⚠️ Exceeds timeout limit ({efficiency:.0f}% efficient)")
            else:
                print(f"   ❌ No successful moves")
            
            engine.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error testing {label}: {e}")
        
        print()

def analyze_fallback_system():
    """Analyze the fallback timeout system"""
    print("🔄 Fallback Timeout System Analysis")
    print("=" * 40)
    
    print("When primary timeout fails, the engine uses these fallbacks:")
    print()
    
    fallback_attempts = [
        (8, 3000),   # Depth 8, 3 seconds
        (6, 2000),   # Depth 6, 2 seconds  
        (4, 1000),   # Depth 4, 1 second
        (2, 500),    # Depth 2, 0.5 seconds
    ]
    
    print("📋 Fallback Sequence:")
    for i, (depth, timeout) in enumerate(fallback_attempts, 1):
        print(f"   {i}. Depth {depth}: {timeout}ms ({timeout/1000:.1f}s)")
    
    print()
    print("🎯 Fallback Strategy:")
    print("   • Progressively reduces depth for faster calculation")
    print("   • Ensures a move is always returned")
    print("   • Prevents infinite thinking time")
    print("   • Maintains game flow even under stress")
    print()
    
    # Calculate total maximum time
    total_max_time = sum(timeout for _, timeout in fallback_attempts)
    print(f"📊 Maximum total time (all fallbacks): {total_max_time}ms ({total_max_time/1000:.1f}s)")
    print()

def show_timeout_recommendations():
    """Show timeout recommendations for different use cases"""
    print("💡 Timeout Recommendations")
    print("=" * 30)
    
    recommendations = [
        ("Casual Play", "Skill 1-10, Depth 8-12", "1-2 seconds", "Fast, responsive gameplay"),
        ("Competitive Play", "Skill 15-18, Depth 15-18", "3-4 seconds", "Strong play with reasonable speed"),
        ("Analysis Mode", "Skill 20, Depth 20", "5+ seconds", "Maximum strength for analysis"),
        ("Blitz Games", "Any skill, Depth 6-10", "0.5-1 second", "Very fast for time pressure"),
        ("Tournament", "Skill 18-20, Depth 18-20", "3-5 seconds", "Strong play for serious games"),
    ]
    
    for use_case, config, timeout, description in recommendations:
        print(f"🎯 {use_case}")
        print(f"   Config: {config}")
        print(f"   Timeout: {timeout}")
        print(f"   Purpose: {description}")
        print()

def main():
    """Main analysis function"""
    try:
        analyze_timeout_matrix()
        print()
        
        test_actual_timeouts()
        print()
        
        analyze_fallback_system()
        print()
        
        show_timeout_recommendations()
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()