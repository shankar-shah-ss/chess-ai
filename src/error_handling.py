# error_handling.py - Enhanced comprehensive error handling system
import logging
import traceback
import sys
import os
from functools import wraps
from typing import Optional, Any, Callable, Dict, List
from datetime import datetime, timezone
import threading

# Enhanced logging configuration
class ChessAIFormatter(logging.Formatter):
    """Custom formatter for chess AI logging"""
    
    def format(self, record):
        # Thread name is already available as threadName in Python logging
        
        # Color coding for different levels
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m'  # Magenta
        }
        reset = '\033[0m'
        
        if hasattr(record, 'levelname') and record.levelname in colors:
            record.levelname = f"{colors[record.levelname]}{record.levelname}{reset}"
        
        return super().format(record)

# Configure enhanced logging
def setup_logging():
    """Setup enhanced logging system"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Main logger
    logger = logging.getLogger('ChessAI')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        'logs/chess_ai.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ChessAIFormatter(
        '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Error file handler
    error_handler = logging.FileHandler('logs/chess_ai_errors.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)
    
    return logger

logger = setup_logging()

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

class ErrorTracker:
    """Track and analyze errors for better debugging"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
        self.max_history = 100
        self._lock = threading.Lock()
    
    def record_error(self, error_type: str, error_msg: str, context: str = ""):
        """Record an error occurrence"""
        with self._lock:
            # Update counts
            key = f"{error_type}:{context}"
            self.error_counts[key] = self.error_counts.get(key, 0) + 1
            
            # Add to history
            error_record = {
                'timestamp': datetime.now(timezone.utc),
                'type': error_type,
                'message': error_msg,
                'context': context,
                'count': self.error_counts[key]
            }
            
            self.error_history.append(error_record)
            
            # Limit history size
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        with self._lock:
            return {
                'total_errors': len(self.error_history),
                'unique_errors': len(self.error_counts),
                'most_common': sorted(self.error_counts.items(), 
                                    key=lambda x: x[1], reverse=True)[:5],
                'recent_errors': self.error_history[-10:]
            }

# Global error tracker
error_tracker = ErrorTracker()

def safe_execute(fallback_value=None, log_errors=True, context="", retry_count=0):
    """Enhanced decorator for safe function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_type = type(e).__name__
                    error_msg = str(e)
                    
                    # Record error
                    error_tracker.record_error(error_type, error_msg, context or func.__name__)
                    
                    if log_errors:
                        if attempt < retry_count:
                            logger.warning(f"Attempt {attempt + 1} failed in {func.__name__}: {e}")
                        else:
                            logger.error(f"Error in {func.__name__}: {e}")
                            logger.debug(traceback.format_exc())
                    
                    if attempt < retry_count:
                        # Brief delay before retry
                        import time
                        time.sleep(0.1 * (attempt + 1))
                    else:
                        break
            
            # All attempts failed
            if log_errors and retry_count > 0:
                logger.error(f"All {retry_count + 1} attempts failed for {func.__name__}")
            
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
    """Enhanced error recovery utilities"""
    
    @staticmethod
    @safe_execute(fallback_value=False, context="analysis_recovery")
    def recover_analysis(analyzer):
        """Recover from analysis errors"""
        if hasattr(analyzer, 'analysis_complete'):
            analyzer.analysis_complete = False
        if hasattr(analyzer, 'analyzed_moves'):
            analyzer.analyzed_moves = []
        if hasattr(analyzer, 'analysis_progress'):
            analyzer.analysis_progress = 0
        if hasattr(analyzer, 'analysis_thread'):
            analyzer.analysis_thread = None
        
        logger.info("Analysis state recovered")
        return True
    
    @staticmethod
    @safe_execute(fallback_value=False, context="game_state_recovery")
    def recover_game_state(game):
        """Recover from game state errors"""
        # Reset to last known good state
        if hasattr(game, 'game_over'):
            game.game_over = False
        if hasattr(game, 'winner'):
            game.winner = None
        if hasattr(game, 'check_alert'):
            game.check_alert = None
        if hasattr(game, 'evaluation_thread'):
            game.evaluation_thread = None
        if hasattr(game, 'engine_thread'):
            game.engine_thread = None
        
        logger.info("Game state recovered")
        return True
    
    @staticmethod
    @safe_execute(fallback_value=False, context="engine_recovery")
    def recover_engine(engine):
        """Recover engine state"""
        if hasattr(engine, '_recover_engine'):
            return engine._recover_engine()
        return False
    
    @staticmethod
    @safe_execute(fallback_value=False, context="resource_recovery")
    def recover_resources():
        """Recover system resources"""
        try:
            from resource_manager import resource_manager
            from thread_manager import thread_manager
            
            # Clean up resources
            resource_manager.cleanup_cache("images")
            
            # Clean up threads
            if thread_manager.get_active_thread_count() > 10:
                thread_manager.cancel_all_tasks()
            
            logger.info("Resources recovered")
            return True
        except ImportError:
            logger.warning("Resource managers not available for recovery")
            return False

class PerformanceMonitor:
    """Monitor performance and detect issues"""
    
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            'memory_mb': 500,  # MB
            'cpu_percent': 80,  # %
            'thread_count': 20,
            'error_rate': 0.1   # errors per second
        }
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float):
        """Record a performance metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            
            self.metrics[name].append({
                'timestamp': datetime.now(timezone.utc),
                'value': value
            })
            
            # Keep only recent metrics (last 100)
            if len(self.metrics[name]) > 100:
                self.metrics[name] = self.metrics[name][-100:]
    
    def check_performance(self) -> Dict[str, Any]:
        """Check current performance status"""
        issues = []
        
        try:
            import psutil
            process = psutil.Process()
            
            # Memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.record_metric('memory_mb', memory_mb)
            if memory_mb > self.thresholds['memory_mb']:
                issues.append(f"High memory usage: {memory_mb:.1f}MB")
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            self.record_metric('cpu_percent', cpu_percent)
            if cpu_percent > self.thresholds['cpu_percent']:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Thread count
            thread_count = process.num_threads()
            self.record_metric('thread_count', thread_count)
            if thread_count > self.thresholds['thread_count']:
                issues.append(f"High thread count: {thread_count}")
                
        except ImportError:
            logger.debug("psutil not available for performance monitoring")
        except Exception as e:
            logger.warning(f"Performance monitoring error: {e}")
        
        return {
            'issues': issues,
            'metrics': self.get_recent_metrics()
        }
    
    def get_recent_metrics(self) -> Dict[str, float]:
        """Get recent average metrics"""
        recent_metrics = {}
        
        with self._lock:
            for name, values in self.metrics.items():
                if values:
                    # Get average of last 10 values
                    recent_values = [v['value'] for v in values[-10:]]
                    recent_metrics[name] = sum(recent_values) / len(recent_values)
        
        return recent_metrics

# Global instances
performance_monitor = PerformanceMonitor()

def monitor_performance():
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now(timezone.utc)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                performance_monitor.record_metric(f"{func.__name__}_duration", duration)
        return wrapper
    return decorator