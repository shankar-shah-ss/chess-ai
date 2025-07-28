# [file name]: board.py
# [file content begin]
from const import *
from square import Square
from piece import *
from move import Move
import copy
import os
from sound import Sound

class Board:

    def __init__(self):
        self.squares = []
        self.last_move = None
        self.en_passant_target = None
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.position_signatures = {}  # Track position signatures for repetition
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')
        self.record_position('white')  # Record initial position

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()
        
        # Reset en passant target if not a double pawn push
        if not (isinstance(piece, Pawn) and abs(initial.row - final.row) == 2):
            self.en_passant_target = None

        # console board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            # Check for en passant opportunity
            if abs(initial.row - final.row) == 2:
                # Set en passant target
                self.en_passant_target = Square(
                    (initial.row + final.row) // 2,
                    initial.col
                )
            else:
                self.en_passant_target = None
            
            # en passant capture
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty and self.en_passant_target and \
               final.row == self.en_passant_target.row and final.col == self.en_passant_target.col:
                # Capture the pawn
                captured_pawn_row = initial.row
                captured_pawn_col = final.col
                self.squares[captured_pawn_row][captured_pawn_col].piece = None
                if not testing:
                    sound = Sound(
                        os.path.join('assets/sounds/capture.wav'))
                    sound.play()
            
            # pawn promotion (for any move reaching last rank)
            if final.row == 0 or final.row == 7:
                self.check_promotion(piece, final)

        # king castling - improved logic
        if isinstance(piece, King):
            # Update castling rights
            if piece.color == 'white':
                self.castling_rights['K'] = False
                self.castling_rights['Q'] = False
            else:
                self.castling_rights['k'] = False
                self.castling_rights['q'] = False
            
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

        # Rook move - update castling rights
        if isinstance(piece, Rook):
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

        # move
        piece.moved = True

        # clear valid moves
        piece.clear_moves()

        # set last move
        self.last_move = move
        
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
        signature += self.castling_rights['K'] and "K" or ""
        signature += self.castling_rights['Q'] and "Q" or ""
        signature += self.castling_rights['k'] and "k" or ""
        signature += self.castling_rights['q'] and "q" or ""
        signature += "-" if not any(self.castling_rights.values()) else ""
        
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
        if not isinstance(piece, Pawn):
            return

        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    self.squares[row][col].piece.en_passant = False
        
        piece.en_passant = True

    def in_check(self, piece, move):
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col, bool=False)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
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
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.squares[row][col].piece
                if piece and piece.color == color:
                    self.calc_moves(piece, row, col, bool=True)
                    for move in piece.moves:
                        # Test if this move gets out of check
                        temp_board = copy.deepcopy(self)
                        temp_piece = temp_board.squares[row][col].piece
                        temp_board.move(temp_piece, move, testing=True)
                        if not temp_board.is_king_in_check(color):
                            return False
        return True
        
    def is_stalemate(self, color):
        # King not in check
        if self.is_king_in_check(color):
            return False
            
        # Check if any legal move exists
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

            # En passant
            r = 3 if piece.color == 'white' else 4
            fr = 2 if piece.color == 'white' else 5
            # Left capture
            if Square.in_range(col-1) and row == r:
                if self.squares[row][col-1].has_enemy_piece(piece.color):
                    p = self.squares[row][col-1].piece
                    if isinstance(p, Pawn) and p.en_passant:
                        initial = Square(row, col)
                        final = Square(fr, col-1)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)
            # Right capture
            if Square.in_range(col+1) and row == r:
                if self.squares[row][col+1].has_enemy_piece(piece.color):
                    p = self.squares[row][col+1].piece
                    if isinstance(p, Pawn) and p.en_passant:
                        initial = Square(row, col)
                        final = Square(fr, col+1)
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
                    piece = square.piece
                    fen_char = piece.symbol()
                    fen += fen_char.upper() if piece.color == 'white' else fen_char.lower()
            if empty_count > 0:
                fen += str(empty_count)
            if row < ROWS - 1:
                fen += '/'
            empty_count = 0
        
        # Active color
        fen += " " + ('w' if next_player == 'white' else 'b') + " "
        
        # Castling availability
        castling = ""
        if self.castling_rights['K']: castling += 'K'
        if self.castling_rights['Q']: castling += 'Q'
        if self.castling_rights['k']: castling += 'k'
        if self.castling_rights['q']: castling += 'q'
        fen += castling if castling else "-"
        fen += " "
        
        # En passant target
        if self.en_passant_target:
            col_char = chr(97 + self.en_passant_target.col)  # a-h
            row_num = 8 - self.en_passant_target.row
            fen += f"{col_char}{row_num}"
        else:
            fen += "-"
        fen += " "
        
        # Halfmove clock and fullmove number
        fen += "0 1"
        return fen
    
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
            elif char.isdigit():
                col += int(char)
            else:
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
            if ep_str != '-':
                col_char = ep_str[0]
                row_char = ep_str[1]
                ep_col = ord(col_char) - 97  # a=0, b=1, etc.
                ep_row = 8 - int(row_char)
                self.en_passant_target = Square(ep_row, ep_col)
            else:
                self.en_passant_target = None
# [file content end]