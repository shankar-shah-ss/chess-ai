"""
Chess.com-style Analysis Screen
Recreates the exact layout and functionality of Chess.com's analysis page
"""

import pygame
import chess as python_chess
import chess.pgn as chess_pgn
from typing import Dict, List, Optional, Tuple
from const import *
import math

class ChessComAnalysis:
    """Chess.com-style analysis interface"""
    
    def __init__(self, config):
        self.config = config
        self.active = False
        self.analyzer = None
        self.current_move_index = 0
        self.game_moves = []
        self.move_analysis = []
        
        # Chess.com color scheme
        self.colors = {
            'bg': (40, 44, 52),           # Dark background
            'board_bg': (48, 52, 61),     # Board container
            'sidebar_bg': (32, 36, 43),   # Right sidebar
            'header_bg': (28, 32, 38),    # Top header
            'white_square': (240, 217, 181),
            'black_square': (181, 136, 99),
            'highlight': (255, 255, 0, 100),
            'move_highlight': (130, 151, 105),
            'text_primary': (255, 255, 255),
            'text_secondary': (170, 170, 170),
            'text_muted': (120, 120, 120),
            'accent': (129, 182, 76),     # Chess.com green
            'brilliant': (17, 172, 206),  # Brilliant move
            'great': (96, 181, 96),       # Great move
            'best': (96, 181, 96),        # Best move
            'good': (96, 181, 96),        # Good move
            'inaccuracy': (219, 169, 0),  # Inaccuracy
            'mistake': (255, 167, 38),    # Mistake
            'blunder': (255, 92, 92),     # Blunder
            'evaluation_bar': (129, 182, 76),
            'evaluation_bg': (60, 60, 60)
        }
        
        self.setup_layout()
        self.fonts = self._setup_fonts()
        
        # UI state
        self.scroll_offset = 0
        self.hovered_move = None
        self.selected_move = 0
        
    def setup_layout(self):
        """Setup Chess.com-style layout"""
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        
        # Header
        self.header_height = 60
        
        # Main content area (below header)
        self.content_y = self.header_height
        self.content_height = self.screen_height - self.header_height
        
        # Left side - Board area (60% of width)
        self.board_area_width = int(self.screen_width * 0.6)
        self.board_area_height = self.content_height
        
        # Board sizing (square, centered in left area)
        max_board_size = min(self.board_area_width - 40, self.content_height - 100)
        self.board_size = max_board_size - (max_board_size % 8)
        self.square_size = self.board_size // 8
        
        # Center board in left area
        self.board_x = (self.board_area_width - self.board_size) // 2
        self.board_y = self.content_y + (self.content_height - self.board_size) // 2
        
        # Evaluation bar (left of board)
        self.eval_bar_width = 8
        self.eval_bar_x = self.board_x - 20
        self.eval_bar_y = self.board_y
        self.eval_bar_height = self.board_size
        
        # Right sidebar (40% of width)
        self.sidebar_x = self.board_area_width
        self.sidebar_width = self.screen_width - self.board_area_width
        self.sidebar_y = self.content_y
        self.sidebar_height = self.content_height
        
        # Sidebar sections
        self.move_info_height = 120
        self.move_list_y = self.sidebar_y + self.move_info_height
        self.move_list_height = self.sidebar_height - self.move_info_height - 300
        self.summary_y = self.move_list_y + self.move_list_height
        self.summary_height = 150
        self.eval_graph_y = self.summary_y + self.summary_height
        self.eval_graph_height = 150
        
    def _setup_fonts(self) -> Dict[str, pygame.font.Font]:
        """Setup Chess.com-style fonts"""
        return {
            'header_title': pygame.font.SysFont('Segoe UI', 24, bold=True),
            'header_subtitle': pygame.font.SysFont('Segoe UI', 14),
            'move_number': pygame.font.SysFont('Segoe UI', 13, bold=True),
            'move_notation': pygame.font.SysFont('Segoe UI', 14, bold=True),
            'evaluation': pygame.font.SysFont('Segoe UI', 12, bold=True),
            'classification': pygame.font.SysFont('Segoe UI', 11, bold=True),
            'body': pygame.font.SysFont('Segoe UI', 13),
            'small': pygame.font.SysFont('Segoe UI', 11),
            'accuracy': pygame.font.SysFont('Segoe UI', 18, bold=True),
            'coordinates': pygame.font.SysFont('Segoe UI', 10),
        }
    
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        self._update_analysis_data()
    
    def _update_analysis_data(self):
        """Update analysis data from analyzer"""
        if not self.analyzer:
            self.move_analysis = []
            self.game_moves = []
            return
            
        # Get analyzed moves from enhanced analyzer
        if hasattr(self.analyzer, 'get_analyzed_moves'):
            analyzed_moves = self.analyzer.get_analyzed_moves()
            self.move_analysis = self._convert_analyzed_moves(analyzed_moves)
            self.game_moves = [move.get('move', '') for move in self.move_analysis]
        elif hasattr(self.analyzer, 'analyzed_moves'):
            # Direct access for compatibility
            analyzed_moves = self.analyzer.analyzed_moves
            self.move_analysis = self._convert_analyzed_moves(analyzed_moves)
            self.game_moves = [move.get('move', '') for move in self.move_analysis]
        else:
            self.move_analysis = []
            self.game_moves = []
    
    def _convert_analyzed_moves(self, analyzed_moves):
        """Convert namedtuple MoveAnalysis to dictionary format for Chess.com display"""
        converted_moves = []
        
        for move_analysis in analyzed_moves:
            # Handle both namedtuple and dictionary formats
            if hasattr(move_analysis, '_asdict'):
                # It's a namedtuple, convert to dict
                move_dict = move_analysis._asdict()
                
                # Map the enhanced analyzer fields to Chess.com format
                chess_com_move = {
                    'move': move_dict.get('move', ''),
                    'notation': self._get_move_notation(move_dict.get('move', '')),
                    'classification': move_dict.get('classification', 'Unknown'),
                    'evaluation_before': move_dict.get('eval_before', 0),
                    'evaluation_after': move_dict.get('eval_after', 0),
                    'player': move_dict.get('player', 'white'),
                    'move_number': move_dict.get('move_number', 0),
                    'eval_loss': move_dict.get('eval_loss', 0),
                    'best_moves': move_dict.get('best_moves', []),
                    'alternative_moves': move_dict.get('alternative_moves', [])
                }
            else:
                # It's already a dictionary
                chess_com_move = move_analysis
                
            converted_moves.append(chess_com_move)
        
        return converted_moves
    
    def _get_move_notation(self, move_obj):
        """Convert move object to algebraic notation"""
        if not move_obj:
            return "Unknown"
        
        try:
            # Handle different move object types
            if hasattr(move_obj, 'initial') and hasattr(move_obj, 'final'):
                # It's your custom Move class
                from_col = chr(ord('a') + move_obj.initial.col)
                from_row = str(move_obj.initial.row + 1)
                to_col = chr(ord('a') + move_obj.final.col)
                to_row = str(move_obj.final.row + 1)
                return f"{from_col}{from_row}{to_col}{to_row}"
                
            elif isinstance(move_obj, str):
                # It's a UCI string
                if len(move_obj) >= 4:
                    return move_obj  # Return UCI as-is for now
                return move_obj
                
            else:
                # Try to convert to string
                return str(move_obj)
                
        except Exception as e:
            # Fallback - return string representation
            try:
                return str(move_obj)
            except:
                return "Unknown"
    
    def _extract_numeric_evaluation(self, eval_data):
        """Extract numeric evaluation from various formats"""
        if eval_data is None:
            return 0
            
        # Handle different evaluation formats
        if isinstance(eval_data, (int, float)):
            # Already a number
            return float(eval_data)
            
        elif isinstance(eval_data, dict):
            # Dictionary format like {'type': 'cp', 'value': 50}
            if 'type' in eval_data and 'value' in eval_data:
                eval_type = eval_data['type']
                value = eval_data['value']
                
                if eval_type == 'cp':
                    # Centipawns - convert to pawns
                    return value / 100.0
                elif eval_type == 'mate':
                    # Mate in X moves - convert to large positive/negative value
                    return 20 if value > 0 else -20
                else:
                    return float(value) if isinstance(value, (int, float)) else 0
            else:
                # Try to find any numeric value in the dict
                for key in ['value', 'eval', 'score', 'evaluation']:
                    if key in eval_data:
                        val = eval_data[key]
                        if isinstance(val, (int, float)):
                            return float(val)
                return 0
                
        elif isinstance(eval_data, str):
            # String format - try to parse
            try:
                return float(eval_data)
            except:
                return 0
                
        else:
            # Unknown format
            try:
                return float(eval_data)
            except:
                return 0
    
    def activate(self):
        """Activate analysis mode"""
        self.active = True
        # Refresh analysis data when activating
        self._update_analysis_data()
        self.current_move_index = len(self.game_moves) if self.game_moves else 0
    
    def deactivate(self):
        """Deactivate analysis mode"""
        self.active = False
    
    def render(self, surface):
        """Render Chess.com-style analysis screen"""
        if not self.active:
            return
        
        # Update analysis data if analyzer is available
        if self.analyzer and hasattr(self.analyzer, 'is_analysis_complete'):
            if self.analyzer.is_analysis_complete() or len(self.analyzer.get_analyzed_moves()) > len(self.move_analysis):
                self._update_analysis_data()
            
        # Fill background
        surface.fill(self.colors['bg'])
        
        # Draw header
        self._draw_header(surface)
        
        # Draw board area
        self._draw_board_area(surface)
        
        # Draw evaluation bar
        self._draw_evaluation_bar(surface)
        
        # Draw board
        self._draw_board(surface)
        
        # Draw sidebar
        self._draw_sidebar(surface)
        
        # Draw evaluation graph
        self._draw_evaluation_graph(surface)
    
    def _draw_header(self, surface):
        """Draw Chess.com-style header"""
        # Header background
        header_rect = pygame.Rect(0, 0, self.screen_width, self.header_height)
        pygame.draw.rect(surface, self.colors['header_bg'], header_rect)
        
        # Title
        title_text = self.fonts['header_title'].render("Game Analysis", True, self.colors['text_primary'])
        surface.blit(title_text, (20, 15))
        
        # Analysis progress bar (center)
        self._draw_progress_bar(surface)
        
        # Controls (right side)
        controls_x = self.screen_width - 200
        
        # Exit button
        exit_text = self.fonts['header_subtitle'].render("Press ESC to exit", True, self.colors['text_secondary'])
        surface.blit(exit_text, (controls_x, 20))
        
        # Divider line
        pygame.draw.line(surface, self.colors['text_muted'], 
                        (0, self.header_height-1), (self.screen_width, self.header_height-1))
    
    def _draw_progress_bar(self, surface):
        """Draw analysis progress bar in header"""
        if not self.analyzer:
            return
            
        # Get progress from analyzer
        progress = 0
        is_complete = False
        
        if hasattr(self.analyzer, 'get_analysis_progress'):
            progress = self.analyzer.get_analysis_progress()
        if hasattr(self.analyzer, 'is_analysis_complete'):
            is_complete = self.analyzer.is_analysis_complete()
            
        # Progress bar dimensions
        bar_width = 300
        bar_height = 6
        bar_x = (self.screen_width - bar_width) // 2
        bar_y = 35
        
        # Progress bar background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, self.colors['text_muted'], bg_rect)
        
        # Progress bar fill
        if progress > 0:
            fill_width = int((progress / 100) * bar_width)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            color = self.colors['accent'] if not is_complete else self.colors['great']
            pygame.draw.rect(surface, color, fill_rect)
        
        # Progress text
        if is_complete:
            progress_text = "Analysis Complete"
            text_color = self.colors['great']
        elif progress > 0:
            progress_text = f"Analyzing... {progress}%"
            text_color = self.colors['accent']
        else:
            progress_text = "Starting Analysis..."
            text_color = self.colors['text_secondary']
            
        text_surface = self.fonts['small'].render(progress_text, True, text_color)
        text_x = bar_x + (bar_width - text_surface.get_width()) // 2
        text_y = bar_y + bar_height + 5
        surface.blit(text_surface, (text_x, text_y))
    
    def _draw_board_area(self, surface):
        """Draw board container area"""
        board_area_rect = pygame.Rect(0, self.content_y, self.board_area_width, self.board_area_height)
        pygame.draw.rect(surface, self.colors['board_bg'], board_area_rect)
    
    def _draw_evaluation_bar(self, surface):
        """Draw Chess.com-style evaluation bar"""
        if not self.move_analysis or self.current_move_index >= len(self.move_analysis):
            return
            
        # Get current evaluation
        current_eval = 0
        if self.current_move_index < len(self.move_analysis):
            move_data = self.move_analysis[self.current_move_index]
            if 'evaluation_after' in move_data:
                eval_data = move_data['evaluation_after']
                current_eval = self._extract_numeric_evaluation(eval_data)
        
        # Convert evaluation to bar position (clamped between -10 and +10)
        clamped_eval = max(-10, min(10, current_eval))
        eval_ratio = (clamped_eval + 10) / 20  # 0 to 1
        
        # Bar background
        bar_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y, self.eval_bar_width, self.eval_bar_height)
        pygame.draw.rect(surface, self.colors['evaluation_bg'], bar_rect)
        
        # White advantage (bottom part)
        white_height = int(self.eval_bar_height * eval_ratio)
        white_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y + self.eval_bar_height - white_height, 
                                self.eval_bar_width, white_height)
        pygame.draw.rect(surface, (255, 255, 255), white_rect)
        
        # Black advantage (top part)
        black_height = self.eval_bar_height - white_height
        if black_height > 0:
            black_rect = pygame.Rect(self.eval_bar_x, self.eval_bar_y, self.eval_bar_width, black_height)
            pygame.draw.rect(surface, (0, 0, 0), black_rect)
        
        # Evaluation text
        eval_text = f"{current_eval:+.1f}" if abs(current_eval) < 10 else ("M" if current_eval > 0 else "-M")
        eval_surface = self.fonts['evaluation'].render(eval_text, True, self.colors['text_primary'])
        text_x = self.eval_bar_x - eval_surface.get_width() - 5
        text_y = self.eval_bar_y + self.eval_bar_height // 2 - eval_surface.get_height() // 2
        surface.blit(eval_surface, (text_x, text_y))
    
    def _draw_board(self, surface):
        """Draw Chess.com-style board"""
        # Draw board border for visibility
        border_rect = pygame.Rect(self.board_x - 2, self.board_y - 2, self.board_size + 4, self.board_size + 4)
        pygame.draw.rect(surface, self.colors['text_muted'], border_rect)
        
        # Board squares
        for row in range(8):
            for col in range(8):
                self._draw_square(surface, row, col)
        
        # Coordinates
        self._draw_coordinates(surface)
        
        # Pieces
        self._draw_pieces(surface)
        
        # Move highlights
        self._draw_move_highlights(surface)
        
        # Move arrows
        self._draw_move_arrows(surface)
    
    def _draw_square(self, surface, row, col):
        """Draw a single board square"""
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size
        
        # Square color
        is_light = (row + col) % 2 == 0
        color = self.colors['white_square'] if is_light else self.colors['black_square']
        
        square_rect = pygame.Rect(x, y, self.square_size, self.square_size)
        pygame.draw.rect(surface, color, square_rect)
    
    def _draw_coordinates(self, surface):
        """Draw board coordinates"""
        # Files (a-h) at bottom
        for col in range(8):
            file_letter = chr(ord('a') + col)
            text = self.fonts['coordinates'].render(file_letter, True, self.colors['text_muted'])
            x = self.board_x + col * self.square_size + self.square_size - text.get_width() - 2
            y = self.board_y + self.board_size + 5
            surface.blit(text, (x, y))
        
        # Ranks (1-8) on left
        for row in range(8):
            rank_number = str(8 - row)
            text = self.fonts['coordinates'].render(rank_number, True, self.colors['text_muted'])
            x = self.board_x - text.get_width() - 5
            y = self.board_y + row * self.square_size + 2
            surface.blit(text, (x, y))
    
    def _draw_pieces(self, surface):
        """Draw pieces on the board"""
        # Get current position
        if not self.move_analysis or self.current_move_index == 0:
            # Starting position
            board = python_chess.Board()
        else:
            # Position after current move
            board = python_chess.Board()
            for i in range(min(self.current_move_index, len(self.move_analysis))):
                move_data = self.move_analysis[i]
                if 'move' in move_data:
                    try:
                        move = python_chess.Move.from_uci(move_data['move'])
                        board.push(move)
                    except:
                        continue
        
        # Draw pieces
        for square in python_chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                self._draw_piece(surface, piece, row, col)
    
    def _draw_piece(self, surface, piece, row, col):
        """Draw a single piece"""
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size
        
        # Unicode chess symbols (preferred)
        piece_symbols = {
            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
        }
        
        # ASCII fallback symbols
        ascii_symbols = {
            'P': 'P', 'R': 'R', 'N': 'N', 'B': 'B', 'Q': 'Q', 'K': 'K',
            'p': 'p', 'r': 'r', 'n': 'n', 'b': 'b', 'q': 'q', 'k': 'k'
        }
        
        # Try to get a working font and symbol - make pieces larger and more visible
        font_size = int(self.square_size * 0.9)  # Increased from 0.8 to 0.9
        piece_font = None
        symbol = None
        
        # First try Unicode symbols with Unicode-capable fonts
        unicode_fonts = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'Liberation Sans']
        for font_name in unicode_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, font_size)
                test_surface = test_font.render('♔', True, (0, 0, 0))
                if test_surface.get_width() > 0:
                    piece_font = test_font
                    symbol = piece_symbols.get(piece.symbol(), piece.symbol())
                    break
            except:
                continue
        
        # If Unicode didn't work, try ASCII with regular fonts
        if piece_font is None:
            regular_fonts = ['Arial', 'Helvetica', 'Times', 'Courier']
            for font_name in regular_fonts:
                try:
                    piece_font = pygame.font.SysFont(font_name, font_size, bold=True)
                    symbol = ascii_symbols.get(piece.symbol(), piece.symbol())
                    break
                except:
                    continue
        
        # Final fallback to default font with ASCII
        if piece_font is None:
            piece_font = pygame.font.Font(None, font_size)
            symbol = ascii_symbols.get(piece.symbol(), piece.symbol())
        
        # Use maximum contrast colors for visibility
        if piece.color == python_chess.WHITE:
            # White pieces - pure black for maximum contrast
            piece_color = (0, 0, 0)
            outline_color = (255, 255, 255)
            bg_color = (200, 200, 200, 128)  # Light background
        else:
            # Black pieces - pure white for maximum contrast
            piece_color = (255, 255, 255)
            outline_color = (0, 0, 0)
            bg_color = (50, 50, 50, 128)  # Dark background
            
        # Create piece surfaces
        piece_surface = piece_font.render(symbol, True, piece_color)
        outline_surface = piece_font.render(symbol, True, outline_color)
        
        # Center piece in square
        piece_x = x + (self.square_size - piece_surface.get_width()) // 2
        piece_y = y + (self.square_size - piece_surface.get_height()) // 2
        
        # Draw background circle for better visibility
        bg_radius = min(self.square_size // 3, 20)
        center_x = x + self.square_size // 2
        center_y = y + self.square_size // 2
        pygame.draw.circle(surface, bg_color[:3], (center_x, center_y), bg_radius)
        
        # Draw thick outline for maximum visibility
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    surface.blit(outline_surface, (piece_x + dx, piece_y + dy))
        
        # Draw main piece on top
        surface.blit(piece_surface, (piece_x, piece_y))
    
    def _draw_move_highlights(self, surface):
        """Draw move highlights"""
        if not self.move_analysis or self.current_move_index == 0:
            return
            
        move_data = self.move_analysis[self.current_move_index - 1]
        if 'move' not in move_data:
            return
            
        try:
            move = python_chess.Move.from_uci(move_data['move'])
            
            # Highlight from square
            from_row = 7 - (move.from_square // 8)
            from_col = move.from_square % 8
            from_x = self.board_x + from_col * self.square_size
            from_y = self.board_y + from_row * self.square_size
            
            highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surface, self.colors['highlight'], 
                           (0, 0, self.square_size, self.square_size))
            surface.blit(highlight_surface, (from_x, from_y))
            
            # Highlight to square
            to_row = 7 - (move.to_square // 8)
            to_col = move.to_square % 8
            to_x = self.board_x + to_col * self.square_size
            to_y = self.board_y + to_row * self.square_size
            
            surface.blit(highlight_surface, (to_x, to_y))
            
        except:
            pass
    
    def _draw_move_arrows(self, surface):
        """Draw move arrows"""
        # This would show engine suggestions and alternative moves
        # Implementation depends on your engine analysis data
        pass
    
    def _draw_sidebar(self, surface):
        """Draw Chess.com-style right sidebar"""
        # Sidebar background
        sidebar_rect = pygame.Rect(self.sidebar_x, self.sidebar_y, self.sidebar_width, self.sidebar_height)
        pygame.draw.rect(surface, self.colors['sidebar_bg'], sidebar_rect)
        
        # Current move info section
        self._draw_current_move_info(surface)
        
        # Move list section
        self._draw_move_list(surface)
        
        # Game summary section
        self._draw_game_summary(surface)
    
    def _draw_current_move_info(self, surface):
        """Draw current move information"""
        y_offset = self.sidebar_y + 20
        x_offset = self.sidebar_x + 20
        
        if not self.move_analysis or self.current_move_index == 0:
            # Show starting position info
            start_text = "Starting Position"
            start_surface = self.fonts['move_notation'].render(start_text, True, self.colors['text_primary'])
            surface.blit(start_surface, (x_offset, y_offset))
            return
            
        # Check if current move index is valid
        if self.current_move_index > len(self.move_analysis):
            return
            
        move_data = self.move_analysis[self.current_move_index - 1]
        
        # Move number and notation
        move_num = (self.current_move_index + 1) // 2
        is_white = self.current_move_index % 2 == 1
        
        notation = move_data.get('notation', move_data.get('move', 'Unknown'))
        move_text = f"{move_num}{'.' if is_white else '...'} {notation}"
        move_surface = self.fonts['move_notation'].render(move_text, True, self.colors['text_primary'])
        surface.blit(move_surface, (x_offset, y_offset))
        
        y_offset += 30
        
        # Classification
        classification = move_data.get('classification', 'Unknown')
        class_color = self._get_classification_color(classification)
        class_surface = self.fonts['classification'].render(classification.upper(), True, class_color)
        surface.blit(class_surface, (x_offset, y_offset))
        
        y_offset += 25
        
        # Evaluation
        eval_before = self._extract_numeric_evaluation(move_data.get('evaluation_before', 0))
        eval_after = self._extract_numeric_evaluation(move_data.get('evaluation_after', 0))
        eval_text = f"Eval: {eval_before:+.1f} → {eval_after:+.1f}"
        eval_surface = self.fonts['body'].render(eval_text, True, self.colors['text_secondary'])
        surface.blit(eval_surface, (x_offset, y_offset))
    
    def _draw_move_list(self, surface):
        """Draw scrollable move list"""
        # Move list header
        header_y = self.move_list_y
        header_text = self.fonts['body'].render("Moves", True, self.colors['text_primary'])
        surface.blit(header_text, (self.sidebar_x + 20, header_y))
        
        # Divider
        pygame.draw.line(surface, self.colors['text_muted'], 
                        (self.sidebar_x + 20, header_y + 25), 
                        (self.sidebar_x + self.sidebar_width - 20, header_y + 25))
        
        # Check if we have move analysis data
        if not self.move_analysis:
            no_moves_text = "No moves to display"
            no_moves_surface = self.fonts['body'].render(no_moves_text, True, self.colors['text_secondary'])
            surface.blit(no_moves_surface, (self.sidebar_x + 20, header_y + 40))
            return
        
        # Move list items
        list_start_y = header_y + 35
        item_height = 35
        visible_moves = (self.move_list_height - 35) // item_height
        
        # Ensure we don't try to display more moves than we have
        moves_to_show = min(visible_moves, len(self.move_analysis))
        
        for i in range(moves_to_show):
            if i < len(self.move_analysis):
                move_data = self.move_analysis[i]
                y = list_start_y + i * item_height
                self._draw_move_list_item(surface, move_data, i, y)
    
    def _draw_move_list_item(self, surface, move_data, move_index, y):
        """Draw a single move list item"""
        x = self.sidebar_x + 20
        
        # Highlight if selected
        if move_index + 1 == self.current_move_index:
            highlight_rect = pygame.Rect(self.sidebar_x, y - 2, self.sidebar_width, 30)
            pygame.draw.rect(surface, (60, 64, 72), highlight_rect)
        
        # Move number
        move_num = (move_index + 2) // 2
        is_white = (move_index + 1) % 2 == 1
        
        if is_white:
            num_text = f"{move_num}."
        else:
            num_text = f"{move_num}..."
        
        num_surface = self.fonts['move_number'].render(num_text, True, self.colors['text_secondary'])
        surface.blit(num_surface, (x, y))
        
        # Move notation
        notation = move_data.get('notation', move_data.get('move', ''))
        notation_surface = self.fonts['move_notation'].render(notation, True, self.colors['text_primary'])
        surface.blit(notation_surface, (x + 40, y))
        
        # Classification badge
        classification = move_data.get('classification', '')
        if classification:
            badge_x = x + 120
            self._draw_classification_badge(surface, classification, badge_x, y)
    
    def _draw_classification_badge(self, surface, classification, x, y):
        """Draw move classification badge"""
        color = self._get_classification_color(classification)
        
        # Badge background
        badge_width = 60
        badge_height = 18
        badge_rect = pygame.Rect(x, y + 3, badge_width, badge_height)
        pygame.draw.rect(surface, color, badge_rect, border_radius=3)
        
        # Badge text
        text = classification[:4].upper()  # Truncate to 4 chars
        text_surface = self.fonts['small'].render(text, True, (255, 255, 255))
        text_x = x + (badge_width - text_surface.get_width()) // 2
        text_y = y + (badge_height - text_surface.get_height()) // 2 + 3
        surface.blit(text_surface, (text_x, text_y))
    
    def _draw_game_summary(self, surface):
        """Draw game analysis summary"""
        summary_y = self.summary_y + 20
        x_offset = self.sidebar_x + 20
        
        # Summary header
        header_text = self.fonts['body'].render("Game Summary", True, self.colors['text_primary'])
        surface.blit(header_text, (x_offset, summary_y))
        
        # Divider
        pygame.draw.line(surface, self.colors['text_muted'], 
                        (x_offset, summary_y + 25), 
                        (self.sidebar_x + self.sidebar_width - 20, summary_y + 25))
        
        summary_y += 40
        
        if self.analyzer and hasattr(self.analyzer, 'get_game_summary'):
            summary = self.analyzer.get_game_summary()
            
            # Check if summary is valid
            if summary and isinstance(summary, dict):
                # Accuracy scores
                white_acc = summary.get('white_accuracy', 0)
                black_acc = summary.get('black_accuracy', 0)
                
                acc_text = f"White: {white_acc:.1f}%  Black: {black_acc:.1f}%"
                acc_surface = self.fonts['accuracy'].render(acc_text, True, self.colors['accent'])
                surface.blit(acc_surface, (x_offset, summary_y))
                
                summary_y += 35
                
                # Move counts
                move_counts = summary.get('move_counts', {})
                for classification, count in move_counts.items():
                    if count > 0:
                        color = self._get_classification_color(classification)
                        count_text = f"{classification}: {count}"
                        count_surface = self.fonts['body'].render(count_text, True, color)
                        surface.blit(count_surface, (x_offset, summary_y))
                        summary_y += 20
            else:
                # Fallback when no summary is available
                fallback_text = "Analysis in progress..."
                fallback_surface = self.fonts['body'].render(fallback_text, True, self.colors['text_secondary'])
                surface.blit(fallback_surface, (x_offset, summary_y))
        else:
            # Fallback when analyzer is not available
            no_data_text = "No analysis data available"
            no_data_surface = self.fonts['body'].render(no_data_text, True, self.colors['text_secondary'])
            surface.blit(no_data_surface, (x_offset, summary_y))
    
    def _get_classification_color(self, classification):
        """Get color for move classification"""
        classification_lower = classification.lower()
        if 'brilliant' in classification_lower:
            return self.colors['brilliant']
        elif 'great' in classification_lower:
            return self.colors['great']
        elif 'best' in classification_lower:
            return self.colors['best']
        elif 'good' in classification_lower or 'excellent' in classification_lower:
            return self.colors['good']
        elif 'inaccuracy' in classification_lower:
            return self.colors['inaccuracy']
        elif 'mistake' in classification_lower:
            return self.colors['mistake']
        elif 'blunder' in classification_lower:
            return self.colors['blunder']
        else:
            return self.colors['text_secondary']
    
    def handle_input(self, event):
        """Handle input events"""
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.deactivate()
                return True
            elif event.key == pygame.K_LEFT:
                self.previous_move()
                return True
            elif event.key == pygame.K_RIGHT:
                self.next_move()
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle move list clicks
            if self._is_in_move_list(event.pos):
                move_index = self._get_clicked_move(event.pos)
                if move_index is not None:
                    self.jump_to_move(move_index)
                return True
                    
        return False
    
    def _is_in_move_list(self, pos):
        """Check if position is in move list area"""
        x, y = pos
        return (self.sidebar_x <= x <= self.sidebar_x + self.sidebar_width and
                self.move_list_y + 35 <= y <= self.move_list_y + self.move_list_height)
    
    def _get_clicked_move(self, pos):
        """Get move index from click position"""
        x, y = pos
        if not self._is_in_move_list(pos):
            return None
            
        relative_y = y - (self.move_list_y + 35)
        move_index = relative_y // 35
        
        if 0 <= move_index < len(self.move_analysis):
            return move_index + 1
        return None
    
    def next_move(self):
        """Go to next move"""
        if self.current_move_index < len(self.game_moves):
            self.current_move_index += 1
    
    def previous_move(self):
        """Go to previous move"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
    
    def jump_to_move(self, move_index):
        """Jump to specific move"""
        if 0 <= move_index <= len(self.game_moves):
            self.current_move_index = move_index
    
    def _draw_evaluation_graph(self, surface):
        """Draw Chess.com-style evaluation graph"""
        # Always draw the graph container, even without data
        graph_x = self.sidebar_x + 20
        graph_y = self.eval_graph_y + 20
        graph_width = self.sidebar_width - 40
        graph_height = self.eval_graph_height - 40
        
        # Graph background
        graph_rect = pygame.Rect(graph_x, graph_y, graph_width, graph_height)
        pygame.draw.rect(surface, (50, 54, 62), graph_rect)
        pygame.draw.rect(surface, self.colors['text_muted'], graph_rect, 1)
        
        # Graph title
        title_text = self.fonts['body'].render("Evaluation", True, self.colors['text_primary'])
        surface.blit(title_text, (graph_x, graph_y - 25))
        
        # Center line (equal position)
        center_y = graph_y + graph_height // 2
        pygame.draw.line(surface, self.colors['text_muted'], 
                        (graph_x, center_y), (graph_x + graph_width, center_y))
        
        # Y-axis labels
        label_font = self.fonts['small']
        for eval_val in [10, 5, 0, -5, -10]:
            y = center_y - (eval_val / 10) * (graph_height // 2)
            label_text = f"{eval_val:+d}" if eval_val != 0 else "0"
            label_surface = label_font.render(label_text, True, self.colors['text_muted'])
            surface.blit(label_surface, (graph_x - 25, y - label_surface.get_height() // 2))
        
        if not self.move_analysis or len(self.move_analysis) < 2:
            # Show "No data" message
            no_data_text = "No evaluation data"
            no_data_surface = self.fonts['body'].render(no_data_text, True, self.colors['text_secondary'])
            text_x = graph_x + (graph_width - no_data_surface.get_width()) // 2
            text_y = center_y - no_data_surface.get_height() // 2
            surface.blit(no_data_surface, (text_x, text_y))
            return
            
        # Draw evaluation curve
        points = []
        for i, move_data in enumerate(self.move_analysis):
            eval_after = self._extract_numeric_evaluation(move_data.get('evaluation_after', 0))
            
            # Clamp evaluation between -10 and +10 for display
            clamped_eval = max(-10, min(10, eval_after))
            
            # Convert to graph coordinates
            x = graph_x + (i / max(1, len(self.move_analysis) - 1)) * graph_width
            # Flip Y axis so positive is up
            y = center_y - (clamped_eval / 10) * (graph_height // 2)
            
            points.append((x, y))
        
        # Draw the evaluation line
        if len(points) > 1:
            pygame.draw.lines(surface, self.colors['accent'], False, points, 2)
        
        # Draw current move indicator
        if 0 < self.current_move_index <= len(points):
            current_point = points[self.current_move_index - 1]
            pygame.draw.circle(surface, (255, 255, 255), 
                             (int(current_point[0]), int(current_point[1])), 4)
            pygame.draw.circle(surface, self.colors['accent'], 
                             (int(current_point[0]), int(current_point[1])), 3)