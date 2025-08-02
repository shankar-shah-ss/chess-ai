"""
Professional Move Validation System
Prevents illegal moves and ensures game integrity
"""

import chess
from typing import Optional, Tuple, List
from move import Move
from square import Square

class MoveValidator:
    """
    Professional-grade move validation system
    Ensures all moves are legal and prevents engine errors
    """
    
    def __init__(self):
        self.last_validated_move = None
        self.move_history = []
        self.validation_cache = {}
        
    def validate_uci_move(self, uci_move: str, board, current_player: str) -> Optional[Move]:
        """
        Validate UCI move from engine and convert to internal Move format
        Returns None if move is invalid
        """
        if not uci_move or len(uci_move) < 4:
            print(f"❌ Invalid UCI move format: {uci_move}")
            return None
        
        try:
            # Parse UCI move (e.g., "e2e4", "e7e8q")
            from_square = uci_move[:2]
            to_square = uci_move[2:4]
            promotion = uci_move[4:] if len(uci_move) > 4 else None
            
            # Convert to internal coordinates
            move = self._uci_to_internal_move(from_square, to_square, promotion)
            if not move:
                return None
            
            # Validate move legality
            if not self._is_move_legal(move, board, current_player):
                print(f"❌ Illegal move detected: {uci_move}")
                return None
            
            # Additional validation checks
            if not self._validate_piece_movement(move, board):
                print(f"❌ Invalid piece movement: {uci_move}")
                return None
            
            # Check for double move prevention
            if self._is_duplicate_move(move):
                print(f"❌ Duplicate move prevented: {uci_move}")
                return None
            
            # Record validated move
            self.last_validated_move = move
            self.move_history.append(move)
            
            print(f"✅ Move validated: {uci_move}")
            return move
            
        except Exception as e:
            print(f"❌ Move validation error for {uci_move}: {e}")
            return None
    
    def _uci_to_internal_move(self, from_square: str, to_square: str, promotion: Optional[str]) -> Optional[Move]:
        """Convert UCI notation to internal Move object"""
        try:
            col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
            
            # Parse from square
            from_col = col_map[from_square[0]]
            from_row = 8 - int(from_square[1])
            
            # Parse to square
            to_col = col_map[to_square[0]]
            to_row = 8 - int(to_square[1])
            
            # Validate coordinates
            if not (0 <= from_row < 8 and 0 <= from_col < 8 and 
                   0 <= to_row < 8 and 0 <= to_col < 8):
                print(f"❌ Invalid coordinates: {from_square} -> {to_square}")
                return None
            
            initial = Square(from_row, from_col)
            final = Square(to_row, to_col)
            
            move = Move(initial, final)
            
            # Handle promotion
            if promotion:
                move.promotion = promotion.lower()
            
            return move
            
        except (KeyError, ValueError, IndexError) as e:
            print(f"❌ UCI parsing error: {e}")
            return None
    
    def _is_move_legal(self, move: Move, board, current_player: str) -> bool:
        """Check if move is legal using chess library validation"""
        try:
            # Convert board to FEN for chess library validation
            fen = board.to_fen(current_player)
            if not fen:
                return False
            
            # Create chess board from FEN
            chess_board = chess.Board(fen)
            
            # Convert internal move to UCI
            uci_move = self._internal_move_to_uci(move)
            if not uci_move:
                return False
            
            # Parse and validate with chess library
            try:
                chess_move = chess.Move.from_uci(uci_move)
                return chess_move in chess_board.legal_moves
            except ValueError:
                return False
                
        except Exception as e:
            print(f"❌ Legal move check error: {e}")
            return False
    
    def _internal_move_to_uci(self, move: Move) -> Optional[str]:
        """Convert internal Move to UCI notation"""
        try:
            col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            
            from_col = col_map[move.initial.col]
            from_row = str(8 - move.initial.row)
            to_col = col_map[move.final.col]
            to_row = str(8 - move.final.row)
            
            uci_move = from_col + from_row + to_col + to_row
            
            # Add promotion if present
            if hasattr(move, 'promotion') and move.promotion:
                uci_move += move.promotion
            
            return uci_move
            
        except (IndexError, AttributeError) as e:
            print(f"❌ UCI conversion error: {e}")
            return None
    
    def _validate_piece_movement(self, move: Move, board) -> bool:
        """Validate that the piece can actually make this move"""
        try:
            from_square = board.squares[move.initial.row][move.initial.col]
            
            # Check if there's a piece at the source
            if not from_square.has_piece():
                print(f"❌ No piece at source square: {move.initial.row}, {move.initial.col}")
                return False
            
            piece = from_square.piece
            
            # Calculate valid moves for this piece
            board.calc_moves(piece, move.initial.row, move.initial.col, bool=True)
            
            # Check if the target square is in the piece's valid moves
            for valid_move in piece.moves:
                if (valid_move.final.row == move.final.row and 
                    valid_move.final.col == move.final.col):
                    return True
            
            print(f"❌ Move not in piece's valid moves: {piece.name} from ({move.initial.row}, {move.initial.col}) to ({move.final.row}, {move.final.col})")
            return False
            
        except Exception as e:
            print(f"❌ Piece movement validation error: {e}")
            return False
    
    def _is_duplicate_move(self, move: Move) -> bool:
        """Check if this move is a duplicate of the last move"""
        if not self.last_validated_move:
            return False
        
        last = self.last_validated_move
        return (move.initial.row == last.initial.row and 
                move.initial.col == last.initial.col and
                move.final.row == last.final.row and
                move.final.col == last.final.col)
    
    def validate_engine_position(self, board, current_player: str) -> bool:
        """Validate that the engine has the correct board position"""
        try:
            fen = board.to_fen(current_player)
            if not fen or len(fen.strip()) == 0:
                print("❌ Invalid FEN generated")
                return False
            
            # Basic FEN validation
            parts = fen.split()
            if len(parts) < 4:
                print(f"❌ Malformed FEN: {fen}")
                return False
            
            # Validate board part
            board_part = parts[0]
            ranks = board_part.split('/')
            if len(ranks) != 8:
                print(f"❌ Invalid FEN board part: {board_part}")
                return False
            
            # Validate active color
            if parts[1] not in ['w', 'b']:
                print(f"❌ Invalid active color in FEN: {parts[1]}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Position validation error: {e}")
            return False
    
    def clear_history(self):
        """Clear move history (for new games)"""
        self.last_validated_move = None
        self.move_history.clear()
        self.validation_cache.clear()
    
    def get_move_statistics(self) -> dict:
        """Get validation statistics"""
        return {
            'total_moves_validated': len(self.move_history),
            'last_move': self.last_validated_move,
            'cache_size': len(self.validation_cache)
        }

class EngineMovePreventer:
    """
    Prevents engine from making multiple moves in a row
    Ensures proper turn alternation
    """
    
    def __init__(self):
        self.last_engine_move_time = 0
        self.last_engine_player = None
        self.move_cooldown = 0.5  # Minimum time between engine moves
        self.turn_tracker = None
        
    def can_engine_move(self, current_player: str, game_turn: str) -> bool:
        """Check if engine is allowed to move now"""
        import time
        current_time = time.time()
        
        # Check turn consistency
        if current_player != game_turn:
            print(f"❌ Turn mismatch: engine thinks {current_player}, game says {game_turn}")
            return False
        
        # Prevent same engine from moving twice in a row
        if self.last_engine_player == current_player:
            time_since_last = current_time - self.last_engine_move_time
            if time_since_last < self.move_cooldown:
                print(f"❌ Engine cooldown active: {time_since_last:.2f}s < {self.move_cooldown}s")
                return False
            else:
                # Even after cooldown, same player shouldn't move twice unless turn changed
                if self.turn_tracker == current_player:
                    print(f"❌ Same player attempting consecutive moves: {current_player}")
                    return False
        
        # Update tracking
        self.last_engine_move_time = current_time
        self.last_engine_player = current_player
        self.turn_tracker = game_turn
        
        return True
    
    def reset(self):
        """Reset for new game"""
        self.last_engine_move_time = 0
        self.last_engine_player = None
        self.turn_tracker = None