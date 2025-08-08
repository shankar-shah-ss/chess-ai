#!/usr/bin/env python3
"""
Test opening book performance - timing and move analysis across different openings
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
    import chess
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

class OpeningBookTester:
    def __init__(self):
        self.results = {}
        
    def simulate_opening_sequence(self, opening_name: str, opening_moves: List[str], max_moves: int = 20):
        """Simulate a complete opening sequence and measure book performance"""
        print(f"🎯 Testing {opening_name}")
        print(f"   Expected moves: {' '.join(opening_moves[:6])}...")
        print("-" * 50)
        
        # Create engine with opening book enabled
        try:
            engine = ChessEngine(skill_level=15, depth=15, use_opening_book=True)
            board = Board()
            
            move_data = []
            book_moves_played = 0
            total_book_time = 0
            total_engine_time = 0
            
            for move_num in range(1, max_moves + 1):
                if board.is_game_over():
                    break
                
                # Reset move count for engine tracking
                engine.reset_move_count()
                engine.move_count = move_num - 1
                
                # Set current position
                engine.set_position(board.fen())
                
                # Time the move generation
                start_time = time.time()
                move_uci = engine.get_best_move()
                end_time = time.time()
                
                move_time_ms = (end_time - start_time) * 1000
                
                if not move_uci:
                    print(f"   Move {move_num}: No move returned!")
                    break
                
                # Check if this was a book move
                is_book_move = False
                if engine.use_opening_book and engine.opening_book:
                    try:
                        # Check if book would return this move
                        book_move = engine.opening_book.get_book_move(board.fen(), move_num)
                        is_book_move = (book_move == move_uci)
                    except:
                        is_book_move = False
                
                # Parse and make the move
                try:
                    move = board.parse_uci(move_uci)
                    move_san = board.san(move)
                    board.push(move)
                except:
                    print(f"   Move {move_num}: Invalid move {move_uci}")
                    break
                
                # Track statistics
                if is_book_move:
                    book_moves_played += 1
                    total_book_time += move_time_ms
                    source = "📖 Book"
                else:
                    total_engine_time += move_time_ms
                    source = "🤖 Engine"
                
                # Get evaluation for engine moves
                evaluation = "N/A"
                if not is_book_move:
                    try:
                        eval_result = engine.get_evaluation()
                        if eval_result and 'value' in eval_result:
                            evaluation = eval_result['value']
                    except:
                        pass
                
                move_data.append({
                    'move_number': move_num,
                    'move_uci': move_uci,
                    'move_san': move_san,
                    'time_ms': move_time_ms,
                    'is_book_move': is_book_move,
                    'source': source,
                    'evaluation': evaluation,
                    'fen': board.fen()
                })
                
                # Display move info
                color = "White" if move_num % 2 == 1 else "Black"
                move_display = f"{(move_num + 1) // 2}.{'.' if move_num % 2 == 1 else '..'} {move_san}"
                
                print(f"   {color:<5} {move_display:<12} {source:<10} {move_time_ms:>6.0f}ms {f'(eval: {evaluation})' if evaluation != 'N/A' else ''}")
            
            # Calculate statistics
            total_moves = len(move_data)
            avg_book_time = total_book_time / book_moves_played if book_moves_played > 0 else 0
            avg_engine_time = total_engine_time / (total_moves - book_moves_played) if (total_moves - book_moves_played) > 0 else 0
            book_percentage = (book_moves_played / total_moves * 100) if total_moves > 0 else 0
            
            results = {
                'opening_name': opening_name,
                'total_moves': total_moves,
                'book_moves': book_moves_played,
                'engine_moves': total_moves - book_moves_played,
                'book_percentage': book_percentage,
                'avg_book_time_ms': avg_book_time,
                'avg_engine_time_ms': avg_engine_time,
                'total_book_time_ms': total_book_time,
                'total_engine_time_ms': total_engine_time,
                'move_data': move_data
            }
            
            # Display summary
            print()
            print(f"📊 {opening_name} Summary:")
            print(f"   Total moves played: {total_moves}")
            print(f"   Book moves: {book_moves_played} ({book_percentage:.1f}%)")
            print(f"   Engine moves: {total_moves - book_moves_played} ({100-book_percentage:.1f}%)")
            print(f"   Average book move time: {avg_book_time:.1f}ms")
            print(f"   Average engine move time: {avg_engine_time:.1f}ms")
            print(f"   Speed difference: {avg_engine_time/avg_book_time:.1f}x faster for book moves" if avg_book_time > 0 else "")
            print()
            
            engine.cleanup()
            return results
            
        except Exception as e:
            print(f"❌ Error testing {opening_name}: {e}")
            return None

    def test_multiple_openings(self):
        """Test multiple different openings"""
        print("🎯 Opening Book Performance Analysis")
        print("=" * 60)
        print()
        
        # Define test openings with expected move sequences
        openings = [
            {
                'name': 'Italian Game',
                'moves': ['e2e4', 'e7e5', 'g1f3', 'b8c6', 'f1c4', 'f8c5', 'd2d3', 'g8f6', 'c1g5', 'd7d6'],
                'description': 'Classical opening with rich theory'
            },
            {
                'name': 'Queen\'s Gambit',
                'moves': ['d2d4', 'd7d5', 'c2c4', 'e7e6', 'b1c3', 'g8f6', 'c1g5', 'f8e7', 'e2e3', 'e8g8'],
                'description': 'Strategic opening with deep theory'
            },
            {
                'name': 'Sicilian Defense',
                'moves': ['e2e4', 'c7c5', 'g1f3', 'd7d6', 'd2d4', 'c5d4', 'f3d4', 'g8f6', 'b1c3', 'a7a6'],
                'description': 'Sharp tactical opening'
            }
        ]
        
        all_results = []
        
        for opening in openings:
            print(f"🔍 {opening['description']}")
            result = self.simulate_opening_sequence(
                opening['name'], 
                opening['moves'], 
                max_moves=20
            )
            if result:
                all_results.append(result)
            print()
        
        return all_results

    def analyze_book_performance(self, results: List[Dict]):
        """Analyze overall book performance across all openings"""
        print("📈 Overall Opening Book Performance Analysis")
        print("=" * 50)
        
        if not results:
            print("❌ No results to analyze")
            return
        
        # Aggregate statistics
        total_moves = sum(r['total_moves'] for r in results)
        total_book_moves = sum(r['book_moves'] for r in results)
        total_engine_moves = sum(r['engine_moves'] for r in results)
        
        total_book_time = sum(r['total_book_time_ms'] for r in results)
        total_engine_time = sum(r['total_engine_time_ms'] for r in results)
        
        avg_book_time = total_book_time / total_book_moves if total_book_moves > 0 else 0
        avg_engine_time = total_engine_time / total_engine_moves if total_engine_moves > 0 else 0
        
        overall_book_percentage = (total_book_moves / total_moves * 100) if total_moves > 0 else 0
        
        print("📊 Aggregate Statistics:")
        print(f"   Total moves across all games: {total_moves}")
        print(f"   Total book moves: {total_book_moves} ({overall_book_percentage:.1f}%)")
        print(f"   Total engine moves: {total_engine_moves} ({100-overall_book_percentage:.1f}%)")
        print()
        
        print("⏱️ Timing Analysis:")
        print(f"   Average book move time: {avg_book_time:.1f}ms ({avg_book_time/1000:.3f}s)")
        print(f"   Average engine move time: {avg_engine_time:.1f}ms ({avg_engine_time/1000:.3f}s)")
        print(f"   Speed advantage: Book moves are {avg_engine_time/avg_book_time:.1f}x faster" if avg_book_time > 0 else "")
        print()
        
        print("🎯 Per-Opening Breakdown:")
        print(f"{'Opening':<20} {'Book Moves':<12} {'Book %':<8} {'Avg Book Time':<15} {'Avg Engine Time':<15}")
        print("-" * 80)
        
        for result in results:
            book_pct = f"{result['book_percentage']:.1f}%"
            book_time = f"{result['avg_book_time_ms']:.1f}ms"
            engine_time = f"{result['avg_engine_time_ms']:.1f}ms"
            
            print(f"{result['opening_name']:<20} {result['book_moves']:<12} {book_pct:<8} {book_time:<15} {engine_time:<15}")
        
        print()
        
        # Analyze book depth patterns
        print("📚 Book Depth Analysis:")
        for result in results:
            print(f"   {result['opening_name']}:")
            
            # Find the last book move
            last_book_move = 0
            for move_data in result['move_data']:
                if move_data['is_book_move']:
                    last_book_move = move_data['move_number']
            
            print(f"     • Book coverage: {result['book_moves']} moves (up to move {last_book_move})")
            print(f"     • Book depth: {last_book_move} half-moves")
            
            # Show transition point
            if last_book_move > 0 and last_book_move < len(result['move_data']):
                transition_move = result['move_data'][last_book_move]  # First engine move
                print(f"     • Transition to engine: Move {transition_move['move_number']} ({transition_move['move_san']})")
        
        print()

    def analyze_timing_patterns(self, results: List[Dict]):
        """Analyze detailed timing patterns"""
        print("⏱️ Detailed Timing Pattern Analysis")
        print("=" * 40)
        
        # Collect all book and engine times
        all_book_times = []
        all_engine_times = []
        
        for result in results:
            for move_data in result['move_data']:
                if move_data['is_book_move']:
                    all_book_times.append(move_data['time_ms'])
                else:
                    all_engine_times.append(move_data['time_ms'])
        
        if all_book_times:
            print("📖 Book Move Timing:")
            print(f"   Count: {len(all_book_times)} moves")
            print(f"   Average: {sum(all_book_times)/len(all_book_times):.1f}ms")
            print(f"   Minimum: {min(all_book_times):.1f}ms")
            print(f"   Maximum: {max(all_book_times):.1f}ms")
            print(f"   Median: {sorted(all_book_times)[len(all_book_times)//2]:.1f}ms")
        
        print()
        
        if all_engine_times:
            print("🤖 Engine Move Timing:")
            print(f"   Count: {len(all_engine_times)} moves")
            print(f"   Average: {sum(all_engine_times)/len(all_engine_times):.1f}ms")
            print(f"   Minimum: {min(all_engine_times):.1f}ms")
            print(f"   Maximum: {max(all_engine_times):.1f}ms")
            print(f"   Median: {sorted(all_engine_times)[len(all_engine_times)//2]:.1f}ms")
        
        print()
        
        # Timing distribution analysis
        if all_book_times and all_engine_times:
            print("📊 Timing Distribution:")
            
            # Book move distribution
            book_ranges = [
                (0, 50, "Ultra-fast"),
                (50, 100, "Very fast"),
                (100, 200, "Fast"),
                (200, 500, "Medium"),
                (500, float('inf'), "Slow")
            ]
            
            print("   Book moves:")
            for min_time, max_time, label in book_ranges:
                count = sum(1 for t in all_book_times if min_time <= t < max_time)
                percentage = (count / len(all_book_times)) * 100
                print(f"     {label:<12}: {count:>3} moves ({percentage:>5.1f}%)")
            
            print()
            
            # Engine move distribution  
            engine_ranges = [
                (0, 1000, "Fast"),
                (1000, 5000, "Medium"),
                (5000, 10000, "Slow"),
                (10000, float('inf'), "Very slow")
            ]
            
            print("   Engine moves:")
            for min_time, max_time, label in engine_ranges:
                count = sum(1 for t in all_engine_times if min_time <= t < max_time)
                percentage = (count / len(all_engine_times)) * 100
                print(f"     {label:<12}: {count:>3} moves ({percentage:>5.1f}%)")

    def generate_performance_report(self, results: List[Dict]):
        """Generate a comprehensive performance report"""
        print("📋 Opening Book Performance Report")
        print("=" * 40)
        
        if not results:
            print("❌ No data to report")
            return
        
        # Key findings
        total_book_moves = sum(r['book_moves'] for r in results)
        total_moves = sum(r['total_moves'] for r in results)
        
        if total_book_moves > 0:
            total_book_time = sum(r['total_book_time_ms'] for r in results)
            total_engine_time = sum(r['total_engine_time_ms'] for r in results)
            total_engine_moves = sum(r['engine_moves'] for r in results)
            
            avg_book_time = total_book_time / total_book_moves
            avg_engine_time = total_engine_time / total_engine_moves if total_engine_moves > 0 else 0
            
            print("🎯 Key Findings:")
            print(f"   • Opening book is active and working")
            print(f"   • Book moves are {avg_engine_time/avg_book_time:.1f}x faster than engine moves")
            print(f"   • Book coverage: {total_book_moves}/{total_moves} moves ({total_book_moves/total_moves*100:.1f}%)")
            print(f"   • Average book move time: {avg_book_time:.1f}ms")
            print(f"   • Average engine move time: {avg_engine_time:.1f}ms")
            print()
            
            print("✅ Performance Assessment:")
            if avg_book_time < 100:
                print("   • Book moves are VERY FAST (< 100ms)")
            elif avg_book_time < 200:
                print("   • Book moves are FAST (< 200ms)")
            else:
                print("   • Book moves are MODERATE (> 200ms)")
            
            if avg_engine_time > avg_book_time * 10:
                print("   • Significant speed advantage for book moves")
            elif avg_engine_time > avg_book_time * 5:
                print("   • Good speed advantage for book moves")
            else:
                print("   • Moderate speed advantage for book moves")
            
            # Book depth assessment
            max_book_depth = 0
            for result in results:
                for move_data in result['move_data']:
                    if move_data['is_book_move']:
                        max_book_depth = max(max_book_depth, move_data['move_number'])
            
            print(f"   • Maximum book depth: {max_book_depth} half-moves")
            
            if max_book_depth >= 15:
                print("   • EXCELLENT book depth coverage")
            elif max_book_depth >= 10:
                print("   • GOOD book depth coverage")
            elif max_book_depth >= 5:
                print("   • MODERATE book depth coverage")
            else:
                print("   • LIMITED book depth coverage")
        else:
            print("❌ No book moves detected - opening book may not be working")
        
        print()

def main():
    """Main test function"""
    try:
        tester = OpeningBookTester()
        
        print("🚀 Starting Opening Book Performance Test")
        print("Testing 3 different openings with timing analysis...")
        print()
        
        # Run the tests
        results = tester.test_multiple_openings()
        
        if results:
            print()
            tester.analyze_book_performance(results)
            tester.analyze_timing_patterns(results)
            tester.generate_performance_report(results)
        else:
            print("❌ No results obtained from testing")
        
        print("🎉 Opening Book Performance Test Complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()