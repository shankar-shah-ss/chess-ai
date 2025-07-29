# game_summary.py - Chess.com Style Game Summary Widget
import pygame
import math

class GameSummaryWidget:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.visible = False
        self.x = 50
        self.y = 50
        self.width = 450
        self.height = 600
        
        # Chess.com color scheme
        self.bg_color = (40, 46, 58)
        self.panel_color = (54, 62, 78)
        self.card_color = (64, 72, 88)
        self.text_color = (255, 255, 255)
        self.secondary_text = (181, 181, 181)
        self.header_color = (255, 255, 255)
        self.border_color = (84, 92, 108)
        self.accent_color = (129, 182, 76)
        
        # Player colors
        self.white_color = (255, 255, 255)
        self.black_color = (120, 120, 120)
        
        # Classification colors matching Chess.com
        self.classification_colors = {
            'BRILLIANT': (28, 158, 255),
            'GREAT': (96, 169, 23),
            'BEST': (96, 169, 23),
            'EXCELLENT': (96, 169, 23),
            'OKAY': (115, 192, 67),
            'MISS': (255, 167, 38),
            'INACCURACY': (255, 167, 38),
            'MISTAKE': (255, 146, 146),
            'BLUNDER': (242, 113, 102)
        }
        
        # Animation
        self.fade_alpha = 0
        self.target_alpha = 255
        self.animation_speed = 15
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        
    def set_position(self, x, y):
        """Set widget position"""
        self.x = x
        self.y = y
        
    def show(self):
        """Show the widget with fade-in animation"""
        self.visible = True
        self.target_alpha = 255
        
    def hide(self):
        """Hide the widget with fade-out animation"""
        self.target_alpha = 0
        
    def render(self, surface):
        """Render the Chess.com style game summary"""
        if not self.visible or not self.analyzer or not self.analyzer.is_analysis_complete():
            return
            
        # Update fade animation
        if self.fade_alpha < self.target_alpha:
            self.fade_alpha = min(self.target_alpha, self.fade_alpha + self.animation_speed)
        elif self.fade_alpha > self.target_alpha:
            self.fade_alpha = max(self.target_alpha, self.fade_alpha - self.animation_speed)
            
        if self.fade_alpha <= 0:
            self.visible = False
            return
            
        # Create main surface
        widget_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw shadow
        shadow_offset = 6
        shadow_rect = pygame.Rect(shadow_offset, shadow_offset, self.width, self.height)
        pygame.draw.rect(widget_surface, (0, 0, 0, 80), shadow_rect, border_radius=20)
        
        # Main background
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(widget_surface, self.bg_color, main_rect, border_radius=20)
        pygame.draw.rect(widget_surface, self.border_color, main_rect, 2, border_radius=20)
        
        # Get analysis summary
        summary = self.analyzer.get_game_summary()
        if not summary:
            return
            
        # Draw all sections
        self._draw_header(widget_surface, summary)
        self._draw_player_stats(widget_surface, summary)
        self._draw_accuracy_circles(widget_surface, summary)
        self._draw_move_breakdown(widget_surface, summary)
        self._draw_game_rating(widget_surface, summary)
        
        # Apply alpha and blit
        widget_surface.set_alpha(self.fade_alpha)
        surface.blit(widget_surface, (self.x, self.y))
        
    def _draw_header(self, surface, summary):
        """Draw the header section"""
        # Title
        title_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
        title_surface = title_font.render("Game Review", True, self.header_color)
        surface.blit(title_surface, (25, 25))
        
        # Close button
        close_rect = pygame.Rect(self.width - 40, 20, 30, 30)
        pygame.draw.rect(surface, (200, 100, 100), close_rect, border_radius=15)
        close_font = pygame.font.SysFont('Arial', 18, bold=True)
        close_surface = close_font.render('×', True, (255, 255, 255))
        close_text_rect = close_surface.get_rect(center=close_rect.center)
        surface.blit(close_surface, close_text_rect)
        
        # Game info
        info_font = pygame.font.SysFont('Segoe UI', 14)
        total_moves = summary.get('total_moves', 0)
        info_text = f"{total_moves} moves played"
        info_surface = info_font.render(info_text, True, self.secondary_text)
        surface.blit(info_surface, (25, 60))
        
    def _draw_player_stats(self, surface, summary):
        """Draw player statistics section like Chess.com"""
        # Section background
        section_rect = pygame.Rect(20, 100, self.width - 40, 140)
        pygame.draw.rect(surface, self.card_color, section_rect, border_radius=15)
        
        # Section title
        title_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Players", True, self.header_color)
        surface.blit(title_surface, (35, 115))
        
        # Player cards side by side
        card_width = (self.width - 80) // 2
        
        # White player card
        white_rect = pygame.Rect(35, 145, card_width - 10, 80)
        pygame.draw.rect(surface, self.panel_color, white_rect, border_radius=12)
        
        # White player info
        player_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        white_surface = player_font.render("White", True, self.white_color)
        surface.blit(white_surface, (45, 155))
        
        white_accuracy = summary.get('white_accuracy', 0)
        white_elo = summary.get('white_elo', 1200)
        
        acc_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
        acc_surface = acc_font.render(f"{white_accuracy:.1f}%", True, self.white_color)
        surface.blit(acc_surface, (45, 175))
        
        elo_font = pygame.font.SysFont('Segoe UI', 12)
        elo_surface = elo_font.render(f"({white_elo} ELO)", True, self.secondary_text)
        surface.blit(elo_surface, (45, 205))
        
        # Black player card
        black_rect = pygame.Rect(35 + card_width, 145, card_width - 10, 80)
        pygame.draw.rect(surface, self.panel_color, black_rect, border_radius=12)
        
        # Black player info
        black_surface = player_font.render("Black", True, self.black_color)
        surface.blit(black_surface, (45 + card_width, 155))
        
        black_accuracy = summary.get('black_accuracy', 0)
        black_elo = summary.get('black_elo', 1200)
        
        acc_surface = acc_font.render(f"{black_accuracy:.1f}%", True, self.black_color)
        surface.blit(acc_surface, (45 + card_width, 175))
        
        elo_surface = elo_font.render(f"({black_elo} ELO)", True, self.secondary_text)
        surface.blit(elo_surface, (45 + card_width, 205))
        
    def _draw_accuracy_circles(self, surface, summary):
        """Draw accuracy visualization circles"""
        white_accuracy = summary.get('white_accuracy', 0)
        black_accuracy = summary.get('black_accuracy', 0)
        
        # White accuracy circle
        white_center_x = 35 + 120
        white_center_y = 185
        self._draw_accuracy_circle(surface, (white_center_x, white_center_y), 25, white_accuracy, self.white_color)
        
        # Black accuracy circle
        black_center_x = 35 + (self.width - 80) // 2 + 120
        black_center_y = 185
        self._draw_accuracy_circle(surface, (black_center_x, black_center_y), 25, black_accuracy, self.black_color)
        
    def _draw_accuracy_circle(self, surface, center, radius, accuracy, color):
        """Draw a single accuracy circle"""
        # Background circle
        pygame.draw.circle(surface, (40, 40, 50), center, radius, 3)
        
        # Accuracy arc
        if accuracy > 0:
            arc_angle = (accuracy / 100) * 2 * math.pi
            self._draw_arc(surface, center, radius - 2, 0, arc_angle, color, 4)
            
    def _draw_move_breakdown(self, surface, summary):
        """Draw move classification breakdown like Chess.com"""
        # Section background
        section_rect = pygame.Rect(20, 260, self.width - 40, 200)
        pygame.draw.rect(surface, self.card_color, section_rect, border_radius=15)
        
        # Section title
        title_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Move Breakdown", True, self.header_color)
        surface.blit(title_surface, (35, 275))
        
        # Get move classifications
        analyzed_moves = self.analyzer.get_analyzed_moves()
        classifications = {}
        
        # Count classifications
        for move in analyzed_moves:
            classification = move.classification
            classifications[classification] = classifications.get(classification, 0) + 1
            
        # Draw classification rows
        y_offset = 305
        row_height = 30
        
        key_classifications = [
            ('Brilliant', 'BRILLIANT', '!!'),
            ('Great', 'GREAT', '!'),
            ('Best', 'BEST', '✓'),
            ('Mistake', 'MISTAKE', '?'),
            ('Miss', 'MISS', '?!'),
            ('Blunder', 'BLUNDER', '??')
        ]
        
        for i, (label, key, symbol) in enumerate(key_classifications):
            count = classifications.get(key, 0)
            color = self.classification_colors.get(key, self.text_color)
            
            y_pos = y_offset + i * row_height
            
            # Symbol
            symbol_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
            symbol_surface = symbol_font.render(symbol, True, color)
            surface.blit(symbol_surface, (45, y_pos))
            
            # Label
            label_font = pygame.font.SysFont('Segoe UI', 14)
            label_surface = label_font.render(label, True, self.text_color)
            surface.blit(label_surface, (70, y_pos + 2))
            
            # Count with white/black split
            white_count = sum(1 for move in analyzed_moves 
                            if move.classification == key and move.player == 'white')
            black_count = count - white_count
            
            count_font = pygame.font.SysFont('Segoe UI', 14, bold=True)
            
            # White count
            white_surface = count_font.render(str(white_count), True, self.white_color)
            surface.blit(white_surface, (280, y_pos + 2))
            
            # Black count  
            black_surface = count_font.render(str(black_count), True, self.black_color)
            surface.blit(black_surface, (320, y_pos + 2))
            
            # Total
            total_surface = count_font.render(str(count), True, self.text_color)
            surface.blit(total_surface, (370, y_pos + 2))
            
    def _draw_game_rating(self, surface, summary):
        """Draw estimated game rating section"""
        # Section background  
        section_rect = pygame.Rect(20, 480, self.width - 40, 100)
        pygame.draw.rect(surface, self.card_color, section_rect, border_radius=15)
        
        # Section title
        title_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Game Rating", True, self.header_color)
        surface.blit(title_surface, (35, 495))
        
        # Rating cards
        card_width = (self.width - 80) // 2
        
        # White rating
        white_elo = summary.get('white_elo', 1200)
        white_rect = pygame.Rect(35, 525, card_width - 10, 40)
        pygame.draw.rect(surface, self.panel_color, white_rect, border_radius=10)
        
        rating_font = pygame.font.SysFont('Segoe UI', 20, bold=True)
        white_rating_surface = rating_font.render(str(white_elo), True, self.white_color)
        white_rating_rect = white_rating_surface.get_rect(center=(35 + (card_width - 10) // 2, 545))
        surface.blit(white_rating_surface, white_rating_rect)
        
        # Black rating
        black_elo = summary.get('black_elo', 1200)
        black_rect = pygame.Rect(35 + card_width, 525, card_width - 10, 40)
        pygame.draw.rect(surface, self.panel_color, black_rect, border_radius=10)
        
        black_rating_surface = rating_font.render(str(black_elo), True, self.black_color)
        black_rating_rect = black_rating_surface.get_rect(center=(35 + card_width + (card_width - 10) // 2, 545))
        surface.blit(black_rating_surface, black_rating_rect)
        
    def _draw_arc(self, surface, center, radius, start_angle, end_angle, color, width):
        """Draw an arc for accuracy circles"""
        steps = max(10, int(abs(end_angle - start_angle) * 20))
        angle_step = (end_angle - start_angle) / steps
        
        points = []
        for i in range(steps + 1):
            angle = start_angle + i * angle_step - math.pi / 2  # Start from top
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
            
        if len(points) > 1:
            for i in range(len(points) - 1):
                pygame.draw.line(surface, color, points[i], points[i + 1], width)
                
    def handle_input(self, event):
        """Handle input events"""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if click is within widget bounds
            widget_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if widget_rect.collidepoint(event.pos):
                # Check close button
                close_rect = pygame.Rect(self.x + self.width - 40, self.y + 20, 30, 30)
                if close_rect.collidepoint(event.pos):
                    self.hide()
                    return True
                return True
                
        return False