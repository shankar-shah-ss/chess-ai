# engine.py - Enhanced version with improved thread safety and resource management
from stockfish import Stockfish
import chess
from chess import Board, Move, STARTING_FEN
from os import environ, path, cpu_count
from os.path import exists, expanduser
from pathlib import Path
import time
import json
from threading import RLock, Lock
import weakref
from typing import Optional, Dict, Any
from logging import basicConfig, getLogger, INFO

# Configure logging for engine
basicConfig(level=INFO)
logger = getLogger(__name__)

# Import Lichess opening book system only
try:
    from lichess_opening_book import get_lichess_opening_book, cleanup_lichess_opening_book
    OPENING_BOOK_AVAILABLE = True
    logger.info("✅ Lichess Masters opening book system loaded")
except ImportError as e:
    logger.warning(f"Lichess opening book system not available: {e}")
    OPENING_BOOK_AVAILABLE = False

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
    def __init__(self, skill_level=None, depth=None, use_opening_book=True, target_elo=None):
        # Handle ELO-based initialization
        if target_elo is not None:
            self.target_elo = target_elo
            self.skill_level, self.depth = self._elo_to_skill_depth(target_elo)
        else:
            self.target_elo = self._skill_depth_to_elo(skill_level or 10, depth or 15)
            self.skill_level = skill_level or 10
            self.depth = depth or 15
            
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self._is_healthy = True
        self._last_health_check = 0
        self._cleanup_registered = False
        
        # Opening book configuration
        self.use_opening_book = use_opening_book and OPENING_BOOK_AVAILABLE
        self.opening_book = None
        self.move_count = 0  # Track move number for book depth
        self._book_config = None
        self._last_move_was_book = False  # Track if last move was from book
        
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
        self.engine = self._create_engine(self.skill_level, self.depth)
        self.board = Board()
        self.last_fen = STARTING_FEN  # Track last valid position
        
        # Register with engine pool for cleanup
        EnginePool().register_engine(self)
        self._cleanup_registered = True
        
        # Initialize opening book
        if self.use_opening_book:
            self._initialize_opening_book()
        
        # Initialize thermal management
        self.thermal_mode_enabled = True  # Default enabled
        self._thermal_mode = True
    
    def _elo_to_skill_depth(self, elo):
        """Convert ELO rating to skill level and depth (800-3600 ELO, 4-30 depth)"""
        if elo <= 900:
            return 1, 4      # 800-900: Beginner
        elif elo <= 1000:
            return 2, 5      # 901-1000: Novice
        elif elo <= 1100:
            return 3, 6      # 1001-1100: Amateur
        elif elo <= 1200:
            return 4, 7      # 1101-1200: Club Beginner
        elif elo <= 1300:
            return 5, 8      # 1201-1300: Club Player
        elif elo <= 1400:
            return 6, 9      # 1301-1400: Club Intermediate
        elif elo <= 1500:
            return 7, 10     # 1401-1500: Club Advanced
        elif elo <= 1600:
            return 8, 11     # 1501-1600: Strong Club
        elif elo <= 1700:
            return 9, 12     # 1601-1700: Tournament Player
        elif elo <= 1800:
            return 10, 13    # 1701-1800: Expert
        elif elo <= 1900:
            return 11, 14    # 1801-1900: Strong Expert
        elif elo <= 2000:
            return 12, 15    # 1901-2000: Candidate Master
        elif elo <= 2100:
            return 13, 16    # 2001-2100: National Master
        elif elo <= 2200:
            return 14, 17    # 2101-2200: FIDE Master
        elif elo <= 2300:
            return 15, 18    # 2201-2300: International Master
        elif elo <= 2400:
            return 16, 19    # 2301-2400: Strong IM
        elif elo <= 2500:
            return 17, 20    # 2401-2500: Grandmaster
        elif elo <= 2600:
            return 18, 22    # 2501-2600: Strong GM
        elif elo <= 2700:
            return 19, 24    # 2601-2700: Super GM
        elif elo <= 2800:
            return 20, 26    # 2701-2800: Elite GM
        elif elo <= 2900:
            return 20, 27    # 2801-2900: World Class
        elif elo <= 3000:
            return 20, 28    # 2901-3000: World Championship Level
        elif elo <= 3200:
            return 20, 29    # 3001-3200: Computer Strength
        else:  # 3201-3600+
            return 20, 30    # 3201+: Maximum Computer Strength
    
    def _skill_depth_to_elo(self, skill, depth):
        """Convert skill level and depth to approximate ELO (supports 800-3600 range)"""
        # Base ELO from skill level (enhanced formula for higher range)
        base_elo = 800 + (skill * 120)  # Increased multiplier for higher range
        
        # Depth bonus (each depth point adds ~35 ELO for extended range)
        depth_bonus = (depth - 4) * 35  # Adjusted for depth 4-30 range
        
        return min(3600, max(800, base_elo + depth_bonus))
    
    def set_elo(self, elo):
        """Set engine strength by ELO rating"""
        self.target_elo = elo
        self.skill_level, self.depth = self._elo_to_skill_depth(elo)
        
        # Apply the new settings
        self.set_skill_level(self.skill_level)
        self.set_depth(self.depth)
    
    def get_strength_category(self):
        """Get human-readable strength category with detailed GM levels"""
        elo = self.target_elo
        if elo <= 900: return "Beginner"
        elif elo <= 1000: return "Novice"
        elif elo <= 1100: return "Amateur"
        elif elo <= 1200: return "Club Beginner"
        elif elo <= 1300: return "Club Player"
        elif elo <= 1400: return "Club Intermediate"
        elif elo <= 1500: return "Club Advanced"
        elif elo <= 1600: return "Strong Club"
        elif elo <= 1700: return "Tournament Player"
        elif elo <= 1800: return "Expert"
        elif elo <= 1900: return "Strong Expert"
        elif elo <= 2000: return "Candidate Master"
        elif elo <= 2100: return "National Master"
        elif elo <= 2200: return "FIDE Master"
        elif elo <= 2300: return "International Master"
        elif elo <= 2400: return "Strong IM"
        elif elo <= 2500: return "Grandmaster"
        elif elo <= 2600: return "Strong GM"
        elif elo <= 2700: return "Super GM"
        elif elo <= 2800: return "Elite GM"
        elif elo <= 2900: return "World Class GM"
        elif elo <= 3000: return "World Championship Level"
        elif elo <= 3200: return "Computer Strength"
        else: return "Maximum Engine Strength"
    
    def _initialize_opening_book(self):
        """Initialize the Lichess opening book system with intelligent variety management"""
        try:
            # Load configuration from file
            config_file = Path(__file__).parent / "lichess_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    self._book_config = config_data.get('lichess_opening_system', {})
            else:
                # Fallback configuration with intelligent variety enabled
                self._book_config = {
                    'max_depth': 20,
                    'min_games': 10,
                    'move_selection': 'intelligent_random',
                    'variety_enabled': True,
                    'min_games_gap': 10,
                    'request_delay': 1.0,
                    'cache_ttl_minutes': 30
                }
            
            # Initialize Lichess opening book
            self.opening_book = get_lichess_opening_book(self._book_config)
            
            logger.info("📚 Lichess Masters opening book initialized")
            logger.info(f"  Max depth: {self._book_config['max_depth']} moves")
            logger.info(f"  Min games threshold: {self._book_config['min_games']}")
            logger.info(f"  Selection strategy: {self._book_config['move_selection']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Lichess opening book: {e}")
            self.use_opening_book = False
            self.opening_book = None
    
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
                
            # Configure for maximum strength at level 20 (with stability limits)
            if skill_level >= 20:
                if depth >= 20:
                    # Cap maximum depth to prevent crashes and infinite thinking
                    max_depth = min(depth, 20)  # Maximum 20 ply depth for stability
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
        """Configure engine with limited core usage (max 3 cores)"""
        system_cores = cpu_count() or 4  # Fallback to 4 if detection fails
        cores = min(3, system_cores)  # Limit to maximum 3 cores
        
        try:
            if hasattr(engine, '_stockfish') and engine._stockfish:
                try:
                    # Use limited CPU cores (max 3)
                    engine._stockfish.stdin.write(f"setoption name Threads value {cores}\n")
                    engine._stockfish.stdin.flush()
                    
                    # Reduce hash table size for limited cores
                    hash_size = min(96, cores * 32)  # Scale with limited cores, max 96MB
                    engine._stockfish.stdin.write(f"setoption name Hash value {hash_size}\n")
                    engine._stockfish.stdin.flush()
                    
                    # Enable multi-PV for parallel analysis
                    engine._stockfish.stdin.write("setoption name MultiPV value 1\n")
                    engine._stockfish.stdin.flush()
                    
                    # Optimize for analysis
                    engine._stockfish.stdin.write("setoption name Contempt value 0\n")
                    engine._stockfish.stdin.flush()
                    
                    logger.info(f"Engine optimized for {cores} cores (max 3) with {hash_size}MB hash")
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
                # Cap maximum depth to prevent crashes and infinite thinking
                max_depth = min(depth, 20)  # Maximum 20 ply depth for stability
                self.engine.set_depth(max_depth)
                print(f"Engine set to MAXIMUM DEPTH (depth {max_depth}, requested {depth})")
            else:
                self.engine.set_depth(depth)
        except (AttributeError, ValueError) as e:
            print(f"Error setting depth: {e}")
            if self._recover_engine() and self.engine:
                try:
                    if self.skill_level >= 20 and depth >= 20:
                        max_depth = min(depth, 20)  # Maximum 20 ply depth for stability
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
    
    def increment_move_count(self):
        """Increment move count for opening book tracking"""
        self.move_count += 1
    
    def reset_move_count(self):
        """Reset move count (e.g., for new game)"""
        self.move_count = 0
        
    def get_best_move(self, time_limit=None):
        """Get best move with optional time limit, checking opening book first"""
        with self.engine_lock:
            if not self.engine or not self._check_engine_health():
                return None
            
            # Check opening book first
            if self.use_opening_book and self.opening_book:
                try:
                    current_fen = self.board.fen() if hasattr(self, 'board') and self.board else self.last_fen
                    book_move = self.opening_book.get_book_move(current_fen, self.move_count + 1)
                    
                    if book_move:
                        # Validate book move is legal
                        try:
                            test_board = Board(current_fen)
                            chess_move = test_board.parse_uci(book_move)
                            if chess_move in test_board.legal_moves:
                                # Record move for variety tracking
                                if hasattr(self.opening_book, 'record_move_played'):
                                    self.opening_book.record_move_played(book_move)
                                
                                logger.info(f"📖 Book move: {book_move} (move #{self.move_count + 1})")
                                # Mark this as a book move for the worker thread
                                self._last_move_was_book = True
                                return book_move
                            else:
                                logger.warning(f"Invalid book move: {book_move}")
                        except Exception as e:
                            logger.warning(f"Error validating book move {book_move}: {e}")
                except Exception as e:
                    logger.error(f"Error getting book move: {e}")
            
            try:
                # Set time limit based on depth/level - tripled timeouts for superior move quality
                if time_limit is None:
                    if self.skill_level >= 20 and self.depth >= 25:
                        time_limit = 45000  # 45 seconds for world-class strength (9x increase)
                    elif self.skill_level >= 18 or self.depth >= 20:
                        time_limit = 36000  # 36 seconds for grandmaster strength (9x increase)
                    elif self.skill_level >= 15 or self.depth >= 15:
                        time_limit = 27000  # 27 seconds for master strength (9x increase)
                    elif self.skill_level >= 10 or self.depth >= 10:
                        time_limit = 18000  # 18 seconds for expert strength (9x increase)
                    else:
                        time_limit = 18000  # 18 seconds for normal play (9x increase)
                
                # Use time-limited move calculation
                logger.debug(f"🤖 Engine calculation (move #{self.move_count + 1})")
                # Mark this as an engine move (not book move)
                self._last_move_was_book = False
                move = self.engine.get_best_move_time(time_limit)
                if move is None:
                    print(f"Engine returned None for best move (time limit: {time_limit}ms)")
                    # Aggressive fallback with multiple attempts (9x increased timeouts)
                    fallback_attempts = [
                        (8, 27000),  # Depth 8, 27 seconds (9x increase)
                        (6, 18000),  # Depth 6, 18 seconds (9x increase)
                        (4, 9000),   # Depth 4, 9 seconds (9x increase)
                        (2, 4500),   # Depth 2, 4.5 seconds (9x increase)
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
                        # Use shorter time limit for recovery (3x increased)
                        return self.engine.get_best_move_time(min(time_limit or 6000, 6000))
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
                # Reset move counter for new game
                self.reset_move_count()
            except (AttributeError, ValueError) as e:
                print(f"Error resetting engine: {e}")
                self._recover_engine()
                
    def _recover_engine(self):
        """Recover from engine crashes by recreating the instance with preserved settings"""
        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            print(f"Max recovery attempts ({self.max_recovery_attempts}) reached. Engine unhealthy.")
            self._is_healthy = False
            return False
            
        print(f"🔄 Recovering crashed engine... (attempt {self.recovery_attempts})")
        print(f"   Preserving settings: skill_level={self.skill_level}, depth={self.depth}")
        
        # Store current settings before cleanup
        preserved_skill_level = self.skill_level
        preserved_depth = self.depth
        preserved_fen = self.last_fen
        
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
            # Create new engine instance with preserved settings
            self.engine = self._create_engine(preserved_skill_level, preserved_depth)
            
            # Restore last known position
            if preserved_fen:
                self.engine.set_fen_position(preserved_fen)
                self.board = Board(preserved_fen)
                self.last_fen = preserved_fen
            else:
                # Fallback to starting position
                self.engine.set_fen_position(STARTING_FEN)
                self.board = Board()
                self.last_fen = STARTING_FEN
                
            # Ensure settings are properly restored
            self.skill_level = preserved_skill_level
            self.depth = preserved_depth
            
            # Reset recovery counter on success
            self.recovery_attempts = 0
            self._is_healthy = True
            print(f"✅ Engine recovered successfully with skill_level={self.skill_level}, depth={self.depth}")
            return True
        except (AttributeError, ValueError, RuntimeError) as e:
            print(f"❌ Engine recovery failed: {e}")
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
                
                # Cleanup opening book (only if this is the last engine instance)
                if hasattr(self, 'opening_book') and self.opening_book:
                    try:
                        # Note: We don't cleanup the global book here as other engines might use it
                        self.opening_book = None
                    except Exception as e:
                        logger.error(f"Error cleaning up opening book: {e}")
                
                logger.info("Engine cleanup completed")
            except (AttributeError, OSError) as e:
                logger.error(f"Error during engine cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except (AttributeError, OSError):
            pass
    
    # Thermal Management Methods
    def enable_thermal_mode(self, enabled=True):
        """Enable or disable thermal management mode"""
        self.thermal_mode_enabled = enabled
        self._thermal_mode = enabled
        logger.info(f"🌡️ Thermal management {'enabled' if enabled else 'disabled'}")
    
    def disable_thermal_mode(self):
        """Disable thermal management mode"""
        self.enable_thermal_mode(False)
    
    def is_thermal_mode_enabled(self):
        """Check if thermal management is enabled"""
        return getattr(self, 'thermal_mode_enabled', True)
    
    # Move Recording Methods
    def record_move_played(self, move, fen_before=None, fen_after=None):
        """Record a move that was played (for tracking/statistics)"""
        try:
            # Initialize move history if not exists
            if not hasattr(self, 'move_history'):
                self.move_history = []
            
            # Record the move with metadata
            move_record = {
                'move': move,
                'fen_before': fen_before,
                'fen_after': fen_after,
                'move_number': len(self.move_history) + 1,
                'timestamp': time.time()
            }
            
            self.move_history.append(move_record)
            logger.debug(f"📝 Recorded move: {move} (#{move_record['move_number']})")
            
        except Exception as e:
            logger.warning(f"Error recording move {move}: {e}")
    
    def get_move_history(self):
        """Get the recorded move history"""
        return getattr(self, 'move_history', [])
    
    def clear_move_history(self):
        """Clear the recorded move history"""
        self.move_history = []
        logger.debug("📝 Move history cleared")
    
    def start_new_game(self, opponent_elo=None, game_type="casual", game_id=None):
        """Start a new game session with optional opponent ELO and game type"""
        try:
            # Reset engine state for new game
            self.reset()
            self.clear_move_history()
            
            # Store game metadata
            self.current_game = {
                'game_id': game_id or f"game_{int(time.time())}",
                'opponent_elo': opponent_elo,
                'game_type': game_type,
                'start_time': time.time(),
                'moves_played': 0
            }
            
            # Initialize opening book for new game with variety tracking
            if hasattr(self, 'opening_book') and self.opening_book:
                # Clear any position-specific cache for fresh start
                if hasattr(self.opening_book, 'clear_cache'):
                    self.opening_book.clear_cache()
                
                # Start variety tracking for this game
                if hasattr(self.opening_book, 'start_new_game'):
                    self.opening_book.start_new_game(
                        elo_level=self.target_elo,
                        game_id=self.current_game['game_id']
                    )
            
            logger.info(f"🎮 New game started: {self.current_game['game_id']}")
            logger.info(f"   Engine ELO: {self.target_elo}")
            if opponent_elo:
                logger.info(f"   Opponent ELO: {opponent_elo}")
            logger.info(f"   Game type: {game_type}")
            logger.info(f"   Opening variety: {'Enabled' if self._book_config.get('variety_enabled') else 'Disabled'}")
            
            return self.current_game['game_id']
            
        except Exception as e:
            logger.error(f"Error starting new game: {e}")
            return None
    
    def get_current_game_info(self):
        """Get information about the current game"""
        return getattr(self, 'current_game', None)
    
    def finish_current_game(self, result: str = None):
        """Finish the current game and record opening for variety tracking"""
        try:
            if hasattr(self, 'current_game') and self.current_game:
                game_id = self.current_game['game_id']
                
                # Record game finish in opening book
                if hasattr(self, 'opening_book') and self.opening_book:
                    if hasattr(self.opening_book, 'finish_game'):
                        self.opening_book.finish_game(game_id, result)
                
                logger.info(f"🏁 Game finished: {game_id}")
                if result:
                    logger.info(f"   Result: {result}")
                
                # Clear current game
                self.current_game = None
                
        except Exception as e:
            logger.error(f"Error finishing game: {e}")
    
    def get_opening_variety_stats(self):
        """Get opening variety statistics"""
        if hasattr(self, 'opening_book') and self.opening_book:
            if hasattr(self.opening_book, 'get_variety_stats'):
                return self.opening_book.get_variety_stats()
        return {'variety_system': 'not_available'}
    
    def end_current_game(self, result: str = None):
        """Alias for finish_current_game for compatibility"""
        return self.finish_current_game(result)