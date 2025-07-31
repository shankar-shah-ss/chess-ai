# notation.py - Chess notation system for algebraic notation and PGN
from piece import *

class ChessNotation:
    def __init__(self, board):
        self.board = board
        
    def move_to_algebraic(self, move, piece, is_capture=False, is_check=False, is_checkmate=False, is_promotion=False, promotion_piece=None):
        """Convert move to standard algebraic notation"""
        notation = ""
        
        # Handle castling
        if isinstance(piece, King) and abs(move.initial.col - move.final.col) == 2:
            if move.final.col > move.initial.col:
                return "O-O"  # Kingside castling
            else:
                return "O-O-O"  # Queenside castling
        
        # Piece symbol (except for pawns)
        if not isinstance(piece, Pawn):
            notation += piece.symbol().upper()
            
            # Check for ambiguity (multiple pieces of same type can reach same square)
            notation += self._resolve_ambiguity(piece, move)
        
        # Capture notation
        if is_capture:
            if isinstance(piece, Pawn):
                # Pawn captures include the file of departure
                notation += chr(97 + move.initial.col)  # a-h
            notation += "x"
        
        # Destination square
        notation += self._square_to_algebraic(move.final.row, move.final.col)
        
        # Pawn promotion
        if is_promotion and promotion_piece:
            notation += "=" + promotion_piece.symbol().upper()
        
        # Check and checkmate
        if is_checkmate:
            notation += "#"
        elif is_check:
            notation += "+"
            
        return notation
    
    def _resolve_ambiguity(self, piece, move):
        """Resolve ambiguity when multiple pieces can reach the same square"""
        same_type_pieces = []
        
        # Find all pieces of same type and color that can reach the destination
        for row in range(8):
            for col in range(8):
                board_piece = self.board.squares[row][col].piece
                if (board_piece and 
                    type(board_piece) == type(piece) and 
                    board_piece.color == piece.color and
                    board_piece != piece):
                    
                    # Check if this piece can also reach the destination
                    self.board.calc_moves(board_piece, row, col, bool=False)
                    for other_move in board_piece.moves:
                        if (other_move.final.row == move.final.row and 
                            other_move.final.col == move.final.col):
                            same_type_pieces.append((row, col))
                            break
        
        if not same_type_pieces:
            return ""
        
        # Check if file disambiguation is sufficient
        file_unique = True
        for row, col in same_type_pieces:
            if col == move.initial.col:
                file_unique = False
                break
        
        if file_unique:
            return chr(97 + move.initial.col)  # Return file (a-h)
        
        # Check if rank disambiguation is sufficient
        rank_unique = True
        for row, col in same_type_pieces:
            if row == move.initial.row:
                rank_unique = False
                break
        
        if rank_unique:
            return str(8 - move.initial.row)  # Return rank (1-8)
        
        # Both file and rank needed
        return chr(97 + move.initial.col) + str(8 - move.initial.row)
    
    def _square_to_algebraic(self, row, col):
        """Convert row,col to algebraic notation (e.g., e4)"""
        file = chr(97 + col)  # a-h
        rank = str(8 - row)   # 1-8
        return file + rank
    
    def algebraic_to_square(self, algebraic):
        """Convert algebraic notation to row,col"""
        if len(algebraic) != 2:
            return None
        
        file = algebraic[0].lower()
        rank = algebraic[1]
        
        if file < 'a' or file > 'h' or rank < '1' or rank > '8':
            return None
        
        col = ord(file) - 97  # a=0, b=1, etc.
        row = 8 - int(rank)   # 1=7, 2=6, etc.
        
        return (row, col)
    
    def parse_algebraic_move(self, notation, color):
        """Parse algebraic notation and return the corresponding move"""
        notation = notation.strip()
        
        # Handle castling
        if notation == "O-O":
            row = 7 if color == 'white' else 0
            return self._create_move(row, 4, row, 6)  # King moves from e to g
        elif notation == "O-O-O":
            row = 7 if color == 'white' else 0
            return self._create_move(row, 4, row, 2)  # King moves from e to c
        
        # Remove check/checkmate indicators
        if notation.endswith('#') or notation.endswith('+'):
            notation = notation[:-1]
        
        # Handle promotion
        promotion_piece = None
        if '=' in notation:
            parts = notation.split('=')
            notation = parts[0]
            promotion_piece = parts[1]
        
        # Extract destination square (last 2 characters)
        if len(notation) < 2:
            return None
        
        dest_square = notation[-2:]
        dest_pos = self.algebraic_to_square(dest_square)
        if not dest_pos:
            return None
        
        dest_row, dest_col = dest_pos
        
        # Determine piece type and source constraints
        piece_type = None
        source_file = None
        source_rank = None
        is_capture = 'x' in notation
        
        # Remove destination and capture indicator
        remaining = notation[:-2]
        if is_capture:
            remaining = remaining.replace('x', '')
        
        if not remaining:
            # Pawn move
            piece_type = Pawn
            if is_capture:
                # Pawn capture - source file is specified
                source_file = ord(notation[0]) - 97
        else:
            # Piece move
            piece_symbol = remaining[0].upper()
            piece_type = self._symbol_to_piece_type(piece_symbol)
            
            # Parse disambiguation
            if len(remaining) > 1:
                disambig = remaining[1:]
                if len(disambig) == 1:
                    if disambig.isdigit():
                        source_rank = 8 - int(disambig)
                    else:
                        source_file = ord(disambig.lower()) - 97
                elif len(disambig) == 2:
                    source_pos = self.algebraic_to_square(disambig)
                    if source_pos:
                        source_rank, source_file = source_pos
        
        # Find the piece that can make this move
        return self._find_piece_move(piece_type, color, dest_row, dest_col, 
                                   source_file, source_rank, is_capture)
    
    def _symbol_to_piece_type(self, symbol):
        """Convert piece symbol to piece class"""
        symbol_map = {
            'K': King, 'Q': Queen, 'R': Rook, 
            'B': Bishop, 'N': Knight, 'P': Pawn
        }
        return symbol_map.get(symbol, None)
    
    def _find_piece_move(self, piece_type, color, dest_row, dest_col, 
                        source_file=None, source_rank=None, is_capture=False):
        """Find the piece that can make the specified move"""
        from move import Move
        from square import Square
        
        candidates = []
        
        for row in range(8):
            for col in range(8):
                piece = self.board.squares[row][col].piece
                if (piece and type(piece) == piece_type and piece.color == color):
                    # Check source constraints
                    if source_file is not None and col != source_file:
                        continue
                    if source_rank is not None and row != source_rank:
                        continue
                    
                    # Check if piece can reach destination
                    self.board.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if (move.final.row == dest_row and move.final.col == dest_col):
                            # Verify capture constraint
                            target_has_piece = self.board.squares[dest_row][dest_col].has_piece()
                            if is_capture == target_has_piece or self._is_en_passant(piece, move):
                                candidates.append(Move(Square(row, col), Square(dest_row, dest_col)))
                                break
        
        return candidates[0] if len(candidates) == 1 else None
    
    def _is_en_passant(self, piece, move):
        """Check if move is en passant capture"""
        return (isinstance(piece, Pawn) and 
                abs(move.initial.col - move.final.col) == 1 and
                self.board.squares[move.final.row][move.final.col].isempty() and
                self.board.en_passant_target and
                move.final.row == self.board.en_passant_target.row and
                move.final.col == self.board.en_passant_target.col)
    
    def _create_move(self, from_row, from_col, to_row, to_col):
        """Create a move object"""
        from move import Move
        from square import Square
        return Move(Square(from_row, from_col), Square(to_row, to_col))