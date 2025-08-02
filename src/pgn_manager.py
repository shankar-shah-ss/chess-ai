#!/usr/bin/env python3
"""
PGN (Portable Game Notation) Manager for Chess AI
Handles recording, formatting, and saving chess games in standard PGN format
"""

import os
import datetime
from typing import List, Dict, Optional, Tuple
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
        
        # Set PGN headers
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
            'Generator': 'Chess AI v1.0'
        }
    
    def add_move(self, move, piece, captured_piece=None, is_check=False, 
                is_checkmate=False, is_castling=False, promotion_piece=None):
        """Add a move to the PGN record"""
        # Generate proper algebraic notation
        notation = self._generate_algebraic_notation(
            move, piece, captured_piece, is_check, is_checkmate, 
            is_castling, promotion_piece
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
            'promotion': promotion_piece
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
                                   is_castling=False, promotion_piece=None) -> str:
        """Generate proper algebraic notation for a move"""
        if is_castling:
            # Determine if kingside or queenside castling
            if move.final.col > move.initial.col:
                return "O-O"  # Kingside
            else:
                return "O-O-O"  # Queenside
        
        notation = ""
        
        # Piece notation (empty for pawns)
        if piece.name != 'pawn':
            piece_symbols = {
                'knight': 'N',
                'bishop': 'B', 
                'rook': 'R',
                'queen': 'Q',
                'king': 'K'
            }
            notation += piece_symbols.get(piece.name, piece.name[0].upper())
        
        # File and rank notation
        col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_file = col_map[move.initial.col]
        from_rank = str(8 - move.initial.row)
        to_file = col_map[move.final.col]
        to_rank = str(8 - move.final.row)
        
        # For pawns, include file only if capturing
        if piece.name == 'pawn':
            if captured_piece:
                notation += from_file
        else:
            # For pieces, we might need disambiguation (simplified for now)
            # TODO: Add proper disambiguation logic for multiple pieces
            pass
        
        # Capture notation
        if captured_piece:
            notation += "x"
        
        # Destination square
        notation += to_file + to_rank
        
        # Promotion
        if promotion_piece:
            notation += "=" + promotion_piece[0].upper()
        
        # Check and checkmate
        if is_checkmate:
            notation += "#"
        elif is_check:
            notation += "+"
        
        return notation
    
    def set_result(self, result: str, reason: str = ""):
        """Set the game result"""
        self.result = result
        self.headers['Result'] = result
        self.game_end_time = datetime.datetime.now()
        
        # Add termination reason if provided
        if reason:
            self.headers['Termination'] = reason
    
    def generate_pgn(self) -> str:
        """Generate the complete PGN string"""
        pgn_lines = []
        
        # Add headers
        for key, value in self.headers.items():
            if value:  # Only include non-empty headers
                pgn_lines.append(f'[{key} "{value}"]')
        
        # Add empty line after headers
        pgn_lines.append("")
        
        # Add moves
        move_line = ""
        current_move_num = 1
        
        for i, move in enumerate(self.moves):
            if move['color'] == 'white':
                if move_line:  # Add previous line if exists
                    pgn_lines.append(move_line.strip())
                move_line = f"{current_move_num}. {move['notation']}"
            else:
                move_line += f" {move['notation']}"
                current_move_num += 1
        
        # Add final move line if exists
        if move_line:
            pgn_lines.append(move_line.strip())
        
        # Add result
        if self.moves:  # Only add result if there are moves
            pgn_lines.append("")
            pgn_lines.append(self.result)
        
        return "\n".join(pgn_lines)
    
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
        """Record a move in PGN format"""
        if not self.recording:
            return
        
        # Check game state
        opponent_color = 'black' if piece.color == 'white' else 'white'
        is_check = self.game.board.is_king_in_check(opponent_color)
        is_checkmate = self.game.board.is_checkmate(opponent_color) if is_check else False
        
        # Check for castling (simplified detection)
        is_castling = (piece.name == 'king' and 
                      abs(move.final.col - move.initial.col) == 2)
        
        # Record the move
        self.pgn_manager.add_move(
            move=move,
            piece=piece,
            captured_piece=captured_piece,
            is_check=is_check,
            is_checkmate=is_checkmate,
            is_castling=is_castling
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