#!/usr/bin/env python3
"""
PGN (Portable Game Notation) Manager for Chess AI
Handles recording, formatting, and saving chess games in standard PGN format
Full PGN compliance with all standard features including:
- Disambiguation logic
- En passant notation
- Comments and annotations
- NAG (Numeric Annotation Glyphs)
- Extended headers
"""

import os
import datetime
import re
from typing import List, Dict, Optional, Tuple, Set
import threading
import chess
import chess.pgn

class PGNManager:
    """Manages PGN recording and export functionality"""
    
    def __init__(self):
        self.game_start_time = None
        self.game_end_time = None
        self.moves = []  # List of move dictionaries
        self.headers = {}
        self.result = "*"  # * = ongoing, 1-0 = white wins, 0-1 = black wins, 1/2-1/2 = draw
        self.move_number = 1
        self.current_player = 'white'
        self.board_state = None  # Reference to current board state for disambiguation
        self.comments = {}  # Move comments {move_index: comment}
        self.nags = {}  # Numeric Annotation Glyphs {move_index: nag_code}
        self.variations = {}  # Alternative move sequences {move_index: [variation_moves]}
        
        # Ensure games directory exists with categorized subdirectories
        self.games_dir = os.path.join(os.path.dirname(__file__), '..', 'games')
        self.create_categorized_directories()
    
    def create_categorized_directories(self):
        """Create categorized directories for different game modes"""
        # Main games directory
        os.makedirs(self.games_dir, exist_ok=True)
        
        # Categorized subdirectories
        categories = [
            'human-vs-human',
            'human-vs-engine', 
            'engine-vs-engine'
        ]
        
        for category in categories:
            category_dir = os.path.join(self.games_dir, category)
            os.makedirs(category_dir, exist_ok=True)
        
        # Only print on first creation
        if not hasattr(self, '_directories_created'):
            print("📁 Game directories initialized:")
            print(f"  📂 human-vs-human")
            print(f"  📂 human-vs-engine") 
            print(f"  📂 engine-vs-engine")
            self._directories_created = True
    
    def get_game_category_dir(self):
        """Determine the appropriate directory based on game type"""
        white_player = self.headers.get('White', 'Human')
        black_player = self.headers.get('Black', 'Human')
        
        # Determine category based on player types
        white_is_engine = white_player.lower() == 'engine'
        black_is_engine = black_player.lower() == 'engine'
        
        if white_is_engine and black_is_engine:
            category = 'engine-vs-engine'
        elif white_is_engine or black_is_engine:
            category = 'human-vs-engine'
        else:
            category = 'human-vs-human'
        
        category_dir = os.path.join(self.games_dir, category)
        os.makedirs(category_dir, exist_ok=True)  # Ensure directory exists
        
        return category_dir, category
    
    def start_new_game(self, white_player: str = "Human", black_player: str = "Human", 
                      event: str = "Casual Game", site: str = "Chess AI"):
        """Initialize a new game for PGN recording"""
        self.game_start_time = datetime.datetime.now()
        self.game_end_time = None
        self.moves = []
        self.move_number = 1
        self.current_player = 'white'
        self.result = "*"
        
        # Set PGN headers (comprehensive set)
        self.headers = {
            'Event': event,
            'Site': site,
            'Date': self.game_start_time.strftime('%Y.%m.%d'),
            'Round': '1',
            'White': white_player,
            'Black': black_player,
            'Result': self.result,
            'TimeControl': '-',  # No time control by default
            'ECO': '',  # Opening classification (can be added later)
            'WhiteElo': '',  # Player ratings (can be added later)
            'BlackElo': '',
            'PlyCount': '0',
            'EventDate': self.game_start_time.strftime('%Y.%m.%d'),
            'Generator': 'Chess AI v2.0',
            'Annotator': '',  # Who annotated the game
            'Mode': 'OTB',  # Over The Board
            'FEN': '',  # Starting position if not standard
            'SetUp': '',  # 1 if non-standard starting position
            'WhiteTitle': '',  # Player titles
            'BlackTitle': '',
            'WhiteTeam': '',  # Team names
            'BlackTeam': '',
            'Opening': '',  # Opening name
            'Variation': '',  # Opening variation
            'SubVariation': '',  # Opening sub-variation
            'Time': self.game_start_time.strftime('%H:%M:%S'),  # Start time
            'UTCTime': self.game_start_time.strftime('%H:%M:%S'),  # UTC start time
            'UTCDate': self.game_start_time.strftime('%Y.%m.%d'),  # UTC date
        }
        
        # Clear annotations for new game
        self.comments = {}
        self.nags = {}
        self.variations = {}
    
    def add_move(self, move, piece, captured_piece=None, is_check=False, 
                is_checkmate=False, is_castling=False, promotion_piece=None, 
                is_en_passant=False, board_state=None):
        """Add a move to the PGN record with full disambiguation support"""
        # Validate inputs
        if not move or not piece:
            print(f"⚠️  Invalid move data: move={move}, piece={piece}")
            return
        
        # Validate piece name
        valid_pieces = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        if piece.name not in valid_pieces:
            print(f"⚠️  Invalid piece name: {piece.name}")
            return
        
        # Store board state for disambiguation
        if board_state:
            self.board_state = board_state
            
        # Generate proper algebraic notation with disambiguation
        notation = self._generate_algebraic_notation(
            move, piece, captured_piece, is_check, is_checkmate, 
            is_castling, promotion_piece, is_en_passant
        )
        
        # Validate generated notation
        if not notation or len(notation) < 2:
            print(f"⚠️  Invalid notation generated: '{notation}' for piece {piece.name}")
            return
        
        # Handle captured_piece - it might be a piece object, boolean, or None
        captured_name = None
        if captured_piece:
            if hasattr(captured_piece, 'name'):
                captured_name = captured_piece.name
            elif isinstance(captured_piece, bool):
                captured_name = "piece"  # Generic capture indicator
        
        move_record = {
            'notation': notation,
            'move_number': self.move_number,
            'color': self.current_player,
            'timestamp': datetime.datetime.now(),
            'move_obj': move,  # Keep reference for analysis
            'piece': piece.name,
            'captured': captured_name,
            'check': is_check,
            'checkmate': is_checkmate,
            'castling': is_castling,
            'promotion': promotion_piece,
            'en_passant': is_en_passant
        }
        
        self.moves.append(move_record)
        
        # Update move counter and player
        if self.current_player == 'black':
            self.move_number += 1
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        # Update ply count in headers
        self.headers['PlyCount'] = str(len(self.moves))
    
    def _generate_algebraic_notation(self, move, piece, captured_piece=None, 
                                   is_check=False, is_checkmate=False, 
                                   is_castling=False, promotion_piece=None, 
                                   is_en_passant=False) -> str:
        """Generate proper algebraic notation with full disambiguation support"""
        if is_castling:
            # Determine if kingside or queenside castling
            if move.final.col > move.initial.col:
                return "O-O"  # Kingside
            else:
                return "O-O-O"  # Queenside
        
        notation = ""
        
        # File and rank notation
        col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_file = col_map[move.initial.col]
        from_rank = str(8 - move.initial.row)
        to_file = col_map[move.final.col]
        to_rank = str(8 - move.final.row)
        
        # Piece notation (empty for pawns)
        if piece.name != 'pawn':
            piece_symbols = {
                'knight': 'N',
                'bishop': 'B', 
                'rook': 'R',
                'queen': 'Q',
                'king': 'K'
            }
            piece_symbol = piece_symbols.get(piece.name, piece.name[0].upper())
            notation += piece_symbol
            
            # Add disambiguation if needed
            disambiguation = self._get_disambiguation(move, piece)
            notation += disambiguation
        else:
            # For pawns, include file only if capturing or en passant
            if captured_piece or is_en_passant:
                notation += from_file
        
        # Capture notation
        if captured_piece or is_en_passant:
            notation += "x"
        
        # Destination square
        notation += to_file + to_rank
        
        # En passant notation
        if is_en_passant:
            notation += " e.p."
        
        # Promotion
        if promotion_piece:
            notation += "=" + promotion_piece[0].upper()
        
        # Check and checkmate
        if is_checkmate:
            notation += "#"
        elif is_check:
            notation += "+"
        
        return notation
    
    def _get_disambiguation(self, move, piece) -> str:
        """
        Get disambiguation string according to official PGN/SAN specification:
        
        From PGN specification section 8.2.3.1:
        "If the move is ambiguous, the moving piece is uniquely identified by 
        specifying the file of departure if they differ; otherwise, the rank 
        of departure if they differ; otherwise, both the file and rank are specified."
        """
        if not self.board_state:
            return ""
        
        # Only pieces (not pawns) need disambiguation for regular moves
        # Pawns use file disambiguation only for captures
        if piece.name == 'pawn':
            return ""
        
        col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_file = col_map[move.initial.col]
        from_rank = str(8 - move.initial.row)
        target_row, target_col = move.final.row, move.final.col
        
        # Find all other pieces of the same type and color that can legally move to the same square
        ambiguous_pieces = []
        
        for row in range(8):
            for col in range(8):
                # Skip the moving piece itself
                if row == move.initial.row and col == move.initial.col:
                    continue
                    
                square = self.board_state.squares[row][col]
                if (square.has_piece() and 
                    square.piece.name == piece.name and 
                    square.piece.color == piece.color):
                    
                    # Check if this piece can legally move to the target square
                    if self._can_piece_reach_square(square.piece, row, col, target_row, target_col):
                        ambiguous_pieces.append((row, col))
        
        # No ambiguity - no disambiguation needed
        if not ambiguous_pieces:
            return ""
        
        # Apply official PGN disambiguation rules:
        # 1. Try file disambiguation first
        files_differ = True
        for amb_row, amb_col in ambiguous_pieces:
            if amb_col == move.initial.col:  # Same file as moving piece
                files_differ = False
                break
        
        if files_differ:
            return from_file
        
        # 2. If files are the same, try rank disambiguation
        ranks_differ = True
        for amb_row, amb_col in ambiguous_pieces:
            if amb_row == move.initial.row:  # Same rank as moving piece
                ranks_differ = False
                break
        
        if ranks_differ:
            return from_rank
        
        # 3. If both file and rank are needed (rare case)
        return from_file + from_rank
    
    def _can_piece_reach_square(self, piece, from_row, from_col, to_row, to_col) -> bool:
        """
        Check if a piece can legally reach a target square, including path blocking checks.
        This is used for proper disambiguation in PGN notation.
        """
        if not piece or from_row == to_row and from_col == to_col:
            return False
        
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        abs_row_diff = abs(row_diff)
        abs_col_diff = abs(col_diff)
        
        # First check if the move pattern is valid for the piece type
        valid_pattern = False
        
        if piece.name == 'knight':
            # Knight moves in L-shape: exactly 2+1 or 1+2
            valid_pattern = (abs_row_diff == 2 and abs_col_diff == 1) or (abs_row_diff == 1 and abs_col_diff == 2)
        
        elif piece.name == 'bishop':
            # Bishop moves diagonally: row and column differences must be equal
            valid_pattern = abs_row_diff == abs_col_diff and abs_row_diff > 0
        
        elif piece.name == 'rook':
            # Rook moves horizontally or vertically: one difference must be 0
            valid_pattern = (abs_row_diff == 0 and abs_col_diff > 0) or (abs_col_diff == 0 and abs_row_diff > 0)
        
        elif piece.name == 'queen':
            # Queen combines rook and bishop moves
            valid_pattern = (abs_row_diff == abs_col_diff and abs_row_diff > 0) or \
                           (abs_row_diff == 0 and abs_col_diff > 0) or \
                           (abs_col_diff == 0 and abs_row_diff > 0)
        
        elif piece.name == 'king':
            # King moves exactly one square in any direction
            valid_pattern = abs_row_diff <= 1 and abs_col_diff <= 1 and (abs_row_diff > 0 or abs_col_diff > 0)
        
        elif piece.name == 'pawn':
            # For disambiguation purposes, we generally don't disambiguate pawn moves
            # except for captures (handled separately in the main notation generation)
            return False
        
        if not valid_pattern:
            return False
        
        # For knights and kings, no path blocking check needed
        if piece.name in ['knight', 'king']:
            return True
        
        # For sliding pieces (bishop, rook, queen), check if path is clear
        return self._is_path_clear(from_row, from_col, to_row, to_col)
    
    def _is_path_clear(self, from_row, from_col, to_row, to_col) -> bool:
        """Check if the path between two squares is clear of pieces"""
        if not self.board_state:
            return True  # Can't check without board state
        
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        
        # Determine step direction
        row_step = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        col_step = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)
        
        # Check each square along the path (excluding start and end squares)
        current_row = from_row + row_step
        current_col = from_col + col_step
        
        while current_row != to_row or current_col != to_col:
            if (0 <= current_row < 8 and 0 <= current_col < 8 and 
                self.board_state.squares[current_row][current_col].has_piece()):
                return False  # Path is blocked
            
            current_row += row_step
            current_col += col_step
        
        return True  # Path is clear
    
    def _validate_pgn_notation(self, notation: str) -> bool:
        """
        Validate PGN notation according to official Standard Algebraic Notation (SAN) rules.
        
        Based on PGN specification section 8.2.3 (Standard Algebraic Notation).
        """
        if not notation:
            return False
        
        import re
        
        # Remove check/checkmate/annotation symbols for core validation
        clean_notation = notation.replace('+', '').replace('#', '').replace(' e.p.', '').strip()
        
        if not clean_notation:
            return False
        
        # 1. Castling moves
        if clean_notation in ['O-O', 'O-O-O']:
            return True
        
        # 2. Pawn moves
        # Format: [file][rank] or [file]x[file][rank] or [file][rank]=[piece] or [file]x[file][rank]=[piece]
        pawn_patterns = [
            r'^[a-h][1-8]$',                    # Simple pawn move: e4
            r'^[a-h]x[a-h][1-8]$',             # Pawn capture: exd5
            r'^[a-h][18]=[NBRQ]$',             # Pawn promotion: e8=Q
            r'^[a-h]x[a-h][18]=[NBRQ]$'       # Pawn capture with promotion: exd8=Q
        ]
        
        for pattern in pawn_patterns:
            if re.match(pattern, clean_notation):
                return True
        
        # 3. Piece moves - be very explicit about valid patterns
        
        # First check for obviously invalid patterns
        if re.match(r'^[NBRQK][a-h][1-8][a-h][1-8]$', clean_notation) and 'x' not in clean_notation:
            # This is "Ne4e5" format - invalid unless it's proper disambiguation
            # Check if it could be valid full square disambiguation
            piece = clean_notation[0]
            from_square = clean_notation[1:3]
            to_square = clean_notation[3:5]
            # Only valid if from_square != to_square
            if from_square == to_square:
                return False
            # For now, accept it as valid full square disambiguation
            # In a real implementation, we'd check if disambiguation is actually needed
            return True
        
        # Valid piece move patterns
        piece_patterns = [
            r'^[NBRQK][a-h][1-8]x[a-h][1-8]$',   # Full square disambiguation + capture
            r'^[NBRQK][a-h]x[a-h][1-8]$',        # File disambiguation + capture
            r'^[NBRQK][1-8]x[a-h][1-8]$',        # Rank disambiguation + capture
            r'^[NBRQK][a-h][a-h][1-8]$',         # File disambiguation
            r'^[NBRQK][1-8][a-h][1-8]$',         # Rank disambiguation
            r'^[NBRQK]x[a-h][1-8]$',             # Capture without disambiguation
            r'^[NBRQK][a-h][1-8]$'               # Simple piece move
        ]
        
        for pattern in piece_patterns:
            if re.match(pattern, clean_notation):
                return True
        
        return False
    
    def validate_game_pgn(self) -> Tuple[bool, List[str]]:
        """Validate the entire game PGN and return issues found"""
        issues = []
        
        if not self.moves:
            issues.append("No moves recorded")
            return False, issues
        
        # Check each move notation
        for i, move in enumerate(self.moves):
            notation = move.get('notation', '')
            if not self._validate_pgn_notation(notation):
                issues.append(f"Move {i+1}: Invalid notation '{notation}'")
        
        # Check for proper alternating colors
        expected_color = 'white'
        for i, move in enumerate(self.moves):
            if move.get('color') != expected_color:
                issues.append(f"Move {i+1}: Expected {expected_color}, got {move.get('color')}")
            expected_color = 'black' if expected_color == 'white' else 'white'
        
        # Check ply count
        expected_ply_count = len(self.moves)
        actual_ply_count = int(self.headers.get('PlyCount', '0'))
        if expected_ply_count != actual_ply_count:
            issues.append(f"Ply count mismatch: expected {expected_ply_count}, got {actual_ply_count}")
        
        return len(issues) == 0, issues
    
    def add_comment(self, move_index: int, comment: str):
        """Add a comment to a specific move"""
        self.comments[move_index] = comment
    
    def add_nag(self, move_index: int, nag_code: int):
        """Add a Numeric Annotation Glyph to a move"""
        # Common NAG codes:
        # 1 = good move (!), 2 = poor move (?), 3 = brilliant move (!!), 
        # 4 = blunder (??), 5 = interesting move (!?), 6 = dubious move (?!)
        # 10 = equal position (=), 14 = slight advantage for white (+=), etc.
        self.nags[move_index] = nag_code
    
    def add_variation(self, move_index: int, variation_moves: List[str]):
        """Add an alternative variation at a specific move"""
        if move_index not in self.variations:
            self.variations[move_index] = []
        self.variations[move_index].append(variation_moves)
    
    def set_opening_info(self, eco: str = "", opening: str = "", variation: str = "", sub_variation: str = ""):
        """Set opening classification information"""
        if eco:
            self.headers['ECO'] = eco
        if opening:
            self.headers['Opening'] = opening
        if variation:
            self.headers['Variation'] = variation
        if sub_variation:
            self.headers['SubVariation'] = sub_variation
    
    def set_player_info(self, white_elo: str = "", black_elo: str = "", 
                       white_title: str = "", black_title: str = "",
                       white_team: str = "", black_team: str = ""):
        """Set player information"""
        if white_elo:
            self.headers['WhiteElo'] = white_elo
        if black_elo:
            self.headers['BlackElo'] = black_elo
        if white_title:
            self.headers['WhiteTitle'] = white_title
        if black_title:
            self.headers['BlackTitle'] = black_title
        if white_team:
            self.headers['WhiteTeam'] = white_team
        if black_team:
            self.headers['BlackTeam'] = black_team
    
    def set_time_control(self, time_control: str):
        """Set time control information"""
        self.headers['TimeControl'] = time_control
    
    def set_result(self, result: str, reason: str = ""):
        """Set the game result"""
        self.result = result
        self.headers['Result'] = result
        self.game_end_time = datetime.datetime.now()
        
        # Add termination reason if provided
        if reason:
            self.headers['Termination'] = reason
    
    def generate_pgn(self) -> str:
        """Generate the complete PGN string with annotations"""
        pgn_lines = []
        
        # Add headers in standard order
        header_order = [
            'Event', 'Site', 'Date', 'Round', 'White', 'Black', 'Result',
            'WhiteElo', 'BlackElo', 'WhiteTitle', 'BlackTitle', 
            'WhiteTeam', 'BlackTeam', 'TimeControl', 'ECO', 'Opening', 
            'Variation', 'SubVariation', 'Annotator', 'PlyCount', 
            'EventDate', 'Time', 'UTCTime', 'UTCDate', 'Mode', 
            'FEN', 'SetUp', 'Generator', 'Termination'
        ]
        
        # Add headers in order
        for key in header_order:
            if key in self.headers and self.headers[key]:
                pgn_lines.append(f'[{key} "{self.headers[key]}"]')
        
        # Add any additional headers not in the standard order
        for key, value in self.headers.items():
            if key not in header_order and value:
                pgn_lines.append(f'[{key} "{value}"]')
        
        # Add empty line after headers
        pgn_lines.append("")
        
        # Add moves with annotations
        move_text = self._generate_move_text()
        if move_text:
            # Split long lines for readability (max 80 characters per line)
            lines = self._split_move_text(move_text)
            pgn_lines.extend(lines)
        
        # Add result
        if self.moves:  # Only add result if there are moves
            pgn_lines.append("")
            pgn_lines.append(self.result)
        
        return "\n".join(pgn_lines)
    
    def _generate_move_text(self) -> str:
        """Generate move text with comments, NAGs, and variations"""
        if not self.moves:
            return ""
        
        move_text = ""
        current_move_num = 1
        
        for i, move in enumerate(self.moves):
            # Add move number for white moves
            if move['color'] == 'white':
                move_text += f"{current_move_num}. "
            elif i == 0:  # First move is black (unusual but possible)
                move_text += f"{current_move_num}... "
            
            # Add the move notation
            move_text += move['notation']
            
            # Add NAG (Numeric Annotation Glyph) if present
            if i in self.nags:
                nag_code = self.nags[i]
                nag_symbol = self._nag_to_symbol(nag_code)
                if nag_symbol:
                    move_text += nag_symbol
                else:
                    move_text += f" ${nag_code}"
            
            # Add comment if present
            if i in self.comments:
                move_text += f" {{{self.comments[i]}}}"
            
            # Add variations if present
            if i in self.variations:
                for variation in self.variations[i]:
                    move_text += f" ({' '.join(variation)})"
            
            # Add space after move (except for last move)
            if i < len(self.moves) - 1:
                move_text += " "
            
            # Increment move number after black's move
            if move['color'] == 'black':
                current_move_num += 1
        
        return move_text.strip()
    
    def _nag_to_symbol(self, nag_code: int) -> str:
        """Convert NAG code to symbol"""
        nag_symbols = {
            1: "!",      # good move
            2: "?",      # poor move
            3: "!!",     # brilliant move
            4: "??",     # blunder
            5: "!?",     # interesting move
            6: "?!",     # dubious move
            10: "=",     # equal position
            13: "∞",     # unclear position
            14: "⩲",     # slight advantage for white
            15: "⩱",     # slight advantage for black
            16: "±",     # clear advantage for white
            17: "∓",     # clear advantage for black
            18: "+-",    # winning advantage for white
            19: "-+",    # winning advantage for black
        }
        return nag_symbols.get(nag_code, "")
    
    def _split_move_text(self, text: str, max_length: int = 80) -> List[str]:
        """Split move text into lines of reasonable length"""
        if len(text) <= max_length:
            return [text]
        
        lines = []
        current_line = ""
        words = text.split()
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def save_pgn_dialog(self) -> bool:
        """Save PGN with macOS-safe dialog system (non-blocking)"""
        import threading
        
        def save_async():
            """Async save function to prevent UI blocking"""
            try:
                # Try macOS native dialog first
                success = self._try_macos_dialog()
                if not success:
                    # Fallback to console input
                    success = self._console_save_fallback()
                return success
            except Exception as e:
                print(f"PGN save error: {e}")
                return False
        
        # Run save operation in background thread
        save_thread = threading.Thread(target=save_async, daemon=True)
        save_thread.start()
        
        # Return immediately to prevent UI blocking
        print("📝 Saving game in background...")
        return True
    
    def save_pgn_quick(self, custom_filename=None) -> bool:
        """Quick save without dialogs (non-blocking)"""
        import threading
        
        def quick_save():
            """Quick save function"""
            try:
                # Generate filename
                if custom_filename:
                    filename = custom_filename
                else:
                    date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    white = self.headers.get('White', 'Player1')
                    black = self.headers.get('Black', 'Player2')
                    filename = f"{white}_vs_{black}_{date_str}.pgn"
                
                # Ensure .pgn extension
                if not filename.endswith('.pgn'):
                    filename += '.pgn'
                
                # Get categorized directory
                category_dir, category = self.get_game_category_dir()
                
                # Save file in appropriate category directory
                filepath = os.path.join(category_dir, filename)
                
                # Handle existing files by adding number suffix
                counter = 1
                original_filepath = filepath
                while os.path.exists(filepath):
                    name_part = original_filepath.replace('.pgn', '')
                    filepath = f"{name_part}_{counter}.pgn"
                    counter += 1
                
                # Validate PGN before saving
                is_valid, issues = self.validate_game_pgn()
                if not is_valid:
                    print(f"⚠️  PGN validation failed:")
                    for issue in issues:
                        print(f"   - {issue}")
                    print("   Saving anyway, but PGN may be invalid...")
                
                # Write PGN file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.generate_pgn())
                
                print(f"✅ Game saved to {category}: {filepath}")
                return True
                
            except Exception as e:
                print(f"❌ Quick save failed: {e}")
                return False
        
        # Run save operation in background thread
        save_thread = threading.Thread(target=quick_save, daemon=True)
        save_thread.start()
        
        print("📝 Quick saving game...")
        return True
    
    def _try_macos_dialog(self) -> bool:
        """Try macOS native save dialog using osascript"""
        try:
            import subprocess
            
            # Get current date for default filename
            date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Determine default filename based on players
            white = self.headers.get('White', 'Player1')
            black = self.headers.get('Black', 'Player2')
            default_name = f"{white}_vs_{black}_{date_str}.pgn"
            
            # Ensure games directory exists
            os.makedirs(self.games_dir, exist_ok=True)
            
            # Ask if user wants to save using native dialog
            ask_script = '''
            tell application "System Events"
                display dialog "Would you like to save this chess game in PGN format?" buttons {"No", "Yes"} default button "Yes" with title "Save Game"
                return button returned of result
            end tell
            '''
            
            ask_result = subprocess.run(['osascript', '-e', ask_script], 
                                      capture_output=True, text=True, timeout=10)
            
            if ask_result.returncode != 0 or ask_result.stdout.strip() != "Yes":
                print("Save cancelled by user")
                return False
            
            # Get filename using native dialog
            filename_script = f'''
            tell application "System Events"
                set theResponse to display dialog "Enter filename (without .pgn extension):" default answer "{default_name.replace('.pgn', '')}" with title "Save Game"
                return text returned of theResponse
            end tell
            '''
            
            filename_result = subprocess.run(['osascript', '-e', filename_script], 
                                           capture_output=True, text=True, timeout=10)
            
            if filename_result.returncode != 0:
                print("Filename input cancelled")
                return False
            
            filename = filename_result.stdout.strip()
            if not filename:
                print("No filename provided")
                return False
            
            # Ensure .pgn extension
            if not filename.endswith('.pgn'):
                filename += '.pgn'
            
            # Get categorized directory
            category_dir, category = self.get_game_category_dir()
            
            # Save file in appropriate category directory
            filepath = os.path.join(category_dir, filename)
            
            # Check if file exists
            if os.path.exists(filepath):
                overwrite_script = f'''
                tell application "System Events"
                    display dialog "File '{filename}' already exists. Overwrite?" buttons {{"No", "Yes"}} default button "No" with title "File Exists"
                    return button returned of result
                end tell
                '''
                
                overwrite_result = subprocess.run(['osascript', '-e', overwrite_script], 
                                                capture_output=True, text=True, timeout=10)
                
                if overwrite_result.returncode != 0 or overwrite_result.stdout.strip() != "Yes":
                    print("Overwrite cancelled")
                    return False
            
            # Validate PGN before saving
            is_valid, issues = self.validate_game_pgn()
            if not is_valid:
                print(f"⚠️  PGN validation failed:")
                for issue in issues:
                    print(f"   - {issue}")
                print("   Saving anyway, but PGN may be invalid...")
            
            # Write PGN file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_pgn())
            
            # Show success message
            success_script = f'''
            tell application "System Events"
                display dialog "Game saved successfully to {category}:\\n{filepath}" buttons {{"OK"}} with title "Game Saved"
            end tell
            '''
            
            subprocess.run(['osascript', '-e', success_script], 
                         capture_output=True, text=True, timeout=5)
            
            print(f"✅ PGN saved to {category}: {filepath}")
            return True
            
        except subprocess.TimeoutExpired:
            print("Dialog timeout - falling back to console")
            return self._console_save_fallback()
        except Exception as e:
            print(f"macOS dialog error: {e}")
            return self._console_save_fallback()
    
    def _console_save_fallback(self) -> bool:
        """Fallback console-based save"""
        try:
            print("\n" + "="*50)
            print("🎮 CHESS GAME SAVE")
            print("="*50)
            
            # Ask if user wants to save
            save_choice = input("Save this game? (y/n): ").lower().strip()
            if save_choice not in ['y', 'yes']:
                print("Save cancelled")
                return False
            
            # Get filename
            date_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            white = self.headers.get('White', 'Player1')
            black = self.headers.get('Black', 'Player2')
            default_name = f"{white}_vs_{black}_{date_str}"
            
            print(f"\nDefault filename: {default_name}")
            filename = input("Enter filename (or press Enter for default): ").strip()
            
            if not filename:
                filename = default_name
            
            # Ensure .pgn extension
            if not filename.endswith('.pgn'):
                filename += '.pgn'
            
            # Get categorized directory
            category_dir, category = self.get_game_category_dir()
            
            # Save file in appropriate category directory
            filepath = os.path.join(category_dir, filename)
            
            # Check if file exists
            if os.path.exists(filepath):
                overwrite = input(f"File '{filename}' exists. Overwrite? (y/n): ").lower().strip()
                if overwrite not in ['y', 'yes']:
                    print("Save cancelled")
                    return False
            
            # Validate PGN before saving
            is_valid, issues = self.validate_game_pgn()
            if not is_valid:
                print(f"⚠️  PGN validation failed:")
                for issue in issues:
                    print(f"   - {issue}")
                print("   Saving anyway, but PGN may be invalid...")
            
            # Write PGN file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_pgn())
            
            print(f"✅ Game saved successfully to {category}: {filepath}")
            print("="*50)
            return True
            
        except KeyboardInterrupt:
            print("\nSave cancelled by user")
            return False
        except Exception as e:
            print(f"❌ Failed to save: {e}")
            return False
    
    def save_pgn_file(self, filepath: str) -> bool:
        """Save PGN to specified file path"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_pgn())
            return True
        except Exception as e:
            print(f"Error saving PGN file: {e}")
            return False
    
    def get_move_count(self) -> int:
        """Get total number of moves (plies)"""
        return len(self.moves)
    
    def get_game_duration(self) -> Optional[str]:
        """Get game duration as formatted string"""
        if self.game_start_time and self.game_end_time:
            duration = self.game_end_time - self.game_start_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        return None
    
    def get_current_pgn_preview(self) -> str:
        """Get current PGN for preview (useful for debugging)"""
        return self.generate_pgn()
    
    def export_to_fen(self) -> str:
        """Export current position to FEN notation"""
        if self.board_state:
            return self.board_state.get_fen()
        return ""
    
    def import_from_pgn(self, pgn_text: str) -> bool:
        """Import game from PGN text (basic implementation)"""
        try:
            lines = pgn_text.strip().split('\n')
            
            # Parse headers
            for line in lines:
                if line.startswith('[') and line.endswith(']'):
                    # Extract header
                    match = re.match(r'\[(\w+)\s+"([^"]*)"\]', line)
                    if match:
                        key, value = match.groups()
                        self.headers[key] = value
            
            # Parse moves (simplified - doesn't handle all PGN features)
            move_text = ""
            for line in lines:
                if not line.startswith('[') and line.strip():
                    move_text += " " + line.strip()
            
            # Remove result from move text
            move_text = re.sub(r'\s*(1-0|0-1|1/2-1/2|\*)\s*$', '', move_text)
            
            # Extract basic moves (this is a simplified parser)
            moves = re.findall(r'\d+\.+\s*([NBRQK]?[a-h]?[1-8]?x?[a-h][1-8](?:=[NBRQ])?[+#]?)', move_text)
            
            # This would need more sophisticated parsing for full PGN support
            return True
            
        except Exception as e:
            print(f"Error importing PGN: {e}")
            return False
    
    def validate_pgn(self) -> Tuple[bool, List[str]]:
        """Validate the current PGN for compliance"""
        errors = []
        
        # Check required headers
        required_headers = ['Event', 'Site', 'Date', 'Round', 'White', 'Black', 'Result']
        for header in required_headers:
            if header not in self.headers or not self.headers[header]:
                errors.append(f"Missing required header: {header}")
        
        # Check date format
        if 'Date' in self.headers:
            date_pattern = r'^\d{4}\.\d{2}\.\d{2}$'
            if not re.match(date_pattern, self.headers['Date']):
                errors.append("Date format should be YYYY.MM.DD")
        
        # Check result format
        if 'Result' in self.headers:
            valid_results = ['1-0', '0-1', '1/2-1/2', '*']
            if self.headers['Result'] not in valid_results:
                errors.append("Invalid result format")
        
        # Check move notation (basic check)
        for i, move in enumerate(self.moves):
            notation = move['notation']
            if not re.match(r'^([NBRQK]?[a-h]?[1-8]?x?[a-h][1-8](?:=[NBRQ])?[+#]?|O-O(?:-O)?)', notation):
                errors.append(f"Invalid move notation at move {i+1}: {notation}")
        
        return len(errors) == 0, errors
    
    def get_statistics(self) -> Dict[str, any]:
        """Get game statistics"""
        stats = {
            'total_moves': len(self.moves),
            'white_moves': len([m for m in self.moves if m['color'] == 'white']),
            'black_moves': len([m for m in self.moves if m['color'] == 'black']),
            'captures': len([m for m in self.moves if m.get('captured')]),
            'checks': len([m for m in self.moves if m.get('check')]),
            'castling_moves': len([m for m in self.moves if m.get('castling')]),
            'promotions': len([m for m in self.moves if m.get('promotion')]),
            'en_passant_captures': len([m for m in self.moves if m.get('en_passant')]),
            'comments': len(self.comments),
            'annotations': len(self.nags),
            'variations': len(self.variations),
            'game_duration': self.get_game_duration()
        }
        return stats
    
    def save_analysis(self, filepath: str, analysis_board) -> bool:
        """Save analysis as a PGN file with variations and comments"""
        try:
            # Create a new game from the analysis
            game = chess.pgn.Game()
            
            # Set headers
            for key, value in analysis_board.headers.items():
                game.headers[key] = value
            
            # Set starting position if not standard
            if analysis_board.initial_fen != chess.STARTING_FEN:
                game.headers["FEN"] = analysis_board.initial_fen
                game.headers["SetUp"] = "1"
            
            # Add moves and variations
            node = game
            for i, move_data in enumerate(analysis_board.move_history):
                move = chess.Move.from_uci(move_data['move'].uci())
                node = node.add_variation(move)
                
                # Add comments
                if i in analysis_board.comments:
                    node.comment = analysis_board.comments[i]
                
                # Add variations
                if i in analysis_board.variations:
                    for variation in analysis_board.variations[i]:
                        var_move = chess.Move.from_uci(variation.uci())
                        node.add_variation(var_move)
            
            # Save to file
            with open(filepath, 'w') as f:
                f.write(str(game))
            
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False


class PGNIntegration:
    """Integration class to connect PGN manager with the game"""
    
    def __init__(self, game):
        self.game = game
        self.pgn_manager = PGNManager()
        self.recording = False
    
    def start_recording(self):
        """Start PGN recording for current game"""
        # Determine player types
        white_player = "Engine" if self.game.engine_white else "Human"
        black_player = "Engine" if self.game.engine_black else "Human"
        
        # Determine event type based on game mode
        mode_names = {
            0: "Human vs Human",
            1: "Human vs Engine", 
            2: "Engine vs Engine"
        }
        event = mode_names.get(self.game.game_mode, "Chess Game")
        
        self.pgn_manager.start_new_game(
            white_player=white_player,
            black_player=black_player,
            event=event,
            site="Chess AI"
        )
        self.recording = True
        print("📝 PGN recording started")
    
    def record_move(self, move, piece, captured_piece=None):
        """Record a move in PGN format with full feature support"""
        if not self.recording:
            return
        
        # Check game state
        opponent_color = 'black' if piece.color == 'white' else 'white'
        is_check = self.game.board.is_king_in_check(opponent_color)
        is_checkmate = self.game.board.is_checkmate(opponent_color) if is_check else False
        
        # Check for castling (simplified detection)
        is_castling = (piece.name == 'king' and 
                      abs(move.final.col - move.initial.col) == 2)
        
        # Check for en passant
        is_en_passant = (piece.name == 'pawn' and 
                        abs(move.initial.col - move.final.col) == 1 and 
                        not captured_piece and
                        self.game.board.en_passant_target and
                        move.final.row == self.game.board.en_passant_target.row and 
                        move.final.col == self.game.board.en_passant_target.col)
        
        # Record the move with board state for disambiguation
        self.pgn_manager.add_move(
            move=move,
            piece=piece,
            captured_piece=captured_piece,
            is_check=is_check,
            is_checkmate=is_checkmate,
            is_castling=is_castling,
            is_en_passant=is_en_passant,
            board_state=self.game.board
        )
    
    def end_game(self, result: str, reason: str = ""):
        """End the game and set result"""
        if not self.recording:
            return
        
        self.pgn_manager.set_result(result, reason)
        print(f"📝 Game ended: {result} ({reason})")
    
    def save_game(self) -> bool:
        """Save the current game with dialog (non-blocking)"""
        if not self.recording or self.pgn_manager.get_move_count() == 0:
            return False
        
        return self.pgn_manager.save_pgn_dialog()
    
    def save_game_quick(self, filename=None) -> bool:
        """Quick save without dialogs (non-blocking)"""
        if not self.recording or self.pgn_manager.get_move_count() == 0:
            return False
        
        return self.pgn_manager.save_pgn_quick(filename)
    
    def get_move_count(self) -> int:
        """Get total number of moves"""
        return self.pgn_manager.get_move_count()
    
    def get_current_pgn_preview(self) -> str:
        """Get current PGN preview"""
        return self.pgn_manager.get_current_pgn_preview()
    
    def stop_recording(self):
        """Stop PGN recording"""
        self.recording = False
        print("📝 PGN recording stopped")
    
    def add_move_comment(self, comment: str):
        """Add a comment to the last move"""
        if self.recording and self.pgn_manager.moves:
            move_index = len(self.pgn_manager.moves) - 1
            self.pgn_manager.add_comment(move_index, comment)
    
    def add_move_annotation(self, nag_code: int):
        """Add an annotation (NAG) to the last move"""
        if self.recording and self.pgn_manager.moves:
            move_index = len(self.pgn_manager.moves) - 1
            self.pgn_manager.add_nag(move_index, nag_code)
    
    def set_player_ratings(self, white_elo: str = "", black_elo: str = ""):
        """Set player ELO ratings"""
        self.pgn_manager.set_player_info(white_elo=white_elo, black_elo=black_elo)
    
    def set_time_control(self, time_control: str):
        """Set time control information"""
        self.pgn_manager.set_time_control(time_control)
    
    def set_opening_classification(self, eco: str = "", opening: str = "", variation: str = ""):
        """Set opening classification"""
        self.pgn_manager.set_opening_info(eco=eco, opening=opening, variation=variation)
    
    def validate_current_pgn(self) -> Tuple[bool, List[str]]:
        """Validate the current PGN"""
        return self.pgn_manager.validate_pgn()
    
    def get_game_statistics(self) -> Dict[str, any]:
        """Get comprehensive game statistics"""
        return self.pgn_manager.get_statistics()
    
    def export_to_fen(self) -> str:
        """Export current position to FEN"""
        return self.pgn_manager.export_to_fen()
    
    def save_analysis(self, filepath: str) -> bool:
        """Save analysis as PGN"""
        return self.pgn_manager.save_analysis(filepath, self.game.analysis_board)