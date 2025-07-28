# [file name]: engine.py
# [file content begin]
from stockfish import Stockfish
import chess
import os

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
        
        self.engine = Stockfish(path=stockfish_path)
        self.set_skill_level(skill_level)
        self.set_depth(depth)
        self.board = chess.Board()
        
    def set_skill_level(self, level):
        self.engine.set_skill_level(level)
        
    def set_depth(self, depth):
        self.engine.set_depth(depth)
        
    def set_position(self, fen):
        self.engine.set_fen_position(fen)
        self.board = chess.Board(fen)
        
    def get_best_move(self):
        return self.engine.get_best_move()
    
    def get_evaluation(self):
        return self.engine.get_evaluation()
    
    def make_move(self, uci_move):
        self.board.push(chess.Move.from_uci(uci_move))
        
    def is_game_over(self):
        return self.board.is_game_over()
    
    def get_board_svg(self):
        return chess.svg.board(board=self.board)
    
    def reset(self):
        self.board.reset()
        self.engine.set_fen_position(self.board.fen())
# [file content end]