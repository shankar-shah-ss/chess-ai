# game_summary.py - Modern Game Summary Widget
import pygame
import math
from typing import Optional, Dict, Any

class GameSummaryWidget:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.visible = False
        self.width = 500
        self.height = 600
        self.x = 0
        self.y = 0
        
        # Modern color palette
        self.colors = {
            'bg_primary': (30, 30, 30),
            'bg_secondary': (37, 37, 38),
            'bg_tertiary': (45, 45, 48),
            'bg_hover': (55, 55, 58),
            'accent_primary': (0, 122, 255),
            'accent_secondary': (52, 168, 83),
            'text_primary': (255, 255, 255),
            'text_secondary': (204, 204, 204),
            'text_muted': (140, 140, 140),
            'border': (68, 68, 68),
            'success': (40, 167, 69),
            'warning': (255, 193, 7),
            'error': (220, 53, 69),
        }
        
        # Classification colors
        self.classification_colors = {
            'BRILLIANT': (138, 43, 226),
            'GREAT': (34, 139, 34),
            'BEST': (52, 168, 83),
            'EXCELLENT': (72, 201, 176),
            'OKAY': (108, 117, 125),
            'MISS': (255, 193, 7),
            'INACCURACY': (255, 158, 56),
            'MISTAKE': (255, 107, 107),
            'BLUNDER': (220, 53, 69),
        }
        
        # Fonts
        self.fonts = {
            'title': pygame.font.SysFont('Segoe UI', 24, bold=True),
            'heading': pygame.font.SysFont('Segoe UI', 18, bold=True),
            'subheading': pygame.font.SysFont('Segoe UI', 16, bold=True),
            'body': pygame.font.SysFont('Segoe UI', 14),
            'body_bold': pygame.font.SysFont('Segoe UI', 14, bold=True),
            'caption': pygame.font.SysFont('Segoe UI', 12),
            'small': pygame.font.SysFont('Segoe UI', 11),
        }
        
        # Animation
        self.animation_progress = 0.0
        self.target_animation = 0.0
        self.animation_speed = 8.0
        
        # Scrolling
        self.scroll_y = 0
        self.max_scroll = 0
        self.content_height = 0
        
        # Close button
        self.close_button_rect = None
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        
    def set_position(self, x, y):
        """Set widget position"""
        self.x = x
        self.y = y
        
    def show(self):
        """Show the widget with animation"""
        self.visible = True
        self.target_animation = 1.0
        self.scroll_y = 0
        
    def hide(self):
        """Hide the widget with animation"""
        self.target_animation = 0.0
        
    def update(self):
        """Update animations"""
        if abs(self.animation_progress - self.target_animation) > 0.01:
            diff = self.target_animation - self.animation_progress
            self.animation_progress += diff * self.animation_speed * (1/60)
            
        if self.target_animation == 0.0 and self.animation_progress < 0.1:
            self.visible = False
            self.animation_progress = 0.0
            
    def render(self, surface):
        """Render the modern summary widget"""
        if not self.visible or not self.analyzer:
            return
            
        self.update()
        
        if self.animation_progress <= 0:
            return
            
        # Get summary data
        summary = self.analyzer.get_game_summary()
        if not summary:
            return
            
        # Apply animation transform
        alpha = int(255 * self.animation_progress)
        scale = 0.8 + (0.2 * self.animation_progress)
        
        # Create widget surface
        widget_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw widget background with shadow
        shadow_offset = 8
        shadow_rect = pygame.Rect(shadow_offset, shadow_offset, self.width, self.height)
        pygame.draw.rect(widget_surface, (0, 0, 0, 60), shadow_rect, border_radius=16)
        
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(widget_surface, (*self.colors['bg_primary'], alpha), main_rect, border_radius=16)
        pygame.draw.rect(widget_surface, (*self.colors['border'], alpha), main_rect, 2, border_radius=16)
        
        # Clip for scrolling content
        content_rect = pygame.Rect(20, 60, self.width - 40, self.height - 80)
        content_surface = pygame.Surface((content_rect.width, content_rect.height + self.max_scroll), pygame.SRCALPHA)
        
        # Draw content
        y_offset = self._draw_header(widget_surface, summary, alpha)
        content_y = self._draw_summary_content(content_surface, summary, alpha)
        
        # Update scroll limits
        self.content_height = content_y
        self.max_scroll = max(0, content_y - content_rect.height)
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
        
        # Blit scrolled content
        scroll_rect = pygame.Rect(0, self.scroll_y, content_rect.width, content_rect.height)
        widget_surface.blit(content_surface, content_rect, scroll_rect)
        
        # Draw close button
        self._draw_close_button(widget_surface, alpha)
        
        # Apply scale and blit to main surface
        if scale != 1.0:
            scaled_width = int(self.width * scale)
            scaled_height = int(self.height * scale)
            scaled_surface = pygame.transform.scale(widget_surface, (scaled_width, scaled_height))
            
            scaled_x = self.x + (self.width - scaled_width) // 2
            scaled_y = self.y + (self.height - scaled_height) // 2
            surface.blit(scaled_surface, (scaled_x, scaled_y))
        else:
            surface.blit(widget_surface, (self.x, self.y))
            
    def _draw_header(self, surface, summary, alpha):
        """Draw widget header"""
        # Title
        title_surface = self.fonts['title'].render("Game Analysis Summary", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (20, 20))
        
        # Subtitle with game result
        result_text = self._get_game_result_text(summary)
        subtitle_surface = self.fonts['body'].render(result_text, True, (*self.colors['text_secondary'], alpha))
        surface.blit(subtitle_surface, (20, 50))
        
        return 80
        
    def _draw_close_button(self, surface, alpha):
        """Draw modern close button"""
        button_size = 32
        button_x = self.width - button_size - 15
        button_y = 15
        
        self.close_button_rect = pygame.Rect(button_x, button_y, button_size, button_size)
        
        # Button background
        pygame.draw.rect(surface, (*self.colors['bg_hover'], alpha), self.close_button_rect, border_radius=6)
        pygame.draw.rect(surface, (*self.colors['border'], alpha), self.close_button_rect, 1, border_radius=6)
        
        # X symbol
        center_x = button_x + button_size // 2
        center_y = button_y + button_size // 2
        size = 8
        
        # Draw X
        pygame.draw.line(surface, (*self.colors['text_primary'], alpha), 
                        (center_x - size, center_y - size), (center_x + size, center_y + size), 2)
        pygame.draw.line(surface, (*self.colors['text_primary'], alpha), 
                        (center_x + size, center_y - size), (center_x - size, center_y + size), 2)
        
    def _draw_summary_content(self, surface, summary, alpha):
        """Draw the main summary content"""
        y = 0
        
        # Player accuracies section
        y = self._draw_accuracy_section(surface, summary, y, alpha)
        y += 20
        
        # ELO estimates section
        y = self._draw_elo_section(surface, summary, y, alpha)
        y += 20
        
        # Move classifications section
        y = self._draw_classifications_section(surface, summary, y, alpha)
        y += 20
        
        # Game phases section
        y = self._draw_phases_section(surface, summary, y, alpha)
        y += 20
        
        # Additional statistics section
        y = self._draw_statistics_section(surface, summary, y, alpha)
        
        return y
        
    def _draw_accuracy_section(self, surface, summary, y, alpha):
        """Draw accuracy comparison section"""
        # Section title
        title_surface = self.fonts['heading'].render("Accuracy", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (0, y))
        y += 35
        
        # Accuracy bars
        white_acc = summary.get('white_accuracy', 0)
        black_acc = summary.get('black_accuracy', 0)
        
        bar_width = 200
        bar_height = 24
        
        # White accuracy bar
        white_label = self.fonts['body_bold'].render("White", True, (*self.colors['text_primary'], alpha))
        surface.blit(white_label, (0, y))
        
        white_bg_rect = pygame.Rect(80, y + 2, bar_width, bar_height)
        pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), white_bg_rect, border_radius=12)
        
        white_fill_width = int(bar_width * white_acc / 100)
        if white_fill_width > 0:
            white_fill_rect = pygame.Rect(80, y + 2, white_fill_width, bar_height)
            color = self._get_accuracy_color(white_acc)
            pygame.draw.rect(surface, (*color, alpha), white_fill_rect, border_radius=12)
            
        white_text = f"{white_acc:.1f}%"
        white_percent = self.fonts['body'].render(white_text, True, (*self.colors['text_primary'], alpha))
        surface.blit(white_percent, (290, y + 4))
        
        y += 35
        
        # Black accuracy bar
        black_label = self.fonts['body_bold'].render("Black", True, (*self.colors['text_primary'], alpha))
        surface.blit(black_label, (0, y))
        
        black_bg_rect = pygame.Rect(80, y + 2, bar_width, bar_height)
        pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), black_bg_rect, border_radius=12)
        
        black_fill_width = int(bar_width * black_acc / 100)
        if black_fill_width > 0:
            black_fill_rect = pygame.Rect(80, y + 2, black_fill_width, bar_height)
            color = self._get_accuracy_color(black_acc)
            pygame.draw.rect(surface, (*color, alpha), black_fill_rect, border_radius=12)
            
        black_text = f"{black_acc:.1f}%"
        black_percent = self.fonts['body'].render(black_text, True, (*self.colors['text_primary'], alpha))
        surface.blit(black_percent, (290, y + 4))
        
        return y + 40
        
    def _draw_elo_section(self, surface, summary, y, alpha):
        """Draw ELO estimates section"""
        title_surface = self.fonts['heading'].render("ELO Estimates", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (0, y))
        y += 35
        
        # ELO cards
        card_width = 180
        card_height = 60
        card_spacing = 20
        
        # White ELO card
        white_card_rect = pygame.Rect(0, y, card_width, card_height)
        pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), white_card_rect, border_radius=8)
        pygame.draw.rect(surface, (*self.colors['border'], alpha), white_card_rect, 1, border_radius=8)
        
        white_label = self.fonts['body_bold'].render("White ELO", True, (*self.colors['text_secondary'], alpha))
        surface.blit(white_label, (white_card_rect.x + 12, white_card_rect.y + 10))
        
        white_elo = summary.get('white_elo', 1200)
        white_elo_text = str(white_elo)
        white_elo_surface = self.fonts['heading'].render(white_elo_text, True, (*self.colors['text_primary'], alpha))
        surface.blit(white_elo_surface, (white_card_rect.x + 12, white_card_rect.y + 28))
        
        # Black ELO card
        black_card_rect = pygame.Rect(card_width + card_spacing, y, card_width, card_height)
        pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), black_card_rect, border_radius=8)
        pygame.draw.rect(surface, (*self.colors['border'], alpha), black_card_rect, 1, border_radius=8)
        
        black_label = self.fonts['body_bold'].render("Black ELO", True, (*self.colors['text_secondary'], alpha))
        surface.blit(black_label, (black_card_rect.x + 12, black_card_rect.y + 10))
        
        black_elo = summary.get('black_elo', 1200)
        black_elo_text = str(black_elo)
        black_elo_surface = self.fonts['heading'].render(black_elo_text, True, (*self.colors['text_primary'], alpha))
        surface.blit(black_elo_surface, (black_card_rect.x + 12, black_card_rect.y + 28))
        
        return y + card_height + 15
        
    def _draw_classifications_section(self, surface, summary, y, alpha):
        """Draw move classifications breakdown"""
        title_surface = self.fonts['heading'].render("Move Quality", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (0, y))
        y += 35
        
        classifications = [
            ('Brilliant', summary.get('brilliant_moves', 0), 'BRILLIANT'),
            ('Great', summary.get('great_moves', 0), 'GREAT'),
            ('Best', summary.get('best_moves', 0), 'BEST'),
            ('Mistakes', summary.get('mistakes', 0), 'MISTAKE'),
            ('Blunders', summary.get('blunders', 0), 'BLUNDER'),
        ]
        
        # Draw classification bars
        max_value = max([count for _, count, _ in classifications]) or 1
        bar_width = 300
        bar_height = 20
        
        for label, count, class_type in classifications:
            if count == 0:
                continue
                
            # Label
            label_surface = self.fonts['body'].render(f"{label}:", True, (*self.colors['text_secondary'], alpha))
            surface.blit(label_surface, (0, y))
            
            # Bar background
            bar_bg_rect = pygame.Rect(80, y + 2, bar_width, bar_height)
            pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), bar_bg_rect, border_radius=10)
            
            # Bar fill
            fill_width = int(bar_width * count / max_value)
            if fill_width > 0:
                fill_rect = pygame.Rect(80, y + 2, fill_width, bar_height)
                color = self.classification_colors.get(class_type, self.colors['text_secondary'])
                pygame.draw.rect(surface, (*color, alpha), fill_rect, border_radius=10)
                
            # Count text
            count_text = str(count)
            count_surface = self.fonts['body_bold'].render(count_text, True, (*self.colors['text_primary'], alpha))
            surface.blit(count_surface, (390, y + 2))
            
            y += 30
            
        return y + 10
        
    def _draw_phases_section(self, surface, summary, y, alpha):
        """Draw game phases analysis"""
        title_surface = self.fonts['heading'].render("Game Phases", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (0, y))
        y += 35
        
        phases = [
            ('Opening', summary.get('opening_accuracy', 0)),
            ('Middlegame', summary.get('middlegame_accuracy', 0)),
            ('Endgame', summary.get('endgame_accuracy', 0)),
        ]
        
        # Phase accuracy chart
        chart_width = 360
        chart_height = 120
        chart_rect = pygame.Rect(0, y, chart_width, chart_height)
        
        # Chart background
        pygame.draw.rect(surface, (*self.colors['bg_tertiary'], alpha), chart_rect, border_radius=8)
        
        # Draw phase bars
        bar_width = 80
        bar_spacing = 40
        max_height = 80
        
        for i, (phase, accuracy) in enumerate(phases):
            x_pos = 30 + i * (bar_width + bar_spacing)
            bar_height = int(max_height * accuracy / 100) if accuracy > 0 else 5
            
            # Bar
            bar_rect = pygame.Rect(x_pos, y + chart_height - 30 - bar_height, bar_width, bar_height)
            color = self._get_accuracy_color(accuracy)
            pygame.draw.rect(surface, (*color, alpha), bar_rect, border_radius=4)
            
            # Phase label
            phase_surface = self.fonts['caption'].render(phase, True, (*self.colors['text_secondary'], alpha))
            label_rect = phase_surface.get_rect(center=(x_pos + bar_width // 2, y + chart_height - 15))
            surface.blit(phase_surface, label_rect)
            
            # Accuracy text
            acc_text = f"{accuracy:.1f}%" if accuracy > 0 else "N/A"
            acc_surface = self.fonts['small'].render(acc_text, True, (*self.colors['text_primary'], alpha))
            acc_rect = acc_surface.get_rect(center=(x_pos + bar_width // 2, y + chart_height - 45 - bar_height))
            surface.blit(acc_surface, acc_rect)
            
        return y + chart_height + 15
        
    def _draw_statistics_section(self, surface, summary, y, alpha):
        """Draw additional statistics"""
        title_surface = self.fonts['heading'].render("Statistics", True, (*self.colors['text_primary'], alpha))
        surface.blit(title_surface, (0, y))
        y += 35
        
        stats = [
            ("Total Moves", summary.get('total_moves', 0)),
            ("Average Eval Loss", f"{summary.get('average_eval_loss', 0):.1f} cp"),
            ("Sacrifices Made", summary.get('sacrifices_made', 0)),
            ("Total Eval Loss", f"{summary.get('total_eval_loss', 0):.0f} cp"),
        ]
        
        # Draw stats in two columns
        col_width = 180
        row_height = 25
        
        for i, (label, value) in enumerate(stats):
            col = i % 2
            row = i // 2
            
            x_pos = col * (col_width + 20)
            y_pos = y + row * row_height
            
            # Label
            label_surface = self.fonts['body'].render(f"{label}:", True, (*self.colors['text_secondary'], alpha))
            surface.blit(label_surface, (x_pos, y_pos))
            
            # Value
            value_surface = self.fonts['body_bold'].render(str(value), True, (*self.colors['text_primary'], alpha))
            surface.blit(value_surface, (x_pos + 120, y_pos))
            
        return y + ((len(stats) + 1) // 2) * row_height + 20
        
    def _get_accuracy_color(self, accuracy):
        """Get color based on accuracy percentage"""
        if accuracy >= 90:
            return self.colors['success']
        elif accuracy >= 80:
            return (129, 182, 76)  # Good green
        elif accuracy >= 70:
            return self.colors['warning']
        else:
            return self.colors['error']
            
    def _get_game_result_text(self, summary):
        """Get game result description"""
        total_moves = summary.get('total_moves', 0)
        white_acc = summary.get('white_accuracy', 0)
        black_acc = summary.get('black_accuracy', 0)
        
        if white_acc > black_acc + 10:
            result = "White played better"
        elif black_acc > white_acc + 10:
            result = "Black played better"
        else:
            result = "Evenly matched game"
            
        return f"{total_moves} moves • {result}"
        
    def handle_input(self, event):
        """Handle input events"""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check close button
            if self.close_button_rect:
                adjusted_close_rect = pygame.Rect(
                    self.x + self.close_button_rect.x,
                    self.y + self.close_button_rect.y,
                    self.close_button_rect.width,
                    self.close_button_rect.height
                )
                
                if adjusted_close_rect.collidepoint(event.pos):
                    self.hide()
                    return True
                    
            # Check if click is inside widget
            widget_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if widget_rect.collidepoint(event.pos):
                return True  # Consume the event
                
        elif event.type == pygame.MOUSEWHEEL:
            # Handle scrolling
            widget_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if widget_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 20))
                return True
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
                
        return False