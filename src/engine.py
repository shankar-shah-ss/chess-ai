# [file name]: engine.py
# [file content begin]
from stockfish import Stockfish
import chess
import os
import time

class ChessEngine:
    def __init__(self, skill_level=10, depth=15):
        # Try to locate Stockfish
        stockfish_path = None
        
        # Common paths for different platforms
        possible_paths = [
            "stockfish",  # Linux/macOS (if in PATH)
            "stockfish.exe",  # Windows (if in PATH)
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/usr/games/stockfish",  # Common Linux path
            "/opt/homebrew/bin/stockfish",
            "C:/Program Files/Stockfish/stockfish.exe",
            os.path.expanduser("~/stockfish/stockfish.exe"),
        ]
        
        # Check environment variable
        if "STOCKFISH_PATH" in os.environ:
            stockfish_path = os.environ["STOCKFISH_PATH"]
        else:
            # Check possible paths
            for path in possible_paths:
                if os.path.exists(path):
                    stockfish_path = path
                    break
        
        if stockfish_path is None:
            raise Exception("Stockfish not found. Please set STOCKFISH_PATH environment variable.")
        
        self.stockfish_path = stockfish_path  # Store for recovery
        self.engine = self._create_engine(skill_level, depth)
        self.board = chess.Board()
        self.last_fen = None  # Track last valid position
        
    def _create_engine(self, skill_level, depth):
        """Create a new engine instance with proper error handling"""
        try:
            engine = Stockfish(path=self.stockfish_path)
            engine.set_skill_level(skill_level)
            engine.set_depth(depth)
            return engine
        except Exception as e:
            print(f"Engine creation failed: {e}")
            raise
        
    def set_skill_level(self, level):
        try:
            self.engine.set_skill_level(level)
        except:
            self._recover_engine()
            self.engine.set_skill_level(level)
        
    def set_depth(self, depth):
        try:
            self.engine.set_depth(depth)
        except:
            self._recover_engine()
            self.engine.set_depth(depth)
        
    def set_position(self, fen):
        self.last_fen = fen  # Store last valid FEN
        try:
            self.engine.set_fen_position(fen)
            self.board = chess.Board(fen)
        except:
            self._recover_engine()
            self.engine.set_fen_position(fen)
            self.board = chess.Board(fen)
        
    def get_best_move(self):
        try:
            return self.engine.get_best_move()
        except:
            self._recover_engine()
            return self.engine.get_best_move()
    
    def get_evaluation(self):
        try:
            return self.engine.get_evaluation()
        except:
            self._recover_engine()
            return self.engine.get_evaluation()
    
    def make_move(self, uci_move):
        try:
            self.board.push(chess.Move.from_uci(uci_move))
        except:
            self._recover_engine()
        
    def is_game_over(self):
        try:
            return self.board.is_game_over()
        except:
            self._recover_engine()
            return self.board.is_game_over()
    
    def get_board_svg(self):
        return chess.svg.board(board=self.board)
    
    def reset(self):
        try:
            self.board.reset()
            self.engine.set_fen_position(self.board.fen())
            self.last_fen = self.board.fen()
        except:
            self._recover_engine()
            
    def _recover_engine(self):
        """Recover from engine crashes by recreating the instance"""
        print("Recovering crashed engine...")
        try:
            # Clean up old engine
            if hasattr(self.engine, '_stockfish'):
                try:
                    self.engine._stockfish.terminate()
                except:
                    pass
        except:
            pass
        
        # Create new engine instance
        self.engine = self._create_engine(self.engine.get_parameters()['Skill Level'], 
                                         self.engine.get_parameters()['Depth'])
        
        # Restore last known position
        if self.last_fen:
            try:
                self.engine.set_fen_position(self.last_fen)
                self.board = chess.Board(self.last_fen)
            except:
                # Fallback to starting position
                self.engine.set_fen_position(chess.STARTING_FEN)
                self.board = chess.Board()
                self.last_fen = chess.STARTING_FEN
# [file content end]