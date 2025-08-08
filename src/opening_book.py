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
        """Create comprehensive opening database covering all major openings and variations"""
        essential_openings = {}
        
        # Starting position - First moves
        essential_openings[STARTING_FEN] = [
            BookMove("e2e4", 1000, 420, 280, 300, 2220, 0),  # King's Pawn
            BookMove("d2d4", 950, 400, 300, 250, 2200, 0),   # Queen's Pawn
            BookMove("g1f3", 650, 280, 220, 150, 2180, 0),   # Reti Opening
            BookMove("c2c4", 550, 240, 190, 120, 2170, 0),   # English Opening
            BookMove("b1c3", 300, 130, 100, 70, 2120, 0),    # Van't Kruijs Opening
            BookMove("f2f4", 200, 80, 60, 60, 2100, 0),      # Bird's Opening
            BookMove("g2g3", 180, 75, 55, 50, 2110, 0),      # Benko's Opening
            BookMove("b2b3", 150, 60, 45, 45, 2090, 0),      # Nimzowitsch-Larsen Attack
        ]
        
        # === 1.e4 OPENINGS ===
        
        # After 1.e4 - Black responses
        fen_1e4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        essential_openings[fen_1e4] = [
            BookMove("e7e5", 850, 340, 255, 255, 2210, 0),   # King's Pawn Game
            BookMove("c7c5", 700, 280, 210, 210, 2200, 0),   # Sicilian Defense
            BookMove("e7e6", 450, 180, 135, 135, 2180, 0),   # French Defense
            BookMove("c7c6", 400, 160, 120, 120, 2170, 0),   # Caro-Kann Defense
            BookMove("d7d6", 350, 140, 105, 105, 2150, 0),   # Pirc Defense
            BookMove("g8f6", 300, 120, 90, 90, 2160, 0),     # Alekhine's Defense
            BookMove("b8c6", 250, 100, 75, 75, 2140, 0),     # Nimzowitsch Defense
            BookMove("d7d5", 200, 80, 60, 60, 2130, 0),      # Scandinavian Defense
            BookMove("g7g6", 180, 72, 54, 54, 2120, 0),      # Modern Defense
        ]
        
        # === KING'S PAWN GAME (1.e4 e5) ===
        
        # After 1.e4 e5 - White's second move
        fen_1e4_e5 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        essential_openings[fen_1e4_e5] = [
            BookMove("g1f3", 800, 320, 240, 240, 2220, 0),   # King's Knight
            BookMove("f2f4", 300, 120, 90, 90, 2180, 0),     # King's Gambit
            BookMove("b1c3", 250, 100, 75, 75, 2160, 0),     # Vienna Game
            BookMove("f1c4", 200, 80, 60, 60, 2150, 0),      # Bishop's Opening
            BookMove("d2d3", 150, 60, 45, 45, 2140, 0),      # King's Indian Attack
        ]
        
        # RUY LOPEZ (1.e4 e5 2.Nf3 Nc6 3.Bb5)
        fen_ruy_lopez = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        essential_openings[fen_ruy_lopez] = [
            BookMove("a7a6", 600, 240, 180, 180, 2200, 0),   # Morphy Defense
            BookMove("g8f6", 300, 120, 90, 90, 2180, 0),     # Berlin Defense
            BookMove("f7f5", 200, 80, 60, 60, 2160, 0),      # Schliemann Defense
            BookMove("b8d7", 150, 60, 45, 45, 2150, 0),      # Steinitz Defense
            BookMove("g7g6", 100, 40, 30, 30, 2140, 0),      # Fianchetto Defense
        ]
        
        # ITALIAN GAME (1.e4 e5 2.Nf3 Nc6 3.Bc4)
        fen_italian = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        essential_openings[fen_italian] = [
            BookMove("f8c5", 400, 160, 120, 120, 2190, 0),   # Italian Game proper
            BookMove("g8f6", 350, 140, 105, 105, 2180, 0),   # Two Knights Defense
            BookMove("f7f5", 200, 80, 60, 60, 2160, 0),      # Rousseau Gambit
            BookMove("b8e7", 150, 60, 45, 45, 2150, 0),      # Hungarian Defense
        ]
        
        # === SICILIAN DEFENSE (1.e4 c5) ===
        
        # After 1.e4 c5 - White's second move
        fen_sicilian = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        essential_openings[fen_sicilian] = [
            BookMove("g1f3", 700, 280, 210, 210, 2210, 0),   # Open Sicilian
            BookMove("b1c3", 300, 120, 90, 90, 2180, 0),     # Closed Sicilian
            BookMove("f2f4", 200, 80, 60, 60, 2160, 0),      # Grand Prix Attack
            BookMove("f1b5", 150, 60, 45, 45, 2150, 0),      # Bb5+ Sicilian
            BookMove("c2c3", 100, 40, 30, 30, 2140, 0),      # Alapin Variation
        ]
        
        # SICILIAN NAJDORF (1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6)
        fen_najdorf = "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
        essential_openings[fen_najdorf] = [
            BookMove("f2f3", 300, 120, 90, 90, 2220, 0),     # Be3 setup
            BookMove("c1e3", 280, 112, 84, 84, 2210, 0),     # English Attack
            BookMove("f1e2", 250, 100, 75, 75, 2200, 0),     # Positional
            BookMove("g2g3", 200, 80, 60, 60, 2190, 0),      # Fianchetto
            BookMove("h2h3", 150, 60, 45, 45, 2180, 0),      # Quiet development
        ]
        
        # === FRENCH DEFENSE (1.e4 e6) ===
        
        # After 1.e4 e6 - White's second move
        fen_french = "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        essential_openings[fen_french] = [
            BookMove("d2d4", 600, 240, 180, 180, 2200, 0),   # Advance/Exchange/Tarrasch
            BookMove("g1f3", 300, 120, 90, 90, 2180, 0),     # King's Indian Attack
            BookMove("b1c3", 200, 80, 60, 60, 2170, 0),      # Two Knights
            BookMove("f2f4", 150, 60, 45, 45, 2160, 0),      # La Bourdonnais
        ]
        
        # FRENCH ADVANCE (1.e4 e6 2.d4 d5 3.e5)
        fen_french_advance = "rnbqkbnr/ppp2ppp/4p3/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3"
        essential_openings[fen_french_advance] = [
            BookMove("c7c5", 400, 160, 120, 120, 2190, 0),   # Main line
            BookMove("b8c6", 300, 120, 90, 90, 2180, 0),     # Milner-Barry Gambit setup
            BookMove("g8e7", 200, 80, 60, 60, 2170, 0),      # Steinitz variation
            BookMove("f7f6", 150, 60, 45, 45, 2160, 0),      # Frenkel-Duz Khotimirsky
        ]
        
        # === CARO-KANN DEFENSE (1.e4 c6) ===
        
        # After 1.e4 c6 - White's second move
        fen_caro_kann = "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        essential_openings[fen_caro_kann] = [
            BookMove("d2d4", 500, 200, 150, 150, 2190, 0),   # Main line
            BookMove("b1c3", 300, 120, 90, 90, 2180, 0),     # Two Knights
            BookMove("g1f3", 200, 80, 60, 60, 2170, 0),      # King's Indian Attack
            BookMove("f2f3", 150, 60, 45, 45, 2160, 0),      # Fantasy Variation
        ]
        
        # === 1.d4 OPENINGS ===
        
        # After 1.d4 - Black responses
        fen_1d4 = "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1"
        essential_openings[fen_1d4] = [
            BookMove("d7d5", 700, 280, 210, 210, 2200, 0),   # Queen's Gambit
            BookMove("g8f6", 650, 260, 195, 195, 2190, 0),   # Indian Defenses
            BookMove("e7e6", 400, 160, 120, 120, 2180, 0),   # Queen's Pawn Game
            BookMove("c7c5", 300, 120, 90, 90, 2170, 0),     # Benoni Defense
            BookMove("f7f5", 250, 100, 75, 75, 2160, 0),     # Dutch Defense
            BookMove("g7g6", 200, 80, 60, 60, 2150, 0),      # King's Indian Defense
            BookMove("b8c6", 150, 60, 45, 45, 2140, 0),      # Chigorin Defense
        ]
        
        # === QUEEN'S GAMBIT (1.d4 d5 2.c4) ===
        
        # After 1.d4 d5 2.c4 - Black responses
        fen_queens_gambit = "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq - 0 2"
        essential_openings[fen_queens_gambit] = [
            BookMove("d5c4", 400, 160, 120, 120, 2190, 0),   # Queen's Gambit Accepted
            BookMove("e7e6", 500, 200, 150, 150, 2200, 0),   # Queen's Gambit Declined
            BookMove("c7c6", 300, 120, 90, 90, 2180, 0),     # Slav Defense
            BookMove("b8c6", 200, 80, 60, 60, 2170, 0),      # Chigorin Defense
            BookMove("e7e5", 150, 60, 45, 45, 2160, 0),      # Albin Counter-Gambit
        ]
        
        # QUEEN'S GAMBIT DECLINED (1.d4 d5 2.c4 e6)
        fen_qgd = "rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3"
        essential_openings[fen_qgd] = [
            BookMove("b1c3", 500, 200, 150, 150, 2200, 0),   # Orthodox Defense
            BookMove("g1f3", 400, 160, 120, 120, 2190, 0),   # Quiet development
            BookMove("c4d5", 200, 80, 60, 60, 2180, 0),      # Exchange Variation
            BookMove("e2e3", 150, 60, 45, 45, 2170, 0),      # Colle System
        ]
        
        # === NIMZO-INDIAN DEFENSE (1.d4 Nf6 2.c4 e6 3.Nc3 Bb4) ===
        
        fen_nimzo_indian = "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4"
        essential_openings[fen_nimzo_indian] = [
            BookMove("e2e3", 400, 160, 120, 120, 2200, 0),   # Rubinstein System
            BookMove("a2a3", 350, 140, 105, 105, 2190, 0),   # Saemisch Variation
            BookMove("g1f3", 300, 120, 90, 90, 2180, 0),     # Classical
            BookMove("f2f3", 200, 80, 60, 60, 2170, 0),      # Kmoch Variation
            BookMove("d1c2", 150, 60, 45, 45, 2160, 0),      # Classical Defense
        ]
        
        # === KING'S INDIAN DEFENSE (1.d4 Nf6 2.c4 g6 3.Nc3 Bg7) ===
        
        fen_kings_indian = "rnbqk2r/ppp1ppbp/3p1np1/8/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4"
        essential_openings[fen_kings_indian] = [
            BookMove("e2e4", 400, 160, 120, 120, 2200, 0),   # Classical System
            BookMove("g1f3", 350, 140, 105, 105, 2190, 0),   # Fianchetto System
            BookMove("f2f3", 300, 120, 90, 90, 2180, 0),     # Saemisch System
            BookMove("h2h3", 200, 80, 60, 60, 2170, 0),      # Makogonov System
            BookMove("c1g5", 150, 60, 45, 45, 2160, 0),      # Averbakh System
        ]
        
        # === ENGLISH OPENING (1.c4) ===
        
        # After 1.c4 - Black responses
        fen_english = "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 1"
        essential_openings[fen_english] = [
            BookMove("e7e5", 400, 160, 120, 120, 2190, 0),   # Reversed Sicilian
            BookMove("g8f6", 350, 140, 105, 105, 2180, 0),   # Anglo-Indian
            BookMove("c7c5", 300, 120, 90, 90, 2170, 0),     # Symmetrical English
            BookMove("e7e6", 250, 100, 75, 75, 2160, 0),     # Anglo-French
            BookMove("g7g6", 200, 80, 60, 60, 2150, 0),      # King's Indian setup
            BookMove("d7d5", 150, 60, 45, 45, 2140, 0),      # Anglo-Scandinavian
        ]
        
        # === RETI OPENING (1.Nf3) ===
        
        # After 1.Nf3 - Black responses
        fen_reti = "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1"
        essential_openings[fen_reti] = [
            BookMove("d7d5", 400, 160, 120, 120, 2180, 0),   # Queen's Pawn
            BookMove("g8f6", 350, 140, 105, 105, 2170, 0),   # King's Indian Attack
            BookMove("c7c5", 300, 120, 90, 90, 2160, 0),     # English Defense
            BookMove("e7e6", 250, 100, 75, 75, 2150, 0),     # French setup
            BookMove("g7g6", 200, 80, 60, 60, 2140, 0),      # King's Indian setup
        ]
        
        # Add more detailed variations for major openings
        self._add_detailed_variations(essential_openings)
        
        self.json_book = essential_openings
        logger.info(f"Created comprehensive opening database with {len(essential_openings)} positions")
    
    def _add_detailed_variations(self, openings: Dict[str, List[BookMove]]):
        """Add detailed variations for major openings"""
        
        # === DETAILED RUY LOPEZ VARIATIONS ===
        
        # Ruy Lopez Morphy Defense (1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4)
        fen_morphy_defense = "r1bqkbnr/1ppp1ppp/p1n5/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4"
        openings[fen_morphy_defense] = [
            BookMove("g8f6", 500, 200, 150, 150, 2200, 0),   # Open Defense
            BookMove("b7b5", 300, 120, 90, 90, 2180, 0),     # Breyer Defense
            BookMove("f7f5", 200, 80, 60, 60, 2160, 0),      # Schliemann Deferred
            BookMove("d7d6", 150, 60, 45, 45, 2150, 0),      # Steinitz Defense Deferred
        ]
        
        # Ruy Lopez Berlin Defense (1.e4 e5 2.Nf3 Nc6 3.Bb5 Nf6)
        fen_berlin = "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        openings[fen_berlin] = [
            BookMove("e1g1", 400, 160, 120, 120, 2200, 0),   # Berlin Defense main
            BookMove("d2d3", 300, 120, 90, 90, 2180, 0),     # Berlin Defense Anti-Marshall
            BookMove("b5c6", 200, 80, 60, 60, 2170, 0),      # Exchange Variation
        ]
        
        # === DETAILED SICILIAN VARIATIONS ===
        
        # Sicilian Dragon (1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 g6)
        fen_dragon = "rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
        openings[fen_dragon] = [
            BookMove("f2f3", 400, 160, 120, 120, 2210, 0),   # Yugoslav Attack
            BookMove("c1e3", 350, 140, 105, 105, 2200, 0),   # Positional System
            BookMove("f1e2", 300, 120, 90, 90, 2190, 0),     # Quiet development
            BookMove("h2h3", 200, 80, 60, 60, 2180, 0),      # Preventing ...Ng4
        ]
        
        # Sicilian Accelerated Dragon (1.e4 c5 2.Nf3 g6 3.d4 cxd4 4.Nxd4 Bg7)
        fen_accel_dragon = "rnbqk1nr/pp1pppbp/6p1/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 2 5"
        openings[fen_accel_dragon] = [
            BookMove("c2c4", 400, 160, 120, 120, 2200, 0),   # Maroczy Bind
            BookMove("b1c3", 350, 140, 105, 105, 2190, 0),   # Normal development
            BookMove("f1e2", 250, 100, 75, 75, 2180, 0),     # Quiet system
        ]
        
        # === DETAILED FRENCH VARIATIONS ===
        
        # French Winawer (1.e4 e6 2.d4 d5 3.Nc3 Bb4)
        fen_winawer = "rnbqk1nr/ppp2ppp/4p3/3p4/1b1PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 2 4"
        openings[fen_winawer] = [
            BookMove("e4e5", 400, 160, 120, 120, 2200, 0),   # Advance Variation
            BookMove("c1d2", 300, 120, 90, 90, 2190, 0),     # Main line
            BookMove("a2a3", 250, 100, 75, 75, 2180, 0),     # Poisoned Pawn
            BookMove("d1g4", 200, 80, 60, 60, 2170, 0),      # Poisoned Pawn Variation
        ]
        
        # French Tarrasch (1.e4 e6 2.d4 d5 3.Nd2)
        fen_tarrasch = "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPPN1PPP/R1BQKBNR b KQkq - 2 3"
        openings[fen_tarrasch] = [
            BookMove("c7c5", 400, 160, 120, 120, 2190, 0),   # Main line
            BookMove("g8f6", 350, 140, 105, 105, 2180, 0),   # Closed System
            BookMove("b8c6", 250, 100, 75, 75, 2170, 0),     # Guimard Variation
        ]
        
        # === DETAILED CARO-KANN VARIATIONS ===
        
        # Caro-Kann Main Line (1.e4 c6 2.d4 d5 3.Nc3 dxe4 4.Nxe4)
        fen_caro_main = "rnbqkbnr/pp2pppp/2p5/8/3PN3/8/PPP2PPP/R1BQKBNR b KQkq - 0 4"
        openings[fen_caro_main] = [
            BookMove("c8f5", 400, 160, 120, 120, 2190, 0),   # Classical Variation
            BookMove("b8d7", 350, 140, 105, 105, 2180, 0),   # Karpov Variation
            BookMove("g8f6", 300, 120, 90, 90, 2170, 0),     # Bronstein-Larsen
        ]
        
        # === DETAILED QUEEN'S GAMBIT VARIATIONS ===
        
        # QGD Orthodox Defense (1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5)
        fen_qgd_orthodox = "rnbqkb1r/ppp2ppp/4pn2/3p2B1/2PP4/2N5/PP2PPPP/R2QKBNR b KQkq - 3 4"
        openings[fen_qgd_orthodox] = [
            BookMove("b8d7", 400, 160, 120, 120, 2200, 0),   # Orthodox Defense
            BookMove("f8e7", 350, 140, 105, 105, 2190, 0),   # Lasker Defense
            BookMove("h7h6", 300, 120, 90, 90, 2180, 0),     # Modern Defense
            BookMove("b7b6", 200, 80, 60, 60, 2170, 0),      # Tartakower Defense
        ]
        
        # Slav Defense (1.d4 d5 2.c4 c6 3.Nf3)
        fen_slav = "rnbqkbnr/pp2pppp/2p5/3p4/2PP4/5N2/PP2PPPP/RNBQKB1R b KQkq - 1 3"
        openings[fen_slav] = [
            BookMove("g8f6", 500, 200, 150, 150, 2190, 0),   # Main line Slav
            BookMove("d5c4", 300, 120, 90, 90, 2180, 0),     # Slav Gambit
            BookMove("c8f5", 250, 100, 75, 75, 2170, 0),     # Chameleon Variation
        ]
        
        # === DETAILED INDIAN DEFENSES ===
        
        # Queen's Indian Defense (1.d4 Nf6 2.c4 e6 3.Nf3 b6)
        fen_queens_indian = "rnbqkb1r/p1pp1ppp/1p2pn2/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4"
        openings[fen_queens_indian] = [
            BookMove("g2g3", 400, 160, 120, 120, 2190, 0),   # Fianchetto System
            BookMove("a2a3", 350, 140, 105, 105, 2180, 0),   # Petrosian System
            BookMove("b1c3", 300, 120, 90, 90, 2170, 0),     # Classical
        ]
        
        # Bogo-Indian Defense (1.d4 Nf6 2.c4 e6 3.Nf3 Bb4+)
        fen_bogo_indian = "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 2 4"
        openings[fen_bogo_indian] = [
            BookMove("b1d2", 400, 160, 120, 120, 2180, 0),   # Nimzowitsch Variation
            BookMove("c1d2", 350, 140, 105, 105, 2170, 0),   # Main line
            BookMove("b1c3", 250, 100, 75, 75, 2160, 0),     # Transposition to Nimzo
        ]
        
        # === DETAILED ENGLISH OPENING VARIATIONS ===
        
        # English Symmetrical (1.c4 c5 2.Nc3)
        fen_english_symm = "rnbqkbnr/pp1ppppp/8/2p5/2P5/2N5/PP1PPPPP/R1BQKBNR b KQkq - 2 2"
        openings[fen_english_symm] = [
            BookMove("b8c6", 400, 160, 120, 120, 2180, 0),   # Ultra-Symmetrical
            BookMove("g7g6", 350, 140, 105, 105, 2170, 0),   # Botvinnik System
            BookMove("g8f6", 300, 120, 90, 90, 2160, 0),     # Anglo-Indian
        ]
        
        # English Reversed Sicilian (1.c4 e5 2.Nc3)
        fen_english_rev_sic = "rnbqkbnr/pppp1ppp/8/4p3/2P5/2N5/PP1PPPPP/R1BQKBNR b KQkq - 2 2"
        openings[fen_english_rev_sic] = [
            BookMove("g8f6", 400, 160, 120, 120, 2180, 0),   # Four Knights
            BookMove("b8c6", 350, 140, 105, 105, 2170, 0),   # Closed System
            BookMove("f7f5", 250, 100, 75, 75, 2160, 0),     # King's Indian Attack
        ]
        
        # === GAMBIT OPENINGS ===
        
        # King's Gambit Accepted (1.e4 e5 2.f4 exf4)
        fen_kings_gambit = "rnbqkbnr/pppp1ppp/8/8/4Pp2/8/PPPP2PP/RNBQKBNR w KQkq - 0 3"
        openings[fen_kings_gambit] = [
            BookMove("g1f3", 400, 160, 120, 120, 2180, 0),   # King's Knight Gambit
            BookMove("f1c4", 350, 140, 105, 105, 2170, 0),   # Bishop's Gambit
            BookMove("b1c3", 200, 80, 60, 60, 2160, 0),      # Vienna Gambit
        ]
        
        # Queen's Gambit Accepted (1.d4 d5 2.c4 dxc4)
        fen_qga = "rnbqkbnr/ppp1pppp/8/8/2pP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3"
        openings[fen_qga] = [
            BookMove("g1f3", 500, 200, 150, 150, 2190, 0),   # Central Variation
            BookMove("e2e3", 300, 120, 90, 90, 2180, 0),     # Alekhine Defense
            BookMove("b1c3", 200, 80, 60, 60, 2170, 0),      # Mannheim Variation
        ]
        
        # === HYPERMODERN OPENINGS ===
        
        # Alekhine's Defense (1.e4 Nf6 2.e5)
        fen_alekhine = "rnbqkb1r/pppppppp/5n2/4P3/8/8/PPPP1PPP/RNBQKBNR b KQkq - 1 2"
        openings[fen_alekhine] = [
            BookMove("g8d5", 400, 160, 120, 120, 2170, 0),   # Modern Variation
            BookMove("g8h5", 200, 80, 60, 60, 2150, 0),      # Hunt Variation
            BookMove("g8g8", 150, 60, 45, 45, 2140, 0),      # Retreat Variation
        ]
        
        # Pirc Defense (1.e4 d6 2.d4 Nf6 3.Nc3 g6)
        fen_pirc = "rnbqkb1r/ppp1pp1p/3p1np1/8/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq - 0 4"
        openings[fen_pirc] = [
            BookMove("f2f3", 350, 140, 105, 105, 2170, 0),   # Austrian Attack
            BookMove("c1e3", 300, 120, 90, 90, 2160, 0),     # Classical System
            BookMove("g1f3", 250, 100, 75, 75, 2150, 0),     # Quiet development
        ]
        
        # === FLANK OPENINGS ===
        
        # Bird's Opening (1.f4 d5)
        fen_bird = "rnbqkbnr/ppp1pppp/8/3p4/5P2/8/PPPPP1PP/RNBQKBNR w KQkq d6 0 2"
        openings[fen_bird] = [
            BookMove("g1f3", 300, 120, 90, 90, 2140, 0),     # King's Indian Attack
            BookMove("e2e3", 250, 100, 75, 75, 2130, 0),     # Dutch System
            BookMove("b1c3", 200, 80, 60, 60, 2120, 0),      # From Gambit
        ]
        
        # Larsen's Opening (1.b3 e5)
        fen_larsen = "rnbqkbnr/pppp1ppp/8/4p3/8/1P6/P1PPPPPP/RNBQKBNR w KQkq e6 0 2"
        openings[fen_larsen] = [
            BookMove("c1b2", 300, 120, 90, 90, 2130, 0),     # Fianchetto
            BookMove("e2e3", 200, 80, 60, 60, 2120, 0),      # Modern System
            BookMove("g1f3", 150, 60, 45, 45, 2110, 0),      # Nimzo-Larsen Attack
        ]
        
        # === ADD MISSING CONTINUATIONS ===
        
        # After 1.d4 d5 - White's third move options
        fen_1d4_d5 = "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"
        openings[fen_1d4_d5] = [
            BookMove("c2c4", 600, 240, 180, 180, 2200, 0),   # Queen's Gambit
            BookMove("g1f3", 400, 160, 120, 120, 2180, 0),   # London System / Colle
            BookMove("c1f4", 300, 120, 90, 90, 2170, 0),     # London System
            BookMove("e2e3", 250, 100, 75, 75, 2160, 0),     # Colle System
            BookMove("b1c3", 200, 80, 60, 60, 2150, 0),      # Veresov Attack
        ]
        
        # After 1.d4 Nf6 - White's second move
        fen_1d4_nf6 = "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 1 2"
        openings[fen_1d4_nf6] = [
            BookMove("c2c4", 600, 240, 180, 180, 2200, 0),   # Indian Systems
            BookMove("g1f3", 400, 160, 120, 120, 2180, 0),   # Reti/Catalan
            BookMove("c1g5", 250, 100, 75, 75, 2170, 0),     # Trompowsky
            BookMove("b1c3", 200, 80, 60, 60, 2160, 0),      # Veresov
            BookMove("f2f3", 150, 60, 45, 45, 2150, 0),      # Gedult Attack
        ]
        
        # After 1.e4 e5 2.Nf3 Nc6 - White's third move
        fen_kings_knight = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        openings[fen_kings_knight] = [
            BookMove("f1b5", 500, 200, 150, 150, 2210, 0),   # Ruy Lopez
            BookMove("f1c4", 400, 160, 120, 120, 2200, 0),   # Italian Game
            BookMove("d2d4", 300, 120, 90, 90, 2190, 0),     # Scotch Game
            BookMove("b1c3", 250, 100, 75, 75, 2180, 0),     # Four Knights
            BookMove("f1e2", 200, 80, 60, 60, 2170, 0),      # Vienna Game
        ]
        
        # After 1.e4 c5 2.Nf3 d6 - White's third move
        fen_sicilian_najdorf_setup = "rnbqkbnr/pp2pppp/3p4/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
        openings[fen_sicilian_najdorf_setup] = [
            BookMove("d2d4", 600, 240, 180, 180, 2210, 0),   # Open Sicilian
            BookMove("f1b5", 200, 80, 60, 60, 2180, 0),      # Bb5+ variation
            BookMove("c2c3", 150, 60, 45, 45, 2170, 0),      # Alapin
            BookMove("b1c3", 300, 120, 90, 90, 2190, 0),     # Closed Sicilian
        ]
        
        # After 1.e4 c5 2.Nf3 Nc6 - White's third move
        fen_sicilian_nc6 = "r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        openings[fen_sicilian_nc6] = [
            BookMove("d2d4", 500, 200, 150, 150, 2210, 0),   # Open Sicilian
            BookMove("f1b5", 300, 120, 90, 90, 2190, 0),     # Bb5 Sicilian
            BookMove("b1c3", 250, 100, 75, 75, 2180, 0),     # Closed Sicilian
            BookMove("f1c4", 200, 80, 60, 60, 2170, 0),      # Grand Prix Attack setup
        ]
        
        # After 1.e4 e6 2.d4 d5 - White's third move
        fen_french_main = "rnbqkbnr/ppp2ppp/4p3/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"
        openings[fen_french_main] = [
            BookMove("b1c3", 400, 160, 120, 120, 2200, 0),   # Winawer/Classical
            BookMove("e4e5", 350, 140, 105, 105, 2190, 0),   # Advance Variation
            BookMove("e4d5", 300, 120, 90, 90, 2180, 0),     # Exchange Variation
            BookMove("b1d2", 250, 100, 75, 75, 2170, 0),     # Tarrasch Variation
        ]
        
        # After 1.e4 c6 2.d4 d5 - White's third move
        fen_caro_kann_main = "rnbqkbnr/pp2pppp/2p5/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3"
        openings[fen_caro_kann_main] = [
            BookMove("b1c3", 400, 160, 120, 120, 2190, 0),   # Main line
            BookMove("e4d5", 350, 140, 105, 105, 2180, 0),   # Exchange Variation
            BookMove("e4e5", 250, 100, 75, 75, 2170, 0),     # Advance Variation
            BookMove("f2f3", 200, 80, 60, 60, 2160, 0),      # Fantasy Variation
        ]
        
        # After 1.c4 e5 - White's second move
        fen_english_e5 = "rnbqkbnr/pppp1ppp/8/4p3/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 0 2"
        openings[fen_english_e5] = [
            BookMove("b1c3", 400, 160, 120, 120, 2180, 0),   # Closed English
            BookMove("g1f3", 350, 140, 105, 105, 2170, 0),   # King's English
            BookMove("g2g3", 250, 100, 75, 75, 2160, 0),     # Fianchetto
            BookMove("d2d3", 200, 80, 60, 60, 2150, 0),      # Great Snake
        ]
        
        # After 1.c4 Nf6 - White's second move
        fen_english_nf6 = "rnbqkb1r/pppppppp/5n2/8/2P5/8/PP1PPPPP/RNBQKBNR w KQkq - 1 2"
        openings[fen_english_nf6] = [
            BookMove("b1c3", 400, 160, 120, 120, 2180, 0),   # Anglo-Indian
            BookMove("g1f3", 350, 140, 105, 105, 2170, 0),   # Reti setup
            BookMove("d2d4", 300, 120, 90, 90, 2160, 0),     # Transpose to d4
            BookMove("g2g3", 250, 100, 75, 75, 2150, 0),     # Fianchetto
        ]
        
        # After 1.Nf3 d5 - White's second move
        fen_reti_d5 = "rnbqkbnr/ppp1pppp/8/3p4/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 0 2"
        openings[fen_reti_d5] = [
            BookMove("d2d4", 400, 160, 120, 120, 2180, 0),   # Transpose to QP
            BookMove("c2c4", 350, 140, 105, 105, 2170, 0),   # English setup
            BookMove("g2g3", 250, 100, 75, 75, 2160, 0),     # King's Indian Attack
            BookMove("e2e3", 200, 80, 60, 60, 2150, 0),      # Colle setup
        ]
        
        # After 1.Nf3 Nf6 - White's second move
        fen_reti_nf6 = "rnbqkb1r/pppppppp/5n2/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 2 2"
        openings[fen_reti_nf6] = [
            BookMove("c2c4", 400, 160, 120, 120, 2170, 0),   # English Opening
            BookMove("d2d4", 350, 140, 105, 105, 2160, 0),   # Transpose to QP
            BookMove("g2g3", 300, 120, 90, 90, 2150, 0),     # King's Indian Attack
            BookMove("b2b3", 200, 80, 60, 60, 2140, 0),      # Nimzo-Larsen
        ]
        
        # Add some deeper continuations for popular lines
        
        # Ruy Lopez Morphy Defense continued (1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6)
        fen_ruy_lopez_main = "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 5"
        openings[fen_ruy_lopez_main] = [
            BookMove("e1g1", 400, 160, 120, 120, 2210, 0),   # Castles
            BookMove("d2d3", 300, 120, 90, 90, 2200, 0),     # Steinitz Defense
            BookMove("b5c6", 200, 80, 60, 60, 2190, 0),      # Exchange Variation
        ]
        
        # Italian Game continued (1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5)
        fen_italian_main = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        openings[fen_italian_main] = [
            BookMove("c2c3", 400, 160, 120, 120, 2200, 0),   # Main line
            BookMove("d2d3", 300, 120, 90, 90, 2190, 0),     # Hungarian Defense
            BookMove("e1g1", 250, 100, 75, 75, 2180, 0),     # Castles
            BookMove("b2b4", 200, 80, 60, 60, 2170, 0),      # Evans Gambit
        ]
        
        # Queen's Gambit Declined continued (1.d4 d5 2.c4 e6 3.Nc3 Nf6)
        fen_qgd_main = "rnbqkb1r/ppp2ppp/4pn2/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq - 2 4"
        openings[fen_qgd_main] = [
            BookMove("c1g5", 400, 160, 120, 120, 2200, 0),   # Orthodox QGD
            BookMove("g1f3", 350, 140, 105, 105, 2190, 0),   # Quiet development
            BookMove("c4d5", 200, 80, 60, 60, 2180, 0),      # Exchange QGD
        ]
        
        logger.info(f"Added detailed variations and continuations, total positions: {len(openings)}")
    
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
        if not self.pgn_database:
            return
            
        try:
            # Get existing moves for this position
            existing_moves = self.pgn_database.get_moves(fen)
            move_dict = {m.move: m for m in existing_moves}
            
            # Create or update the move
            if move not in move_dict:
                move_dict[move] = BookMove(
                    move=move,
                    weight=0,
                    wins=0,
                    draws=0,
                    losses=0,
                    avg_rating=avg_rating,
                    last_played=0
                )
            
            book_move = move_dict[move]
            
            # Update statistics
            book_move.weight += 1
            
            # Update results (simplified - assumes move is from White's perspective)
            if result == '1-0':
                book_move.wins += 1
            elif result == '0-1':
                book_move.losses += 1
            elif result == '1/2-1/2':
                book_move.draws += 1
            
            # Update average rating (weighted average)
            if book_move.avg_rating > 0:
                book_move.avg_rating = (book_move.avg_rating * (book_move.weight - 1) + avg_rating) / book_move.weight
            else:
                book_move.avg_rating = avg_rating
            
            # Calculate depth from FEN (rough approximation)
            fen_parts = fen.split()
            move_number = int(fen_parts[5]) if len(fen_parts) > 5 else 1
            depth = (move_number - 1) * 2 + (1 if fen_parts[1] == 'b' else 0)
            
            # Update database
            self.pgn_database.add_position(fen, list(move_dict.values()), depth)
            
        except Exception as e:
            logger.error(f"Error updating position stats for {fen}: {e}")
    
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