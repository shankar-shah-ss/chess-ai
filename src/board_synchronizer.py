# board_synchronizer.py - Ensures proper synchronization between custom board and python-chess
import chess
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class BoardSynchronizer:
    """
    Handles synchronization between the custom board representation and python-chess library.
    This prevents position corruption and ensures moves are valid.
    """
    
    def __init__(self):
        self.python_chess_board = chess.Board()
        self.move_history = []
        
    def reset_to_starting_position(self):
        """Reset both boards to starting position"""
        self.python_chess_board = chess.Board()
        self.move_history = []
        
    def apply_uci_move(self, uci_move: str) -> bool:
        """
        Apply a UCI move to the python-chess board and validate it.
        Returns True if successful, False if invalid.
        """
        try:
            if not uci_move or len(uci_move) < 4:
                logger.warning(f"Invalid UCI move format: {uci_move}")
                return False
                
            # Parse and validate the move
            move = chess.Move.from_uci(uci_move)
            
            if move not in self.python_chess_board.legal_moves:
                logger.warning(f"Illegal move {uci_move} in position {self.python_chess_board.fen()}")
                logger.warning(f"Legal moves: {[str(m) for m in list(self.python_chess_board.legal_moves)[:10]]}")
                return False
                
            # Apply the move
            self.python_chess_board.push(move)
            self.move_history.append(uci_move)
            
            logger.debug(f"Applied move {uci_move}, new position: {self.python_chess_board.fen()}")
            return True
            
        except (ValueError, chess.InvalidMoveError) as e:
            logger.error(f"Error applying UCI move {uci_move}: {e}")
            return False
            
    def get_current_fen(self) -> str:
        """Get the current FEN from the python-chess board"""
        return self.python_chess_board.fen()
        
    def is_move_legal(self, uci_move: str) -> bool:
        """Check if a UCI move is legal in the current position"""
        try:
            if not uci_move or len(uci_move) < 4:
                return False
                
            move = chess.Move.from_uci(uci_move)
            return move in self.python_chess_board.legal_moves
            
        except (ValueError, chess.InvalidMoveError):
            return False
            
    def get_legal_moves(self) -> list:
        """Get all legal moves in UCI format"""
        return [str(move) for move in self.python_chess_board.legal_moves]
        
    def validate_fen(self, fen: str) -> bool:
        """Validate a FEN string"""
        try:
            test_board = chess.Board(fen)
            return test_board.is_valid()
        except (ValueError, chess.InvalidFenError):
            return False
            
    def set_position_from_fen(self, fen: str) -> bool:
        """Set the board position from a FEN string"""
        try:
            if not self.validate_fen(fen):
                logger.error(f"Invalid FEN: {fen}")
                return False
                
            self.python_chess_board = chess.Board(fen)
            logger.debug(f"Set position from FEN: {fen}")
            return True
            
        except (ValueError, chess.InvalidFenError) as e:
            logger.error(f"Error setting position from FEN {fen}: {e}")
            return False
            
    def get_piece_at_square(self, square: str) -> Optional[str]:
        """Get the piece at a given square (e.g., 'e4')"""
        try:
            square_index = chess.parse_square(square)
            piece = self.python_chess_board.piece_at(square_index)
            return str(piece) if piece else None
        except ValueError:
            return None
            
    def is_check(self) -> bool:
        """Check if the current player is in check"""
        return self.python_chess_board.is_check()
        
    def is_checkmate(self) -> bool:
        """Check if the current player is in checkmate"""
        return self.python_chess_board.is_checkmate()
        
    def is_stalemate(self) -> bool:
        """Check if the current player is in stalemate"""
        return self.python_chess_board.is_stalemate()
        
    def get_turn(self) -> str:
        """Get whose turn it is ('white' or 'black')"""
        return 'white' if self.python_chess_board.turn == chess.WHITE else 'black'
        
    def debug_position(self) -> str:
        """Get a debug string representation of the current position"""
        return f"FEN: {self.python_chess_board.fen()}\nBoard:\n{self.python_chess_board}\nTurn: {self.get_turn()}\nLegal moves: {len(list(self.python_chess_board.legal_moves))}"