# pgn_manager.py - PGN format support for game records
import datetime
from notation import ChessNotation

class PGNManager:
    def __init__(self, board):
        self.board = board
        self.notation = ChessNotation(board)
        self.game_info = {
            'Event': 'Chess AI Game',
            'Site': 'Local',
            'Date': datetime.datetime.now().strftime('%Y.%m.%d'),
            'Round': '1',
            'White': 'Player',
            'Black': 'Player',
            'Result': '*'
        }
        self.moves = []
        self.move_number = 1
        self.current_player = 'white'
        
    def set_game_info(self, **kwargs):
        """Set game information (Event, Site, White, Black, etc.)"""
        for key, value in kwargs.items():
            if key in self.game_info:
                self.game_info[key] = value
    
    def add_move(self, move, piece, captured=False, check=False, checkmate=False, 
                 promotion_piece=None):
        """Add a move to the PGN record"""
        # Generate algebraic notation
        algebraic = self.notation.move_to_algebraic(
            move, piece, captured, check, checkmate, 
            promotion_piece is not None, promotion_piece
        )
        
        # Store move with metadata
        move_data = {
            'number': self.move_number,
            'player': self.current_player,
            'notation': algebraic,
            'move_obj': move,
            'piece': piece,
            'captured': captured,
            'check': check,
            'checkmate': checkmate,
            'timestamp': datetime.datetime.now()
        }
        
        self.moves.append(move_data)
        
        # Update move counter and player
        if self.current_player == 'black':
            self.move_number += 1
        self.current_player = 'black' if self.current_player == 'white' else 'white'
        
        return algebraic
    
    def set_result(self, result):
        """Set game result (1-0, 0-1, 1/2-1/2, *)"""
        self.game_info['Result'] = result
    
    def get_pgn_string(self, include_analysis=False, analysis_data=None):
        """Generate complete PGN string"""
        pgn_lines = []
        
        # Add headers
        for key, value in self.game_info.items():
            pgn_lines.append(f'[{key} "{value}"]')
        
        # Add analysis info if available
        if include_analysis and analysis_data:
            pgn_lines.append(f'[WhiteElo "{analysis_data.get("white_elo", "?")}"]')
            pgn_lines.append(f'[BlackElo "{analysis_data.get("black_elo", "?")}"]')
            pgn_lines.append(f'[Annotator "Chess AI Analysis"]')
        
        pgn_lines.append('')  # Empty line after headers
        
        # Add moves
        move_text = self._format_moves(include_analysis, analysis_data)
        pgn_lines.append(move_text)
        
        return '\n'.join(pgn_lines)
    
    def _format_moves(self, include_analysis=False, analysis_data=None):
        """Format moves in PGN notation"""
        formatted_moves = []
        current_line = ""
        
        i = 0
        while i < len(self.moves):
            move = self.moves[i]
            
            # Add move number for white moves
            if move['player'] == 'white':
                move_num_text = f"{move['number']}."
                if len(current_line) + len(move_num_text) > 70:
                    formatted_moves.append(current_line.strip())
                    current_line = ""
                current_line += move_num_text + " "
            
            # Add the move
            move_text = move['notation']
            
            # Add analysis annotation if available
            if include_analysis and analysis_data:
                annotation = self._get_move_annotation(i, analysis_data)
                if annotation:
                    move_text += annotation
            
            # Check line length
            if len(current_line) + len(move_text) > 70:
                formatted_moves.append(current_line.strip())
                current_line = ""
            
            current_line += move_text + " "
            
            # Add black move on same line if it exists
            if (move['player'] == 'white' and i + 1 < len(self.moves) and 
                self.moves[i + 1]['player'] == 'black'):
                i += 1
                black_move = self.moves[i]
                black_text = black_move['notation']
                
                # Add analysis annotation for black move
                if include_analysis and analysis_data:
                    annotation = self._get_move_annotation(i, analysis_data)
                    if annotation:
                        black_text += annotation
                
                if len(current_line) + len(black_text) > 70:
                    formatted_moves.append(current_line.strip())
                    current_line = ""
                
                current_line += black_text + " "
            
            i += 1
        
        # Add remaining moves and result
        if current_line.strip():
            formatted_moves.append(current_line.strip())
        
        # Add result
        result_line = self.game_info['Result']
        if formatted_moves:
            formatted_moves[-1] += " " + result_line
        else:
            formatted_moves.append(result_line)
        
        return '\n'.join(formatted_moves)
    
    def _get_move_annotation(self, move_index, analysis_data):
        """Get analysis annotation for a move"""
        if not analysis_data or 'analyzed_moves' not in analysis_data:
            return ""
        
        analyzed_moves = analysis_data['analyzed_moves']
        if move_index >= len(analyzed_moves):
            return ""
        
        move_analysis = analyzed_moves[move_index]
        classification = move_analysis.get('classification', '')
        
        # Map classifications to PGN annotations
        annotation_map = {
            'brilliant': '!!',
            'great': '!',
            'best': '',
            'excellent': '',
            'okay': '',
            'miss': '?!',
            'inaccuracy': '?!',
            'mistake': '?',
            'blunder': '??'
        }
        
        annotation = annotation_map.get(classification.lower(), '')
        
        # Add evaluation if significant change
        eval_loss = move_analysis.get('eval_loss', 0)
        if eval_loss > 100:  # Significant evaluation loss
            if not annotation:
                annotation = '?'
        
        return annotation
    
    def save_to_file(self, filename, include_analysis=False, analysis_data=None):
        """Save PGN to file"""
        try:
            pgn_content = self.get_pgn_string(include_analysis, analysis_data)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pgn_content)
            return True
        except Exception as e:
            print(f"Error saving PGN: {e}")
            return False
    
    def load_from_file(self, filename):
        """Load PGN from file (basic implementation)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            
            # Parse headers
            for line in lines:
                if line.startswith('[') and line.endswith(']'):
                    # Extract header
                    header_content = line[1:-1]
                    if ' "' in header_content:
                        key, value = header_content.split(' "', 1)
                        value = value.rstrip('"')
                        if key in self.game_info:
                            self.game_info[key] = value
            
            # Find move text (after empty line)
            move_text = ""
            in_moves = False
            for line in lines:
                if not line.strip() and not in_moves:
                    in_moves = True
                    continue
                if in_moves and not line.startswith('['):
                    move_text += line + " "
            
            # Parse moves (basic implementation)
            self._parse_move_text(move_text.strip())
            
            return True
        except Exception as e:
            print(f"Error loading PGN: {e}")
            return False
    
    def _parse_move_text(self, move_text):
        """Parse move text from PGN (basic implementation)"""
        # This is a simplified parser - a full implementation would be more complex
        tokens = move_text.split()
        
        self.moves = []
        self.move_number = 1
        self.current_player = 'white'
        
        for token in tokens:
            # Skip move numbers
            if token.endswith('.') and token[:-1].isdigit():
                continue
            
            # Skip result
            if token in ['1-0', '0-1', '1/2-1/2', '*']:
                self.game_info['Result'] = token
                break
            
            # Remove annotations
            clean_token = token.rstrip('!?+#')
            
            if clean_token:
                # This would need to be connected to actual move parsing
                # For now, just store the notation
                move_data = {
                    'number': self.move_number,
                    'player': self.current_player,
                    'notation': clean_token,
                    'move_obj': None,
                    'piece': None,
                    'captured': 'x' in clean_token,
                    'check': '+' in token,
                    'checkmate': '#' in token,
                    'timestamp': datetime.datetime.now()
                }
                
                self.moves.append(move_data)
                
                if self.current_player == 'black':
                    self.move_number += 1
                self.current_player = 'black' if self.current_player == 'white' else 'white'
    
    def get_move_list(self):
        """Get list of moves in algebraic notation"""
        return [move['notation'] for move in self.moves]
    
    def get_current_position_fen(self):
        """Get FEN of current position"""
        return self.board.to_fen(self.current_player)
    
    def reset(self):
        """Reset PGN manager for new game"""
        self.moves = []
        self.move_number = 1
        self.current_player = 'white'
        self.game_info['Date'] = datetime.datetime.now().strftime('%Y.%m.%d')
        self.game_info['Result'] = '*'
    
    def get_game_summary(self):
        """Get summary of the game"""
        if not self.moves:
            return "No moves recorded"
        
        total_moves = len([m for m in self.moves if m['player'] == 'white'])
        duration = "Unknown"
        
        if len(self.moves) >= 2:
            start_time = self.moves[0]['timestamp']
            end_time = self.moves[-1]['timestamp']
            duration_seconds = (end_time - start_time).total_seconds()
            duration = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
        
        return f"Game: {self.game_info['White']} vs {self.game_info['Black']}\n" \
               f"Result: {self.game_info['Result']}\n" \
               f"Moves: {total_moves}\n" \
               f"Duration: {duration}"