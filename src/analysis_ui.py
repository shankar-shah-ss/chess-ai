# analysis_ui.py
import pygame
from const import *

class AnalysisUI:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.current_move_index = 0
        self.show_analysis = False
        self.scroll_offset = 0
        self.move_height = 60
        self.panel_width = 400
        
        # UI colors
        self.bg_color = (40, 40, 40)
        self.panel_color = (60, 60, 60)
        self.text_color = (255, 255, 255)
        self.header_color = (200, 200, 200)
        
        # Move classification colors
        self.classification_colors = {
            'GREAT': (0, 100, 255),
            'BEST': (0, 200, 0),
            'EXCELLENT': (100, 255, 100),
            'GOOD': (150, 255, 150),
            'INACCURACY': (255, 255, 100),
            'MISTAKE': (255, 165, 0),
            'BLUNDER': (255, 0, 0)
        }
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        self.current_move_index = 0
        self.scroll_offset = 0
        
    def toggle_analysis_view(self):
        """Toggle analysis view on/off"""
        self.show_analysis = not self.show_analysis
        
    def show_analysis_panel(self, surface):
        """Show the analysis panel"""
        if not self.show_analysis or not self.analyzer:
            return
            
        # Draw background panel
        panel_rect = pygame.Rect(WIDTH - self.panel_width, 0, self.panel_width, HEIGHT)
        pygame.draw.rect(surface, self.panel_color, panel_rect)
        pygame.draw.line(surface, (100, 100, 100), 
                        (WIDTH - self.panel_width, 0), 
                        (WIDTH - self.panel_width, HEIGHT), 2)
        
        # Show analysis status
        if not self.analyzer.is_analysis_complete():
            self._show_analysis_progress(surface)
        else:
            self._show_move_analysis(surface)
            
    def _show_analysis_progress(self, surface):
        """Show analysis progress"""
        progress = self.analyzer.get_analysis_progress()
        
        # Title
        title_font = pygame.font.SysFont('monospace', 24, bold=True)
        title = title_font.render("Analyzing Game...", True, self.header_color)
        surface.blit(title, (WIDTH - self.panel_width + 20, 20))
        
        # Progress bar
        bar_rect = pygame.Rect(WIDTH - self.panel_width + 20, 60, self.panel_width - 40, 20)
        pygame.draw.rect(surface, (100, 100, 100), bar_rect)
        
        fill_width = int((self.panel_width - 40) * progress / 100)
        fill_rect = pygame.Rect(WIDTH - self.panel_width + 20, 60, fill_width, 20)
        pygame.draw.rect(surface, (0, 200, 0), fill_rect)
        
        # Progress text
        progress_text = self.config.font.render(f"{progress}% Complete", True, self.text_color)
        surface.blit(progress_text, (WIDTH - self.panel_width + 20, 90))
        
    def _show_move_analysis(self, surface):
        """Show detailed move analysis"""
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        # Title
        title_font = pygame.font.SysFont('monospace', 20, bold=True)
        title = title_font.render("Game Analysis", True, self.header_color)
        surface.blit(title, (WIDTH - self.panel_width + 20, 10))
        
        # Controls info
        controls_font = pygame.font.SysFont('monospace', 12)
        controls = [
            "↑/↓: Navigate moves",
            "A: Toggle analysis",
            "R: Restart game"
        ]
        
        y_pos = 40
        for control in controls:
            text = controls_font.render(control, True, (150, 150, 150))
            surface.blit(text, (WIDTH - self.panel_width + 20, y_pos))
            y_pos += 15
            
        # Move list
        start_y = 120
        visible_moves = min(len(analyzed_moves), (HEIGHT - start_y) // self.move_height)
        
        for i in range(visible_moves):
            move_index = i + self.scroll_offset
            if move_index >= len(analyzed_moves):
                break
                
            move_analysis = analyzed_moves[move_index]
            y = start_y + i * self.move_height
            
            # Highlight current move
            if move_index == self.current_move_index:
                highlight_rect = pygame.Rect(WIDTH - self.panel_width + 10, y - 5, 
                                           self.panel_width - 20, self.move_height - 10)
                pygame.draw.rect(surface, (80, 80, 80), highlight_rect)
                
            self._draw_move_entry(surface, move_analysis, y)
            
    def _draw_move_entry(self, surface, move_analysis, y):
        """Draw a single move analysis entry"""
        x_base = WIDTH - self.panel_width + 20
        
        # Move number and player
        move_font = pygame.font.SysFont('monospace', 14, bold=True)
        player_color = "W" if move_analysis.player == 'white' else "B"
        move_text = f"{move_analysis.move_number}.{player_color}"
        move_surface = move_font.render(move_text, True, self.text_color)
        surface.blit(move_surface, (x_base, y))
        
        # Move notation (simplified)
        move_notation = self._get_move_notation(move_analysis.move)
        notation_surface = self.config.font.render(move_notation, True, self.text_color)
        surface.blit(notation_surface, (x_base + 50, y))
        
        # Classification with color
        classification = move_analysis.classification
        class_color = self.classification_colors.get(classification, self.text_color)
        class_surface = self.config.font.render(classification, True, class_color)
        surface.blit(class_surface, (x_base, y + 20))
        
        # Evaluation change
        if move_analysis.eval_loss > 0:
            eval_text = f"-{move_analysis.eval_loss}"
            eval_surface = self.config.font.render(eval_text, True, (255, 100, 100))
            surface.blit(eval_surface, (x_base + 150, y + 20))
            
        # Best move suggestion (if not best move)
        if (move_analysis.classification not in ['BEST', 'GREAT'] and 
            move_analysis.best_moves):
            best_notation = self._uci_to_notation(move_analysis.best_moves[0])
            best_text = f"Best: {best_notation}"
            best_surface = pygame.font.SysFont('monospace', 12).render(
                best_text, True, (100, 255, 100))
            surface.blit(best_surface, (x_base, y + 40))
            
    def _get_move_notation(self, move):
        """Convert move to simple notation"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
        to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
        
        return f"{from_square}-{to_square}"
        
    def _uci_to_notation(self, uci_move):
        """Convert UCI move to readable notation"""
        if len(uci_move) >= 4:
            return f"{uci_move[:2]}-{uci_move[2:4]}"
        return uci_move
        
    def handle_analysis_input(self, event):
        """Handle input for analysis view"""
        if not self.show_analysis or not self.analyzer:
            return False
            
        if event.type == pygame.KEYDOWN:
            analyzed_moves = self.analyzer.get_analyzed_moves()
            
            if event.key == pygame.K_UP:
                if self.current_move_index > 0:
                    self.current_move_index -= 1
                    self._update_scroll()
                return True
                
            elif event.key == pygame.K_DOWN:
                if self.current_move_index < len(analyzed_moves) - 1:
                    self.current_move_index += 1
                    self._update_scroll()
                return True
                
            elif event.key == pygame.K_a:
                self.toggle_analysis_view()
                return True
                
        return False
        
    def _update_scroll(self):
        """Update scroll offset to keep current move visible"""
        visible_moves = (HEIGHT - 120) // self.move_height
        
        if self.current_move_index < self.scroll_offset:
            self.scroll_offset = self.current_move_index
        elif self.current_move_index >= self.scroll_offset + visible_moves:
            self.scroll_offset = self.current_move_index - visible_moves + 1
            
    def show_move_analysis_overlay(self, surface, board):
        """Show analysis overlay on the board"""
        if (not self.show_analysis or not self.analyzer or 
            not self.analyzer.is_analysis_complete()):
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if (self.current_move_index >= len(analyzed_moves) or 
            self.current_move_index < 0):
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        
        # Highlight the move on the board
        move = current_analysis.move
        initial_rect = (move.initial.col * SQSIZE, move.initial.row * SQSIZE, SQSIZE, SQSIZE)
        final_rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
        
        # Use classification color for highlighting
        color = self.classification_colors.get(current_analysis.classification, (255, 255, 255))
        
        pygame.draw.rect(surface, color, initial_rect, 4)
        pygame.draw.rect(surface, color, final_rect, 4)
        
        # Show evaluation change as text overlay
        if current_analysis.eval_loss > 0:
            font = pygame.font.SysFont('monospace', 24, bold=True)
            eval_text = f"-{current_analysis.eval_loss}"
            text_surface = font.render(eval_text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(
                move.final.col * SQSIZE + SQSIZE // 2,
                move.final.row * SQSIZE + SQSIZE // 2
            ))
            
            # Add background for better visibility
            bg_rect = text_rect.inflate(10, 5)
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
            surface.blit(text_surface, text_rect)