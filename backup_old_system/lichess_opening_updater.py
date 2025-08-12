#!/usr/bin/env python3
"""
Lichess Opening Database Updater
Fetches popular opening moves from Lichess masters database and updates local opening book
"""

import requests
import json
import sqlite3
import time
import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))
from opening_book import BookMove, PGNDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lichess_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LichessMove:
    """Represents a move from Lichess opening explorer"""
    uci: str
    san: str
    white: int
    draws: int
    black: int
    average_rating: Optional[float] = None

class LichessOpeningUpdater:
    """Updates opening database with data from Lichess masters database"""
    
    def __init__(self, db_path: str = "src/books/openings.db"):
        self.db_path = db_path
        self.base_url = "https://explorer.lichess.ovh"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess-AI Opening Book Updater 1.0'
        })
        
        # Rate limiting
        self.request_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
        # Date range for filtering (last 5 years)
        current_date = datetime.now()
        five_years_ago = current_date - timedelta(days=5*365)
        self.since_date = str(five_years_ago.year)
        self.until_date = str(current_date.year)
        
        # Initialize database
        self.pgn_db = PGNDatabase(db_path)
        
        # Popular opening positions to explore (FEN -> name)
        self.popular_openings = {
            # Starting position
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": "Starting Position",
            
            # After 1.e4
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1": "After 1.e4",
            
            # After 1.d4
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1": "After 1.d4",
            
            # After 1.Nf3
            "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1": "After 1.Nf3",
            
            # After 1.c4
            "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1": "After 1.c4",
            
            # King's Pawn Game (1.e4 e5)
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "King's Pawn Game",
            
            # Sicilian Defense (1.e4 c5)
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Sicilian Defense",
            
            # French Defense (1.e4 e6)
            "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "French Defense",
            
            # Caro-Kann Defense (1.e4 c6)
            "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2": "Caro-Kann Defense",
            
            # Queen's Gambit (1.d4 d5 2.c4)
            "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2": "Queen's Gambit",
            
            # King's Indian Defense setup (1.d4 Nf6 2.c4 g6)
            "rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3": "King's Indian Defense",
            
            # Ruy Lopez (1.e4 e5 2.Nf3 Nc6 3.Bb5)
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Ruy Lopez",
            
            # Italian Game (1.e4 e5 2.Nf3 Nc6 3.Bc4)
            "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3": "Italian Game",
            
            # Scotch Game (1.e4 e5 2.Nf3 Nc6 3.d4)
            "r1bqkbnr/pppp1ppp/2n5/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3": "Scotch Game",
            
            # Queen's Gambit Declined (1.d4 d5 2.c4 e6)
            "rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3": "Queen's Gambit Declined",
            
            # Nimzo-Indian Defense (1.d4 Nf6 2.c4 e6 3.Nc3 Bb4)
            "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4": "Nimzo-Indian Defense",
        }
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def fetch_masters_data(self, fen: str, max_depth: int = 15) -> Optional[Dict]:
        """Fetch opening data from Lichess masters database"""
        self._rate_limit()
        
        try:
            params = {
                'fen': fen,
                'since': self.since_date,
                'until': self.until_date,
                'moves': '12',  # Get top 12 moves
                'topGames': '0'  # We don't need individual games
            }
            
            url = f"{self.base_url}/masters"
            logger.info(f"Fetching masters data for position: {fen[:50]}...")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Received {len(data.get('moves', []))} moves for position")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching masters data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return None
    
    def convert_lichess_moves(self, lichess_data: Dict, position_fen: str) -> List[BookMove]:
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
                if total_games < 5:  # Skip moves with very few games
                    continue
                
                # Calculate average rating (use a reasonable default if not available)
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
                    last_played=0  # Will be updated when move is played
                )
                
                book_moves.append(book_move)
                logger.debug(f"Added move {uci}: {total_games} games, score: {book_move.score:.3f}")
                
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing move data: {e}")
                continue
        
        # Sort by total games (weight) descending
        book_moves.sort(key=lambda m: m.weight, reverse=True)
        return book_moves
    
    def explore_position_tree(self, fen: str, depth: int = 0, max_depth: int = 8) -> int:
        """Recursively explore and update opening tree from a position"""
        if depth >= max_depth:
            return 0
        
        positions_updated = 0
        
        # Fetch data for current position
        lichess_data = self.fetch_masters_data(fen)
        if not lichess_data:
            return positions_updated
        
        # Convert to BookMove objects
        book_moves = self.convert_lichess_moves(lichess_data, fen)
        if not book_moves:
            return positions_updated
        
        # Update database with this position
        self.pgn_db.add_position(fen, book_moves, depth)
        positions_updated += 1
        logger.info(f"Updated position at depth {depth} with {len(book_moves)} moves")
        
        # Explore child positions for the most popular moves
        board = chess.Board(fen)
        for i, book_move in enumerate(book_moves[:5]):  # Only explore top 5 moves
            if book_move.weight < 20:  # Skip moves with very few games
                break
                
            try:
                move = chess.Move.from_uci(book_move.move)
                if move in board.legal_moves:
                    board.push(move)
                    child_fen = board.fen()
                    
                    # Recursively explore child position
                    child_updates = self.explore_position_tree(child_fen, depth + 1, max_depth)
                    positions_updated += child_updates
                    
                    board.pop()
                else:
                    logger.warning(f"Illegal move {book_move.move} in position {fen}")
                    
            except (ValueError, chess.InvalidMoveError) as e:
                logger.warning(f"Error processing move {book_move.move}: {e}")
                continue
        
        return positions_updated
    
    def update_opening_database(self):
        """Main method to update the opening database"""
        logger.info("Starting Lichess opening database update...")
        logger.info(f"Filtering games from {self.since_date} to {self.until_date}")
        
        total_positions_updated = 0
        
        # Process each popular opening
        for i, (fen, name) in enumerate(self.popular_openings.items(), 1):
            logger.info(f"\n=== Processing {name} ({i}/{len(self.popular_openings)}) ===")
            
            try:
                positions_updated = self.explore_position_tree(fen, depth=0, max_depth=6)
                total_positions_updated += positions_updated
                logger.info(f"Updated {positions_updated} positions for {name}")
                
                # Add a longer delay between different openings
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")
                continue
        
        logger.info(f"\n=== Update Complete ===")
        logger.info(f"Total positions updated: {total_positions_updated}")
        logger.info(f"Database updated: {self.db_path}")
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the current database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total positions
            cursor.execute("SELECT COUNT(*) FROM opening_moves")
            total_positions = cursor.fetchone()[0]
            
            # Get positions by depth
            cursor.execute("SELECT depth, COUNT(*) FROM opening_moves GROUP BY depth ORDER BY depth")
            depth_stats = dict(cursor.fetchall())
            
            # Get recent updates
            cursor.execute("SELECT COUNT(*) FROM opening_moves WHERE last_updated > ?", 
                         (int(time.time()) - 86400,))  # Last 24 hours
            recent_updates = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_positions': total_positions,
                'depth_distribution': depth_stats,
                'recent_updates': recent_updates
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

def main():
    """Main function"""
    print("🚀 Lichess Opening Database Updater")
    print("=" * 50)
    
    # Initialize updater
    updater = LichessOpeningUpdater()
    
    # Show current database stats
    print("\n📊 Current Database Statistics:")
    stats = updater.get_database_stats()
    if stats:
        print(f"Total positions: {stats.get('total_positions', 0)}")
        print(f"Recent updates (24h): {stats.get('recent_updates', 0)}")
        depth_dist = stats.get('depth_distribution', {})
        if depth_dist:
            print("Positions by depth:")
            for depth, count in sorted(depth_dist.items()):
                print(f"  Depth {depth}: {count} positions")
    
    # Confirm update
    print(f"\n🎯 This will update your opening database with popular moves from Lichess masters")
    print(f"📅 Date range: {updater.since_date} to {updater.until_date}")
    print(f"🎲 Openings to process: {len(updater.popular_openings)}")
    
    response = input("\nProceed with update? (y/N): ").strip().lower()
    if response != 'y':
        print("Update cancelled.")
        return
    
    # Perform update
    start_time = time.time()
    try:
        updater.update_opening_database()
        
        # Show final stats
        print("\n📊 Updated Database Statistics:")
        final_stats = updater.get_database_stats()
        if final_stats:
            print(f"Total positions: {final_stats.get('total_positions', 0)}")
            print(f"Recent updates: {final_stats.get('recent_updates', 0)}")
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ Update completed in {elapsed_time:.1f} seconds")
        print(f"📝 Check lichess_update.log for detailed logs")
        
    except KeyboardInterrupt:
        print("\n⚠️  Update interrupted by user")
    except Exception as e:
        logger.error(f"Update failed: {e}")
        print(f"\n❌ Update failed: {e}")

if __name__ == "__main__":
    main()