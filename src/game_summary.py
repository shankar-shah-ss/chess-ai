# game_summary.py - Enhanced Game Summary Widget
import pygame
import math

class GameSummaryWidget:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.visible = False
        self.x = 50
        self.y = 50
        self.width = 350
        self.height = 450
        
        # Modern color scheme
        self.bg_color = (30, 30, 40)
        self.panel_color = (40, 40, 55)
        self.text_color = (240, 240, 245)
        self.header_color = (220, 220, 230)
        self.border_color = (70, 70, 85)
        self.accent_color = (100, 150, 255)
        
        # Classification colors
        self.classification_colors = {
            'BRILLIANT': (30, 175, 255),
            'GREAT': (120, 210, 150),
            'BEST': (130, 200, 140),
            'EXCELLENT': (150, 220, 160),
            'OKAY': (200, 200, 205),
            'MISS': (255, 193, 87),
            'INACCURACY': (255, 193, 87),
            'MISTAKE': (255, 162, 132),
            'BLUNDER': (255, 74, 74)
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
        """Render the game summary widget"""
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
            
        # Create surface with alpha
        widget_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Draw main panel with shadow
        shadow_offset = 4
        shadow_rect = pygame.Rect(shadow_offset, shadow_offset, self.width, self.height)
        pygame.draw.rect(widget_surface, (0, 0, 0, 100), shadow_rect, border_radius=15)
        
        main_rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(widget_surface, (*self.bg_color, self.fade_alpha), main_rect, border_radius=15)
        pygame.draw.rect(widget_surface, (*self.border_color, self.fade_alpha), main_rect, 3, border_radius=15)
        
        # Get game summary
        summary = self.analyzer.get_game_summary()
        if not summary:
            return
            
        # Draw header
        self._draw_header(widget_surface, summary)
        
        # Draw accuracy section
        self._draw_accuracy_section(widget_surface, summary)
        
        # Draw move breakdown
        self._draw_move_breakdown(widget_surface, summary)
        
        # Draw classification chart
        self._draw_classification_chart(widget_surface, summary)
        
        # Apply alpha and blit to main surface
        widget_surface_alpha = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        widget_surface_alpha.set_alpha(self.fade_alpha)
        widget_surface_alpha.blit(widget_surface, (0, 0))
        surface.blit(widget_surface_alpha, (self.x, self.y))
        
    def _draw_header(self, surface, summary):
        """Draw the widget header"""
        # Title
        title_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
        title_text = "Game Summary"
        title_surface = title_font.render(title_text, True, self.header_color)
        surface.blit(title_surface, (20, 20))
        
        # Close button
        close_rect = pygame.Rect(self.width - 35, 15, 20, 20)
        pygame.draw.rect(surface, (200, 100, 100), close_rect, border_radius=10)
        close_font = pygame.font.SysFont('Arial', 14, bold=True)
        close_surface = close_font.render('×', True, (255, 255, 255))
        close_text_rect = close_surface.get_rect(center=close_rect.center)
        surface.blit(close_surface, close_text_rect)
        
        # Total moves
        moves_font = pygame.font.SysFont('Segoe UI', 14)
        moves_text = f"Total Moves: {summary['total_moves']}"
        moves_surface = moves_font.render(moves_text, True, self.text_color)
        surface.blit(moves_surface, (20, 55))
        
    def _draw_accuracy_section(self, surface, summary):
        """Draw the accuracy section with visual indicator"""
        accuracy = summary['accuracy']
        
        # Section header
        section_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        section_surface = section_font.render('Accuracy', True, self.header_color)
        surface.blit(section_surface, (20, 90))
        
        # Accuracy circle
        center_x, center_y = 85, 140
        radius = 35
        
        # Background circle
        pygame.draw.circle(surface, (60, 60, 75), (center_x, center_y), radius, 4)
        
        # Accuracy arc
        if accuracy > 0:
            # Calculate arc angle (0 to 2π)
            arc_angle = (accuracy / 100) * 2 * math.pi
            
            # Draw accuracy arc
            accuracy_color = self._get_accuracy_color(accuracy)
            self._draw_arc(surface, (center_x, center_y), radius - 2, 0, arc_angle, accuracy_color, 6)
        
        # Accuracy percentage text
        accuracy_font = pygame.font.SysFont('Segoe UI', 20, bold=True)
        accuracy_text = f"{accuracy:.1f}%"
        accuracy_surface = accuracy_font.render(accuracy_text, True, self.text_color)
        accuracy_rect = accuracy_surface.get_rect(center=(center_x, center_y))
        surface.blit(accuracy_surface, accuracy_rect)
        
        # Accuracy description
        desc_font = pygame.font.SysFont('Segoe UI', 12)
        desc_text = self._get_accuracy_description(accuracy)
        desc_surface = desc_font.render(desc_text, True, self._get_accuracy_color(accuracy))
        surface.blit(desc_surface, (140, 125))
        
    def _draw_move_breakdown(self, surface, summary):
        """Draw move classification breakdown"""
        classifications = summary['classifications']
        
        # Section header
        section_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        section_surface = section_font.render('Move Breakdown', True, self.header_color)
        surface.blit(section_surface, (20, 190))
        
        # Key moves stats
        y_offset = 220
        key_stats = [
            ('Brilliant', classifications.get('BRILLIANT', 0), self.classification_colors['BRILLIANT']),
            ('Great', classifications.get('GREAT', 0), self.classification_colors['GREAT']),
            ('Mistakes', classifications.get('MISTAKE', 0), self.classification_colors['MISTAKE']),
            ('Blunders', classifications.get('BLUNDER', 0), self.classification_colors['BLUNDER'])
        ]
        
        for i, (label, count, color) in enumerate(key_stats):
            x_offset = 20 + (i % 2) * 160
            y_pos = y_offset + (i // 2) * 30
            
            # Color indicator
            color_rect = pygame.Rect(x_offset, y_pos + 5, 12, 12)
            pygame.draw.rect(surface, color, color_rect, border_radius=2)
            
            # Label and count
            stat_font = pygame.font.SysFont('Segoe UI', 13)
            stat_text = f"{label}: {count}"
            stat_surface = stat_font.render(stat_text, True, self.text_color)
            surface.blit(stat_surface, (x_offset + 20, y_pos))
            
    def _draw_classification_chart(self, surface, summary):
        """Draw a simple bar chart of move classifications"""
        classifications = summary['classifications']
        
        # Section header
        section_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        section_surface = section_font.render('Classification Chart', True, self.header_color)
        surface.blit(section_surface, (20, 290))
        
        # Chart area
        chart_x, chart_y = 20, 320
        chart_width, chart_height = 310, 100
        
        # Background
        chart_rect = pygame.Rect(chart_x, chart_y, chart_width, chart_height)
        pygame.draw.rect(surface, self.panel_color, chart_rect, border_radius=8)
        
        # Get top classifications to display
        sorted_classifications = sorted(classifications.items(), key=lambda x: x[1], reverse=True)
        top_classifications = sorted_classifications[:6]  # Show top 6
        
        if not top_classifications:
            return
            
        max_count = max(count for _, count in top_classifications) if top_classifications else 1
        bar_width = chart_width // len(top_classifications)
        
        for i, (classification, count) in enumerate(top_classifications):
            if count == 0:
                continue
                
            # Calculate bar height
            bar_height = int((count / max_count) * (chart_height - 20))
            
            # Bar position
            bar_x = chart_x + i * bar_width + 5
            bar_y = chart_y + chart_height - bar_height - 10
            
            # Draw bar
            color = self.classification_colors.get(classification, self.text_color)
            bar_rect = pygame.Rect(bar_x, bar_y, bar_width - 10, bar_height)
            pygame.draw.rect(surface, color, bar_rect, border_radius=3)
            
            # Draw count on top of bar
            count_font = pygame.font.SysFont('Segoe UI', 10, bold=True)
            count_surface = count_font.render(str(count), True, self.text_color)
            count_rect = count_surface.get_rect(center=(bar_x + (bar_width - 10) // 2, bar_y - 8))
            surface.blit(count_surface, count_rect)
            
            # Draw classification label
            label_font = pygame.font.SysFont('Segoe UI', 9)
            label_text = classification[:4]  # Truncate long names
            label_surface = label_font.render(label_text, True, self.text_color)
            label_rect = label_surface.get_rect(center=(bar_x + (bar_width - 10) // 2, chart_y + chart_height + 5))
            surface.blit(label_surface, label_rect)
            
    def _draw_arc(self, surface, center, radius, start_angle, end_angle, color, width):
        """Draw an arc (used for accuracy circle)"""
        # Simple arc drawing using lines
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
                
    def _get_accuracy_color(self, accuracy):
        """Get color based on accuracy percentage"""
        if accuracy >= 90:
            return (100, 255, 150)  # Excellent - Green
        elif accuracy >= 80:
            return (150, 255, 100)  # Good - Light green
        elif accuracy >= 70:
            return (255, 255, 100)  # OK - Yellow
        elif accuracy >= 60:
            return (255, 200, 100)  # Poor - Orange
        else:
            return (255, 150, 150)  # Bad - Red
            
    def _get_accuracy_description(self, accuracy):
        """Get accuracy description text"""
        if accuracy >= 90:
            return "Excellent!"
        elif accuracy >= 80:
            return "Very Good"
        elif accuracy >= 70:
            return "Good"
        elif accuracy >= 60:
            return "Fair"
        else:
            return "Needs Work"
            
    def handle_input(self, event):
        """Handle input events for the widget"""
        if not self.visible:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if click is within widget bounds
            widget_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if widget_rect.collidepoint(event.pos):
                # Check if close button was clicked
                close_rect = pygame.Rect(self.x + self.width - 35, self.y + 15, 20, 20)
                if close_rect.collidepoint(event.pos):
                    self.hide()
                    return True
                # Widget was clicked, don't propagate
                return True
                
        return False