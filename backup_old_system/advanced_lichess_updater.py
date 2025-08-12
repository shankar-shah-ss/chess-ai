#!/usr/bin/env python3
"""
Advanced Lichess Opening Database Updater
Comprehensive update of opening database with latest Lichess masters data
Includes all major openings and their popular variations
"""

import requests
import json
import sqlite3
import time
import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import concurrent.futures
from threading import Lock

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))
from opening_book import BookMove, PGNDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_lichess_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedLichessUpdater:
    """Advanced updater with comprehensive opening coverage"""
    
    def __init__(self, db_path: str = "src/books/openings.db"):
        self.db_path = db_path
        self.base_url = "https://explorer.lichess.ovh"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess-AI Advanced Opening Book Updater 2.0'
        })
        
        # Rate limiting
        self.request_delay = 0.8  # Slightly faster but still respectful
        self.last_request_time = 0
        self.request_lock = Lock()
        
        # Date range for filtering (last 5 years)
        current_date = datetime.now()
        five_years_ago = current_date - timedelta(days=5*365)
        self.since_date = str(five_years_ago.year)
        self.until_date = str(current_date.year)
        
        # Initialize database
        self.pgn_db = PGNDatabase(db_path)
        
        # Track processed positions to avoid duplicates
        self.processed_positions: Set[str] = set()
        
        # Comprehensive opening lines to explore
        self.opening_lines = self._get_comprehensive_opening_lines()
    
    def _get_comprehensive_opening_lines(self) -> Dict[str, List[str]]:
        """Get comprehensive list of opening lines to explore"""
        return {
            # === KING'S PAWN OPENINGS ===
            "King's Pawn Game": [
                "e2e4",
                "e2e4 e7e5",
                "e2e4 e7e5 g1f3",
                "e2e4 e7e5 g1f3 b8c6",
            ],
            
            "Ruy Lopez": [
                "e2e4 e7e5 g1f3 b8c6 f1b5",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5",
                "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3",
            ],
            
            "Italian Game": [
                "e2e4 e7e5 g1f3 b8c6 f1c4",
                "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5",
                "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3",
                "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 d2d3",
                "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6",
            ],
            
            "Scotch Game": [
                "e2e4 e7e5 g1f3 b8c6 d2d4",
                "e2e4 e7e5 g1f3 b8c6 d2d4 e5d4",
                "e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f3d4",
            ],
            
            "King's Gambit": [
                "e2e4 e7e5 f2f4",
                "e2e4 e7e5 f2f4 e5f4",
                "e2e4 e7e5 f2f4 e5f4 g1f3",
                "e2e4 e7e5 f2f4 e5f4 f1c4",
            ],
            
            "Vienna Game": [
                "e2e4 e7e5 b1c3",
                "e2e4 e7e5 b1c3 g8f6",
                "e2e4 e7e5 b1c3 b8c6",
            ],
            
            "Sicilian Defense": [
                "e2e4 c7c5",
                "e2e4 c7c5 g1f3",
                "e2e4 c7c5 g1f3 d7d6",
                "e2e4 c7c5 g1f3 d7d6 d2d4",
                "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4",
                "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4",
                "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6",
                "e2e4 c7c5 g1f3 b8c6",
                "e2e4 c7c5 g1f3 b8c6 d2d4",
                "e2e4 c7c5 g1f3 b8c6 d2d4 c5d4",
                "e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4",
            ],
            
            "French Defense": [
                "e2e4 e7e6",
                "e2e4 e7e6 d2d4",
                "e2e4 e7e6 d2d4 d7d5",
                "e2e4 e7e6 d2d4 d7d5 b1c3",
                "e2e4 e7e6 d2d4 d7d5 e4d5",
                "e2e4 e7e6 d2d4 d7d5 e4e5",
            ],
            
            "Caro-Kann Defense": [
                "e2e4 c7c6",
                "e2e4 c7c6 d2d4",
                "e2e4 c7c6 d2d4 d7d5",
                "e2e4 c7c6 d2d4 d7d5 b1c3",
                "e2e4 c7c6 d2d4 d7d5 e4d5",
                "e2e4 c7c6 d2d4 d7d5 e4e5",
            ],
            
            "Alekhine's Defense": [
                "e2e4 g8f6",
                "e2e4 g8f6 e4e5",
                "e2e4 g8f6 e4e5 f6d5",
                "e2e4 g8f6 e4e5 f6d5 d2d4",
            ],
            
            "Scandinavian Defense": [
                "e2e4 d7d5",
                "e2e4 d7d5 e4d5",
                "e2e4 d7d5 e4d5 d8d5",
                "e2e4 d7d5 e4d5 g8f6",
            ],
            
            # === QUEEN'S PAWN OPENINGS ===
            "Queen's Pawn Game": [
                "d2d4",
                "d2d4 d7d5",
                "d2d4 g8f6",
            ],
            
            "Queen's Gambit": [
                "d2d4 d7d5 c2c4",
                "d2d4 d7d5 c2c4 e7e6",
                "d2d4 d7d5 c2c4 e7e6 b1c3",
                "d2d4 d7d5 c2c4 e7e6 g1f3",
                "d2d4 d7d5 c2c4 d5c4",
                "d2d4 d7d5 c2c4 c7c6",
            ],
            
            "King's Indian Defense": [
                "d2d4 g8f6 c2c4 g7g6",
                "d2d4 g8f6 c2c4 g7g6 b1c3",
                "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7",
                "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4",
                "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6",
            ],
            
            "Nimzo-Indian Defense": [
                "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4",
                "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 e2e3",
                "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 d1c2",
                "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 a2a3",
            ],
            
            "Queen's Indian Defense": [
                "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6",
                "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6 g2g3",
                "d2d4 g8f6 c2c4 e7e6 g1f3 b7b6 e2e3",
            ],
            
            "Grünfeld Defense": [
                "d2d4 g8f6 c2c4 g7g6 b1c3 d7d5",
                "d2d4 g8f6 c2c4 g7g6 b1c3 d7d5 c4d5",
                "d2d4 g8f6 c2c4 g7g6 b1c3 d7d5 g1f3",
            ],
            
            "Benoni Defense": [
                "d2d4 g8f6 c2c4 c7c5",
                "d2d4 g8f6 c2c4 c7c5 d4d5",
                "d2d4 g8f6 c2c4 c7c5 d4d5 e7e6",
            ],
            
            "Dutch Defense": [
                "d2d4 f7f5",
                "d2d4 f7f5 g1f3",
                "d2d4 f7f5 c2c4",
                "d2d4 f7f5 g2g3",
            ],
            
            # === FLANK OPENINGS ===
            "English Opening": [
                "c2c4",
                "c2c4 e7e5",
                "c2c4 e7e5 b1c3",
                "c2c4 e7e5 g1f3",
                "c2c4 g8f6",
                "c2c4 g8f6 b1c3",
                "c2c4 g8f6 g1f3",
                "c2c4 c7c5",
                "c2c4 c7c6",
            ],
            
            "Réti Opening": [
                "g1f3",
                "g1f3 d7d5",
                "g1f3 d7d5 c2c4",
                "g1f3 g8f6",
                "g1f3 g8f6 c2c4",
                "g1f3 g8f6 g2g3",
            ],
            
            "King's Indian Attack": [
                "g1f3 d7d5 g2g3",
                "g1f3 g8f6 g2g3",
                "g1f3 d7d5 g2g3 g8f6 f1g2",
            ],
            
            "Bird's Opening": [
                "f2f4",
                "f2f4 d7d5",
                "f2f4 g8f6",
                "f2f4 c7c5",
            ],
            
            # === IRREGULAR OPENINGS ===
            "Larsen's Opening": [
                "b2b3",
                "b2b3 e7e5",
                "b2b3 d7d5",
                "b2b3 g8f6",
            ],
            
            "Modern Defense": [
                "e2e4 g7g6",
                "e2e4 g7g6 d2d4",
                "e2e4 g7g6 d2d4 f8g7",
                "d2d4 g7g6",
                "d2d4 g7g6 e2e4",
            ],
            
            "Pirc Defense": [
                "e2e4 d7d6",
                "e2e4 d7d6 d2d4",
                "e2e4 d7d6 d2d4 g8f6",
                "e2e4 d7d6 d2d4 g8f6 b1c3",
            ],
        }
    
    def _rate_limit(self):
        """Thread-safe rate limiting"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                time.sleep(self.request_delay - time_since_last)
            self.last_request_time = time.time()
    
    def fetch_masters_data(self, fen: str) -> Optional[Dict]:
        """Fetch opening data from Lichess masters database"""
        self._rate_limit()
        
        try:
            params = {
                'fen': fen,
                'since': self.since_date,
                'until': self.until_date,
                'moves': '15',  # Get top 15 moves
                'topGames': '0'
            }
            
            url = f"{self.base_url}/masters"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching masters data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
    
    def convert_lichess_moves(self, lichess_data: Dict) -> List[BookMove]:
        """Convert Lichess move data to BookMove objects"""
        book_moves = []
        
        if not lichess_data or 'moves' not in lichess_data:
            return book_moves
        
        for move_data in lichess_data['moves']:
            try:
                uci = move_data['uci']
                white_wins = move_data.get('white', 0)
                draws = move_data.get('draws', 0)
                black_wins = move_data.get('black', 0)
                
                total_games = white_wins + draws + black_wins
                if total_games < 3:  # Lower threshold for more coverage
                    continue
                
                avg_rating = move_data.get('averageRating', 2200)
                if avg_rating is None:
                    avg_rating = 2200
                
                book_move = BookMove(
                    move=uci,
                    weight=total_games,
                    wins=white_wins,
                    draws=draws,
                    losses=black_wins,
                    avg_rating=float(avg_rating),
                    last_played=0
                )
                
                book_moves.append(book_move)
                
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing move data: {e}")
                continue
        
        book_moves.sort(key=lambda m: m.weight, reverse=True)
        return book_moves
    
    def process_move_sequence(self, moves: List[str]) -> List[Tuple[str, int]]:
        """Process a sequence of moves and return (FEN, depth) pairs"""
        positions = []
        board = chess.Board()
        
        for depth, move_uci in enumerate(moves):
            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    board.push(move)
                    fen = board.fen()
                    positions.append((fen, depth + 1))
                else:
                    logger.warning(f"Illegal move {move_uci} at depth {depth}")
                    break
            except (ValueError, chess.InvalidMoveError) as e:
                logger.warning(f"Invalid move {move_uci}: {e}")
                break
        
        return positions
    
    def update_position(self, fen: str, depth: int) -> bool:
        """Update a single position in the database"""
        if fen in self.processed_positions:
            return False
        
        lichess_data = self.fetch_masters_data(fen)
        if not lichess_data:
            return False
        
        book_moves = self.convert_lichess_moves(lichess_data)
        if not book_moves:
            return False
        
        self.pgn_db.add_position(fen, book_moves, depth)
        self.processed_positions.add(fen)
        
        logger.info(f"Updated position at depth {depth} with {len(book_moves)} moves "
                   f"(total games: {sum(m.weight for m in book_moves)})")
        return True
    
    def process_opening_line(self, opening_name: str, move_sequences: List[str]) -> int:
        """Process all variations of an opening line"""
        logger.info(f"\n=== Processing {opening_name} ===")
        positions_updated = 0
        
        # Always include the starting position
        if self.update_position(chess.STARTING_FEN, 0):
            positions_updated += 1
        
        for sequence in move_sequences:
            moves = sequence.split()
            positions = self.process_move_sequence(moves)
            
            for fen, depth in positions:
                if self.update_position(fen, depth):
                    positions_updated += 1
                    
                # Small delay between positions
                time.sleep(0.1)
        
        logger.info(f"Completed {opening_name}: {positions_updated} positions updated")
        return positions_updated
    
    def update_comprehensive_database(self):
        """Update database with comprehensive opening coverage"""
        logger.info("Starting comprehensive Lichess opening database update...")
        logger.info(f"Date range: {self.since_date} to {self.until_date}")
        logger.info(f"Opening lines to process: {len(self.opening_lines)}")
        
        total_positions_updated = 0
        start_time = time.time()
        
        for i, (opening_name, move_sequences) in enumerate(self.opening_lines.items(), 1):
            try:
                logger.info(f"\n[{i}/{len(self.opening_lines)}] Processing {opening_name}...")
                positions_updated = self.process_opening_line(opening_name, move_sequences)
                total_positions_updated += positions_updated
                
                # Progress update
                elapsed = time.time() - start_time
                avg_time_per_opening = elapsed / i
                remaining_openings = len(self.opening_lines) - i
                eta = remaining_openings * avg_time_per_opening
                
                logger.info(f"Progress: {i}/{len(self.opening_lines)} openings "
                           f"({total_positions_updated} positions updated, "
                           f"ETA: {eta/60:.1f} minutes)")
                
                # Longer delay between openings
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error processing {opening_name}: {e}")
                continue
        
        elapsed_time = time.time() - start_time
        logger.info(f"\n=== Update Complete ===")
        logger.info(f"Total positions updated: {total_positions_updated}")
        logger.info(f"Total time: {elapsed_time/60:.1f} minutes")
        logger.info(f"Average positions per minute: {total_positions_updated/(elapsed_time/60):.1f}")
        logger.info(f"Database: {self.db_path}")
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total positions
            cursor.execute("SELECT COUNT(*) FROM opening_moves")
            total_positions = cursor.fetchone()[0]
            
            # Positions by depth
            cursor.execute("SELECT depth, COUNT(*) FROM opening_moves GROUP BY depth ORDER BY depth")
            depth_stats = dict(cursor.fetchall())
            
            # Recent updates (last 24 hours)
            cursor.execute("SELECT COUNT(*) FROM opening_moves WHERE last_updated > ?", 
                         (int(time.time()) - 86400,))
            recent_updates = cursor.fetchone()[0]
            
            # Total moves in database
            cursor.execute("SELECT moves FROM opening_moves")
            total_moves = 0
            for row in cursor.fetchall():
                try:
                    moves_data = json.loads(row[0])
                    total_moves += len(moves_data)
                except:
                    continue
            
            # Average moves per position
            avg_moves = total_moves / total_positions if total_positions > 0 else 0
            
            conn.close()
            
            return {
                'total_positions': total_positions,
                'total_moves': total_moves,
                'avg_moves_per_position': avg_moves,
                'depth_distribution': depth_stats,
                'recent_updates': recent_updates
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

def main():
    """Main function"""
    print("🚀 Advanced Lichess Opening Database Updater")
    print("=" * 60)
    
    # Initialize updater
    updater = AdvancedLichessUpdater()
    
    # Show current database stats
    print("\n📊 Current Database Statistics:")
    stats = updater.get_database_stats()
    if stats:
        print(f"Total positions: {stats.get('total_positions', 0):,}")
        print(f"Total moves: {stats.get('total_moves', 0):,}")
        print(f"Average moves per position: {stats.get('avg_moves_per_position', 0):.1f}")
        print(f"Recent updates (24h): {stats.get('recent_updates', 0)}")
        
        depth_dist = stats.get('depth_distribution', {})
        if depth_dist:
            print("\nPositions by depth:")
            for depth, count in sorted(depth_dist.items()):
                print(f"  Depth {depth}: {count:,} positions")
    
    # Show what will be updated
    print(f"\n🎯 This will comprehensively update your opening database")
    print(f"📅 Date range: {updater.since_date} to {updater.until_date} (last 5 years)")
    print(f"🎲 Opening systems: {len(updater.opening_lines)}")
    
    total_lines = sum(len(lines) for lines in updater.opening_lines.values())
    print(f"📈 Total opening lines: {total_lines}")
    print(f"⏱️  Estimated time: {total_lines * 2 / 60:.0f}-{total_lines * 4 / 60:.0f} minutes")
    
    print("\n🔍 Opening systems to be updated:")
    for i, opening_name in enumerate(updater.opening_lines.keys(), 1):
        print(f"  {i:2d}. {opening_name}")
    
    response = input(f"\nProceed with comprehensive update? (y/N): ").strip().lower()
    if response != 'y':
        print("Update cancelled.")
        return
    
    # Perform update
    start_time = time.time()
    try:
        updater.update_comprehensive_database()
        
        # Show final stats
        print("\n📊 Final Database Statistics:")
        final_stats = updater.get_database_stats()
        if final_stats:
            print(f"Total positions: {final_stats.get('total_positions', 0):,}")
            print(f"Total moves: {final_stats.get('total_moves', 0):,}")
            print(f"Average moves per position: {final_stats.get('avg_moves_per_position', 0):.1f}")
            print(f"Recent updates: {final_stats.get('recent_updates', 0):,}")
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ Comprehensive update completed in {elapsed_time/60:.1f} minutes")
        print(f"📝 Check advanced_lichess_update.log for detailed logs")
        
    except KeyboardInterrupt:
        print("\n⚠️  Update interrupted by user")
    except Exception as e:
        logger.error(f"Update failed: {e}")
        print(f"\n❌ Update failed: {e}")

if __name__ == "__main__":
    main()