# opening_database.py - ECO Opening Theory Database
import sqlite3
import json
import chess
import chess.pgn
from pathlib import Path

class OpeningDatabase:
    def __init__(self, db_path="data/openings.db"):
        self.db_path = db_path
        self.ensure_database()
        self.opening_cache = {}
        
    def ensure_database(self):
        """Create database and tables if they don't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS openings (
                    id INTEGER PRIMARY KEY,
                    eco_code TEXT,
                    name TEXT,
                    moves TEXT,
                    fen TEXT,
                    frequency INTEGER DEFAULT 0,
                    white_wins INTEGER DEFAULT 0,
                    black_wins INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    fen TEXT UNIQUE,
                    opening_id INTEGER,
                    move_number INTEGER,
                    is_theoretical BOOLEAN DEFAULT 1,
                    FOREIGN KEY (opening_id) REFERENCES openings (id)
                )
            ''')
            
            # Initialize with basic openings if empty
            if conn.execute("SELECT COUNT(*) FROM openings").fetchone()[0] == 0:
                self._populate_basic_openings(conn)
    
    def _populate_basic_openings(self, conn):
        """Add basic opening data"""
        basic_openings = [
            ("B00", "King's Pawn", "1.e4", 0),
            ("D00", "Queen's Pawn", "1.d4", 0),
            ("A00", "Uncommon Opening", "1.b3", 0),
            ("C20", "King's Pawn Game", "1.e4 e5", 0),
            ("C44", "Italian Game", "1.e4 e5 2.Nf3 Nc6 3.Bc4", 0),
            ("C50", "Italian Game", "1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5", 0),
            ("C65", "Ruy Lopez", "1.e4 e5 2.Nf3 Nc6 3.Bb5", 0),
            ("D20", "Queen's Gambit Accepted", "1.d4 d5 2.c4 dxc4", 0),
            ("D06", "Queen's Gambit", "1.d4 d5 2.c4", 0),
            ("E20", "Nimzo-Indian Defense", "1.d4 Nf6 2.c4 e6 3.Nc3 Bb4", 0),
        ]
        
        for eco, name, moves, freq in basic_openings:
            conn.execute(
                "INSERT INTO openings (eco_code, name, moves, frequency) VALUES (?, ?, ?, ?)",
                (eco, name, moves, freq)
            )
    
    def detect_opening(self, board):
        """Detect opening from current board position"""
        moves_str = self._board_to_moves_string(board)
        
        # Check cache first
        if moves_str in self.opening_cache:
            return self.opening_cache[moves_str]
        
        with sqlite3.connect(self.db_path) as conn:
            # Find longest matching opening
            cursor = conn.execute('''
                SELECT eco_code, name, moves FROM openings 
                WHERE ? LIKE moves || '%'
                ORDER BY LENGTH(moves) DESC
                LIMIT 1
            ''', (moves_str,))
            
            result = cursor.fetchone()
            if result:
                opening_info = {
                    'eco': result[0],
                    'name': result[1],
                    'moves': result[2],
                    'is_theoretical': True
                }
                self.opening_cache[moves_str] = opening_info
                return opening_info
        
        return None
    
    def get_book_moves(self, board):
        """Get theoretical book moves for current position"""
        fen = board.fen().split(' ')[0]  # Position only, ignore move counters
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT o.moves FROM openings o
                JOIN positions p ON o.id = p.opening_id
                WHERE p.fen = ? AND p.is_theoretical = 1
            ''', (fen,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def is_book_move(self, board, move):
        """Check if a move is a book move"""
        test_board = board.copy()
        test_board.push(move)
        
        book_moves = self.get_book_moves(board)
        move_san = board.san(move)
        
        for book_line in book_moves:
            if move_san in book_line:
                return True
        return False
    
    def get_opening_statistics(self, eco_code):
        """Get win/loss/draw statistics for an opening"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT white_wins, black_wins, draws, frequency
                FROM openings WHERE eco_code = ?
            ''', (eco_code,))
            
            result = cursor.fetchone()
            if result:
                total = sum(result[:3])
                if total > 0:
                    return {
                        'white_percentage': result[0] / total * 100,
                        'black_percentage': result[1] / total * 100,
                        'draw_percentage': result[2] / total * 100,
                        'frequency': result[3]
                    }
        return None
    
    def _board_to_moves_string(self, board):
        """Convert board to moves string"""
        moves = []
        temp_board = chess.Board()
        
        for move in board.move_stack:
            moves.append(temp_board.san(move))
            temp_board.push(move)
        
        # Format as "1.e4 e5 2.Nf3 Nc6" etc.
        formatted_moves = []
        for i, move in enumerate(moves):
            if i % 2 == 0:
                formatted_moves.append(f"{i//2 + 1}.{move}")
            else:
                formatted_moves.append(move)
        
        return " ".join(formatted_moves)
    
    def add_game_result(self, board, result):
        """Add game result to opening statistics"""
        opening = self.detect_opening(board)
        if not opening:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            if result == "1-0":  # White wins
                conn.execute(
                    "UPDATE openings SET white_wins = white_wins + 1, frequency = frequency + 1 WHERE eco_code = ?",
                    (opening['eco'],)
                )
            elif result == "0-1":  # Black wins
                conn.execute(
                    "UPDATE openings SET black_wins = black_wins + 1, frequency = frequency + 1 WHERE eco_code = ?",
                    (opening['eco'],)
                )
            elif result == "1/2-1/2":  # Draw
                conn.execute(
                    "UPDATE openings SET draws = draws + 1, frequency = frequency + 1 WHERE eco_code = ?",
                    (opening['eco'],)
                )