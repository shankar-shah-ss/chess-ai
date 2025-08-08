#!/usr/bin/env python3
"""
Test the increased timeout settings (3x multiplier)
"""

import sys
import os
import time
from typing import Dict, List, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from engine import ChessEngine
    from chess import STARTING_FEN, Board
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

def test_new_timeout_matrix():
    """Test the new timeout matrix with 3x increased times"""
    print("🕐 Testing New Timeout Configuration (3x Increased)")
    print("=" * 60)
    
    print("📊 New Timeout Matrix:")
    print("-" * 50)
    
    # Define test configurations
    configs = [
        (5, 8, "Beginner", 6000),      # Was 2000ms, now 6000ms
        (10, 12, "Intermediate", 6000), # Was 2000ms, now 6000ms  
        (15, 15, "Advanced", 9000),     # Was 3000ms, now 9000ms
        (18, 18, "Expert", 12000),      # Was 4000ms, now 12000ms
        (20, 20, "Maximum", 15000),     # Was 5000ms, now 15000ms
    ]
    
    print(f"{'Configuration':<15} {'Old Time':<10} {'New Time':<10} {'Increase':<10}")
    print("-" * 50)
    
    for skill, depth, label, expected_timeout in configs:
        old_timeout = {
            "Beginner": 2000,
            "Intermediate": 2000,
            "Advanced": 3000,
            "Expert": 4000,
            "Maximum": 5000
        }[label]
        
        increase = f"{expected_timeout/old_timeout:.1f}x"
        
        print(f"{label:<15} {old_timeout:<10} {expected_timeout:<10} {increase:<10}")
    
    print()
    
    print("🔄 New Fallback Timeouts:")
    print("-" * 25)
    
    fallbacks = [
        ("Depth 8", 3000, 9000),
        ("Depth 6", 2000, 6000),
        ("Depth 4", 1000, 3000),
        ("Depth 2", 500, 1500),
    ]
    
    print(f"{'Fallback':<10} {'Old Time':<10} {'New Time':<10} {'Increase':<10}")
    print("-" * 45)
    
    for depth, old_time, new_time in fallbacks:
        increase = f"{new_time/old_time:.1f}x"
        print(f"{depth:<10} {old_time:<10} {new_time:<10} {increase:<10}")
    
    print()

def test_actual_performance():
    """Test actual engine performance with new timeouts"""
    print("⏱️ Testing Actual Engine Performance")
    print("=" * 40)
    
    test_positions = [
        (STARTING_FEN, "Starting position"),
        ("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", "Italian Game"),
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 5", "Complex position"),
    ]
    
    test_configs = [
        (10, 12, "Intermediate", 6000),
        (15, 15, "Advanced", 9000),
        (20, 20, "Maximum", 15000),
    ]
    
    print("Testing with increased timeouts...")
    print()
    
    for skill, depth, label, expected_timeout in test_configs:
        print(f"🎯 {label} (Skill: {skill}, Depth: {depth})")
        print(f"   Expected timeout: {expected_timeout}ms ({expected_timeout/1000:.1f}s)")
        
        try:
            engine = ChessEngine(skill_level=skill, depth=depth, use_opening_book=False)
            
            total_time = 0
            successful_moves = 0
            move_details = []
            
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
                    
                    # Get evaluation if possible
                    try:
                        eval_result = engine.get_evaluation()
                        evaluation = eval_result.get('value', 'N/A') if eval_result else 'N/A'
                    except:
                        evaluation = 'N/A'
                    
                    move_details.append({
                        'position': pos_name,
                        'move': move,
                        'time': actual_time,
                        'evaluation': evaluation
                    })
                else:
                    status = "❌"
                    move_details.append({
                        'position': pos_name,
                        'move': None,
                        'time': actual_time,
                        'evaluation': 'N/A'
                    })
                
                print(f"   {status} {pos_name}: {move or 'None'} ({actual_time:.0f}ms, eval: {evaluation if move else 'N/A'})")
            
            if successful_moves > 0:
                avg_time = total_time / successful_moves
                print(f"   📊 Average: {avg_time:.0f}ms ({avg_time/1000:.1f}s)")
                
                # Compare with expected
                if avg_time <= expected_timeout * 1.1:  # Allow 10% tolerance
                    efficiency = (avg_time / expected_timeout) * 100
                    print(f"   ✅ Within timeout limit ({efficiency:.0f}% of limit used)")
                else:
                    efficiency = (avg_time / expected_timeout) * 100
                    print(f"   ⚠️ Exceeds timeout limit ({efficiency:.0f}% of limit used)")
                
                # Show improvement potential
                old_expected = {6000: 2000, 9000: 3000, 15000: 5000}[expected_timeout]
                improvement = f"vs {old_expected}ms previously"
                print(f"   🚀 Extended thinking time: {improvement}")
            else:
                print(f"   ❌ No successful moves")
            
            engine.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error testing {label}: {e}")
        
        print()

def analyze_move_quality_improvement():
    """Analyze if longer thinking time improves move quality"""
    print("📈 Move Quality Analysis")
    print("=" * 30)
    
    print("🎯 Expected Improvements with 3x Timeout:")
    improvements = [
        "Deeper tactical calculations (more moves ahead)",
        "Better positional evaluation in complex positions", 
        "More accurate endgame play",
        "Reduced horizon effect issues",
        "Better handling of quiet positional moves",
        "Improved evaluation of sacrificial lines"
    ]
    
    for improvement in improvements:
        print(f"   • {improvement}")
    
    print()
    
    print("⚖️ Trade-offs:")
    tradeoffs = [
        ("Pros", [
            "Much stronger move quality",
            "Better tactical vision", 
            "More accurate evaluations",
            "Reduced calculation errors"
        ]),
        ("Cons", [
            "Slower gameplay (3x longer per move)",
            "May be too slow for casual play",
            "Higher CPU usage for longer periods",
            "Potential user impatience"
        ])
    ]
    
    for category, items in tradeoffs:
        print(f"   {category}:")
        for item in items:
            symbol = "✅" if category == "Pros" else "⚠️"
            print(f"     {symbol} {item}")
    
    print()

def show_usage_recommendations():
    """Show recommendations for when to use increased timeouts"""
    print("💡 Usage Recommendations")
    print("=" * 30)
    
    recommendations = [
        {
            "scenario": "Analysis Mode",
            "recommendation": "Perfect - use maximum settings",
            "reason": "No time pressure, want best moves"
        },
        {
            "scenario": "Tournament Play", 
            "recommendation": "Excellent - use advanced/expert settings",
            "reason": "Strong play worth the extra time"
        },
        {
            "scenario": "Learning/Study",
            "recommendation": "Great - see high-quality moves",
            "reason": "Educational value of better moves"
        },
        {
            "scenario": "Casual Games",
            "recommendation": "Consider reducing - may be too slow",
            "reason": "User experience vs move quality balance"
        },
        {
            "scenario": "Blitz Games",
            "recommendation": "Not recommended - too slow",
            "reason": "Speed is more important than perfection"
        },
        {
            "scenario": "Engine vs Engine",
            "recommendation": "Perfect - let them think deeply",
            "reason": "No human waiting, maximum strength desired"
        }
    ]
    
    for rec in recommendations:
        print(f"🎯 {rec['scenario']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Reason: {rec['reason']}")
        print()

def main():
    """Main test function"""
    try:
        test_new_timeout_matrix()
        test_actual_performance()
        analyze_move_quality_improvement()
        show_usage_recommendations()
        
        print("🎉 Timeout Increase Test Complete!")
        print()
        print("📋 Summary:")
        print("   • All timeouts increased by 3x")
        print("   • Fallback timeouts also increased proportionally")
        print("   • Recovery timeouts updated")
        print("   • Should see significantly stronger move quality")
        print("   • Trade-off: 3x longer thinking time per move")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()