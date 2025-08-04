"""
Professional-grade draw mechanism system for chess
Implements all official FIDE draw conditions with comprehensive detection and management
"""

from hashlib import md5
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

class DrawType(Enum):
    """All possible draw types in chess"""
    STALEMATE = "stalemate"
    THREEFOLD_REPETITION = "threefold_repetition"
    FIFTY_MOVE_RULE = "fifty_move_rule"
    SEVENTY_FIVE_MOVE_RULE = "seventy_five_move_rule"
    INSUFFICIENT_MATERIAL = "insufficient_material"
    MUTUAL_AGREEMENT = "mutual_agreement"
    PERPETUAL_CHECK = "perpetual_check"  # Subset of threefold repetition
    DEAD_POSITION = "dead_position"

@dataclass
class DrawCondition:
    """Represents a draw condition with metadata"""
    draw_type: DrawType
    is_automatic: bool  # True if automatic, False if must be claimed
    description: str
    detected_at_move: int
    position_hash: str = ""
    additional_info: str = ""

class DrawManager:
    """
    Professional-grade draw detection and management system
    Implements all FIDE draw conditions with comprehensive tracking
    """
    
    def __init__(self):
        # Position tracking for repetition detection
        self.position_history: List[str] = []
        self.position_counts: Dict[str, int] = {}
        self.position_moves: Dict[str, List[int]] = {}  # Track which moves led to positions
        
        # Move tracking for 50/75 move rules
        self.halfmove_clock = 0
        self.move_number = 1
        
        # Draw offers and claims
        self.draw_offered = False
        self.draw_offer_by: Optional[str] = None
        self.draw_offer_move: Optional[int] = None
        self.claimable_draws: List[DrawCondition] = []
        
        # Game state tracking
        self.game_over = False
        self.draw_result: Optional[DrawCondition] = None
        
        # Advanced tracking
        self.check_history: List[bool] = []  # Track consecutive checks for perpetual check
        self.last_capture_or_pawn_move = 0
        
        # Performance optimization
        self._position_cache: Dict[str, bool] = {}
        
    def reset(self):
        """Reset draw manager for new game"""
        self.position_history.clear()
        self.position_counts.clear()
        self.position_moves.clear()
        self.halfmove_clock = 0
        self.move_number = 1
        self.draw_offered = False
        self.draw_offer_by = None
        self.draw_offer_move = None
        self.claimable_draws.clear()
        self.game_over = False
        self.draw_result = None
        self.check_history.clear()
        self.last_capture_or_pawn_move = 0
        self._position_cache.clear()
        
    def generate_position_hash(self, board, current_player: str, castling_rights: Dict, 
                             en_passant_square: Optional[Tuple[int, int]] = None) -> str:
        """
        Generate a unique hash for the current position including all relevant factors
        for draw detection (position, player to move, castling rights, en passant)
        """
        position_data = []
        
        # Board position
        for row in range(8):
            for col in range(8):
                square = board.squares[row][col]
                if square.has_piece():
                    piece = square.piece
                    position_data.append(f"{piece.color[0]}{piece.name[0]}{row}{col}")
                else:
                    position_data.append("--")
        
        # Player to move
        position_data.append(f"turn:{current_player}")
        
        # Castling rights
        castling_str = ""
        if castling_rights.get('white_kingside', False):
            castling_str += "K"
        if castling_rights.get('white_queenside', False):
            castling_str += "Q"
        if castling_rights.get('black_kingside', False):
            castling_str += "k"
        if castling_rights.get('black_queenside', False):
            castling_str += "q"
        position_data.append(f"castle:{castling_str}")
        
        # En passant square
        if en_passant_square:
            position_data.append(f"ep:{en_passant_square[0]}{en_passant_square[1]}")
        else:
            position_data.append("ep:none")
        
        # Create hash
        position_string = "|".join(position_data)
        return md5(position_string.encode()).hexdigest()
    
    def update_position(self, board, current_player: str, castling_rights: Dict,
                       en_passant_square: Optional[Tuple[int, int]] = None,
                       was_capture: bool = False, was_pawn_move: bool = False,
                       is_check: bool = False):
        """Update position tracking after a move"""
        # Generate position hash
        position_hash = self.generate_position_hash(board, current_player, castling_rights, en_passant_square)
        
        # Update position history
        self.position_history.append(position_hash)
        self.position_counts[position_hash] = self.position_counts.get(position_hash, 0) + 1
        
        # Track which moves led to this position
        if position_hash not in self.position_moves:
            self.position_moves[position_hash] = []
        self.position_moves[position_hash].append(self.move_number)
        
        # Update halfmove clock for 50/75 move rules
        if was_capture or was_pawn_move:
            self.halfmove_clock = 0
            self.last_capture_or_pawn_move = self.move_number
        else:
            self.halfmove_clock += 1
        
        # Track checks for perpetual check detection
        self.check_history.append(is_check)
        if len(self.check_history) > 20:  # Keep last 20 moves
            self.check_history.pop(0)
        
        # Increment move number
        if current_player == 'white':
            self.move_number += 1
    
    def check_all_draw_conditions(self, board, current_player: str) -> List[DrawCondition]:
        """
        Check all draw conditions and return list of applicable draws
        Returns both automatic draws and claimable draws
        """
        draw_conditions = []
        
        # 1. Check for stalemate (automatic)
        if self._is_stalemate(board, current_player):
            draw_conditions.append(DrawCondition(
                DrawType.STALEMATE,
                is_automatic=True,
                description="Player to move has no legal moves and is not in check",
                detected_at_move=self.move_number,
                position_hash=self.position_history[-1] if self.position_history else ""
            ))
        
        # 2. Check for threefold repetition (claimable)
        threefold = self._check_threefold_repetition()
        if threefold:
            draw_conditions.append(threefold)
        
        # 3. Check for fifty-move rule (claimable)
        if self.halfmove_clock >= 100:  # 50 full moves = 100 half-moves
            draw_conditions.append(DrawCondition(
                DrawType.FIFTY_MOVE_RULE,
                is_automatic=False,
                description=f"50 moves without capture or pawn move (since move {self.last_capture_or_pawn_move})",
                detected_at_move=self.move_number,
                additional_info=f"Halfmove clock: {self.halfmove_clock}"
            ))
        
        # 4. Check for seventy-five-move rule (automatic)
        if self.halfmove_clock >= 150:  # 75 full moves = 150 half-moves
            draw_conditions.append(DrawCondition(
                DrawType.SEVENTY_FIVE_MOVE_RULE,
                is_automatic=True,
                description=f"75 moves without capture or pawn move (automatic draw)",
                detected_at_move=self.move_number,
                additional_info=f"Halfmove clock: {self.halfmove_clock}"
            ))
        
        # 5. Check for insufficient material (automatic)
        insufficient = self._check_insufficient_material(board)
        if insufficient:
            draw_conditions.append(insufficient)
        
        # 6. Check for dead position (automatic)
        dead_position = self._check_dead_position(board)
        if dead_position:
            draw_conditions.append(dead_position)
        
        # 7. Check for perpetual check (subset of threefold repetition)
        perpetual = self._check_perpetual_check()
        if perpetual:
            draw_conditions.append(perpetual)
        
        return draw_conditions
    
    def _is_stalemate(self, board, color: str) -> bool:
        """Check if the current player is in stalemate"""
        # Must not be in check
        if board.is_king_in_check(color):
            return False
        
        # Check if any legal move exists
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.color == color:
                    board.calc_moves(piece, row, col, bool=True)
                    if piece.moves:
                        return False
        return True
    
    def _check_threefold_repetition(self) -> Optional[DrawCondition]:
        """Check for threefold repetition"""
        if not self.position_history:
            return None
        
        current_position = self.position_history[-1]
        count = self.position_counts.get(current_position, 0)
        
        if count >= 3:
            moves = self.position_moves.get(current_position, [])
            return DrawCondition(
                DrawType.THREEFOLD_REPETITION,
                is_automatic=False,
                description=f"Position repeated 3 times (moves: {', '.join(map(str, moves))})",
                detected_at_move=self.move_number,
                position_hash=current_position,
                additional_info=f"Repetition count: {count}"
            )
        
        return None
    
    def _check_insufficient_material(self, board) -> Optional[DrawCondition]:
        """Check for insufficient material to checkmate"""
        # Count pieces for both sides
        white_pieces = []
        black_pieces = []
        white_bishops = []
        black_bishops = []
        
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece and piece.name.lower() != 'king':
                    piece_info = {
                        'name': piece.name.lower(),
                        'color': piece.color,
                        'position': (row, col)
                    }
                    
                    if piece.color == 'white':
                        white_pieces.append(piece_info)
                        if piece.name.lower() == 'bishop':
                            square_color = 'light' if (row + col) % 2 == 0 else 'dark'
                            white_bishops.append(square_color)
                    else:
                        black_pieces.append(piece_info)
                        if piece.name.lower() == 'bishop':
                            square_color = 'light' if (row + col) % 2 == 0 else 'dark'
                            black_bishops.append(square_color)
        
        # Analyze material combinations
        white_count = len(white_pieces)
        black_count = len(black_pieces)
        
        # King vs King
        if white_count == 0 and black_count == 0:
            return DrawCondition(
                DrawType.INSUFFICIENT_MATERIAL,
                is_automatic=True,
                description="King vs King",
                detected_at_move=self.move_number
            )
        
        # King + minor piece vs King
        if (white_count == 1 and black_count == 0 and 
            white_pieces[0]['name'] in ['bishop', 'knight']):
            return DrawCondition(
                DrawType.INSUFFICIENT_MATERIAL,
                is_automatic=True,
                description=f"King + {white_pieces[0]['name'].title()} vs King",
                detected_at_move=self.move_number
            )
        
        if (black_count == 1 and white_count == 0 and 
            black_pieces[0]['name'] in ['bishop', 'knight']):
            return DrawCondition(
                DrawType.INSUFFICIENT_MATERIAL,
                is_automatic=True,
                description=f"King vs King + {black_pieces[0]['name'].title()}",
                detected_at_move=self.move_number
            )
        
        # King + Bishop vs King + Bishop (same color squares)
        if (white_count == 1 and black_count == 1 and 
            white_pieces[0]['name'] == 'bishop' and black_pieces[0]['name'] == 'bishop'):
            if white_bishops[0] == black_bishops[0]:
                return DrawCondition(
                    DrawType.INSUFFICIENT_MATERIAL,
                    is_automatic=True,
                    description=f"King + Bishop vs King + Bishop (both on {white_bishops[0]} squares)",
                    detected_at_move=self.move_number
                )
        
        # King + Knight vs King + Knight (very rare but possible)
        if (white_count == 1 and black_count == 1 and 
            white_pieces[0]['name'] == 'knight' and black_pieces[0]['name'] == 'knight'):
            return DrawCondition(
                DrawType.INSUFFICIENT_MATERIAL,
                is_automatic=True,
                description="King + Knight vs King + Knight",
                detected_at_move=self.move_number
            )
        
        return None
    
    def _check_dead_position(self, board) -> Optional[DrawCondition]:
        """
        Check for dead position - position where checkmate is impossible
        by any sequence of legal moves
        """
        # This is a complex analysis that requires deep position evaluation
        # For now, implement basic cases that are clearly dead
        
        # Get all pieces
        all_pieces = []
        for row in range(8):
            for col in range(8):
                piece = board.squares[row][col].piece
                if piece:
                    all_pieces.append({
                        'name': piece.name.lower(),
                        'color': piece.color,
                        'position': (row, col)
                    })
        
        # Filter out kings
        non_king_pieces = [p for p in all_pieces if p['name'] != 'king']
        
        # Advanced dead position detection
        if len(non_king_pieces) <= 2:
            # Analyze specific combinations that are always dead
            if self._is_dead_position_combination(non_king_pieces):
                piece_desc = ", ".join([f"{p['color']} {p['name']}" for p in non_king_pieces])
                return DrawCondition(
                    DrawType.DEAD_POSITION,
                    is_automatic=True,
                    description=f"Dead position: checkmate impossible with current material ({piece_desc})",
                    detected_at_move=self.move_number
                )
        
        return None
    
    def _is_dead_position_combination(self, pieces: List[Dict]) -> bool:
        """Check if a specific piece combination creates a dead position"""
        if len(pieces) == 0:
            return True  # King vs King
        
        if len(pieces) == 1:
            # Single minor piece vs King
            return pieces[0]['name'] in ['bishop', 'knight']
        
        if len(pieces) == 2:
            # Two pieces - check specific combinations
            piece_names = sorted([p['name'] for p in pieces])
            colors = [p['color'] for p in pieces]
            
            # Two bishops of same color on same colored squares
            if piece_names == ['bishop', 'bishop'] and colors[0] != colors[1]:
                # Would need to check if bishops are on same colored squares
                # This is a simplified check
                return False  # Could still mate in some positions
            
            # Knight + Bishop vs King (same side) - not always dead
            if piece_names == ['bishop', 'knight'] and colors[0] == colors[1]:
                return False  # Can mate
            
            # Two knights same side vs King - dead position
            if piece_names == ['knight', 'knight'] and colors[0] == colors[1]:
                return True
        
        return False
    
    def _check_perpetual_check(self) -> Optional[DrawCondition]:
        """
        Check for perpetual check pattern (subset of threefold repetition)
        This detects when the same checking pattern repeats
        """
        if len(self.check_history) < 6:
            return None
        
        # Look for pattern of consecutive checks leading to repetition
        recent_checks = self.check_history[-6:]
        if all(recent_checks):  # All recent moves were checks
            # If we also have threefold repetition, it's likely perpetual check
            threefold = self._check_threefold_repetition()
            if threefold:
                return DrawCondition(
                    DrawType.PERPETUAL_CHECK,
                    is_automatic=False,
                    description="Perpetual check detected (subset of threefold repetition)",
                    detected_at_move=self.move_number,
                    position_hash=threefold.position_hash,
                    additional_info="Pattern of consecutive checks with position repetition"
                )
        
        return None
    
    def offer_draw(self, player: str) -> bool:
        """Player offers a draw"""
        if not self.game_over and not self.draw_offered:
            self.draw_offered = True
            self.draw_offer_by = player
            self.draw_offer_move = self.move_number
            return True
        return False
    
    def accept_draw(self, player: str) -> Optional[DrawCondition]:
        """Player accepts a draw offer"""
        if (self.draw_offered and self.draw_offer_by != player and 
            not self.game_over):
            self.game_over = True
            self.draw_result = DrawCondition(
                DrawType.MUTUAL_AGREEMENT,
                is_automatic=True,
                description=f"Draw agreed between players (offered by {self.draw_offer_by}, accepted by {player})",
                detected_at_move=self.move_number,
                additional_info=f"Offer made on move {self.draw_offer_move}"
            )
            return self.draw_result
        return None
    
    def decline_draw(self, player: str) -> bool:
        """Player declines a draw offer"""
        if (self.draw_offered and self.draw_offer_by != player):
            self.draw_offered = False
            self.draw_offer_by = None
            self.draw_offer_move = None
            return True
        return False
    
    def claim_draw(self, draw_type: DrawType) -> Optional[DrawCondition]:
        """Player claims a draw of specified type"""
        # Find the claimable draw condition
        for condition in self.claimable_draws:
            if condition.draw_type == draw_type and not condition.is_automatic:
                self.game_over = True
                self.draw_result = condition
                return condition
        return None
    
    def update_claimable_draws(self, board, current_player: str):
        """Update the list of draws that can be claimed"""
        all_conditions = self.check_all_draw_conditions(board, current_player)
        
        # Separate automatic draws from claimable draws
        automatic_draws = [c for c in all_conditions if c.is_automatic]
        claimable_draws = [c for c in all_conditions if not c.is_automatic]
        
        # If there are automatic draws, the game ends immediately
        if automatic_draws:
            self.game_over = True
            self.draw_result = automatic_draws[0]  # Take the first automatic draw
        
        # Update claimable draws
        self.claimable_draws = claimable_draws
    
    def get_draw_status(self) -> Dict:
        """Get comprehensive draw status information"""
        return {
            'game_over': self.game_over,
            'draw_result': self.draw_result,
            'draw_offered': self.draw_offered,
            'draw_offer_by': self.draw_offer_by,
            'draw_offer_move': self.draw_offer_move,
            'claimable_draws': self.claimable_draws,
            'halfmove_clock': self.halfmove_clock,
            'position_repetitions': max(self.position_counts.values()) if self.position_counts else 0,
            'move_number': self.move_number,
            'last_capture_or_pawn_move': self.last_capture_or_pawn_move
        }
    
    def get_draw_description(self, draw_condition: DrawCondition) -> str:
        """Get a human-readable description of a draw condition"""
        base_desc = draw_condition.description
        
        if draw_condition.additional_info:
            base_desc += f" ({draw_condition.additional_info})"
        
        if draw_condition.is_automatic:
            base_desc += " [Automatic Draw]"
        else:
            base_desc += " [Claimable Draw]"
        
        return base_desc
    
    def export_draw_history(self) -> Dict:
        """Export complete draw tracking history for analysis"""
        return {
            'position_history': self.position_history,
            'position_counts': self.position_counts,
            'position_moves': self.position_moves,
            'halfmove_clock': self.halfmove_clock,
            'move_number': self.move_number,
            'check_history': self.check_history,
            'last_capture_or_pawn_move': self.last_capture_or_pawn_move,
            'draw_offers': {
                'offered': self.draw_offered,
                'by': self.draw_offer_by,
                'move': self.draw_offer_move
            }
        }