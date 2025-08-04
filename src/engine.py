# engine.py - Enhanced version with improved thread safety and resource management
from stockfish import Stockfish
from chess import Board, Move, STARTING_FEN
from os import environ, path, cpu_count
from os.path import exists, expanduser
import time
from threading import RLock, Lock
import weakref
from typing import Optional, Dict, Any
from logging import basicConfig, getLogger, INFO

# Configure logging for engine
basicConfig(level=INFO)
logger = getLogger(__name__)

class EnginePool:
    """Singleton engine pool for better resource management"""
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._engines = weakref.WeakSet()
                    cls._instance._initialized = False
        return cls._instance
    
    def register_engine(self, engine):
        """Register engine for cleanup tracking"""
        self._engines.add(engine)
    
    def cleanup_all(self):
        """Cleanup all registered engines"""
        for engine in list(self._engines):
            try:
                engine.cleanup()
            except:
                pass

class ChessEngine:
    def __init__(self, skill_level=10, depth=15):
        self.skill_level = skill_level
        self.depth = depth
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self._is_healthy = True
        self._last_health_check = 0
        self._cleanup_registered = False
        
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
            expanduser("~/stockfish/stockfish.exe"),
        ]
        
        # Check environment variable
        if "STOCKFISH_PATH" in environ:
            stockfish_path = environ["STOCKFISH_PATH"]
        else:
            # Check possible paths
            for possible_path in possible_paths:
                if exists(possible_path):
                    stockfish_path = possible_path
                    break
        
        if stockfish_path is None:
            raise Exception("Stockfish not found. Please set STOCKFISH_PATH environment variable.")
        
        self.stockfish_path = stockfish_path  # Store for recovery
        self.engine_lock = RLock()  # Use RLock for nested locking
        self.engine = self._create_engine(skill_level, depth)
        self.board = Board()
        self.last_fen = STARTING_FEN  # Track last valid position
        
        # Register with engine pool for cleanup
        EnginePool().register_engine(self)
        self._cleanup_registered = True
        
    def _test_engine_health(self, engine):
        """Test if engine is responsive"""
        try:
            engine.set_fen_position(STARTING_FEN)
            return engine.get_best_move() is not None
        except:
            return False
    
    def _check_engine_health(self):
        """Check engine health with throttling"""
        current_time = time.time()
        if current_time - self._last_health_check < 5:  # Check every 5 seconds max
            return self._is_healthy
        
        self._last_health_check = current_time
        if self.engine:
            self._is_healthy = self._test_engine_health(self.engine)
        return self._is_healthy
        
    def _create_engine(self, skill_level, depth):
        """Create a new engine instance with proper error handling"""
        try:
            engine = Stockfish(path=self.stockfish_path)
            if not engine or not self._test_engine_health(engine):
                raise Exception("Engine failed health check")
                
            # Configure for maximum strength at level 20 (with reasonable limits)
            if skill_level >= 20:
                if depth >= 20:
                    # Cap maximum depth to prevent infinite thinking
                    max_depth = min(depth, 25)  # Maximum 25 ply depth
                    engine.set_depth(max_depth)
                    print(f"Engine configured for MAXIMUM STRENGTH (level {skill_level}, depth {max_depth})")
                else:
                    engine.set_depth(depth)
                    print(f"Engine configured for HIGH STRENGTH (level {skill_level}, depth {depth})")
                    
                # Configure for maximum performance using safe methods
                self._configure_engine_options(engine)
            else:
                # Normal skill level mode
                engine.set_skill_level(skill_level)
                engine.set_depth(depth)
                
            self._is_healthy = True
            return engine
        except Exception as e:
            print(f"Engine creation failed: {e}")
            self._is_healthy = False
            raise
    
    def _configure_engine_options(self, engine):
        """Configure engine for maximum multi-core performance"""
        cores = cpu_count() or 4  # Fallback to 4 if detection fails
        
        try:
            if hasattr(engine, '_stockfish') and engine._stockfish:
                try:
                    # Use all available CPU cores
                    engine._stockfish.stdin.write(f"setoption name Threads value {cores}\n")
                    engine._stockfish.stdin.flush()
                    
                    # Increase hash table size for better performance (MB)
                    hash_size = min(512, cores * 64)  # Scale with cores, max 512MB
                    engine._stockfish.stdin.write(f"setoption name Hash value {hash_size}\n")
                    engine._stockfish.stdin.flush()
                    
                    # Enable multi-PV for parallel analysis
                    engine._stockfish.stdin.write("setoption name MultiPV value 1\n")
                    engine._stockfish.stdin.flush()
                    
                    # Optimize for analysis
                    engine._stockfish.stdin.write("setoption name Contempt value 0\n")
                    engine._stockfish.stdin.flush()
                    
                    logger.info(f"Engine optimized for {cores} cores with {hash_size}MB hash")
                    return True
                except (AttributeError, IOError) as e:
                    logger.warning(f"Failed to configure engine options: {e}")
                    return False
        except (AttributeError, IOError) as e:
            logger.error(f"Error configuring engine options: {e}")
            return False
    
    def _apply_skill_level(self, level):
        """Apply skill level with error recovery"""
        try:
            if level >= 20:
                print(f"Engine set to UNLIMITED STRENGTH (level {level})")
                if self.depth >= 20:
                    self.engine.set_depth(0)  # Unlimited depth
                self._configure_engine_options(self.engine)
            else:
                self.engine.set_skill_level(level)
        except (AttributeError, ValueError) as e:
            print(f"Error setting skill level: {e}")
            if self._recover_engine() and self.engine:
                try:
                    if level >= 20:
                        print(f"Engine set to UNLIMITED STRENGTH (level {level}) after recovery")
                    else:
                        self.engine.set_skill_level(level)
                except (AttributeError, ValueError) as e2:
                    print(f"Failed to set skill level after recovery: {e2}")
    
    def _apply_depth(self, depth):
        """Apply depth setting with error recovery"""
        try:
            if self.skill_level >= 20 and depth >= 20:
                # Cap maximum depth to prevent infinite thinking
                max_depth = min(depth, 25)  # Maximum 25 ply depth
                self.engine.set_depth(max_depth)
                print(f"Engine set to MAXIMUM DEPTH (depth {max_depth}, requested {depth})")
            else:
                self.engine.set_depth(depth)
        except (AttributeError, ValueError) as e:
            print(f"Error setting depth: {e}")
            if self._recover_engine() and self.engine:
                try:
                    if self.skill_level >= 20 and depth >= 20:
                        max_depth = min(depth, 25)
                        self.engine.set_depth(max_depth)
                        print(f"Engine set to MAXIMUM DEPTH (depth {max_depth}) after recovery")
                    else:
                        self.engine.set_depth(depth)
                except (AttributeError, ValueError) as e2:
                    print(f"Failed to set depth after recovery: {e2}")
        
    def set_skill_level(self, level):
        self.skill_level = level
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return
            self._apply_skill_level(level)
        
    def set_depth(self, depth):
        self.depth = depth
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return
            self._apply_depth(depth)
        
    def set_position(self, fen):
        # Validate FEN before using
        if not fen or not isinstance(fen, str) or len(fen.strip()) == 0:
            return False
        try:
            test_board = Board(fen)  # Test if FEN is valid
            if not test_board.is_valid():
                return False
        except (ValueError, AttributeError) as e:
            print(f"Invalid FEN: {fen}, error: {e}")
            return False
            
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return False
            try:
                self.last_fen = fen  # Store last valid FEN
                self.engine.set_fen_position(fen)
                self.board = Board(fen)
                return True
            except (AttributeError, ValueError) as e:
                print(f"Error setting position: {e}")
                if self._recover_engine() and self.engine:
                    try:
                        self.engine.set_fen_position(fen)
                        self.board = Board(fen)
                        return True
                    except (AttributeError, ValueError) as e2:
                        print(f"Failed to set position after recovery: {e2}")
                        return False
                return False
        
    def get_best_move(self, time_limit=None):
        """Get best move with optional time limit"""
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return None
            try:
                # Set time limit based on depth/level - reduced for stability
                if time_limit is None:
                    if self.skill_level >= 20 and self.depth >= 20:
                        time_limit = 8000   # 8 seconds for maximum strength (reduced from 10)
                    elif self.skill_level >= 18 or self.depth >= 18:
                        time_limit = 6000   # 6 seconds for very high strength
                    elif self.skill_level >= 15 or self.depth >= 15:
                        time_limit = 4000   # 4 seconds for high strength
                    else:
                        time_limit = 2000   # 2 seconds for normal play
                
                # Use time-limited move calculation
                move = self.engine.get_best_move_time(time_limit)
                if move is None:
                    print(f"Engine returned None for best move (time limit: {time_limit}ms)")
                    # Aggressive fallback with multiple attempts
                    fallback_attempts = [
                        (8, 3000),   # Depth 8, 3 seconds
                        (6, 2000),   # Depth 6, 2 seconds  
                        (4, 1000),   # Depth 4, 1 second
                        (2, 500),    # Depth 2, 0.5 seconds
                    ]
                    
                    original_depth = self.depth
                    for fallback_depth, fallback_time in fallback_attempts:
                        try:
                            print(f"Trying fallback: depth {fallback_depth}, time {fallback_time}ms")
                            self.engine.set_depth(fallback_depth)
                            move = self.engine.get_best_move_time(fallback_time)
                            if move is not None:
                                print(f"Fallback successful at depth {fallback_depth}")
                                break
                        except (AttributeError, ValueError, RuntimeError) as e:
                            print(f"Fallback failed at depth {fallback_depth}: {e}")
                            continue
                    
                    # Restore original depth
                    try:
                        self.engine.set_depth(original_depth)
                    except (AttributeError, ValueError):
                        pass
                return move
            except (AttributeError, ValueError, RuntimeError) as e:
                print(f"Error getting best move: {e}")
                if self._recover_engine() and self.engine:
                    try:
                        # Use shorter time limit for recovery
                        return self.engine.get_best_move_time(min(time_limit or 2000, 2000))
                    except (AttributeError, ValueError, RuntimeError) as e2:
                        print(f"Failed to get best move after recovery: {e2}")
                        return None
                return None
    
    def get_evaluation(self):
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return None
            try:
                eval_result = self.engine.get_evaluation()
                if eval_result is None:
                    print("Engine returned None for evaluation")
                return eval_result
            except (AttributeError, ValueError, RuntimeError) as e:
                print(f"Error getting evaluation: {e}")
                if self._recover_engine() and self.engine:
                    try:
                        return self.engine.get_evaluation()
                    except (AttributeError, ValueError, RuntimeError) as e2:
                        print(f"Failed to get evaluation after recovery: {e2}")
                        return None
                return None
    
    def make_move(self, uci_move):
        with self.engine_lock:
            try:
                self.board.push(Move.from_uci(uci_move))
            except (AttributeError, ValueError) as e:
                print(f"Error making move: {e}")
                self._recover_engine()
        
    def is_game_over(self):
        with self.engine_lock:
            try:
                return self.board.is_game_over()
            except (AttributeError, ValueError) as e:
                print(f"Error checking game over: {e}")
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
            except (AttributeError, ValueError) as e:
                print(f"Error resetting engine: {e}")
                self._recover_engine()
                
    def _recover_engine(self):
        """Recover from engine crashes by recreating the instance"""
        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            print(f"Max recovery attempts ({self.max_recovery_attempts}) reached. Engine unhealthy.")
            self._is_healthy = False
            return False
            
        print(f"Recovering crashed engine... (attempt {self.recovery_attempts})")
        try:
            # Clean up old engine
            if hasattr(self.engine, '_stockfish'):
                try:
                    self.engine._stockfish.terminate()
                except (AttributeError, OSError):
                    pass
        except (AttributeError, OSError):
            pass
        
        try:
            # Create new engine instance with stored values
            self.engine = self._create_engine(self.skill_level, self.depth)
            
            # Restore last known position
            if self.last_fen:
                self.engine.set_fen_position(self.last_fen)
                self.board = Board(self.last_fen)
            else:
                # Fallback to starting position
                self.engine.set_fen_position(STARTING_FEN)
                self.board = Board()
                self.last_fen = STARTING_FEN
                
            # Reset recovery counter on success
            self.recovery_attempts = 0
            self._is_healthy = True
            return True
        except (AttributeError, ValueError, RuntimeError) as e:
            print(f"Engine recovery failed: {e}")
            if self.recovery_attempts >= self.max_recovery_attempts:
                self._is_healthy = False
            return False
    
    def cleanup(self):
        """Cleanup engine resources"""
        with self.engine_lock:
            try:
                if hasattr(self, 'engine') and self.engine:
                    if hasattr(self.engine, '_stockfish') and self.engine._stockfish:
                        try:
                            self.engine._stockfish.terminate()
                            self.engine._stockfish.wait(timeout=2)
                        except (AttributeError, OSError):
                            try:
                                self.engine._stockfish.kill()
                            except (AttributeError, OSError):
                                pass
                    self.engine = None
                logger.info("Engine cleanup completed")
            except (AttributeError, OSError) as e:
                logger.error(f"Error during engine cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except (AttributeError, OSError):
            pass