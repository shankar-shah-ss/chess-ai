# performance_fixes.py - Critical performance and bug fixes
import threading
import weakref
from functools import lru_cache
from piece import Pawn

class ImageCache:
    """Singleton image cache to prevent memory leaks"""
    _instance = None
    _cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @lru_cache(maxsize=32)
    def get_piece_image(self, piece_name, color, size):
        """Get cached piece image"""
        key = f"{piece_name}_{color}_{size}"
        if key not in self._cache:
            # Load image logic here
            pass
        return self._cache.get(key)
    
    def clear_cache(self):
        """Clear image cache"""
        self._cache.clear()

class ThreadSafeEngine:
    """Thread-safe engine wrapper"""
    def __init__(self, engine):
        self.engine = engine
        self._lock = threading.RLock()
        self._active_threads = weakref.WeakSet()
    
    def execute_safely(self, func, *args, **kwargs):
        """Execute engine function safely"""
        with self._lock:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Engine error: {e}")
                return None

class OptimizedMoveValidation:
    """Optimized move validation"""
    
    @staticmethod
    def is_valid_en_passant(board, piece, move):
        """Simplified en passant validation"""
          # Use absolute import for local module
        if not isinstance(piece, Pawn):
            return False
        
        # Check if target square matches en passant target
        if not board.en_passant_target:
            return False
            
        return (move.final.row == board.en_passant_target.row and 
                move.final.col == board.en_passant_target.col and
                abs(move.initial.col - move.final.col) == 1)