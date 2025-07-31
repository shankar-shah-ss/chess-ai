# modern_analysis_interface.py - Consolidated Analysis Interface
import pygame
import math
import os
from typing import Optional, List, Dict, Any
from const import *
from utils_analysis_complete import (
    draw_arrow, draw_classification_badge, draw_progress_bar,
    classification_to_color, draw_rounded_rect
)

try:
    import chess
except ImportError:
    chess = None

class ModernAnalysisInterface:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.current_move_index = 0
        self.active = False
        
        # UI state
        self.show_evaluation_bar = True
        self.show_move_arrows = True
        self.move_list_scroll = 0
        self.sidebar_width = 380
        
        self.setup_layout()
        self.colors = self._setup_colors()
        self.fonts = self._setup_fonts()
        self.piece_images = {}
        self._load_piece_images()
        
    def setup_layout(self):
        """Setup responsive layout"""
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        
        # Board dimensions
        max_board_size = min(self.screen_width * 0.55, self.screen_height * 0.85)
        self.board_size = max_board_size - (max_board_size % 8)
        self.square_size = self.board_size // 8
        
        # Center board
        self.board_x = (self.screen_width - self.sidebar_width - self.board_size) // 2
        self.board_y = (self.screen_height - self.board_size) // 2
        
        # Sidebar
        self.sidebar_x = self.screen_width - self.sidebar_width
        self.sidebar_y = 0
        self.sidebar_height = self.screen_height
        
    def _setup_colors(self):
        """Setup modern color palette"""
        return {
            'bg_primary': (30, 30, 30),
            'bg_secondary': (37, 37, 38),
            'bg_tertiary': (45, 45, 48),
            'accent_primary': (0, 122, 255),
            'text_primary': (255, 255, 255),
            'text_secondary': (204, 204, 204),
            'text_muted': (140, 140, 140),
            'border': (68, 68, 68),
            'success': (40, 167, 69),
            'error': (220, 53, 69),
            'warning': (255, 193, 7),
            'light_square': (240, 238, 228),
            'dark_square': (181, 136, 99),
            'BRILLIANT': (138, 43, 226),
            'GREAT': (34, 139, 34),
            'BEST': (52, 168, 83),
            'EXCELLENT': (72, 201, 176),
            'OKAY': (108, 117, 125),
            'INACCURACY': (255, 158, 56),
            'MISTAKE': (255, 107, 107),
            'BLUNDER': (220, 53, 69),
        }
        
    def _setup_fonts(self):
        """Setup font hierarchy"""
        return {
            'title': pygame.font.SysFont('Segoe UI', 28, bold=True),
            'heading': pygame.font.SysFont('Segoe UI', 20, bold=True),
            'subheading': pygame.font.SysFont('Segoe UI', 16, bold=True),
            'body': pygame.font.SysFont('Segoe UI', 14),
            'body_medium': pygame.font.SysFont('Segoe UI', 14, bold=True),
            'caption': pygame.font.SysFont('Segoe UI', 12),
            'small': pygame.font.SysFont('Segoe UI', 11),
        }
        
    def _load_piece_images(self):
        """Load piece images"""
        piece_files = {
            'K': 'white_king.png', 'Q': 'white_queen.png', 'R': 'white_rook.png',
            'B': 'white_bishop.png', 'N': 'white_knight.png', 'P': 'white_pawn.png',
            'k': 'black_king.png', 'q': 'black_queen.png', 'r': 'black_rook.png', 
            'b': 'black_bishop.png', 'n': 'black_knight.png', 'p': 'black_pawn.png'
        }
        
        base_paths = [
            os.path.join('assets', 'images', 'imgs-80px'),
            os.path.join('..', 'assets', 'images', 'imgs-80px')
        ]
        
        for char, filename in piece_files.items():
            for base_path in base_paths:
                try:
                    piece_path = os.path.join(base_path, filename)
                    if os.path.exists(piece_path):
                        self.piece_images[char] = pygame.image.load(piece_path)
                        break
                except:
                    continue
                    
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        self.current_move_index = 0
        self.move_list_scroll = 0
        
    def activate(self):
        """Activate analysis interface"""
        self.active = True
        
    def deactivate(self):
        """Deactivate analysis interface"""
        self.active = False
        
    def render(self, surface):
        """Render the analysis interface"""
        if not self.active or not self.analyzer:
            return
            
        surface.fill(self.colors['bg_primary'])
        
        self._draw_header(surface)
        self._draw_board_section(surface)
        self._draw_sidebar(surface)
        self._draw_evaluation_bar(surface)
        
        if not self.analyzer.is_analysis_complete():
            self._draw_analysis_progress_overlay(surface)
            
    def _draw_header(self, surface):
        """Draw header with controls"""
        header_height = 60
        header_rect = pygame.Rect(0, 0, self.screen_width, header_height)
        
        pygame.draw.rect(surface, self.colors['bg_secondary'], header_rect)
        pygame.draw.line(surface, self.colors['border'], 
                        (0, header_height), (self.screen_width, header_height))
        
        # Title
        title_surface = self.fonts['title'].render("Game Analysis", True, self.colors['text_primary'])
        surface.blit(title_surface, (24, 16))
        
        # Status
        if self.analyzer.is_analysis_complete():
            status_text = "✓ Analysis Complete"
            status_color = self.colors['success']
        else:
            progress = self.analyzer.get_analysis_progress()
            status_text = f"Analyzing... {progress}%"
            status_color = self.colors['accent_primary']
            
        status_surface = self.fonts['body'].render(status_text, True, status_color)
        surface.blit(status_surface, (24, 40))
        
    def _draw_board_section(self, surface):
        """Draw the chess board"""
        # Board background
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(surface, self.colors['bg_tertiary'], board_rect, border_radius=12)
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                self._draw_square(surface, row, col)
                
        self._draw_coordinates(surface)
        self._draw_move_highlights(surface)
        self._draw_pieces(surface)
        
        if self.show_move_arrows:
            self._draw_move_arrows(surface)
            
    def _draw_square(self, surface, row, col):
        """Draw individual square"""
        x = self.board_x + col * self.square_size + 6
        y = self.board_y + row * self.square_size + 6
        size = self.square_size - 12
        
        is_light = (row + col) % 2 == 0
        color = self.colors['light_square'] if is_light else self.colors['dark_square']
        
        square_rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, color, square_rect, border_radius=4)
        
    def _draw_coordinates(self, surface):
        """Draw coordinate labels"""
        coord_font = self.fonts['small']
        coord_color = (100, 100, 100)
        
        # Files (a-h)
        for col in range(8):
            file_label = chr(ord('a') + col)
            label_surface = coord_font.render(file_label, True, coord_color)
            x = self.board_x + col * self.square_size + self.square_size - 16
            y = self.board_y + self.board_size - 16
            surface.blit(label_surface, (x, y))
            
        # Ranks (1-8)
        for row in range(8):
            rank_label = str(8 - row)
            label_surface = coord_font.render(rank_label, True, coord_color)
            x = self.board_x + 8
            y = self.board_y + row * self.square_size + 8
            surface.blit(label_surface, (x, y))
            
    def _draw_move_highlights(self, surface):
        """Draw current move highlights"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves) or self.current_move_index < 0:
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        move = current_analysis.move
        
        classification_color = self.colors.get(current_analysis.classification, self.colors['text_secondary'])
        
        # From square
        from_x = self.board_x + move.initial.col * self.square_size + 6
        from_y = self.board_y + move.initial.row * self.square_size + 6
        
        highlight_surface = pygame.Surface((self.square_size - 12, self.square_size - 12), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (*classification_color, 80), highlight_surface.get_rect(), border_radius=4)
        pygame.draw.rect(highlight_surface, classification_color, highlight_surface.get_rect(), 3, border_radius=4)
        surface.blit(highlight_surface, (from_x, from_y))
        
        # To square
        to_x = self.board_x + move.final.col * self.square_size + 6
        to_y = self.board_y + move.final.row * self.square_size + 6
        
        highlight_surface = pygame.Surface((self.square_size - 12, self.square_size - 12), pygame.SRCALPHA)
        pygame.draw.rect(highlight_surface, (*classification_color, 60), highlight_surface.get_rect(), border_radius=4)
        pygame.draw.rect(highlight_surface, classification_color, highlight_surface.get_rect(), 3, border_radius=4)
        surface.blit(highlight_surface, (to_x, to_y))
        
    def _draw_pieces(self, surface):
        """Draw chess pieces"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves or self.current_move_index < 0:
            return
            
        if self.current_move_index < len(analyzed_moves):
            current_analysis = analyzed_moves[self.current_move_index]
            position_fen = current_analysis.position_after
        else:
            return
            
        try:
            board_part = position_fen.split()[0]
            self._render_pieces_from_fen(surface, board_part)
        except:
            pass
            
    def _render_pieces_from_fen(self, surface, board_fen):
        """Render pieces from FEN"""
        row = 0
        col = 0
        
        for char in board_fen:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            elif char in self.piece_images:
                x = self.board_x + col * self.square_size + 6
                y = self.board_y + row * self.square_size + 6
                
                try:
                    piece_img = self.piece_images[char]
                    piece_size = int((self.square_size - 12) * 0.85)
                    piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                    
                    piece_center_x = x + (self.square_size - 12) // 2
                    piece_center_y = y + (self.square_size - 12) // 2
                    
                    piece_rect = piece_img.get_rect(center=(piece_center_x, piece_center_y))
                    surface.blit(piece_img, piece_rect)
                    
                except:
                    self._draw_fallback_piece(surface, char, x, y)
                    
                col += 1
                
    def _draw_fallback_piece(self, surface, piece_char, x, y):
        """Draw fallback piece representation"""
        color = self.colors['text_primary'] if piece_char.isupper() else self.colors['text_muted']
        center = (x + (self.square_size - 12) // 2, y + (self.square_size - 12) // 2)
        
        pygame.draw.circle(surface, self.colors['bg_tertiary'], center, (self.square_size - 12) // 4)
        pygame.draw.circle(surface, color, center, (self.square_size - 12) // 4, 2)
        
        symbol_surface = self.fonts['body_medium'].render(piece_char.upper(), True, color)
        symbol_rect = symbol_surface.get_rect(center=center)
        surface.blit(symbol_surface, symbol_rect)
        
    def _draw_move_arrows(self, surface):
        """Draw move arrows"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves) or self.current_move_index < 0:
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        move = current_analysis.move
        
        from_center = (
            self.board_x + move.initial.col * self.square_size + self.square_size // 2,
            self.board_y + move.initial.row * self.square_size + self.square_size // 2
        )
        to_center = (
            self.board_x + move.final.col * self.square_size + self.square_size // 2,
            self.board_y + move.final.row * self.square_size + self.square_size // 2
        )
        
        classification_color = self.colors.get(current_analysis.classification, self.colors['accent_primary'])
        draw_arrow(surface, from_center, to_center, classification_color, 4)
        

        
    def _draw_sidebar(self, surface):
        """Draw sidebar with analysis details"""
        sidebar_rect = pygame.Rect(self.sidebar_x, self.sidebar_y, self.sidebar_width, self.sidebar_height)
        pygame.draw.rect(surface, self.colors['bg_secondary'], sidebar_rect)
        pygame.draw.line(surface, self.colors['border'], 
                        (self.sidebar_x, 0), (self.sidebar_x, self.sidebar_height))
        
        if not self.analyzer.is_analysis_complete():
            return
            
        content_y = 80
        y_offset = self._draw_current_move_info(surface, content_y)
        y_offset = self._draw_move_list(surface, y_offset)
        self._draw_analysis_summary(surface, y_offset)
        
    def _draw_current_move_info(self, surface, start_y):
        """Draw current move information"""
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves) or self.current_move_index < 0:
            return start_y
            
        current_analysis = analyzed_moves[self.current_move_index]
        
        card_margin = 16
        card_padding = 16
        card_height = 120
        
        card_rect = pygame.Rect(
            self.sidebar_x + card_margin, 
            start_y + card_margin,
            self.sidebar_width - 2 * card_margin, 
            card_height
        )
        
        pygame.draw.rect(surface, self.colors['bg_tertiary'], card_rect, border_radius=8)
        pygame.draw.rect(surface, self.colors['border'], card_rect, 1, border_radius=8)
        
        x = card_rect.x + card_padding
        y = card_rect.y + card_padding
        
        # Move header
        move_text = f"Move {current_analysis.move_number}"
        player_color = "White" if current_analysis.player == 'white' else "Black"
        header_text = f"{move_text} • {player_color}"
        
        header_surface = self.fonts['subheading'].render(header_text, True, self.colors['text_primary'])
        surface.blit(header_surface, (x, y))
        
        # Classification badge
        self._draw_classification_badge(surface, current_analysis.classification, 
                                      card_rect.right - card_padding - 80, y - 2)
        
        # Move notation
        move_notation = self._get_move_notation(current_analysis.move)
        notation_surface = self.fonts['body_medium'].render(move_notation, True, self.colors['text_secondary'])
        surface.blit(notation_surface, (x, y + 28))
        
        # Evaluation change
        if hasattr(current_analysis, 'eval_loss') and current_analysis.eval_loss > 0:
            eval_text = f"Evaluation loss: -{current_analysis.eval_loss}"
            eval_color = self.colors['error'] if current_analysis.eval_loss > 100 else self.colors['warning']
            eval_surface = self.fonts['body'].render(eval_text, True, eval_color)
            surface.blit(eval_surface, (x, y + 52))
        
        return start_y + card_height + 2 * card_margin
        
    def _draw_classification_badge(self, surface, classification, x, y):
        """Draw classification badge"""
        draw_classification_badge(surface, classification, x, y, self.fonts['small'])
        
    def _draw_move_list(self, surface, start_y):
        """Draw scrollable move list"""
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return start_y
            
        section_margin = 16
        header_y = start_y + section_margin
        
        header_surface = self.fonts['heading'].render("Game Moves", True, self.colors['text_primary'])
        surface.blit(header_surface, (self.sidebar_x + section_margin, header_y))
        
        list_start_y = header_y + 40
        list_height = 300
        move_item_height = 48
        
        visible_moves = list_height // move_item_height
        max_scroll = max(0, len(analyzed_moves) - visible_moves)
        
        if self.current_move_index < self.move_list_scroll:
            self.move_list_scroll = self.current_move_index
        elif self.current_move_index >= self.move_list_scroll + visible_moves:
            self.move_list_scroll = self.current_move_index - visible_moves + 1
            
        self.move_list_scroll = max(0, min(max_scroll, self.move_list_scroll))
        
        for i in range(visible_moves):
            move_index = i + self.move_list_scroll
            if move_index >= len(analyzed_moves):
                break
                
            move_analysis = analyzed_moves[move_index]
            item_y = list_start_y + i * move_item_height
            
            self._draw_move_list_item(surface, move_analysis, move_index, item_y, 
                                    move_index == self.current_move_index)
            
        return list_start_y + list_height + section_margin
        
    def _draw_move_list_item(self, surface, move_analysis, move_index, y, is_selected):
        """Draw individual move list item"""
        item_margin = 16
        item_padding = 12
        item_height = 44
        
        item_rect = pygame.Rect(
            self.sidebar_x + item_margin,
            y,
            self.sidebar_width - 2 * item_margin,
            item_height
        )
        
        if is_selected:
            pygame.draw.rect(surface, self.colors['accent_primary'], item_rect, border_radius=6)
            text_color = (255, 255, 255)
            secondary_color = (220, 220, 220)
        else:
            pygame.draw.rect(surface, self.colors['bg_tertiary'], item_rect, border_radius=6)
            text_color = self.colors['text_primary']
            secondary_color = self.colors['text_secondary']
            
        x = item_rect.x + item_padding
        move_text = f"{move_analysis.move_number}."
        player_symbol = "●" if move_analysis.player == 'white' else "○"
        
        move_surface = self.fonts['body_medium'].render(f"{move_text} {player_symbol}", True, text_color)
        surface.blit(move_surface, (x, y + 8))
        
        notation = self._get_move_notation(move_analysis.move)
        notation_surface = self.fonts['body'].render(notation, True, text_color)
        surface.blit(notation_surface, (x, y + 26))
        
        classification_color = self.colors.get(move_analysis.classification, secondary_color)
        indicator_size = 8
        indicator_x = item_rect.right - item_padding - indicator_size
        indicator_y = y + (item_height - indicator_size) // 2
        
        pygame.draw.circle(surface, classification_color, (indicator_x - indicator_size//2, indicator_y), indicator_size//2)
        
    def _draw_analysis_summary(self, surface, start_y):
        """Draw analysis summary"""
        if not hasattr(self.analyzer, 'get_game_summary'):
            return
            
        summary = self.analyzer.get_game_summary()
        if not summary:
            return
            
        section_margin = 16
        header_y = start_y + section_margin
        
        header_surface = self.fonts['heading'].render("Analysis Summary", True, self.colors['text_primary'])
        surface.blit(header_surface, (self.sidebar_x + section_margin, header_y))
        
        card_y = header_y + 40
        card_margin = 16
        card_padding = 12
        
        # Accuracy card
        accuracy_rect = pygame.Rect(
            self.sidebar_x + card_margin,
            card_y,
            (self.sidebar_width - 3 * card_margin) // 2,
            60
        )
        
        pygame.draw.rect(surface, self.colors['bg_tertiary'], accuracy_rect, border_radius=6)
        
        white_acc = summary.get('white_accuracy', 0)
        white_text = f"White: {white_acc:.1f}%"
        white_surface = self.fonts['body'].render(white_text, True, self.colors['text_primary'])
        surface.blit(white_surface, (accuracy_rect.x + card_padding, accuracy_rect.y + 8))
        
        black_acc = summary.get('black_accuracy', 0)
        black_text = f"Black: {black_acc:.1f}%"
        black_surface = self.fonts['body'].render(black_text, True, self.colors['text_secondary'])
        surface.blit(black_surface, (accuracy_rect.x + card_padding, accuracy_rect.y + 32))
        
        # Mistakes card
        mistakes_rect = pygame.Rect(
            accuracy_rect.right + card_margin,
            card_y,
            (self.sidebar_width - 3 * card_margin) // 2,
            60
        )
        
        pygame.draw.rect(surface, self.colors['bg_tertiary'], mistakes_rect, border_radius=6)
        
        blunders = summary.get('blunders', 0)
        blunder_text = f"Blunders: {blunders}"
        blunder_surface = self.fonts['body'].render(blunder_text, True, self.colors['error'])
        surface.blit(blunder_surface, (mistakes_rect.x + card_padding, mistakes_rect.y + 8))
        
        mistakes = summary.get('mistakes', 0)
        mistake_text = f"Mistakes: {mistakes}"
        mistake_surface = self.fonts['body'].render(mistake_text, True, self.colors['warning'])
        surface.blit(mistake_surface, (mistakes_rect.x + card_padding, mistakes_rect.y + 32))
        
    def _draw_evaluation_bar(self, surface):
        """Draw evaluation bar"""
        if not self.show_evaluation_bar or not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        bar_width = 12
        bar_height = self.board_size
        bar_x = self.board_x - 24
        bar_y = self.board_y
        
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, self.colors['bg_tertiary'], bg_rect, border_radius=6)
        
        if self.current_move_index < len(analyzed_moves):
            current_analysis = analyzed_moves[self.current_move_index]
            if hasattr(current_analysis, 'eval_after') and current_analysis.eval_after:
                evaluation = current_analysis.eval_after
                
                if evaluation and 'value' in evaluation:
                    if evaluation['type'] == 'cp':
                        eval_cp = max(-800, min(800, evaluation['value']))
                        bar_position = (eval_cp + 800) / 1600
                    else:
                        bar_position = 1.0 if evaluation['value'] > 0 else 0.0
                        
                    white_height = int(bar_height * bar_position)
                    black_height = bar_height - white_height
                    
                    if black_height > 0:
                        black_rect = pygame.Rect(bar_x, bar_y, bar_width, black_height)
                        pygame.draw.rect(surface, (80, 80, 80), black_rect, border_radius=6)
                        
                    if white_height > 0:
                        white_rect = pygame.Rect(bar_x, bar_y + black_height, bar_width, white_height)
                        pygame.draw.rect(surface, (240, 240, 240), white_rect, border_radius=6)
                        
                    center_y = bar_y + bar_height // 2
                    pygame.draw.line(surface, self.colors['border'], 
                                   (bar_x, center_y), (bar_x + bar_width, center_y), 2)
                    
    def _draw_analysis_progress_overlay(self, surface):
        """Draw analysis progress overlay"""
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        
        card_width = 400
        card_height = 200
        card_x = (self.screen_width - card_width) // 2
        card_y = (self.screen_height - card_height) // 2
        
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(surface, self.colors['bg_secondary'], card_rect, border_radius=16)
        pygame.draw.rect(surface, self.colors['border'], card_rect, 2, border_radius=16)
        
        progress = self.analyzer.get_analysis_progress()
        
        title_surface = self.fonts['title'].render("Analyzing Game", True, self.colors['text_primary'])
        title_rect = title_surface.get_rect(center=(card_x + card_width // 2, card_y + 40))
        surface.blit(title_surface, title_rect)
        
        bar_width = card_width - 60
        bar_height = 8
        bar_x = card_x + 30
        bar_y = card_y + 80
        
        progress_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        draw_progress_bar(surface, progress_rect, progress / 100, 
                         self.colors['bg_tertiary'], self.colors['accent_primary'])
            
        progress_text = f"{progress}% Complete"
        progress_surface = self.fonts['body'].render(progress_text, True, self.colors['text_secondary'])
        progress_rect = progress_surface.get_rect(center=(card_x + card_width // 2, card_y + 110))
        surface.blit(progress_surface, progress_rect)
        
    def _get_move_notation(self, move):
        """Convert move to algebraic notation"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
        to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
        
        return f"{from_square}{to_square}"
        
    def handle_input(self, event):
        """Handle input events"""
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            analyzed_moves = self.analyzer.get_analyzed_moves()
            
            if event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                if self.current_move_index > 0:
                    self.current_move_index -= 1
                return True
                
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                if self.current_move_index < len(analyzed_moves) - 1:
                    self.current_move_index += 1
                return True
                
            elif event.key == pygame.K_HOME:
                self.current_move_index = 0
                return True
                
            elif event.key == pygame.K_END:
                if analyzed_moves:
                    self.current_move_index = len(analyzed_moves) - 1
                return True
                
            elif event.key == pygame.K_e:
                self.show_evaluation_bar = not self.show_evaluation_bar
                return True
                
            elif event.key == pygame.K_m:
                self.show_move_arrows = not self.show_move_arrows
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.analyzer.is_analysis_complete():
                analyzed_moves = self.analyzer.get_analyzed_moves()
                
                list_start_y = 200
                move_item_height = 48
                
                if (self.sidebar_x + 16 <= event.pos[0] <= self.sidebar_x + self.sidebar_width - 16 and
                    list_start_y <= event.pos[1] <= list_start_y + 300):
                    
                    relative_y = event.pos[1] - list_start_y
                    clicked_move = (relative_y // move_item_height) + self.move_list_scroll
                    
                    if 0 <= clicked_move < len(analyzed_moves):
                        self.current_move_index = clicked_move
                        return True
                        
        return False
        
    def next_move(self):
        """Navigate to next move"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index < len(analyzed_moves) - 1:
            self.current_move_index += 1
            
    def previous_move(self):
        """Navigate to previous move"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
            
    def jump_to_move(self, move_number):
        """Jump to specific move"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        for i, move_analysis in enumerate(analyzed_moves):
            if move_analysis.move_number == move_number:
                self.current_move_index = i
                break
                
    def get_current_move(self):
        """Get current move analysis"""
        if not self.analyzer.is_analysis_complete():
            return None
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if 0 <= self.current_move_index < len(analyzed_moves):
            return analyzed_moves[self.current_move_index]
        return None