# analysis_screen.py - Modern Chess.com Style Analysis Interface
import pygame
import os
import math
from const import *

class AnalysisScreen:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.current_move_index = 0
        self.show_analysis = False
        self.scroll_offset = 0
        self.active = False
        
        # Screen dimensions
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        
        # Modern layout - Chess.com inspired
        self.board_size = min(self.screen_width * 0.6, self.screen_height * 0.9)
        self.board_square_size = self.board_size // 8
        self.board_x = 50
        self.board_y = (self.screen_height - self.board_size) // 2
        
        # Analysis panel on the right
        self.panel_x = self.board_x + self.board_size + 30
        self.panel_width = self.screen_width - self.panel_x - 20
        self.panel_height = self.screen_height - 100
        
        # Modern Chess.com color scheme
        self.bg_color = (40, 46, 58)           # Dark blue-gray background
        self.panel_color = (54, 62, 78)        # Slightly lighter panel
        self.card_color = (64, 72, 88)         # Card backgrounds
        self.selected_color = (80, 90, 110)    # Selected items
        self.text_color = (255, 255, 255)      # Pure white text
        self.secondary_text = (181, 181, 181)  # Gray secondary text
        self.header_color = (255, 255, 255)    # Headers
        self.border_color = (84, 92, 108)      # Subtle borders
        self.accent_color = (129, 182, 76)     # Chess.com green
        
        # Board colors - Chess.com style
        self.light_square = (240, 217, 181)
        self.dark_square = (181, 136, 99)
        
        # Move classification colors (Chess.com exact colors)
        self.classification_colors = {
            'BRILLIANT': (28, 158, 255),       # Brilliant blue
            'GREAT': (96, 169, 23),            # Great green  
            'BEST': (96, 169, 23),             # Best green
            'EXCELLENT': (96, 169, 23),        # Excellent green
            'OKAY': (115, 192, 67),            # Light green
            'MISS': (255, 167, 38),            # Orange
            'INACCURACY': (255, 167, 38),      # Orange
            'MISTAKE': (255, 146, 146),        # Light red
            'BLUNDER': (242, 113, 102)         # Red
        }
        
        # UI state
        self.show_evaluation_bar = True
        self.evaluation_history = []
        self.move_list_scroll = 0
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        self.current_move_index = 0
        self.scroll_offset = 0
        self.evaluation_history = []
        
    def activate(self):
        """Activate the analysis screen"""
        self.active = True
        self.show_analysis = True
        
    def deactivate(self):
        """Deactivate the analysis screen"""
        self.active = False
        self.show_analysis = False
        
    def render(self, surface):
        """Render the modern analysis screen"""
        if not self.active or not self.analyzer:
            return
            
        # Fill background
        surface.fill(self.bg_color)
        
        # Draw main analysis board
        self._draw_modern_board(surface)
        
        # Draw right panel
        self._draw_right_panel(surface)
        
        # Draw evaluation bar
        if self.show_evaluation_bar:
            self._draw_evaluation_bar(surface)
            
    def _draw_modern_board(self, surface):
        """Draw the chess board with modern styling"""
        # Board shadow
        shadow_offset = 5
        shadow_rect = pygame.Rect(self.board_x + shadow_offset, self.board_y + shadow_offset, 
                                 self.board_size, self.board_size)
        pygame.draw.rect(surface, (20, 20, 30), shadow_rect, border_radius=12)
        
        # Board background
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(surface, self.border_color, board_rect, border_radius=12)
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                square_x = self.board_x + col * self.board_square_size + 4
                square_y = self.board_y + row * self.board_square_size + 4
                
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                square_rect = pygame.Rect(square_x, square_y, 
                                        self.board_square_size - 8, self.board_square_size - 8)
                pygame.draw.rect(surface, color, square_rect)
        
        # Draw coordinates
        self._draw_board_coordinates(surface)
        
        # Draw move highlight
        self._draw_move_highlight(surface)
        
        # Draw pieces
        self._draw_pieces(surface)
        
    def _draw_pieces(self, surface):
        """Draw chess pieces on the analysis board"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves or self.current_move_index < 0:
            return
            
        # Get the position after the current move
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
        """Render pieces from FEN string"""
        piece_files = {
            'K': 'white_king.png', 'Q': 'white_queen.png', 'R': 'white_rook.png',
            'B': 'white_bishop.png', 'N': 'white_knight.png', 'P': 'white_pawn.png',
            'k': 'black_king.png', 'q': 'black_queen.png', 'r': 'black_rook.png', 
            'b': 'black_bishop.png', 'n': 'black_knight.png', 'p': 'black_pawn.png'
        }
        
        row = 0
        col = 0
        
        for char in board_fen:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            elif char in piece_files:
                screen_x = self.board_x + col * self.board_square_size + 4
                screen_y = self.board_y + row * self.board_square_size + 4
                
                try:
                    piece_file = os.path.join('assets', 'images', 'imgs-80px', piece_files[char])
                    if os.path.exists(piece_file):
                        piece_img = pygame.image.load(piece_file)
                        piece_size = int((self.board_square_size - 8) * 0.8)
                        piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                        
                        piece_rect = piece_img.get_rect()
                        piece_rect.center = (screen_x + (self.board_square_size - 8) // 2, 
                                           screen_y + (self.board_square_size - 8) // 2)
                        surface.blit(piece_img, piece_rect)
                except:
                    # Fallback rendering
                    color = (255, 255, 255) if char.isupper() else (50, 50, 50)
                    center = (screen_x + (self.board_square_size - 8) // 2, 
                             screen_y + (self.board_square_size - 8) // 2)
                    radius = (self.board_square_size - 8) // 6
                    pygame.draw.circle(surface, color, center, radius)
                    
                    font = pygame.font.SysFont('Arial', (self.board_square_size - 8) // 8, bold=True)
                    text_color = (0, 0, 0) if char.isupper() else (255, 255, 255)
                    symbol_surface = font.render(char.upper(), True, text_color)
                    symbol_rect = symbol_surface.get_rect(center=center)
                    surface.blit(symbol_surface, symbol_rect)
                
                col += 1
                
    def _draw_board_coordinates(self, surface):
        """Draw coordinate labels"""
        coord_font = pygame.font.SysFont('Segoe UI', 12, bold=True)
        coord_color = (140, 140, 140)
        
        # Files
        for col in range(8):
            file_label = chr(ord('a') + col)
            label_surface = coord_font.render(file_label, True, coord_color)
            x = self.board_x + col * self.board_square_size + self.board_square_size - 15
            y = self.board_y + self.board_size - 15
            surface.blit(label_surface, (x, y))
            
        # Ranks
        for row in range(8):
            rank_label = str(8 - row)
            label_surface = coord_font.render(rank_label, True, coord_color)
            x = self.board_x + 8
            y = self.board_y + row * self.board_square_size + 8
            surface.blit(label_surface, (x, y))
            
    def _draw_move_highlight(self, surface):
        """Highlight the current move"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if (self.current_move_index >= len(analyzed_moves) or 
            self.current_move_index < 0):
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        move = current_analysis.move
        
        # Get classification color
        color = self.classification_colors.get(current_analysis.classification, (255, 255, 255))
        
        # Highlight squares
        from_x = self.board_x + move.initial.col * self.board_square_size + 4
        from_y = self.board_y + move.initial.row * self.board_square_size + 4
        from_rect = pygame.Rect(from_x, from_y, 
                               self.board_square_size - 8, self.board_square_size - 8)
        pygame.draw.rect(surface, color, from_rect, 3)
        
        to_x = self.board_x + move.final.col * self.board_square_size + 4
        to_y = self.board_y + move.final.row * self.board_square_size + 4
        to_rect = pygame.Rect(to_x, to_y, 
                             self.board_square_size - 8, self.board_square_size - 8)
        pygame.draw.rect(surface, color, to_rect, 3)
        
    def _draw_right_panel(self, surface):
        """Draw the right analysis panel"""
        # Panel background
        panel_rect = pygame.Rect(self.panel_x, 20, self.panel_width, self.panel_height)
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=16)
        
        # Header
        self._draw_panel_header(surface)
        
        if not self.analyzer.is_analysis_complete():
            self._draw_analysis_progress(surface)
        else:
            self._draw_move_list(surface)
            self._draw_current_move_info(surface)
            
    def _draw_panel_header(self, surface):
        """Draw panel header"""
        # Title
        title_font = pygame.font.SysFont('Segoe UI', 28, bold=True)
        title_text = "Analysis"
        title_surface = title_font.render(title_text, True, self.header_color)
        surface.blit(title_surface, (self.panel_x + 20, 35))
        
        # Status
        status_font = pygame.font.SysFont('Segoe UI', 14)
        if self.analyzer.is_analysis_complete():
            status_text = "✓ Analysis Complete"
            status_color = self.accent_color
        else:
            progress = self.analyzer.get_analysis_progress()
            status_text = f"Analyzing... {progress}%"
            status_color = self.secondary_text
            
        status_surface = status_font.render(status_text, True, status_color)
        surface.blit(status_surface, (self.panel_x + 20, 75))
        
    def _draw_analysis_progress(self, surface):
        """Draw analysis progress"""
        progress = self.analyzer.get_analysis_progress()
        
        # Progress bar background
        bar_rect = pygame.Rect(self.panel_x + 20, 120, self.panel_width - 40, 8)
        pygame.draw.rect(surface, (64, 72, 88), bar_rect, border_radius=4)
        
        # Progress fill
        fill_width = int((self.panel_width - 40) * progress / 100)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.panel_x + 20, 120, fill_width, 8)
            pygame.draw.rect(surface, self.accent_color, fill_rect, border_radius=4)
            
    def _draw_move_list(self, surface):
        """Draw the move list with modern cards"""
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        # Move list header
        header_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        header_surface = header_font.render("Moves", True, self.header_color)
        surface.blit(header_surface, (self.panel_x + 20, 110))
        
        # Calculate visible area
        start_y = 150
        move_height = 60
        visible_area_height = self.panel_height - 200
        visible_moves = min(len(analyzed_moves), visible_area_height // move_height)
        
        # Ensure current move is visible
        if self.current_move_index < self.move_list_scroll:
            self.move_list_scroll = self.current_move_index
        elif self.current_move_index >= self.move_list_scroll + visible_moves:
            self.move_list_scroll = self.current_move_index - visible_moves + 1
            
        # Draw move cards
        for i in range(visible_moves):
            move_index = i + self.move_list_scroll
            if move_index >= len(analyzed_moves):
                break
                
            move_analysis = analyzed_moves[move_index]
            y = start_y + i * move_height
            
            # Card background
            is_selected = move_index == self.current_move_index
            card_color = self.selected_color if is_selected else self.card_color
            
            card_rect = pygame.Rect(self.panel_x + 15, y - 5, self.panel_width - 30, move_height - 10)
            pygame.draw.rect(surface, card_color, card_rect, border_radius=12)
            
            self._draw_move_card(surface, move_analysis, move_index, y, is_selected)
            
    def _draw_move_card(self, surface, move_analysis, move_index, y, is_selected):
        """Draw individual move card"""
        x_base = self.panel_x + 25
        
        # Move number and notation
        move_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        player_symbol = "●" if move_analysis.player == 'white' else "○"
        move_text = f"{move_analysis.move_number}. {player_symbol}"
        move_surface = move_font.render(move_text, True, self.text_color)
        surface.blit(move_surface, (x_base, y))
        
        # Move notation
        notation_font = pygame.font.SysFont('Segoe UI', 16)
        move_notation = self._get_move_notation(move_analysis.move)
        notation_surface = notation_font.render(move_notation, True, self.text_color)
        surface.blit(notation_surface, (x_base + 80, y))
        
        # Classification badge
        self._draw_classification_badge(surface, move_analysis.classification, 
                                      x_base + 160, y - 2)
        
        # Evaluation change
        if hasattr(move_analysis, 'eval_loss') and move_analysis.eval_loss > 0:
            eval_font = pygame.font.SysFont('Segoe UI', 12, bold=True)
            eval_text = f"-{move_analysis.eval_loss}"
            eval_color = (255, 146, 146) if move_analysis.eval_loss > 100 else (255, 167, 38)
            eval_surface = eval_font.render(eval_text, True, eval_color)
            surface.blit(eval_surface, (x_base + 250, y + 2))
            
        # Best move suggestion (if not best)
        if (move_analysis.classification not in ['BEST', 'BRILLIANT', 'GREAT'] and 
            hasattr(move_analysis, 'best_moves') and move_analysis.best_moves):
            best_notation = self._uci_to_notation(move_analysis.best_moves[0])
            best_text = f"Best: {best_notation}"
            best_font = pygame.font.SysFont('Segoe UI', 11)
            best_surface = best_font.render(best_text, True, self.secondary_text)
            surface.blit(best_surface, (x_base, y + 25))
            
    def _draw_classification_badge(self, surface, classification, x, y):
        """Draw modern classification badge"""
        color = self.classification_colors.get(classification, self.secondary_text)
        
        # Badge background
        badge_width = 80
        badge_height = 22
        badge_rect = pygame.Rect(x, y, badge_width, badge_height)
        pygame.draw.rect(surface, color, badge_rect, border_radius=11)
        
        # Badge text
        badge_font = pygame.font.SysFont('Segoe UI', 10, bold=True)
        text_color = (255, 255, 255) if classification in ['BLUNDER', 'MISTAKE'] else (0, 0, 0)
        badge_surface = badge_font.render(classification.title(), True, text_color)
        text_rect = badge_surface.get_rect(center=badge_rect.center)
        surface.blit(badge_surface, text_rect)
        
    def _draw_current_move_info(self, surface):
        """Draw current move detailed info"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if (self.current_move_index >= len(analyzed_moves) or 
            self.current_move_index < 0):
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        
        # Info card
        info_y = self.panel_height - 120
        info_rect = pygame.Rect(self.panel_x + 15, info_y, self.panel_width - 30, 100)
        pygame.draw.rect(surface, self.card_color, info_rect, border_radius=12)
        
        # Move details
        details_font = pygame.font.SysFont('Segoe UI', 14)
        details_text = f"Move {current_analysis.move_number} - {current_analysis.player.title()}"
        details_surface = details_font.render(details_text, True, self.header_color)
        surface.blit(details_surface, (self.panel_x + 25, info_y + 15))
        
        # Evaluation
        if hasattr(current_analysis, 'eval_after') and current_analysis.eval_after:
            eval_info = self._format_evaluation(current_analysis.eval_after)
            eval_surface = details_font.render(f"Position: {eval_info}", True, self.secondary_text)
            surface.blit(eval_surface, (self.panel_x + 25, info_y + 40))
            
        # Quality score if available
        if hasattr(current_analysis, 'move_quality_score'):
            score_text = f"Quality: {current_analysis.move_quality_score:.0f}/100"
            score_surface = details_font.render(score_text, True, self.secondary_text)
            surface.blit(score_surface, (self.panel_x + 25, info_y + 65))
            
    def _draw_evaluation_bar(self, surface):
        """Draw evaluation bar"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        # Bar dimensions
        bar_x = self.board_x + self.board_size + 15
        bar_y = self.board_y
        bar_width = 8
        bar_height = self.board_size
        
        # Background
        pygame.draw.rect(surface, (64, 72, 88), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        
        # Current evaluation
        if self.current_move_index < len(analyzed_moves):
            current_analysis = analyzed_moves[self.current_move_index]
            if hasattr(current_analysis, 'eval_after') and current_analysis.eval_after:
                evaluation = current_analysis.eval_after
                
                if evaluation and 'value' in evaluation:
                    if evaluation['type'] == 'cp':
                        eval_cp = max(-500, min(500, evaluation['value']))
                        bar_position = (eval_cp + 500) / 1000
                    else:  # mate
                        bar_position = 1.0 if evaluation['value'] > 0 else 0.0
                        
                    # Draw evaluation
                    white_height = int(bar_height * bar_position)
                    black_height = bar_height - white_height
                    
                    if white_height > 0:
                        white_rect = pygame.Rect(bar_x, bar_y + black_height, bar_width, white_height)
                        pygame.draw.rect(surface, (240, 240, 240), white_rect, border_radius=4)
                        
                    if black_height > 0:
                        black_rect = pygame.Rect(bar_x, bar_y, bar_width, black_height)
                        pygame.draw.rect(surface, (60, 60, 60), black_rect, border_radius=4)
                        
                    # Center line
                    center_y = bar_y + bar_height // 2
                    pygame.draw.line(surface, (120, 120, 130), 
                                   (bar_x, center_y), (bar_x + bar_width, center_y), 2)
                    
    def _get_move_notation(self, move):
        """Convert move to notation"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
        to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
        
        return f"{from_square}{to_square}"
        
    def _uci_to_notation(self, uci_move):
        """Convert UCI to notation"""
        if len(uci_move) >= 4:
            return f"{uci_move[:2]}{uci_move[2:4]}"
        return uci_move
        
    def _format_evaluation(self, evaluation):
        """Format evaluation for display"""
        if not evaluation or 'value' not in evaluation:
            return "N/A"
            
        if evaluation['type'] == 'cp':
            score = evaluation['value'] / 100.0
            return f"{score:+.2f}"
        else:  # mate
            moves_to_mate = abs(evaluation['value'])
            side = "White" if evaluation['value'] > 0 else "Black"
            return f"Mate in {moves_to_mate} for {side}"
            
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
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check for move card clicks
            if self.analyzer.is_analysis_complete():
                analyzed_moves = self.analyzer.get_analyzed_moves()
                start_y = 150
                move_height = 60
                
                if (self.panel_x + 15 <= event.pos[0] <= self.panel_x + self.panel_width - 15):
                    relative_y = event.pos[1] - start_y + 5
                    if relative_y >= 0:
                        clicked_move = (relative_y // move_height) + self.move_list_scroll
                        if 0 <= clicked_move < len(analyzed_moves):
                            self.current_move_index = clicked_move
                            return True
                            
        return False
        
    def next_move(self):
        """Move to next move"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index < len(analyzed_moves) - 1:
            self.current_move_index += 1

    def previous_move(self):
        """Move to previous move"""
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