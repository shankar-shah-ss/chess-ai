# [file name]: engine.py
# [file content begin]
from stockfish import Stockfish
import chess
import os
import time
import threading

class ChessEngine:
    def __init__(self, skill_level=10, depth=15):
        self.skill_level = skill_level
        self.depth = depth
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
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
        self.engine_lock = threading.Lock()
        self.engine = self._create_engine(skill_level, depth)
        self.board = chess.Board()
        self.last_fen = None  # Track last valid position
        
    def _create_engine(self, skill_level, depth):
        """Create a new engine instance with proper error handling"""
        try:
            with self.engine_lock:
                engine = Stockfish(path=self.stockfish_path)
                
                # Configure for maximum strength at level 20
                if skill_level >= 20:
                    # UNLIMITED STRENGTH MODE
                    # 1. No skill level limitation
                    # 2. Use maximum depth or unlimited if depth >= 20
                    # 3. Enable multi-threading
                    # 4. Set longer thinking time
                    
                    if depth >= 20:
                        # Unlimited depth - let engine decide
                        engine.set_depth(0)  # 0 = unlimited depth in Stockfish
                    else:
                        engine.set_depth(depth)
                        
                    # Configure for maximum performance
                    try:
                        # Enable multi-threading (use fewer threads to avoid delays)
                        engine._stockfish.stdin.write("setoption name Threads value 2\n")
                        engine._stockfish.stdin.flush()
                        # Use hash table for better performance
                        engine._stockfish.stdin.write("setoption name Hash value 128\n")
                        engine._stockfish.stdin.flush()
                    except:
                        pass  # Ignore if options not supported
                        
                    print(f"Engine configured for UNLIMITED STRENGTH (level {skill_level})")
                else:
                    # Normal skill level mode
                    engine.set_skill_level(skill_level)
                    engine.set_depth(depth)
                    
                return engine
        except Exception as e:
            print(f"Engine creation failed: {e}")
            raise
        
    def set_skill_level(self, level):
        self.skill_level = level
        with self.engine_lock:
            if not self.engine:
                return
            try:
                if level >= 20:
                    # UNLIMITED STRENGTH MODE
                    print(f"Engine set to UNLIMITED STRENGTH (level {level})")
                    
                    # Configure unlimited depth if current depth is also max
                    if self.depth >= 20:
                        self.engine.set_depth(0)  # Unlimited depth
                        
                    # Set performance options
                    try:
                        self.engine._stockfish.stdin.write("setoption name Threads value 2\n")
                        self.engine._stockfish.stdin.flush()
                        self.engine._stockfish.stdin.write("setoption name Hash value 128\n")
                        self.engine._stockfish.stdin.flush()
                    except:
                        pass
                else:
                    self.engine.set_skill_level(level)
            except Exception as e:
                print(f"Error setting skill level: {e}")
                self._recover_engine()
                if self.engine:
                    try:
                        if level >= 20:
                            print(f"Engine set to UNLIMITED STRENGTH (level {level}) after recovery")
                        else:
                            self.engine.set_skill_level(level)
                    except Exception as e2:
                        print(f"Failed to set skill level after recovery: {e2}")
        
    def set_depth(self, depth):
        self.depth = depth
        with self.engine_lock:
            if not self.engine:
                return
            try:
                # If at maximum level and depth, use unlimited depth
                if self.skill_level >= 20 and depth >= 20:
                    self.engine.set_depth(0)  # 0 = unlimited depth
                    print(f"Engine set to UNLIMITED DEPTH (depth {depth})")
                else:
                    self.engine.set_depth(depth)
            except Exception as e:
                print(f"Error setting depth: {e}")
                self._recover_engine()
                if self.engine:
                    try:
                        if self.skill_level >= 20 and depth >= 20:
                            self.engine.set_depth(0)
                            print(f"Engine set to UNLIMITED DEPTH (depth {depth}) after recovery")
                        else:
                            self.engine.set_depth(depth)
                    except Exception as e2:
                        print(f"Failed to set depth after recovery: {e2}")
        
    def set_position(self, fen):
        # Validate FEN before using
        try:
            chess.Board(fen)  # Test if FEN is valid
        except Exception as e:
            print(f"Invalid FEN: {fen}, error: {e}")
            return False
            
        self.last_fen = fen  # Store last valid FEN
        with self.engine_lock:
            if not self.engine:
                return False
            try:
                self.engine.set_fen_position(fen)
                self.board = chess.Board(fen)
                return True
            except Exception as e:
                print(f"Error setting position: {e}")
                self._recover_engine()
                if self.engine:
                    try:
                        self.engine.set_fen_position(fen)
                        self.board = chess.Board(fen)
                        return True
                    except Exception as e2:
                        print(f"Failed to set position after recovery: {e2}")
                        return False
                return False
        
    def get_best_move(self):
        with self.engine_lock:
            if not self.engine:
                return None
            try:
                move = self.engine.get_best_move()
                if move is None:
                    print("Engine returned None for best move")
                return move
            except Exception as e:
                print(f"Error getting best move: {e}")
                self._recover_engine()
                if self.engine:
                    try:
                        return self.engine.get_best_move()
                    except Exception as e2:
                        print(f"Failed to get best move after recovery: {e2}")
                        return None
                return None
    
    def get_evaluation(self):
        with self.engine_lock:
            if not self.engine:
                return None
            try:
                eval_result = self.engine.get_evaluation()
                if eval_result is None:
                    print("Engine returned None for evaluation")
                return eval_result
            except Exception as e:
                print(f"Error getting evaluation: {e}")
                self._recover_engine()
                if self.engine:
                    try:
                        return self.engine.get_evaluation()
                    except Exception as e2:
                        print(f"Failed to get evaluation after recovery: {e2}")
                        return None
                return None
    
    def make_move(self, uci_move):
        with self.engine_lock:
            try:
                self.board.push(chess.Move.from_uci(uci_move))
            except:
                self._recover_engine()
        
    def is_game_over(self):
        with self.engine_lock:
            try:
                return self.board.is_game_over()
            except:
                self._recover_engine()
                return self.board.is_game_over()
    
    def get_board_svg(self):
        with self.engine_lock:
            return chess.svg.board(board=self.board)
    
    def reset(self):
        with self.engine_lock:
            try:
                self.board.reset()
                self.engine.set_fen_position(self.board.fen())
                self.last_fen = self.board.fen()
            except:
                self._recover_engine()
                
    def _recover_engine(self):
        """Recover from engine crashes by recreating the instance"""
        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            print(f"Max recovery attempts ({self.max_recovery_attempts}) reached. Disabling engine.")
            self.engine = None
            return
            
        print(f"Recovering crashed engine... (attempt {self.recovery_attempts})")
        try:
            # Clean up old engine
            if hasattr(self.engine, '_stockfish'):
                try:
                    self.engine._stockfish.terminate()
                except:
                    pass
        except:
            pass
        
        try:
            # Create new engine instance with stored values
            self.engine = self._create_engine(self.skill_level, self.depth)
            
            # Restore last known position
            if self.last_fen:
                self.engine.set_fen_position(self.last_fen)
                self.board = chess.Board(self.last_fen)
            else:
                # Fallback to starting position
                self.engine.set_fen_position(chess.STARTING_FEN)
                self.board = chess.Board()
                self.last_fen = chess.STARTING_FEN
                
            # Reset recovery counter on success
            self.recovery_attempts = 0
        except Exception as e:
            print(f"Engine recovery failed: {e}")
            if self.recovery_attempts >= self.max_recovery_attempts:
                self.engine = None
# [file content end]