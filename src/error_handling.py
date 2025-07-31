# error_handling.py - Comprehensive error handling system
import logging
import traceback
from functools import wraps
from typing import Optional, Any, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chess_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ChessAI')

class ChessAIError(Exception):
    """Base exception for Chess AI"""
    pass

class EngineError(ChessAIError):
    """Engine-related errors"""
    pass

class AnalysisError(ChessAIError):
    """Analysis-related errors"""
    pass

class GameStateError(ChessAIError):
    """Game state errors"""
    pass

def safe_execute(fallback_value=None, log_errors=True):
    """Decorator for safe function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())
                return fallback_value
        return wrapper
    return decorator

def validate_game_state(game) -> bool:
    """Validate game state consistency"""
    try:
        # Check board integrity
        if not game.board or not game.board.squares:
            raise GameStateError("Invalid board state")
        
        # Check piece positions
        king_count = {'white': 0, 'black': 0}
        for row in range(8):
            for col in range(8):
                piece = game.board.squares[row][col].piece
                if piece and piece.name == 'king':
                    king_count[piece.color] += 1
        
        if king_count['white'] != 1 or king_count['black'] != 1:
            raise GameStateError("Invalid king count")
        
        return True
    except Exception as e:
        logger.error(f"Game state validation failed: {e}")
        return False

def handle_engine_error(engine_func):
    """Handle engine errors gracefully"""
    @wraps(engine_func)
    def wrapper(*args, **kwargs):
        try:
            return engine_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Engine error in {engine_func.__name__}: {e}")
            # Attempt engine recovery
            if hasattr(args[0], '_recover_engine'):
                args[0]._recover_engine()
            return None
    return wrapper

class ErrorRecovery:
    """Error recovery utilities"""
    
    @staticmethod
    def recover_analysis(analyzer):
        """Recover from analysis errors"""
        try:
            analyzer.analysis_complete = False
            analyzer.analyzed_moves = []
            analyzer.analysis_progress = 0
            logger.info("Analysis state recovered")
        except Exception as e:
            logger.error(f"Analysis recovery failed: {e}")
    
    @staticmethod
    def recover_game_state(game):
        """Recover from game state errors"""
        try:
            # Reset to last known good state
            game.game_over = False
            game.winner = None
            game.check_alert = None
            logger.info("Game state recovered")
        except Exception as e:
            logger.error(f"Game state recovery failed: {e}")