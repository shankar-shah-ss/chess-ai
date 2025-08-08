# opening_book.py - Comprehensive Opening Book System
import json
import sqlite3
import hashlib
import random
import time
import os
from typing import Dict, List, Optional, Tuple, Any
from threading import Lock
from chess import Board, Move as ChessMove, STARTING_FEN
import chess.pgn
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BookMove:
    """Represents a move in the opening book"""
    move: str  # UCI format (e.g., "e2e4")
    weight: int  # How often this move was played
    wins: int  # Number of wins with this move
    draws: int  # Number of draws with this move
    losses: int  # Number of losses with this move
    avg_rating: float  # Average rating of players who played this move
    last_played: int  # Timestamp when last played by engine (for rotation)
    
    @property
    def score(self) -> float:
        """Calculate move score based on results"""
        total_games = self.wins + self.draws + self.losses
        if total_games == 0:
            return 0.5
        return (self.wins + 0.5 * self.draws) / total_games
    
    @property
    def popularity(self) -> float:
        """Normalized popularity score"""
        return min(self.weight / 1000.0, 1.0)

class PolyglotReader:
    """Reader for Polyglot opening book format (.bin files)"""
    
    def __init__(self, book_path: str):
        self.book_path = book_path
        self.entries = {}
        self._load_book()
    
    def _load_book(self):
        """Load Polyglot book entries"""
        if not os.path.exists(self.book_path):
            logger.warning(f"Polyglot book not found: {self.book_path}")
            return
            
        try:
            with open(self.book_path, 'rb') as f:
                while True:
                    entry = f.read(16)  # Each entry is 16 bytes
                    if len(entry) < 16:
                        break
                    
                    # Parse Polyglot entry format
                    key = int.from_bytes(entry[0:8], 'big')
                    move = int.from_bytes(entry[8:10], 'big')
                    weight = int.from_bytes(entry[10:12], 'big')
                    learn = int.from_bytes(entry[12:16], 'big')
                    
                    if key not in self.entries:
                        self.entries[key] = []
                    
                    self.entries[key].append({
                        'move': move,
                        'weight': weight,
                        'learn': learn
                    })
            
            logger.info(f"Loaded {len(self.entries)} positions from Polyglot book")
        except Exception as e:
            logger.error(f"Error loading Polyglot book: {e}")
    
    def get_moves(self, position_hash: int) -> List[Dict]:
        """Get moves for a position hash"""
        return self.entries.get(position_hash, [])

class PGNDatabase:
    """Database built from PGN master games"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS opening_moves (
                    position_hash TEXT PRIMARY KEY,
                    fen TEXT,
                    moves TEXT,  -- JSON array of BookMove objects
                    depth INTEGER,
                    last_updated INTEGER
                )
            ''')
            self.conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_depth ON opening_moves(depth)
            ''')
            self.conn.commit()
            logger.info(f"PGN database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing PGN database: {e}")
    
    def add_position(self, fen: str, moves: List[BookMove], depth: int):
        """Add position and moves to database"""
        if not self.conn:
            return
            
        try:
            position_hash = self._hash_position(fen)
            moves_json = json.dumps([{
                'move': m.move,
                'weight': m.weight,
                'wins': m.wins,
                'draws': m.draws,
                'losses': m.losses,
                'avg_rating': m.avg_rating,
                'last_played': m.last_played
            } for m in moves])
            
            self.conn.execute('''
                INSERT OR REPLACE INTO opening_moves 
                (position_hash, fen, moves, depth, last_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (position_hash, fen, moves_json, depth, int(time.time())))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error adding position to database: {e}")
    
    def get_moves(self, fen: str) -> List[BookMove]:
        """Get moves for a position"""
        if not self.conn:
            return []
            
        try:
            position_hash = self._hash_position(fen)
            cursor = self.conn.execute(
                'SELECT moves FROM opening_moves WHERE position_hash = ?',
                (position_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                moves_data = json.loads(row[0])
                return [BookMove(**move_data) for move_data in moves_data]
            return []
        except Exception as e:
            logger.error(f"Error getting moves from database: {e}")
            return []
    
    def _hash_position(self, fen: str) -> str:
        """Create hash for position"""
        return hashlib.md5(fen.encode()).hexdigest()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class OpeningBook:
    """Hybrid opening book system combining multiple sources"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.lock = Lock()
        
        # Configuration
        self.max_book_depth = self.config.get('max_depth', 25)
        self.min_games_threshold = self.config.get('min_games', 5)
        self.rotation_factor = self.config.get('rotation_factor', 0.3)  # 30% chance to rotate
        self.variety_bonus = self.config.get('variety_bonus', 0.1)
        
        # Initialize book sources
        self.polyglot_book = None
        self.pgn_database = None
        self.json_book = {}
        
        # Move rotation tracking
        self.move_history = defaultdict(list)  # position -> [moves played]
        self.last_move_times = defaultdict(dict)  # position -> {move: timestamp}
        
        self._initialize_books()
    
    def _initialize_books(self):
        """Initialize all book sources"""
        try:
            # Initialize built-in JSON book with essential openings
            self._create_essential_openings()
            
            # Try to load Polyglot book if available
            polyglot_path = self.config.get('polyglot_path', 'books/book.bin')
            if os.path.exists(polyglot_path):
                self.polyglot_book = PolyglotReader(polyglot_path)
            
            # Initialize PGN database
            db_path = self.config.get('pgn_db_path', 'books/openings.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.pgn_database = PGNDatabase(db_path)
            
            logger.info("Opening book system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing opening books: {e}")
    
    def _create_essential_openings(self):
        """Create essential opening moves for immediate use"""
        # This provides basic opening coverage while other sources are being built
        essential_openings = {
            STARTING_FEN: [
                BookMove("e2e4", 1000, 400, 300, 300, 2200, 0),  # King's Pawn
                BookMove("d2d4", 900, 380, 320, 200, 2180, 0),   # Queen's Pawn
                BookMove("g1f3", 600, 250, 200, 150, 2150, 0),   # Reti Opening
                BookMove("c2c4", 500, 220, 180, 100, 2160, 0),   # English Opening
                BookMove("b1c3", 300, 120, 100, 80, 2100, 0),    # Van't Kruijs Opening
            ],
            # Add responses to 1.e4
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": [
                BookMove("e7e5", 800, 320, 240, 240, 2200, 0),   # King's Pawn Game
                BookMove("c7c5", 600, 240, 180, 180, 2180, 0),   # Sicilian Defense
                BookMove("e7e6", 400, 160, 120, 120, 2160, 0),   # French Defense
                BookMove("c7c6", 350, 140, 105, 105, 2140, 0),   # Caro-Kann Defense
                BookMove("d7d6", 300, 120, 90, 90, 2120, 0),     # Pirc Defense
            ],
            # Add responses to 1.d4
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1": [
                BookMove("d7d5", 700, 280, 210, 210, 2190, 0),   # Queen's Gambit
                BookMove("g8f6", 650, 260, 195, 195, 2180, 0),   # Indian Defenses
                BookMove("f7f5", 300, 120, 90, 90, 2120, 0),     # Dutch Defense
                BookMove("c7c5", 250, 100, 75, 75, 2100, 0),     # Benoni Defense
                BookMove("e7e6", 400, 160, 120, 120, 2160, 0),   # Queen's Pawn Game
            ]
        }
        
        self.json_book = essential_openings
        logger.info(f"Created essential openings for {len(essential_openings)} positions")
    
    def get_book_move(self, fen: str, move_number: int = 1) -> Optional[str]:
        """Get best book move for position with rotation logic"""
        with self.lock:
            try:
                # Check if we're still in book (depth limit)
                if move_number > self.max_book_depth:
                    return None
                
                # Collect moves from all sources
                all_moves = self._collect_moves_from_sources(fen)
                
                if not all_moves:
                    return None
                
                # Filter moves by minimum games threshold
                viable_moves = [m for m in all_moves if (m.wins + m.draws + m.losses) >= self.min_games_threshold]
                
                if not viable_moves:
                    viable_moves = all_moves  # Fallback to all moves if none meet threshold
                
                # Apply move rotation and selection logic
                selected_move = self._select_move_with_rotation(fen, viable_moves)
                
                if selected_move:
                    # Update move history for rotation
                    self._update_move_history(fen, selected_move.move)
                    logger.debug(f"Book move selected: {selected_move.move} (score: {selected_move.score:.3f})")
                
                return selected_move.move if selected_move else None
                
            except Exception as e:
                logger.error(f"Error getting book move: {e}")
                return None
    
    def _collect_moves_from_sources(self, fen: str) -> List[BookMove]:
        """Collect moves from all available sources"""
        all_moves = {}  # move_uci -> BookMove
        
        # 1. JSON book (highest priority for essential positions)
        if fen in self.json_book:
            for move in self.json_book[fen]:
                all_moves[move.move] = move
        
        # 2. PGN database
        if self.pgn_database:
            pgn_moves = self.pgn_database.get_moves(fen)
            for move in pgn_moves:
                if move.move in all_moves:
                    # Combine statistics
                    existing = all_moves[move.move]
                    all_moves[move.move] = BookMove(
                        move=move.move,
                        weight=existing.weight + move.weight,
                        wins=existing.wins + move.wins,
                        draws=existing.draws + move.draws,
                        losses=existing.losses + move.losses,
                        avg_rating=(existing.avg_rating + move.avg_rating) / 2,
                        last_played=max(existing.last_played, move.last_played)
                    )
                else:
                    all_moves[move.move] = move
        
        # 3. Polyglot book (if available)
        # Note: Polyglot integration would require position hash calculation
        # This is a placeholder for future Polyglot integration
        
        return list(all_moves.values())
    
    def _select_move_with_rotation(self, fen: str, moves: List[BookMove]) -> Optional[BookMove]:
        """Select move with rotation logic to add variety"""
        if not moves:
            return None
        
        # Sort moves by combined score (performance + popularity)
        moves.sort(key=lambda m: m.score + m.popularity * self.variety_bonus, reverse=True)
        
        # Get move history for this position
        position_history = self.move_history.get(fen, [])
        
        # Check if we should rotate (add variety)
        should_rotate = (
            len(position_history) > 0 and 
            random.random() < self.rotation_factor and
            len(moves) > 1
        )
        
        if should_rotate:
            # Find moves that haven't been played recently
            current_time = int(time.time())
            fresh_moves = []
            
            for move in moves[:min(3, len(moves))]:  # Consider top 3 moves
                last_played = self.last_move_times.get(fen, {}).get(move.move, 0)
                time_since_played = current_time - last_played
                
                # Consider move "fresh" if not played in last 10 games or 1 hour
                if move.move not in position_history[-5:] or time_since_played > 3600:
                    fresh_moves.append(move)
            
            if fresh_moves:
                # Weighted random selection from fresh moves
                weights = [m.score + m.popularity * self.variety_bonus for m in fresh_moves]
                return random.choices(fresh_moves, weights=weights)[0]
        
        # Default: return best move
        return moves[0]
    
    def _update_move_history(self, fen: str, move: str):
        """Update move history for rotation tracking"""
        self.move_history[fen].append(move)
        self.last_move_times[fen][move] = int(time.time())
        
        # Keep only last 20 moves in history
        if len(self.move_history[fen]) > 20:
            self.move_history[fen] = self.move_history[fen][-20:]
    
    def add_pgn_games(self, pgn_file_path: str, max_games: int = 10000):
        """Add games from PGN file to database"""
        if not self.pgn_database:
            logger.error("PGN database not initialized")
            return
        
        try:
            games_processed = 0
            positions_added = 0
            
            with open(pgn_file_path, 'r') as pgn_file:
                while games_processed < max_games:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    
                    # Extract game metadata
                    result = game.headers.get('Result', '*')
                    white_elo = int(game.headers.get('WhiteElo', 1500))
                    black_elo = int(game.headers.get('BlackElo', 1500))
                    avg_rating = (white_elo + black_elo) / 2
                    
                    # Skip low-rated games
                    if avg_rating < 2000:
                        continue
                    
                    # Process moves
                    board = Board()
                    move_number = 0
                    
                    for move in game.mainline_moves():
                        if move_number >= self.max_book_depth:
                            break
                        
                        fen = board.fen()
                        uci_move = move.uci()
                        
                        # Update position statistics
                        self._update_position_stats(fen, uci_move, result, avg_rating)
                        
                        board.push(move)
                        move_number += 1
                        positions_added += 1
                    
                    games_processed += 1
                    if games_processed % 100 == 0:
                        logger.info(f"Processed {games_processed} games, {positions_added} positions")
            
            logger.info(f"Finished processing {games_processed} games, added {positions_added} positions")
            
        except Exception as e:
            logger.error(f"Error processing PGN file: {e}")
    
    def _update_position_stats(self, fen: str, move: str, result: str, avg_rating: float):
        """Update statistics for a position and move"""
        # This would update the PGN database with move statistics
        # Implementation depends on how you want to structure the data
        pass
    
    def get_book_info(self) -> Dict[str, Any]:
        """Get information about loaded books"""
        info = {
            'json_positions': len(self.json_book),
            'polyglot_loaded': self.polyglot_book is not None,
            'pgn_database_loaded': self.pgn_database is not None,
            'max_depth': self.max_book_depth,
            'rotation_factor': self.rotation_factor
        }
        
        if self.pgn_database and self.pgn_database.conn:
            try:
                cursor = self.pgn_database.conn.execute('SELECT COUNT(*) FROM opening_moves')
                info['pgn_positions'] = cursor.fetchone()[0]
            except:
                info['pgn_positions'] = 0
        
        return info
    
    def cleanup(self):
        """Cleanup resources"""
        if self.pgn_database:
            self.pgn_database.close()

# Global opening book instance
_opening_book = None
_book_lock = Lock()

def get_opening_book(config: Dict[str, Any] = None) -> OpeningBook:
    """Get global opening book instance (singleton)"""
    global _opening_book
    with _book_lock:
        if _opening_book is None:
            _opening_book = OpeningBook(config)
        return _opening_book

def cleanup_opening_book():
    """Cleanup global opening book"""
    global _opening_book
    with _book_lock:
        if _opening_book:
            _opening_book.cleanup()
            _opening_book = None