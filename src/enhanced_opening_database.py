# enhanced_opening_database.py - Comprehensive opening database with advanced features
import chess
import chess.pgn
import json
import os
import sqlite3
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from error_handling import safe_execute, logger
from resource_manager import resource_manager

class EnhancedOpeningDatabase:
    """Enhanced opening database with comprehensive ECO codes and statistics"""
    
    def __init__(self, db_path="data/enhanced_openings.db"):
        self.db_path = db_path
        self.opening_cache = {}
        self.position_cache = {}
        self.transposition_table = {}
        
        # Statistics
        self.stats = {
            'total_openings': 0,
            'total_positions': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Ensure database exists
        self._ensure_database()
        
        # Load comprehensive opening data
        self._load_comprehensive_openings()
    
    def _ensure_database(self):
        """Create enhanced database structure"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Main openings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS openings (
                    id INTEGER PRIMARY KEY,
                    eco_code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    variation TEXT,
                    moves TEXT NOT NULL,
                    fen TEXT NOT NULL,
                    move_count INTEGER,
                    frequency INTEGER DEFAULT 0,
                    white_wins INTEGER DEFAULT 0,
                    black_wins INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    avg_rating INTEGER DEFAULT 1500,
                    popularity_score REAL DEFAULT 0.0,
                    theoretical_depth INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Positions table for transpositions
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    fen TEXT UNIQUE NOT NULL,
                    opening_id INTEGER,
                    move_number INTEGER,
                    is_critical BOOLEAN DEFAULT 0,
                    evaluation REAL DEFAULT 0.0,
                    best_moves TEXT,
                    FOREIGN KEY (opening_id) REFERENCES openings (id)
                )
            ''')
            
            # Transpositions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transpositions (
                    id INTEGER PRIMARY KEY,
                    position_fen TEXT NOT NULL,
                    transposed_fen TEXT NOT NULL,
                    opening_id INTEGER,
                    move_order TEXT,
                    FOREIGN KEY (opening_id) REFERENCES openings (id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_eco_code ON openings (eco_code)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_fen ON positions (fen)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_opening_name ON openings (name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_popularity ON openings (popularity_score DESC)')
    
    def _load_comprehensive_openings(self):
        """Load comprehensive opening database"""
        comprehensive_openings = [
            # King's Pawn Openings (1.e4)
            {"eco": "B00", "name": "King's Pawn", "moves": "e2e4", "variation": ""},
            {"eco": "B01", "name": "Scandinavian Defense", "moves": "e2e4 d7d5", "variation": ""},
            {"eco": "B02", "name": "Alekhine's Defense", "moves": "e2e4 g8f6", "variation": ""},
            {"eco": "B03", "name": "Alekhine's Defense", "moves": "e2e4 g8f6 e4e5 f6d5", "variation": "Four Pawns Attack"},
            {"eco": "B04", "name": "Alekhine's Defense", "moves": "e2e4 g8f6 e4e5 f6d5 d2d4 d7d6", "variation": "Modern Variation"},
            {"eco": "B05", "name": "Alekhine's Defense", "moves": "e2e4 g8f6 e4e5 f6d5 d2d4 d7d6 g1f3", "variation": "Modern, Main Line"},
            
            # French Defense
            {"eco": "C00", "name": "French Defense", "moves": "e2e4 e7e6", "variation": ""},
            {"eco": "C01", "name": "French Defense", "moves": "e2e4 e7e6 d2d4 d7d5", "variation": "Exchange Variation"},
            {"eco": "C02", "name": "French Defense", "moves": "e2e4 e7e6 d2d4 d7d5 e4e5", "variation": "Advance Variation"},
            {"eco": "C03", "name": "French Defense", "moves": "e2e4 e7e6 d2d4 d7d5 b1d2", "variation": "Tarrasch Variation"},
            {"eco": "C04", "name": "French Defense", "moves": "e2e4 e7e6 d2d4 d7d5 b1d2 g8f6", "variation": "Tarrasch, Guimard Main Line"},
            {"eco": "C05", "name": "French Defense", "moves": "e2e4 e7e6 d2d4 d7d5 b1d2 g8f6 e4e5", "variation": "Tarrasch, Closed Variation"},
            
            # Caro-Kann Defense
            {"eco": "B10", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6", "variation": ""},
            {"eco": "B11", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 b1c3", "variation": "Two Knights Variation"},
            {"eco": "B12", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5", "variation": ""},
            {"eco": "B13", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 e4d5", "variation": "Exchange Variation"},
            {"eco": "B14", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 e4d5 c6d5", "variation": "Panov-Botvinnik Attack"},
            {"eco": "B15", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 b1c3", "variation": ""},
            {"eco": "B16", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4", "variation": "Bronstein-Larsen Variation"},
            {"eco": "B17", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4", "variation": "Steinitz Variation"},
            {"eco": "B18", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 f8f5", "variation": "Classical Variation"},
            {"eco": "B19", "name": "Caro-Kann Defense", "moves": "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 f8f5 e4g3 f5g6", "variation": "Classical, Spassky System"},
            
            # Sicilian Defense
            {"eco": "B20", "name": "Sicilian Defense", "moves": "e2e4 c7c5", "variation": ""},
            {"eco": "B21", "name": "Sicilian Defense", "moves": "e2e4 c7c5 f2f4", "variation": "Grand Prix Attack"},
            {"eco": "B22", "name": "Sicilian Defense", "moves": "e2e4 c7c5 c2c3", "variation": "Alapin Variation"},
            {"eco": "B23", "name": "Sicilian Defense", "moves": "e2e4 c7c5 b1c3", "variation": "Closed Variation"},
            {"eco": "B24", "name": "Sicilian Defense", "moves": "e2e4 c7c5 b1c3 b8c6", "variation": "Closed, Traditional"},
            {"eco": "B25", "name": "Sicilian Defense", "moves": "e2e4 c7c5 b1c3 b8c6 g2g3", "variation": "Closed, Botvinnik System"},
            {"eco": "B26", "name": "Sicilian Defense", "moves": "e2e4 c7c5 b1c3 b8c6 g2g3 g7g6", "variation": "Closed, 6.Be3"},
            {"eco": "B27", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3", "variation": ""},
            {"eco": "B28", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 a7a6", "variation": "O'Kelly Variation"},
            {"eco": "B29", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 g8f6", "variation": "Nimzowitsch Variation"},
            
            # Sicilian Dragon
            {"eco": "B70", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6", "variation": "Dragon Variation"},
            {"eco": "B71", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6 f2f4", "variation": "Dragon, Levenfish Attack"},
            {"eco": "B72", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6 c1e3", "variation": "Dragon, 6.Be3"},
            {"eco": "B73", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6 c1e3 f8g7", "variation": "Dragon, Classical"},
            {"eco": "B74", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6 c1e3 f8g7 f2f3", "variation": "Dragon, Classical, 9.f3"},
            {"eco": "B75", "name": "Sicilian Defense", "moves": "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 g7g6 c1e3 f8g7 f2f3 e8g8", "variation": "Dragon, Yugoslav Attack"},
            
            # Italian Game
            {"eco": "C50", "name": "Italian Game", "moves": "e2e4 e7e5 g1f3 b8c6 f1c4", "variation": ""},
            {"eco": "C51", "name": "Italian Game", "moves": "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5", "variation": "Evans Gambit"},
            {"eco": "C52", "name": "Italian Game", "moves": "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 b2b4", "variation": "Evans Gambit Accepted"},
            {"eco": "C53", "name": "Italian Game", "moves": "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3", "variation": "Classical Variation"},
            {"eco": "C54", "name": "Italian Game", "moves": "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 c2c3 g8f6", "variation": "Classical, Giuoco Piano"},
            
            # Spanish Opening (Ruy Lopez)
            {"eco": "C60", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5", "variation": "Ruy Lopez"},
            {"eco": "C61", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 f8d6", "variation": "Bird's Defense"},
            {"eco": "C62", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 d7d6", "variation": "Steinitz Defense"},
            {"eco": "C63", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 f7f5", "variation": "Schliemann Defense"},
            {"eco": "C64", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 f8c5", "variation": "Classical Defense"},
            {"eco": "C65", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 g8f6", "variation": "Berlin Defense"},
            {"eco": "C66", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 g8f6 e1g1", "variation": "Berlin Defense, Improved Steinitz Defense"},
            {"eco": "C67", "name": "Spanish Opening", "moves": "e2e4 e7e5 g1f3 b8c6 f1b5 g8f6 e1g1 f6e4", "variation": "Berlin Defense, Rio Gambit"},
            
            # Queen's Pawn Openings (1.d4)
            {"eco": "D00", "name": "Queen's Pawn", "moves": "d2d4", "variation": ""},
            {"eco": "D01", "name": "Queen's Pawn", "moves": "d2d4 g8f6 b1c3", "variation": "Richter-Veresov Attack"},
            {"eco": "D02", "name": "Queen's Pawn", "moves": "d2d4 g8f6 g1f3 e7e6", "variation": "London System"},
            {"eco": "D03", "name": "Queen's Pawn", "moves": "d2d4 g8f6 g1f3 g7g6", "variation": "Torre Attack"},
            {"eco": "D04", "name": "Queen's Pawn", "moves": "d2d4 g8f6 g1f3 e7e6 c1g5", "variation": "Colle System"},
            {"eco": "D05", "name": "Queen's Pawn", "moves": "d2d4 g8f6 g1f3 e7e6 e2e3", "variation": "Colle System"},
            
            # Queen's Gambit
            {"eco": "D06", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4", "variation": ""},
            {"eco": "D07", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 b8c6", "variation": "Chigorin Defense"},
            {"eco": "D08", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 e7e5", "variation": "Albin Counter-Gambit"},
            {"eco": "D09", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 e7e5 d4e5 d5d4", "variation": "Albin Counter-Gambit, 5.dxe5"},
            {"eco": "D10", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6", "variation": "Slav Defense"},
            {"eco": "D11", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6 g1f3", "variation": "Slav Defense, 3.Nf3"},
            {"eco": "D12", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6", "variation": "Slav Defense, 4.Nf6"},
            {"eco": "D13", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 c4d5", "variation": "Slav Defense, Exchange Variation"},
            {"eco": "D14", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 c4d5 c6d5", "variation": "Slav Defense, Exchange, 5.cxd5 cxd5"},
            {"eco": "D15", "name": "Queen's Gambit", "moves": "d2d4 d7d5 c2c4 c7c6 g1f3 g8f6 b1c3", "variation": "Slav Defense, 4.Nc3"},
            
            # King's Indian Defense
            {"eco": "E60", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6", "variation": ""},
            {"eco": "E61", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6 b1c3", "variation": ""},
            {"eco": "E62", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7", "variation": "Fianchetto Variation"},
            {"eco": "E63", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 g1f3", "variation": "Fianchetto, Panno Variation"},
            {"eco": "E64", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 g1f3 e8g8", "variation": "Fianchetto, Yugoslav System"},
            {"eco": "E65", "name": "King's Indian Defense", "moves": "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 g1f3 e8g8 g2g3", "variation": "Fianchetto, Yugoslav, 7.0-0"},
            
            # Nimzo-Indian Defense
            {"eco": "E20", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4", "variation": ""},
            {"eco": "E21", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 g1f3", "variation": "Three Knights Variation"},
            {"eco": "E22", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 d1b3", "variation": "Spielmann Variation"},
            {"eco": "E23", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 d1c2", "variation": "Saemisch Variation"},
            {"eco": "E24", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 a2a3", "variation": "Saemisch, Accelerated"},
            {"eco": "E25", "name": "Nimzo-Indian Defense", "moves": "d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 a2a3 b4c3", "variation": "Saemisch, Keres Variation"},
            
            # English Opening
            {"eco": "A10", "name": "English Opening", "moves": "c2c4", "variation": ""},
            {"eco": "A11", "name": "English Opening", "moves": "c2c4 c7c6", "variation": "Caro-Kann Defensive System"},
            {"eco": "A12", "name": "English Opening", "moves": "c2c4 c7c6 g1f3", "variation": "Caro-Kann Defensive System, 2.Nf3"},
            {"eco": "A13", "name": "English Opening", "moves": "c2c4 e7e6", "variation": ""},
            {"eco": "A14", "name": "English Opening", "moves": "c2c4 e7e6 g1f3", "variation": "Neo-Catalan"},
            {"eco": "A15", "name": "English Opening", "moves": "c2c4 g8f6", "variation": "Anglo-Indian Defense"},
            {"eco": "A16", "name": "English Opening", "moves": "c2c4 g8f6 b1c3", "variation": "Anglo-Indian, Queen's Knight Variation"},
            {"eco": "A17", "name": "English Opening", "moves": "c2c4 g8f6 b1c3 e7e6", "variation": "Anglo-Indian, Hedgehog System"},
            {"eco": "A18", "name": "English Opening", "moves": "c2c4 g8f6 b1c3 e7e6 e2e4", "variation": "Mikenas-Carls Variation"},
            {"eco": "A19", "name": "English Opening", "moves": "c2c4 g8f6 b1c3 e7e6 e2e4 c7c5", "variation": "Mikenas-Carls, Sicilian Variation"},
            
            # Flank Openings
            {"eco": "A00", "name": "Irregular Opening", "moves": "", "variation": ""},
            {"eco": "A01", "name": "Nimzowitsch-Larsen Attack", "moves": "b2b3", "variation": ""},
            {"eco": "A02", "name": "Bird's Opening", "moves": "f2f4", "variation": ""},
            {"eco": "A03", "name": "Bird's Opening", "moves": "f2f4 d7d5", "variation": ""},
            {"eco": "A04", "name": "Reti Opening", "moves": "g1f3", "variation": ""},
            {"eco": "A05", "name": "Reti Opening", "moves": "g1f3 g8f6", "variation": ""},
            {"eco": "A06", "name": "Reti Opening", "moves": "g1f3 d7d5", "variation": ""},
            {"eco": "A07", "name": "King's Indian Attack", "moves": "g1f3 d7d5 g2g3", "variation": ""},
            {"eco": "A08", "name": "King's Indian Attack", "moves": "g1f3 d7d5 g2g3 c7c5", "variation": ""},
            {"eco": "A09", "name": "Reti Opening", "moves": "g1f3 d7d5 c2c4", "variation": ""},
        ]
        
        # Insert openings into database
        with sqlite3.connect(self.db_path) as conn:
            for opening in comprehensive_openings:
                try:
                    # Calculate FEN position after moves
                    board = chess.Board()
                    moves = opening["moves"].split() if opening["moves"] else []
                    
                    for move_str in moves:
                        try:
                            move = chess.Move.from_uci(move_str)
                            if move in board.legal_moves:
                                board.push(move)
                        except:
                            continue
                    
                    fen = board.fen()
                    move_count = len(moves)
                    
                    # Calculate popularity score (simplified)
                    popularity = self._calculate_popularity_score(opening["eco"], opening["name"])
                    
                    conn.execute('''
                        INSERT OR REPLACE INTO openings 
                        (eco_code, name, variation, moves, fen, move_count, popularity_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (opening["eco"], opening["name"], opening["variation"], 
                          opening["moves"], fen, move_count, popularity))
                    
                    # Insert position
                    conn.execute('''
                        INSERT OR REPLACE INTO positions (fen, opening_id, move_number)
                        VALUES (?, last_insert_rowid(), ?)
                    ''', (fen, move_count))
                    
                except Exception as e:
                    logger.warning(f"Failed to insert opening {opening['name']}: {e}")
            
            conn.commit()
        
        # Update statistics
        self._update_stats()
        logger.info(f"Loaded {self.stats['total_openings']} openings into database")
    
    def _calculate_popularity_score(self, eco_code: str, name: str) -> float:
        """Calculate popularity score based on opening characteristics"""
        # Popular openings get higher scores
        popular_openings = {
            "Sicilian Defense": 9.5,
            "French Defense": 8.5,
            "Caro-Kann Defense": 8.0,
            "Spanish Opening": 9.0,
            "Italian Game": 7.5,
            "Queen's Gambit": 9.0,
            "King's Indian Defense": 8.5,
            "Nimzo-Indian Defense": 8.0,
            "English Opening": 7.0,
            "Reti Opening": 6.5
        }
        
        base_score = popular_openings.get(name, 5.0)
        
        # Adjust based on ECO code (earlier codes are often more fundamental)
        if eco_code.startswith('A'):
            base_score *= 0.8  # Flank openings less popular
        elif eco_code.startswith('B'):
            base_score *= 1.1  # King's pawn openings popular
        elif eco_code.startswith('C'):
            base_score *= 1.2  # Classical openings very popular
        elif eco_code.startswith('D'):
            base_score *= 1.1  # Queen's pawn openings popular
        elif eco_code.startswith('E'):
            base_score *= 1.0  # Indian defenses moderately popular
        
        return min(base_score, 10.0)
    
    def _update_stats(self):
        """Update database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM openings")
            self.stats['total_openings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM positions")
            self.stats['total_positions'] = cursor.fetchone()[0]
    
    @safe_execute(fallback_value=None, context="detect_opening")
    def detect_opening(self, board: chess.Board) -> Optional[Dict]:
        """Detect opening from current board position"""
        fen = board.fen().split(' ')[0]  # Position only, ignore move counters
        
        # Check cache first
        if fen in self.position_cache:
            self.stats['cache_hits'] += 1
            return self.position_cache[fen]
        
        self.stats['cache_misses'] += 1
        
        # Search database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Try exact FEN match first
            cursor.execute('''
                SELECT o.eco_code, o.name, o.variation, o.moves, o.popularity_score
                FROM openings o
                JOIN positions p ON o.id = p.opening_id
                WHERE p.fen LIKE ?
                ORDER BY o.popularity_score DESC, o.move_count DESC
                LIMIT 1
            ''', (f"{fen}%",))
            
            result = cursor.fetchone()
            
            if result:
                opening_data = {
                    'eco': result[0],
                    'name': result[1],
                    'variation': result[2] or '',
                    'moves': result[3],
                    'popularity': result[4],
                    'full_name': f"{result[1]}" + (f", {result[2]}" if result[2] else "")
                }
                
                # Cache result
                self.position_cache[fen] = opening_data
                return opening_data
        
        # Try transposition detection
        transposed_opening = self._detect_transposition(board)
        if transposed_opening:
            self.position_cache[fen] = transposed_opening
            return transposed_opening
        
        return None
    
    def _detect_transposition(self, board: chess.Board) -> Optional[Dict]:
        """Detect opening through transposition"""
        # This is a simplified transposition detection
        # In a full implementation, you'd check various move orders
        
        # Get all pieces and their positions
        piece_positions = {}
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_key = f"{piece.symbol()}"
                if piece_key not in piece_positions:
                    piece_positions[piece_key] = []
                piece_positions[piece_key].append(chess.square_name(square))
        
        # Create a normalized position signature
        signature = []
        for piece_type in ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']:
            if piece_type in piece_positions:
                signature.append(f"{piece_type}:{''.join(sorted(piece_positions[piece_type]))}")
        
        signature_str = '|'.join(signature)
        
        # This is where you'd implement more sophisticated transposition detection
        # For now, return None
        return None
    
    def get_opening_statistics(self, eco_code: str = None) -> Dict:
        """Get opening statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if eco_code:
                cursor.execute('''
                    SELECT name, variation, frequency, white_wins, black_wins, draws, popularity_score
                    FROM openings WHERE eco_code = ?
                ''', (eco_code,))
                result = cursor.fetchone()
                
                if result:
                    total_games = result[2] + result[3] + result[4]
                    return {
                        'name': result[0],
                        'variation': result[1],
                        'total_games': total_games,
                        'white_wins': result[2],
                        'black_wins': result[3],
                        'draws': result[4],
                        'white_percentage': (result[2] / total_games * 100) if total_games > 0 else 0,
                        'popularity': result[6]
                    }
            
            return self.stats.copy()
    
    def get_popular_openings(self, limit: int = 10) -> List[Dict]:
        """Get most popular openings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT eco_code, name, variation, popularity_score, move_count
                FROM openings
                ORDER BY popularity_score DESC, move_count ASC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            return [
                {
                    'eco': row[0],
                    'name': row[1],
                    'variation': row[2] or '',
                    'popularity': row[3],
                    'moves': row[4],
                    'full_name': f"{row[1]}" + (f", {row[2]}" if row[2] else "")
                }
                for row in results
            ]
    
    def search_openings(self, query: str) -> List[Dict]:
        """Search openings by name or ECO code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT eco_code, name, variation, popularity_score
                FROM openings
                WHERE name LIKE ? OR eco_code LIKE ? OR variation LIKE ?
                ORDER BY popularity_score DESC
                LIMIT 20
            ''', (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            results = cursor.fetchall()
            return [
                {
                    'eco': row[0],
                    'name': row[1],
                    'variation': row[2] or '',
                    'popularity': row[3],
                    'full_name': f"{row[1]}" + (f", {row[2]}" if row[2] else "")
                }
                for row in results
            ]
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.position_cache),
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': hit_rate,
            'total_openings': self.stats['total_openings'],
            'total_positions': self.stats['total_positions']
        }
    
    def cleanup_cache(self):
        """Clean up caches to free memory"""
        self.position_cache.clear()
        self.opening_cache.clear()
        logger.info("Opening database caches cleared")

# Global enhanced opening database instance
enhanced_opening_db = EnhancedOpeningDatabase()