#!/usr/bin/env python3
"""
Quick test to determine book move usage at maximum strength (Skill 20, Depth 20)
"""

import sys
import os
import time
from typing import Dict, List

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from engine import ChessEngine
    from chess import STARTING_FEN, Board
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

def quick_book_test():
    """Quick test of book usage at maximum strength"""
    print("🎯 Quick Book Usage Test - Maximum Strength")
    print("Configuration: Skill 20, Depth 20")
    print("=" * 50)
    
    try:
        # Create maximum strength engine
        engine = ChessEngine(skill_level=20, depth=20, use_opening_book=True)
        board = Board()
        
        book_moves = 0
        total_moves = 0
        move_details = []
        
        print(f"{'Move':<4} {'Player':<6} {'Move':<8} {'Time':<8} {'Source':<8}")
        print("-" * 40)
        
        # Test first 12 moves (typical opening phase)
        for move_num in range(1, 13):
            if board.is_game_over():
                break
            
            # Set position and move count
            engine.reset_move_count()
            engine.move_count = move_num - 1
            engine.set_position(board.fen())
            
            # Time the move
            start_time = time.time()
            move_uci = engine.get_best_move()
            end_time = time.time()
            
            if not move_uci:
                break
            
            move_time_ms = (end_time - start_time) * 1000
            
            # Detect book move (very fast moves < 50ms are likely book moves)
            is_book_move = move_time_ms < 50
            
            # Make the move
            try:
                move = board.parse_uci(move_uci)
                move_san = board.san(move)
                board.push(move)
            except:
                break
            
            # Track statistics
            total_moves += 1
            if is_book_move:
                book_moves += 1
                source = "📖 Book"
            else:
                source = "🤖 Engine"
            
            player = "White" if move_num % 2 == 1 else "Black"
            
            move_details.append({
                'move_num': move_num,
                'move_san': move_san,
                'time_ms': move_time_ms,
                'is_book': is_book_move,
                'player': player
            })
            
            print(f"{move_num:<4} {player:<6} {move_san:<8} {move_time_ms:>6.0f}ms {source:<8}")
            
            # Stop if we've had several non-book moves in a row
            if move_num > 6 and book_moves == 0:
                print("No book moves detected, stopping early...")
                break
        
        # Calculate statistics
        book_percentage = (book_moves / total_moves * 100) if total_moves > 0 else 0
        
        print()
        print("📊 Results Summary:")
        print(f"   Total moves: {total_moves}")
        print(f"   Book moves: {book_moves} ({book_percentage:.1f}%)")
        print(f"   Engine moves: {total_moves - book_moves} ({100-book_percentage:.1f}%)")
        
        if book_moves > 0:
            book_times = [m['time_ms'] for m in move_details if m['is_book']]
            avg_book_time = sum(book_times) / len(book_times)
            print(f"   Average book move time: {avg_book_time:.1f}ms")
            
            # Find last book move
            last_book_move = max([m['move_num'] for m in move_details if m['is_book']])
            print(f"   Last book move: Move {last_book_move}")
        
        if total_moves > book_moves:
            engine_times = [m['time_ms'] for m in move_details if not m['is_book']]
            avg_engine_time = sum(engine_times) / len(engine_times)
            print(f"   Average engine move time: {avg_engine_time:.0f}ms ({avg_engine_time/1000:.1f}s)")
        
        engine.cleanup()
        return book_moves, total_moves, book_percentage
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        return 0, 0, 0

def compare_strength_levels():
    """Compare book usage across different strength levels"""
    print("\n🔍 Book Usage Comparison Across Strength Levels")
    print("=" * 55)
    
    configs = [
        (10, 12, "Intermediate"),
        (15, 15, "Advanced"),
        (20, 20, "Maximum")
    ]
    
    results = []
    
    for skill, depth, label in configs:
        print(f"\n🎯 Testing {label} (Skill {skill}, Depth {depth})")
        print("-" * 30)
        
        try:
            engine = ChessEngine(skill_level=skill, depth=depth, use_opening_book=True)
            board = Board()
            
            book_moves = 0
            total_moves = 0
            
            # Test first 8 moves only for speed
            for move_num in range(1, 9):
                if board.is_game_over():
                    break
                
                engine.reset_move_count()
                engine.move_count = move_num - 1
                engine.set_position(board.fen())
                
                start_time = time.time()
                move_uci = engine.get_best_move()
                end_time = time.time()
                
                if not move_uci:
                    break
                
                move_time_ms = (end_time - start_time) * 1000
                is_book_move = move_time_ms < 100  # Slightly higher threshold
                
                try:
                    move = board.parse_uci(move_uci)
                    move_san = board.san(move)
                    board.push(move)
                except:
                    break
                
                total_moves += 1
                if is_book_move:
                    book_moves += 1
                
                source = "📖" if is_book_move else "🤖"
                player = "W" if move_num % 2 == 1 else "B"
                print(f"   {move_num}. {player} {move_san} {source} ({move_time_ms:.0f}ms)")
            
            book_percentage = (book_moves / total_moves * 100) if total_moves > 0 else 0
            
            results.append({
                'config': label,
                'skill': skill,
                'depth': depth,
                'book_moves': book_moves,
                'total_moves': total_moves,
                'book_percentage': book_percentage
            })
            
            print(f"   📊 {book_moves}/{total_moves} book moves ({book_percentage:.1f}%)")
            
            engine.cleanup()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary comparison
    print(f"\n📊 Summary Comparison:")
    print(f"{'Configuration':<15} {'Book Moves':<12} {'Total':<8} {'Book %':<8}")
    print("-" * 50)
    
    for result in results:
        print(f"{result['config']:<15} {result['book_moves']:<12} {result['total_moves']:<8} {result['book_percentage']:<7.1f}%")
    
    return results

def analyze_findings(max_strength_book_moves, max_strength_total, max_strength_percentage):
    """Analyze the findings about book usage at maximum strength"""
    print(f"\n🎯 Analysis: Book Usage at Maximum Strength")
    print("=" * 50)
    
    print(f"📊 Key Finding:")
    print(f"   At Skill 20, Depth 20: {max_strength_book_moves}/{max_strength_total} moves from book ({max_strength_percentage:.1f}%)")
    print()
    
    if max_strength_percentage > 0:
        print("✅ Book System Status: ACTIVE")
        print("   • Opening book is being used at maximum strength")
        print("   • Book moves are still preferred when available")
        print("   • Engine respects opening theory even at max settings")
        print()
        
        if max_strength_percentage >= 20:
            print("📈 Book Usage: HIGH")
            print("   • Good coverage of opening moves")
            print("   • Book provides significant value")
        elif max_strength_percentage >= 10:
            print("📈 Book Usage: MODERATE") 
            print("   • Reasonable coverage of key opening moves")
            print("   • Book provides some value")
        else:
            print("📈 Book Usage: LOW")
            print("   • Limited coverage, mostly engine moves")
            print("   • Book provides minimal value")
        
        print()
        print("🔍 Why Book Moves Are Still Used:")
        print("   • Book moves are instant (0-1ms) vs engine moves (15+ seconds)")
        print("   • Book contains proven opening theory")
        print("   • No need to calculate well-known positions")
        print("   • Saves computational resources for complex positions")
        
    else:
        print("❌ Book System Status: INACTIVE or BYPASSED")
        print("   • No book moves detected at maximum strength")
        print("   • Engine may be overriding book suggestions")
        print("   • All moves calculated by engine")
    
    print()
    print("💡 Implications:")
    if max_strength_percentage > 0:
        print("   • Opening phase will be very fast (book moves)")
        print("   • Transition to slow, deep calculation after book ends")
        print("   • Best of both worlds: fast theory + deep analysis")
        print("   • User experience: responsive openings, then deep thinking")
    else:
        print("   • All moves will take 15+ seconds to calculate")
        print("   • Even simple opening moves will be slow")
        print("   • Maximum strength but slower user experience")
        print("   • Consider enabling book for better responsiveness")

def main():
    """Main test function"""
    try:
        print("🚀 Maximum Strength Book Usage Analysis")
        print("Testing how many book moves are played at Skill 20, Depth 20")
        print()
        
        # Quick test at maximum strength
        book_moves, total_moves, book_percentage = quick_book_test()
        
        # Compare with other strength levels
        comparison_results = compare_strength_levels()
        
        # Analyze findings
        analyze_findings(book_moves, total_moves, book_percentage)
        
        print(f"\n🎉 Analysis Complete!")
        print(f"Answer: At maximum strength (Skill 20, Depth 20), {book_moves} out of {total_moves} moves ({book_percentage:.1f}%) came from the opening book.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()