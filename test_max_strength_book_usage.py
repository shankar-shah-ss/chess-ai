#!/usr/bin/env python3
"""
Test opening book usage specifically at maximum engine settings (Skill 20, Depth 20)
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

class MaxStrengthBookTester:
    def __init__(self):
        self.results = {}
        
    def test_maximum_strength_book_usage(self, opening_name: str, max_moves: int = 25):
        """Test book usage at maximum engine strength"""
        print(f"🎯 Testing {opening_name} at MAXIMUM STRENGTH")
        print(f"   Configuration: Skill 20, Depth 20, 15-second timeouts")
        print("-" * 60)
        
        try:
            # Create maximum strength engine
            engine = ChessEngine(skill_level=20, depth=20, use_opening_book=True)
            board = Board()
            
            move_data = []
            book_moves_played = 0
            engine_moves_played = 0
            total_book_time = 0
            total_engine_time = 0
            
            print(f"{'Move':<6} {'Player':<6} {'Move':<12} {'Source':<10} {'Time':<8} {'Evaluation':<12}")
            print("-" * 70)
            
            for move_num in range(1, max_moves + 1):
                if board.is_game_over():
                    break
                
                # Reset and set position
                engine.reset_move_count()
                engine.move_count = move_num - 1
                engine.set_position(board.fen())
                
                # Time the move generation
                start_time = time.time()
                move_uci = engine.get_best_move()
                end_time = time.time()
                
                move_time_ms = (end_time - start_time) * 1000
                
                if not move_uci:
                    print(f"   {move_num:<6} No move returned!")
                    break
                
                # Check if this was a book move by examining the logs or engine state
                is_book_move = False
                book_move_detected = False
                
                # Try to detect book move by checking if engine would return same move from book
                if engine.use_opening_book and engine.opening_book:
                    try:
                        # Get what the book would suggest
                        book_suggestion = engine.opening_book.get_book_move(board.fen(), move_num)
                        if book_suggestion == move_uci:
                            # Additional check: book moves should be very fast (< 100ms)
                            if move_time_ms < 100:
                                is_book_move = True
                                book_move_detected = True
                    except:
                        pass
                
                # Parse and make the move
                try:
                    move = board.parse_uci(move_uci)
                    move_san = board.san(move)
                    board.push(move)
                except Exception as e:
                    print(f"   {move_num:<6} Invalid move {move_uci}: {e}")
                    break
                
                # Get evaluation for engine moves
                evaluation = "N/A"
                if not is_book_move:
                    try:
                        eval_result = engine.get_evaluation()
                        if eval_result and 'value' in eval_result:
                            evaluation = str(eval_result['value'])
                    except:
                        evaluation = "N/A"
                
                # Track statistics
                if is_book_move:
                    book_moves_played += 1
                    total_book_time += move_time_ms
                    source = "📖 Book"
                    source_color = "📖"
                else:
                    engine_moves_played += 1
                    total_engine_time += move_time_ms
                    source = "🤖 Engine"
                    source_color = "🤖"
                
                # Store move data
                move_data.append({
                    'move_number': move_num,
                    'move_uci': move_uci,
                    'move_san': move_san,
                    'time_ms': move_time_ms,
                    'is_book_move': is_book_move,
                    'source': source,
                    'evaluation': evaluation,
                    'fen_before': engine.get_current_fen() if hasattr(engine, 'get_current_fen') else board.fen()
                })
                
                # Display move
                player = "White" if move_num % 2 == 1 else "Black"
                move_display = f"{(move_num + 1) // 2}.{'.' if move_num % 2 == 1 else '..'} {move_san}"
                time_display = f"{move_time_ms:.0f}ms"
                eval_display = f"(eval: {evaluation})" if evaluation != "N/A" else ""
                
                print(f"   {move_num:<6} {player:<6} {move_display:<12} {source:<10} {time_display:<8} {eval_display:<12}")
                
                # Early termination if no book moves for several moves
                if move_num > 10 and book_moves_played == 0:
                    print(f"   No book moves detected in first 10 moves, stopping early...")
                    break
            
            # Calculate final statistics
            total_moves = len(move_data)
            book_percentage = (book_moves_played / total_moves * 100) if total_moves > 0 else 0
            avg_book_time = total_book_time / book_moves_played if book_moves_played > 0 else 0
            avg_engine_time = total_engine_time / engine_moves_played if engine_moves_played > 0 else 0
            
            # Find last book move
            last_book_move = 0
            for move in move_data:
                if move['is_book_move']:
                    last_book_move = move['move_number']
            
            results = {
                'opening_name': opening_name,
                'engine_config': 'Skill 20, Depth 20',
                'total_moves': total_moves,
                'book_moves': book_moves_played,
                'engine_moves': engine_moves_played,
                'book_percentage': book_percentage,
                'last_book_move': last_book_move,
                'avg_book_time_ms': avg_book_time,
                'avg_engine_time_ms': avg_engine_time,
                'total_book_time_ms': total_book_time,
                'total_engine_time_ms': total_engine_time,
                'move_data': move_data
            }
            
            # Display summary
            print()
            print(f"📊 {opening_name} - Maximum Strength Summary:")
            print(f"   Engine Configuration: Skill 20, Depth 20")
            print(f"   Total moves analyzed: {total_moves}")
            print(f"   Book moves played: {book_moves_played} ({book_percentage:.1f}%)")
            print(f"   Engine moves played: {engine_moves_played} ({100-book_percentage:.1f}%)")
            if last_book_move > 0:
                print(f"   Last book move: Move {last_book_move}")
                print(f"   Book depth: {last_book_move} half-moves")
            else:
                print(f"   No book moves detected")
            
            if book_moves_played > 0:
                print(f"   Average book move time: {avg_book_time:.1f}ms")
            if engine_moves_played > 0:
                print(f"   Average engine move time: {avg_engine_time:.1f}ms ({avg_engine_time/1000:.1f}s)")
            
            if book_moves_played > 0 and engine_moves_played > 0:
                speed_ratio = avg_engine_time / avg_book_time
                print(f"   Speed advantage: Book moves {speed_ratio:.0f}x faster")
            
            engine.cleanup()
            return results
            
        except Exception as e:
            print(f"❌ Error testing {opening_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def compare_with_lower_strength(self):
        """Compare book usage between maximum and lower strength settings"""
        print("🔍 Comparing Book Usage: Maximum vs Lower Strength")
        print("=" * 60)
        
        test_position = STARTING_FEN
        max_moves = 15
        
        configurations = [
            (10, 12, "Intermediate"),
            (15, 15, "Advanced"), 
            (20, 20, "Maximum")
        ]
        
        results = []
        
        for skill, depth, label in configurations:
            print(f"\n🎯 Testing {label} Configuration (Skill {skill}, Depth {depth})")
            print("-" * 50)
            
            try:
                engine = ChessEngine(skill_level=skill, depth=depth, use_opening_book=True)
                board = Board()
                
                book_moves = 0
                total_moves = 0
                move_times = []
                
                for move_num in range(1, max_moves + 1):
                    if board.is_game_over():
                        break
                    
                    engine.reset_move_count()
                    engine.move_count = move_num - 1
                    engine.set_position(board.fen())
                    
                    start_time = time.time()
                    move_uci = engine.get_best_move()
                    end_time = time.time()
                    
                    move_time_ms = (end_time - start_time) * 1000
                    
                    if not move_uci:
                        break
                    
                    # Detect book move (fast moves < 100ms are likely book moves)
                    is_book_move = move_time_ms < 100
                    
                    if is_book_move:
                        book_moves += 1
                    
                    total_moves += 1
                    move_times.append(move_time_ms)
                    
                    # Make the move
                    try:
                        move = board.parse_uci(move_uci)
                        move_san = board.san(move)
                        board.push(move)
                        
                        source = "📖" if is_book_move else "🤖"
                        print(f"   Move {move_num}: {move_san} {source} ({move_time_ms:.0f}ms)")
                        
                    except:
                        break
                
                book_percentage = (book_moves / total_moves * 100) if total_moves > 0 else 0
                avg_time = sum(move_times) / len(move_times) if move_times else 0
                
                result = {
                    'config': label,
                    'skill': skill,
                    'depth': depth,
                    'book_moves': book_moves,
                    'total_moves': total_moves,
                    'book_percentage': book_percentage,
                    'avg_time': avg_time
                }
                
                results.append(result)
                
                print(f"   📊 {label}: {book_moves}/{total_moves} book moves ({book_percentage:.1f}%)")
                
                engine.cleanup()
                
            except Exception as e:
                print(f"   ❌ Error testing {label}: {e}")
        
        # Compare results
        print(f"\n📊 Book Usage Comparison:")
        print(f"{'Configuration':<15} {'Book Moves':<12} {'Total Moves':<12} {'Book %':<10} {'Avg Time':<10}")
        print("-" * 65)
        
        for result in results:
            print(f"{result['config']:<15} {result['book_moves']:<12} {result['total_moves']:<12} {result['book_percentage']:<9.1f}% {result['avg_time']:<9.0f}ms")
        
        return results

    def analyze_book_vs_engine_preference(self):
        """Analyze if maximum strength engine prefers book moves or its own calculation"""
        print("\n🤔 Book vs Engine Preference Analysis")
        print("=" * 45)
        
        print("Testing if maximum strength engine (Skill 20, Depth 20) prefers:")
        print("   📖 Fast book moves from theory")
        print("   🤖 Deep engine calculation (15-second analysis)")
        print()
        
        # Test specific positions where book and engine might differ
        test_positions = [
            {
                'name': 'Opening Position',
                'fen': STARTING_FEN,
                'expected_book': 'e2e4 or d2d4',
                'move_number': 1
            },
            {
                'name': 'After 1.e4',
                'fen': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
                'expected_book': 'e7e5 or c7c5',
                'move_number': 2
            },
            {
                'name': 'Italian Game Setup',
                'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3',
                'expected_book': 'f8c5 or f7f5',
                'move_number': 6
            }
        ]
        
        try:
            engine = ChessEngine(skill_level=20, depth=20, use_opening_book=True)
            
            for pos in test_positions:
                print(f"🎯 Testing: {pos['name']}")
                print(f"   FEN: {pos['fen']}")
                print(f"   Expected book moves: {pos['expected_book']}")
                
                engine.set_position(pos['fen'])
                engine.move_count = pos['move_number'] - 1
                
                # Time the move selection
                start_time = time.time()
                chosen_move = engine.get_best_move()
                end_time = time.time()
                
                move_time_ms = (end_time - start_time) * 1000
                
                # Determine if it was a book move
                is_book_move = move_time_ms < 100
                source = "📖 Book" if is_book_move else "🤖 Engine"
                
                print(f"   Chosen move: {chosen_move}")
                print(f"   Source: {source}")
                print(f"   Time taken: {move_time_ms:.0f}ms ({move_time_ms/1000:.1f}s)")
                
                if is_book_move:
                    print(f"   ✅ Used book move (fast response)")
                else:
                    print(f"   🤖 Used engine calculation (deep analysis)")
                
                print()
            
            engine.cleanup()
            
        except Exception as e:
            print(f"❌ Error in preference analysis: {e}")

def main():
    """Main test function"""
    try:
        tester = MaxStrengthBookTester()
        
        print("🚀 Maximum Strength Opening Book Usage Analysis")
        print("Testing Skill 20, Depth 20 with 15-second timeouts")
        print("=" * 65)
        print()
        
        # Test different openings at maximum strength
        openings = [
            "Italian Game (Max Strength)",
            "Queen's Gambit (Max Strength)", 
            "Sicilian Defense (Max Strength)"
        ]
        
        results = []
        for opening in openings:
            result = tester.test_maximum_strength_book_usage(opening, max_moves=20)
            if result:
                results.append(result)
            print()
        
        # Compare with lower strengths
        comparison_results = tester.compare_with_lower_strength()
        
        # Analyze preferences
        tester.analyze_book_vs_engine_preference()
        
        # Final summary
        print("🎉 Maximum Strength Book Usage Analysis Complete!")
        print()
        
        if results:
            total_book_moves = sum(r['book_moves'] for r in results)
            total_moves = sum(r['total_moves'] for r in results)
            overall_percentage = (total_book_moves / total_moves * 100) if total_moves > 0 else 0
            
            print("📋 Final Summary:")
            print(f"   • Configuration: Skill 20, Depth 20")
            print(f"   • Total moves analyzed: {total_moves}")
            print(f"   • Book moves at max strength: {total_book_moves} ({overall_percentage:.1f}%)")
            print(f"   • Engine moves at max strength: {total_moves - total_book_moves} ({100-overall_percentage:.1f}%)")
            
            if total_book_moves > 0:
                avg_book_time = sum(r['total_book_time_ms'] for r in results) / total_book_moves
                print(f"   • Average book move time: {avg_book_time:.1f}ms")
            
            if total_moves > total_book_moves:
                total_engine_time = sum(r['total_engine_time_ms'] for r in results)
                avg_engine_time = total_engine_time / (total_moves - total_book_moves)
                print(f"   • Average engine move time: {avg_engine_time:.1f}ms ({avg_engine_time/1000:.1f}s)")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()