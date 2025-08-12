# thread_safe_board_manager.py - Thread-safe board state management
import threading
import chess
import logging
from typing import Optional, List, Tuple
try:
    from .board_synchronizer import BoardSynchronizer
except ImportError:
    from board_synchronizer import BoardSynchronizer

logger = logging.getLogger(__name__)

class ThreadSafeBoardManager:
    """
    Thread-safe manager for chess board state that prevents race conditions
    and ensures consistency between custom board and python-chess representations.
    """
    
    def __init__(self, custom_board=None):
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._synchronizer = BoardSynchronizer()
        self._custom_board = custom_board
        self._move_history = []
        self._position_cache = {}
        
        # Initialize with starting position
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self._synchronizer.set_position_from_fen(starting_fen)
        
    def get_current_fen(self) -> str:
        """Get current FEN in a thread-safe manner"""
        with self._lock:
            return self._synchronizer.get_current_fen()
    
    def get_legal_moves(self) -> List[str]:
        """Get legal moves in UCI format"""
        with self._lock:
            return self._synchronizer.get_legal_moves()
    
    def is_move_legal(self, uci_move: str) -> bool:
        """Check if a move is legal"""
        with self._lock:
            return self._synchronizer.is_move_legal(uci_move)
    
    def apply_move(self, uci_move: str) -> bool:
        """Apply a move in a thread-safe manner"""
        with self._lock:
            try:
                # Validate move first
                if not self._synchronizer.is_move_legal(uci_move):
                    logger.warning(f"Illegal move rejected: {uci_move}")
                    return False
                
                # Apply to synchronizer
                if not self._synchronizer.apply_uci_move(uci_move):
                    logger.error(f"Failed to apply move to synchronizer: {uci_move}")
                    return False
                
                # Record in history
                self._move_history.append(uci_move)
                
                # Clear position cache since position changed
                self._position_cache.clear()
                
                logger.debug(f"Applied move {uci_move}, new position: {self._synchronizer.get_current_fen()}")
                return True
                
            except Exception as e:
                logger.error(f"Error applying move {uci_move}: {e}")
                return False
    
    def set_position(self, fen: str) -> bool:
        """Set board position from FEN"""
        with self._lock:
            try:
                if not self._synchronizer.validate_fen(fen):
                    logger.error(f"Invalid FEN: {fen}")
                    return False
                
                if not self._synchronizer.set_position_from_fen(fen):
                    logger.error(f"Failed to set position: {fen}")
                    return False
                
                # Clear history and cache
                self._move_history.clear()
                self._position_cache.clear()
                
                logger.debug(f"Set position: {fen}")
                return True
                
            except Exception as e:
                logger.error(f"Error setting position {fen}: {e}")
                return False
    
    def reset_to_starting_position(self):
        """Reset to starting position"""
        with self._lock:
            self._synchronizer.reset_to_starting_position()
            self._move_history.clear()
            self._position_cache.clear()
            logger.debug("Reset to starting position")
    
    def get_turn(self) -> str:
        """Get whose turn it is"""
        with self._lock:
            return self._synchronizer.get_turn()
    
    def is_check(self) -> bool:
        """Check if current player is in check"""
        with self._lock:
            return self._synchronizer.is_check()
    
    def is_checkmate(self) -> bool:
        """Check if current player is in checkmate"""
        with self._lock:
            return self._synchronizer.is_checkmate()
    
    def is_stalemate(self) -> bool:
        """Check if current player is in stalemate"""
        with self._lock:
            return self._synchronizer.is_stalemate()
    
    def get_move_history(self) -> List[str]:
        """Get move history"""
        with self._lock:
            return self._move_history.copy()
    
    def validate_position_consistency(self) -> bool:
        """Validate that the position is consistent and legal"""
        with self._lock:
            try:
                current_fen = self._synchronizer.get_current_fen()
                
                # Basic FEN validation
                if not self._synchronizer.validate_fen(current_fen):
                    logger.error(f"Position validation failed: invalid FEN {current_fen}")
                    return False
                
                # Check for impossible positions
                board = chess.Board(current_fen)
                
                # Count pieces
                white_pieces = len(board.piece_map())
                if white_pieces > 32:  # Maximum possible pieces
                    logger.error(f"Too many pieces on board: {white_pieces}")
                    return False
                
                # Check king count
                white_kings = len(board.pieces(chess.KING, chess.WHITE))
                black_kings = len(board.pieces(chess.KING, chess.BLACK))
                
                if white_kings != 1 or black_kings != 1:
                    logger.error(f"Invalid king count: white={white_kings}, black={black_kings}")
                    return False
                
                # Check for pawns on back ranks
                white_pawns_back = len(board.pieces(chess.PAWN, chess.WHITE) & chess.BB_RANK_8)
                black_pawns_back = len(board.pieces(chess.PAWN, chess.BLACK) & chess.BB_RANK_1)
                
                if white_pawns_back > 0 or black_pawns_back > 0:
                    logger.error(f"Pawns on back rank: white={white_pawns_back}, black={black_pawns_back}")
                    return False
                
                return True
                
            except Exception as e:
                logger.error(f"Position validation error: {e}")
                return False
    
    def debug_position(self) -> str:
        """Get debug information about current position"""
        with self._lock:
            return self._synchronizer.debug_position()
    
    def get_position_hash(self) -> str:
        """Get a hash of the current position for caching"""
        with self._lock:
            fen = self._synchronizer.get_current_fen()
            import hashlib
            return hashlib.md5(fen.encode()).hexdigest()
    
    def sync_with_custom_board(self, custom_board, next_player: str):
        """Synchronize with the custom board representation"""
        with self._lock:
            try:
                if custom_board and hasattr(custom_board, 'to_fen'):
                    custom_fen = custom_board.to_fen(next_player)
                    if custom_fen and self._synchronizer.validate_fen(custom_fen):
                        current_fen = self._synchronizer.get_current_fen()
                        if custom_fen != current_fen:
                            logger.warning(f"Board desync detected: custom={custom_fen}, sync={current_fen}")
                            # Trust the synchronizer over custom board
                            return False
                return True
            except Exception as e:
                logger.error(f"Error syncing with custom board: {e}")
                return False