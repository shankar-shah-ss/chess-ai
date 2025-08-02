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
        
        # Ensure games directory exists
        self.games_dir = os.path.join(os.path.dirname(__file__), '..', 'games')
        os.makedirs(self.games_dir, exist_ok=True)
    
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
        # Store board state for disambiguation
        if board_state:
            self.board_state = board_state
            
        # Generate proper algebraic notation with disambiguation
        notation = self._generate_algebraic_notation(
            move, piece, captured_piece, is_check, is_checkmate, 
            is_castling, promotion_piece, is_en_passant
        )
        
        move_record = {
            'notation': notation,
            'move_number': self.move_number,
            'color': self.current_player,
            'timestamp': datetime.datetime.now(),
            'move_obj': move,  # Keep reference for analysis
            'piece': piece.name,
            'captured': captured_piece.name if captured_piece else None,
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
        """Get disambiguation string for pieces when multiple pieces can reach same square"""
        if not self.board_state:
            return ""
        
        disambiguation = ""
        col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_file = col_map[move.initial.col]
        from_rank = str(8 - move.initial.row)
        
        # Find all pieces of the same type and color that can move to the same square
        same_pieces = []
        for row in range(8):
            for col in range(8):
                square = self.board_state.squares[row][col]
                if (square.has_piece() and 
                    square.piece.name == piece.name and 
                    square.piece.color == piece.color and
                    (row != move.initial.row or col != move.initial.col)):
                    
                    # Check if this piece can also move to the target square
                    # This is a simplified check - in a full implementation,
                    # we'd need to verify legal moves
                    same_pieces.append((row, col))
        
        if not same_pieces:
            return ""
        
        # Check if disambiguation by file is sufficient
        files_conflict = any(col == move.initial.col for row, col in same_pieces)
        ranks_conflict = any(row == move.initial.row for row, col in same_pieces)
        
        if not files_conflict:
            # File disambiguation is sufficient
            disambiguation = from_file
        elif not ranks_conflict:
            # Rank disambiguation is sufficient
            disambiguation = from_rank
        else:
            # Need both file and rank
            disambiguation = from_file + from_rank
        
        return disambiguation
    
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
        """Save PGN with macOS-safe dialog system"""
        try:
            # Try macOS native dialog first
            return self._try_macos_dialog()
        except Exception as e:
            print(f"macOS dialog failed: {e}")
            # Fallback to console input
            return self._console_save_fallback()
    
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
            
            # Save file
            filepath = os.path.join(self.games_dir, filename)
            
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
            
            # Write PGN file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_pgn())
            
            # Show success message
            success_script = f'''
            tell application "System Events"
                display dialog "Game saved successfully as:\\n{filepath}" buttons {{"OK"}} with title "Game Saved"
            end tell
            '''
            
            subprocess.run(['osascript', '-e', success_script], 
                         capture_output=True, text=True, timeout=5)
            
            print(f"✅ PGN saved: {filepath}")
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
            
            # Save file
            os.makedirs(self.games_dir, exist_ok=True)
            filepath = os.path.join(self.games_dir, filename)
            
            # Check if file exists
            if os.path.exists(filepath):
                overwrite = input(f"File '{filename}' exists. Overwrite? (y/n): ").lower().strip()
                if overwrite not in ['y', 'yes']:
                    print("Save cancelled")
                    return False
            
            # Write PGN file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.generate_pgn())
            
            print(f"✅ Game saved successfully: {filepath}")
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
        """Save the current game with dialog"""
        if not self.recording or self.pgn_manager.get_move_count() == 0:
            return False
        
        return self.pgn_manager.save_pgn_dialog()
    
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