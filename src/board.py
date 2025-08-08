# [file name]: board.py
from const import *
from square import Square
from piece import Piece, Pawn, Knight, Bishop, Rook, Queen, King
from move import Move
from copy import deepcopy
from os.path import join, exists
from sound import Sound

class Board:

    def __init__(self):
        self.squares = []
        self.last_move = None
        self.en_passant_target = None
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.position_signatures = {}  # Track position signatures for repetition
        self.halfmove_clock = 0  # Track moves since last pawn move or capture (for 50-move rule)
        self.fullmove_number = 1  # Track full move number
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')
        self.record_position('white')  # Record initial position

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final

        # Check if this is an en passant capture
        is_en_passant = (piece.name.lower() == 'pawn' and 
                        abs(initial.col - final.col) == 1 and 
                        self.squares[final.row][final.col].isempty() and
                        self.en_passant_target and
                        final.row == self.en_passant_target.row and 
                        final.col == self.en_passant_target.col)
        
        # Check if this move is a capture or pawn move (for 50-move rule)
        is_capture = self.squares[final.row][final.col].has_piece() or is_en_passant
        is_pawn_move = piece.name.lower() == 'pawn'
        
        # Clear the en passant target from previous move
        old_en_passant = self.en_passant_target
        self.en_passant_target = None

        # Move the piece
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        # Handle pawn-specific moves
        if piece.name.lower() == 'pawn':
            # Check for double pawn push (sets new en passant target)
            if abs(initial.row - final.row) == 2:
                self.en_passant_target = Square(
                    (initial.row + final.row) // 2,
                    initial.col
                )
            
            # Handle en passant capture
            if is_en_passant:
                # Remove the captured pawn
                captured_pawn_row = initial.row  # Same row as attacking pawn
                captured_pawn_col = final.col    # Same column as target square
                self.squares[captured_pawn_row][captured_pawn_col].piece = None
                if not testing:
                    sound_path = join('..', 'assets', 'sounds', 'capture.wav')
                    if not exists(sound_path):
                        sound_path = join('assets', 'sounds', 'capture.wav')
                    sound = Sound(sound_path)
                    sound.play()
            
            # Handle pawn promotion
            if final.row == 0 or final.row == 7:
                self.check_promotion(piece, final)

        # Handle king castling
        if piece.name.lower() == 'king':
            # Update castling rights
            if piece.color == 'white':
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False
            
            # Handle castling move
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook_col = 0 if diff < 0 else 7
                new_rook_col = 3 if diff < 0 else 5
                
                # Get rook from original position
                rook = self.squares[initial.row][rook_col].piece
                
                # Move rook to new position
                self.squares[initial.row][rook_col].piece = None
                self.squares[initial.row][new_rook_col].piece = rook
                rook.moved = True

        # Handle rook moves - update castling rights
        if piece.name.lower() == 'rook':
            if initial.col == 0:  # Queenside rook
                if piece.color == 'white':
                    self.castling_rights['Q'] = False
                else:
                    self.castling_rights['q'] = False
            elif initial.col == 7:  # Kingside rook
                if piece.color == 'white':
                    self.castling_rights['K'] = False
                else:
                    self.castling_rights['k'] = False

        # Mark piece as moved
        piece.moved = True

        # Clear valid moves
        piece.clear_moves()

        # Set last move
        self.last_move = move
        
        # Update halfmove clock for 50-move rule
        if is_capture or is_pawn_move:
            self.halfmove_clock = 0  # Reset on capture or pawn move
        else:
            self.halfmove_clock += 1
        
        # Update fullmove number (increments after black's move)
        if piece.color == 'black':
            self.fullmove_number += 1
        
        # Record position for next player
        next_player = 'black' if piece.color == 'white' else 'white'
        self.record_position(next_player)

    def record_position(self, next_player):
        """Record the current position signature"""
        signature = self.get_position_signature(next_player)
        self.position_signatures[signature] = self.position_signatures.get(signature, 0) + 1

    def get_position_signature(self, next_player):
        """Create a unique signature for the current position"""
        # Signature includes: board state + castling rights + en passant + next player
        signature = ""
        
        # Board state
        for row in range(ROWS):
            for col in range(COLS):
                if self.squares[row][col].isempty():
                    signature += "."
                else:
                    piece = self.squares[row][col].piece
                    symbol = piece.symbol()
                    signature += symbol.upper() if piece.color == 'white' else symbol.lower()
        
        # Castling rights
        castling_str = ""
        if self.castling_rights['K']: castling_str += "K"
        if self.castling_rights['Q']: castling_str += "Q"
        if self.castling_rights['k']: castling_str += "k"
        if self.castling_rights['q']: castling_str += "q"
        signature += castling_str if castling_str else "-"
        
        # En passant
        if self.en_passant_target:
            col_char = chr(97 + self.en_passant_target.col)
            row_num = 8 - self.en_passant_target.row
            signature += f"{col_char}{row_num}"
        else:
            signature += "-"
        
        # Next player
        signature += next_player[0]  # 'w' or 'b'
        
        return signature

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        # This method is no longer needed since we handle en passant with target squares
        # Keeping it for compatibility but it does nothing
        pass

    def in_check(self, piece, move):
        # Use shallow copy where possible for better performance
        temp_piece = deepcopy(piece)
        temp_board = deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        
        # Find the king position after the move
        king_pos = None
        for row in range(ROWS):
            for col in range(COLS):
                p = temp_board.squares[row][col].piece
                if isinstance(p, King) and p.color == piece.color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if not king_pos:
            return False
        
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    for m in p.moves:
                        if (m.final.row == king_pos[0] and m.final.col == king_pos[1]):
                            return True
        
        return False
                        
    def is_king_in_check(self, color):
        # Find the king
        king_pos = None
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
                
        if not king_pos:
            return False
            
        # Check if any enemy piece can attack the king
        enemy_color = 'black' if color == 'white' else 'white'
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color == enemy_color:
                    self.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if move.final.row == king_pos[0] and move.final.col == king_pos[1]:
                            piece.clear_moves()
                            return True
                    piece.clear_moves()
                    
        return False
        
    def is_checkmate(self, color):
        # King must be in check
        if not self.is_king_in_check(color):
            return False
            
        # Check if any move can get out of check
        return not self._has_legal_move(color)
    
    def _has_legal_move(self, color):
        """Check if the given color has any legal moves"""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    if self._can_escape_check(piece, row, col, color):
                        return True
        return False
    
    def _can_escape_check(self, piece, row, col, color):
        """Check if any move by this piece can escape check"""
        for move in piece.moves:
            temp_board = deepcopy(self)
            temp_piece = temp_board.squares[row][col].piece
            temp_board.move(temp_piece, move, testing=True)
            if not temp_board.is_king_in_check(color):
                return True
        return False
        
    def is_stalemate(self, color):
        # King not in check
        if self.is_king_in_check(color):
            return False
            
        # Check if any piece has legal moves
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    if piece.moves:
                        return False
        return True
        
    def is_threefold_repetition(self):
        # Check if any position has occurred 3 times
        for count in self.position_signatures.values():
            if count >= 3:
                return True
        return False
    
    def is_fifty_move_rule(self):
        """Check if 50-move rule applies (50 moves without pawn move or capture)"""
        return self.halfmove_clock >= 100  # 100 half-moves = 50 full moves

    def calc_moves(self, piece, row, col, bool=True):
        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        initial = Square(row, col)
                        final = Square(possible_move_row, col)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)
                    else: break
                else: break

            # Regular diagonal captures
            possible_move_row = row + piece.dir
            possible_move_cols = [col-1, col+1]
            for possible_move_col in possible_move_cols:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

            # En passant captures
            if self.en_passant_target:
                # Check if pawn is on the correct rank for en passant
                en_passant_rank = 3 if piece.color == 'white' else 4
                if row == en_passant_rank:
                    # Check if pawn is adjacent to the en passant target column
                    if abs(col - self.en_passant_target.col) == 1:
                        # Check if there's an enemy pawn to capture
                        # The enemy pawn is on the same row as our pawn (adjacent)
                        enemy_pawn_row = row
                        if (Square.in_range(enemy_pawn_row, self.en_passant_target.col) and
                            self.squares[enemy_pawn_row][self.en_passant_target.col].has_enemy_piece(piece.color) and
                            isinstance(self.squares[enemy_pawn_row][self.en_passant_target.col].piece, Pawn)):
                            
                            initial = Square(row, col)
                            final = Square(self.en_passant_target.row, self.en_passant_target.col)
                            move = Move(initial, final)
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

        def knight_moves():
            possible_moves = [
                (row-2, col+1),
                (row-1, col+2),
                (row+1, col+2),
                (row+2, col+1),
                (row+2, col-1),
                (row+1, col-2),
                (row-1, col-2),
                (row-2, col-1),
            ]
            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

        def straightline_moves(incrs):
            for incr in incrs:
                row_incr, col_incr = incr
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr
                while True:
                    if Square.in_range(possible_move_row, possible_move_col):
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if self.squares[possible_move_row][possible_move_col].isempty():
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                        elif self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                            break
                        elif self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
                            break
                    else: break
                    possible_move_row += row_incr
                    possible_move_col += col_incr

        def king_moves():
            adjs = [
                (row-1, col+0),
                (row-1, col+1),
                (row+0, col+1),
                (row+1, col+1),
                (row+1, col+0),
                (row+1, col-1),
                (row+0, col-1),
                (row-1, col-1),
            ]
            for possible_move in adjs:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

            # Castling
            if not piece.moved:
                # Kingside castling
                if (piece.color == 'white' and self.castling_rights['K']) or \
                   (piece.color == 'black' and self.castling_rights['k']):
                    if self.squares[row][7].has_piece() and isinstance(self.squares[row][7].piece, Rook) and not self.squares[row][7].piece.moved:
                        empty = True
                        for c in range(5, 7):  # Between king and rook
                            if self.squares[row][c].has_piece():
                                empty = False
                                break
                        if empty:
                            initial = Square(row, col)
                            final = Square(row, 6)
                            move = Move(initial, final)
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

                # Queenside castling
                if (piece.color == 'white' and self.castling_rights['Q']) or \
                   (piece.color == 'black' and self.castling_rights['q']):
                    if self.squares[row][0].has_piece() and isinstance(self.squares[row][0].piece, Rook) and not self.squares[row][0].piece.moved:
                        empty = True
                        for c in range(1, 4):  # Between king and rook
                            if self.squares[row][c].has_piece():
                                empty = False
                                break
                        if empty:
                            initial = Square(row, col)
                            final = Square(row, 2)
                            move = Move(initial, final)
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

        if isinstance(piece, Pawn): pawn_moves()
        elif isinstance(piece, Knight): knight_moves()
        elif isinstance(piece, Bishop): 
            straightline_moves([(-1, 1), (-1, -1), (1, 1), (1, -1)])
        elif isinstance(piece, Rook): 
            straightline_moves([(-1, 0), (0, 1), (1, 0), (0, -1)])
        elif isinstance(piece, Queen): 
            straightline_moves([
                (-1, 1), (-1, -1), (1, 1), (1, -1),
                (-1, 0), (0, 1), (1, 0), (0, -1)
            ])
        elif isinstance(piece, King): king_moves()

    def _create(self):
        self.squares = [[Square(row, col) for col in range(COLS)] for row in range(ROWS)]

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))
        self.squares[row_other][4] = Square(row_other, 4, King(color))
    
    def to_fen(self, next_player):
        try:
            # Validate board state before generating FEN
            if not self._validate_board_state():
                print("Warning: Board state validation failed before FEN generation")
                return None
                
            board_fen = self._generate_board_fen()
            if board_fen is None:
                return None
            
            active_color = self._get_active_color_fen(next_player)
            if active_color is None:
                return None
            
            castling_fen = self._get_castling_fen()
            en_passant_fen = self._get_en_passant_fen()
            move_counts = self._get_move_counts_fen()
            
            return f"{board_fen} {active_color} {castling_fen} {en_passant_fen} {move_counts}"
            
        except Exception as e:
            print(f"Error generating FEN: {e}")
            return None
    
    def _validate_board_state(self):
        """Validate basic board state consistency"""
        try:
            # Check for exactly one king of each color
            white_kings = 0
            black_kings = 0
            
            for row in range(ROWS):
                for col in range(COLS):
                    square = self.squares[row][col]
                    if square.has_piece():
                        piece = square.piece
                        if piece.name.lower() == 'king':
                            if piece.color == 'white':
                                white_kings += 1
                            else:
                                black_kings += 1
            
            if white_kings != 1:
                print(f"Invalid board state: {white_kings} white kings found")
                return False
            if black_kings != 1:
                print(f"Invalid board state: {black_kings} black kings found")
                return False
                
            return True
        except Exception as e:
            print(f"Error validating board state: {e}")
            return False
    
    def _generate_board_fen(self):
        """Generate the board position part of FEN notation"""
        fen = ""
        empty_count = 0
        for row in range(ROWS):
            for col in range(COLS):
                square = self.squares[row][col]
                if square.isempty():
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    piece_char = self._get_piece_fen_char(square.piece, row, col)
                    if piece_char is None:
                        return None
                    fen += piece_char
            if empty_count > 0:
                fen += str(empty_count)
            if row < ROWS - 1:
                fen += '/'
            empty_count = 0
        return fen
    
    def _get_piece_fen_char(self, piece, row, col):
        """Get FEN character for a piece with validation"""
        if piece is None:
            print(f"Warning: Found None piece at ({row},{col}) in non-empty square")
            return None
        if not hasattr(piece, 'symbol') or not hasattr(piece, 'color'):
            print(f"Warning: Invalid piece at ({row},{col}): {piece}")
            return None
        fen_char = piece.symbol()
        if not fen_char or fen_char == '?':
            print(f"Warning: Invalid piece symbol at ({row},{col}): {piece.name}")
            return None
        return fen_char.upper() if piece.color == 'white' else fen_char.lower()
    
    def _get_active_color_fen(self, next_player):
        """Get active color part of FEN notation"""
        if next_player not in ['white', 'black']:
            print(f"Warning: Invalid next_player: {next_player}")
            return None
        return 'w' if next_player == 'white' else 'b'
    
    def _get_castling_fen(self):
        """Get castling rights part of FEN notation"""
        castling = ""
        if self.castling_rights and isinstance(self.castling_rights, dict):
            if self.castling_rights.get('K'): castling += 'K'
            if self.castling_rights.get('Q'): castling += 'Q'
            if self.castling_rights.get('k'): castling += 'k'
            if self.castling_rights.get('q'): castling += 'q'
        return castling if castling else "-"
    
    def _get_en_passant_fen(self):
        """Get en passant target part of FEN notation"""
        if (self.en_passant_target and 
            hasattr(self.en_passant_target, 'col') and 
            hasattr(self.en_passant_target, 'row') and
            0 <= self.en_passant_target.col <= 7 and 
            0 <= self.en_passant_target.row <= 7):
            col_char = chr(97 + self.en_passant_target.col)
            row_num = 8 - self.en_passant_target.row
            return f"{col_char}{row_num}"
        return "-"
    
    def _get_move_counts_fen(self):
        """Get halfmove clock and fullmove number for FEN notation"""
        halfmove = self.halfmove_clock if isinstance(self.halfmove_clock, int) and self.halfmove_clock >= 0 else 0
        fullmove = self.fullmove_number if isinstance(self.fullmove_number, int) and self.fullmove_number >= 1 else 1
        return f"{halfmove} {fullmove}"
    
    def from_fen(self, fen):
        # Clear the board first
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col].piece = None
        
        parts = fen.split()
        if len(parts) < 1:
            return
        
        # Parse piece placement
        board_part = parts[0]
        row = 0
        col = 0
        for char in board_part:
            if char == '/':
                row += 1
                col = 0
                if row >= ROWS:  # Bounds check
                    break
            elif char.isdigit():
                col += int(char)
                if col >= COLS:  # Bounds check
                    col = COLS - 1
            else:
                if row >= ROWS or col >= COLS:  # Bounds check
                    continue
                color = 'white' if char.isupper() else 'black'
                piece_type = char.lower()
                if piece_type == 'p': piece = Pawn(color)
                elif piece_type == 'n': piece = Knight(color)
                elif piece_type == 'b': piece = Bishop(color)
                elif piece_type == 'r': piece = Rook(color)
                elif piece_type == 'q': piece = Queen(color)
                elif piece_type == 'k': piece = King(color)
                else: continue  # Skip invalid pieces
                
                self.squares[row][col].piece = piece
                col += 1
        
        # Parse active color
        if len(parts) > 1:
            # Set active color - though not directly used here
            pass
        
        # Parse castling rights
        if len(parts) > 2:
            castling_str = parts[2]
            if castling_str == '-':
                self.castling_rights = {'K': False, 'Q': False, 'k': False, 'q': False}
            else:
                self.castling_rights = {
                    'K': 'K' in castling_str,
                    'Q': 'Q' in castling_str,
                    'k': 'k' in castling_str,
                    'q': 'q' in castling_str
                }
        
        # Parse en passant target
        if len(parts) > 3:
            ep_str = parts[3]
            if ep_str != '-' and len(ep_str) >= 2:
                try:
                    col_char = ep_str[0]
                    row_char = ep_str[1]
                    ep_col = ord(col_char) - 97  # a=0, b=1, etc.
                    ep_row = 8 - int(row_char)
                    # Bounds check
                    if 0 <= ep_row < ROWS and 0 <= ep_col < COLS:
                        self.en_passant_target = Square(ep_row, ep_col)
                    else:
                        self.en_passant_target = None
                except (ValueError, IndexError):
                    self.en_passant_target = None
            else:
                self.en_passant_target = None
# [file content end]