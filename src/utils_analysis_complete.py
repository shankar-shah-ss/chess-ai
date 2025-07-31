# analysis_utils.py - Utility functions for chess analysis
import pygame
import math
from typing import Tuple, List, Dict, Optional

def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Interpolate between two colors"""
    factor = max(0, min(1, factor))
    return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))

def draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect, color1: Tuple[int, int, int], 
                      color2: Tuple[int, int, int], vertical: bool = True):
    """Draw a gradient rectangle"""
    if vertical:
        for y in range(rect.height):
            factor = y / rect.height
            color = interpolate_color(color1, color2, factor)
            pygame.draw.line(surface, color, (rect.x, rect.y + y), (rect.right, rect.y + y))
    else:
        for x in range(rect.width):
            factor = x / rect.width
            color = interpolate_color(color1, color2, factor)
            pygame.draw.line(surface, color, (rect.x + x, rect.y), (rect.x + x, rect.bottom))

def draw_rounded_rect(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], 
                     radius: int, width: int = 0):
    """Draw a rounded rectangle (fallback for older pygame versions)"""
    try:
        pygame.draw.rect(surface, color, rect, width, border_radius=radius)
    except TypeError:
        # Fallback for older pygame versions
        pygame.draw.rect(surface, color, rect, width)

def draw_shadow(surface: pygame.Surface, rect: pygame.Rect, offset: int = 4, 
               shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 60)):
    """Draw a drop shadow for a rectangle"""
    shadow_surface = pygame.Surface((rect.width + offset, rect.height + offset), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(0, 0, rect.width + offset, rect.height + offset)
    pygame.draw.rect(shadow_surface, shadow_color, shadow_rect, border_radius=8)
    surface.blit(shadow_surface, (rect.x + offset//2, rect.y + offset//2))

def format_evaluation(evaluation: Dict) -> str:
    """Format evaluation for display"""
    if not evaluation or 'value' not in evaluation:
        return "N/A"
        
    if evaluation['type'] == 'cp':
        score = evaluation['value'] / 100.0
        return f"{score:+.2f}"
    else:  # mate
        moves = abs(evaluation['value'])
        side = 'W' if evaluation['value'] > 0 else 'B'
        return f"M{moves} {side}"

def get_evaluation_color(evaluation: Dict, colors: Dict) -> Tuple[int, int, int]:
    """Get color based on evaluation"""
    if not evaluation or 'value' not in evaluation:
        return colors['text_secondary']
        
    if evaluation['type'] == 'mate':
        return colors['success'] if evaluation['value'] > 0 else colors['error']
    
    score = evaluation['value'] / 100.0
    if score > 0.5:
        return colors['success']
    elif score < -0.5:
        return colors['error']
    else:
        return colors['text_secondary']

def classification_to_color(classification: str) -> Tuple[int, int, int]:
    """Get color for move classification"""
    color_map = {
        'BRILLIANT': (138, 43, 226),     # Purple
        'GREAT': (34, 139, 34),          # Forest green
        'BEST': (52, 168, 83),           # Success green  
        'EXCELLENT': (72, 201, 176),     # Teal
        'OKAY': (108, 117, 125),         # Gray
        'MISS': (255, 193, 7),           # Warning yellow
        'INACCURACY': (255, 158, 56),    # Orange
        'MISTAKE': (255, 107, 107),      # Light red
        'BLUNDER': (220, 53, 69),        # Error red
    }
    return color_map.get(classification, (108, 117, 125))

def draw_classification_badge(surface, x, y, classification, color):
    """Draw a classification badge"""
    # Badge dimensions
    badge_width = 80
    badge_height = 24
    
    # Badge background
    badge_surface = pygame.Surface((badge_width, badge_height), pygame.SRCALPHA)
    
    # Background with transparency
    pygame.draw.rect(badge_surface, (*color, 40), pygame.Rect(0, 0, badge_width, badge_height), border_radius=12)
    pygame.draw.rect(badge_surface, color, pygame.Rect(0, 0, badge_width, badge_height), 1, border_radius=12)
    
    # Text
    font = pygame.font.SysFont('Segoe UI', 12, bold=True)
    text_surface = font.render(classification.title(), True, color)
    text_rect = text_surface.get_rect(center=(badge_width//2, badge_height//2))
    badge_surface.blit(text_surface, text_rect)
    
    surface.blit(badge_surface, (x, y))

def draw_progress_bar(surface, x, y, width, height, progress):
    """Draw a progress bar"""
    # Background
    bg_color = (60, 60, 60)
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, bg_color, rect, border_radius=height//2)
    
    # Fill
    if progress > 0:
        fill_color = (129, 182, 76)
        fill_width = int(width * (progress / 100))
        fill_rect = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=height//2)

def draw_evaluation_bar(surface: pygame.Surface, rect: pygame.Rect, evaluation: Dict,
                       white_color: Tuple[int, int, int] = (240, 240, 240),
                       black_color: Tuple[int, int, int] = (80, 80, 80)):
    """Draw evaluation bar showing position assessment"""
    # Background
    pygame.draw.rect(surface, black_color, rect, border_radius=6)
    
    if evaluation and 'value' in evaluation:
        if evaluation['type'] == 'cp':
            # Normalize centipawn evaluation to 0-1 range
            eval_cp = max(-800, min(800, evaluation['value']))
            white_advantage = (eval_cp + 800) / 1600
        else:  # mate
            white_advantage = 1.0 if evaluation['value'] > 0 else 0.0
            
        # Draw white portion
        white_height = int(rect.height * white_advantage)
        if white_height > 0:
            white_rect = pygame.Rect(rect.x, rect.bottom - white_height, rect.width, white_height)
            pygame.draw.rect(surface, white_color, white_rect, border_radius=6)
    
    # Center line
    center_y = rect.y + rect.height // 2
    pygame.draw.line(surface, (150, 150, 150), (rect.x, center_y), (rect.right, center_y), 1)

def create_piece_texture(piece_name: str, color: str, size: int = 60) -> pygame.Surface:
    """Create a simple piece texture using shapes"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    
    # Base colors
    piece_color = (245, 245, 245) if color == 'white' else (50, 50, 50)
    outline_color = (100, 100, 100)
    
    # Draw based on piece type
    if piece_name.lower() == 'pawn':
        # Simple pawn shape
        pygame.draw.circle(surface, piece_color, (center, center - 5), size//6)
        pygame.draw.rect(surface, piece_color, (center - size//8, center - 2, size//4, size//3))
        pygame.draw.circle(surface, outline_color, (center, center - 5), size//6, 2)
    
    elif piece_name.lower() == 'rook':
        # Castle-like shape
        rect_height = size//2
        pygame.draw.rect(surface, piece_color, (center - size//4, center - rect_height//2, size//2, rect_height))
        # Crenellations
        for i in range(3):
            x = center - size//6 + i * size//6
            pygame.draw.rect(surface, piece_color, (x, center - rect_height//2 - 4, 4, 8))
        pygame.draw.rect(surface, outline_color, (center - size//4, center - rect_height//2, size//2, rect_height), 2)
    
    elif piece_name.lower() == 'knight':
        # Horse-like shape
        points = [
            (center - size//6, center + size//4),
            (center - size//4, center),
            (center - size//8, center - size//4),
            (center + size//8, center - size//6),
            (center + size//4, center + size//6),
            (center + size//6, center + size//4)
        ]
        pygame.draw.polygon(surface, piece_color, points)
        pygame.draw.polygon(surface, outline_color, points, 2)
    
    elif piece_name.lower() == 'bishop':
        # Bishop mitre shape
        points = [
            (center, center - size//3),
            (center - size//6, center),
            (center - size//8, center + size//4),
            (center + size//8, center + size//4),
            (center + size//6, center)
        ]
        pygame.draw.polygon(surface, piece_color, points)
        pygame.draw.circle(surface, piece_color, (center, center - size//4), size//12)
        pygame.draw.polygon(surface, outline_color, points, 2)
    
    elif piece_name.lower() == 'queen':
        # Crown-like shape
        base_rect = pygame.Rect(center - size//4, center - size//8, size//2, size//3)
        pygame.draw.rect(surface, piece_color, base_rect)
        # Crown points
        for i in range(5):
            x = center - size//4 + i * size//8
            height = size//6 if i % 2 == 0 else size//8
            pygame.draw.rect(surface, piece_color, (x, center - size//8 - height, size//16, height))
        pygame.draw.rect(surface, outline_color, base_rect, 2)
    
    elif piece_name.lower() == 'king':
        # King with cross
        base_rect = pygame.Rect(center - size//4, center - size//8, size//2, size//3)
        pygame.draw.rect(surface, piece_color, base_rect)
        # Cross
        pygame.draw.line(surface, piece_color, (center, center - size//3), (center, center - size//6), 3)
        pygame.draw.line(surface, piece_color, (center - size//12, center - size//4), (center + size//12, center - size//4), 3)
        pygame.draw.rect(surface, outline_color, base_rect, 2)
    
    return surface

def animate_value(current: float, target: float, speed: float = 0.1) -> float:
    """Animate a value towards a target"""
    diff = target - current
    return current + diff * speed

def ease_in_out_cubic(t: float) -> float:
    """Cubic easing function"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def draw_arrow(surface: pygame.Surface, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
               color: Tuple[int, int, int], width: int = 3, arrow_size: int = 10):
    """Draw an arrow from start to end position"""
    # Main line
    pygame.draw.line(surface, color, start_pos, end_pos, width)
    
    # Arrow head
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    length = math.sqrt(dx*dx + dy*dy)
    
    if length > 0:
        # Normalize direction
        dx /= length
        dy /= length
        
        # Arrow head points
        arrow_points = [
            end_pos,
            (end_pos[0] - arrow_size * dx + arrow_size * dy * 0.5,
             end_pos[1] - arrow_size * dy - arrow_size * dx * 0.5),
            (end_pos[0] - arrow_size * dx - arrow_size * dy * 0.5,
             end_pos[1] - arrow_size * dy + arrow_size * dx * 0.5)
        ]
        pygame.draw.polygon(surface, color, arrow_points)

def draw_circle_progress(surface: pygame.Surface, center: Tuple[int, int], radius: int, 
                        progress: float, color: Tuple[int, int, int], width: int = 4):
    """Draw a circular progress indicator"""
    # Background circle
    pygame.draw.circle(surface, (60, 60, 60), center, radius, width)
    
    # Progress arc
    if progress > 0:
        start_angle = -math.pi / 2  # Start at top
        end_angle = start_angle + (2 * math.pi * progress)
        
        # Draw arc using lines (pygame.draw.arc doesn't support thickness well)
        points = []
        steps = max(3, int(360 * progress))
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                pygame.draw.line(surface, color, points[i], points[i + 1], width)

def format_time(seconds: float) -> str:
    """Format time duration for display"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}:{minutes:02d}:00"

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(max_val, value))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b"""
    return a + (b - a) * clamp(t, 0.0, 1.0)

def get_accuracy_rating(accuracy: float) -> str:
    """Get accuracy rating text"""
    if accuracy >= 95:
        return "Excellent"
    elif accuracy >= 90:
        return "Great"
    elif accuracy >= 85:
        return "Good"
    elif accuracy >= 80:
        return "Fair"
    elif accuracy >= 70:
        return "Poor"
    else:
        return "Very Poor"

def draw_text_with_outline(surface: pygame.Surface, text: str, font: pygame.font.Font,
                          pos: Tuple[int, int], text_color: Tuple[int, int, int],
                          outline_color: Tuple[int, int, int] = (0, 0, 0), outline_width: int = 1):
    """Draw text with outline for better visibility"""
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                outline_surface = font.render(text, True, outline_color)
                surface.blit(outline_surface, (pos[0] + dx, pos[1] + dy))
    
    # Draw main text
    text_surface = font.render(text, True, text_color)
    surface.blit(text_surface, pos)

def calculate_text_size(text: str, font: pygame.font.Font) -> Tuple[int, int]:
    """Calculate the size of rendered text"""
    return font.size(text)

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width"""
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0
    
    for word in words:
        word_width = font.size(word + ' ')[0]
        
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
            else:
                # Word is too long for the line
                lines.append(word)
                current_line = []
                current_width = 0
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def create_tooltip_surface(text: str, font: pygame.font.Font, 
                          bg_color: Tuple[int, int, int] = (50, 50, 50),
                          text_color: Tuple[int, int, int] = (255, 255, 255),
                          padding: int = 8) -> pygame.Surface:
    """Create a tooltip surface"""
    text_surface = font.render(text, True, text_color)
    tooltip_width = text_surface.get_width() + padding * 2
    tooltip_height = text_surface.get_height() + padding * 2
    
    tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
    pygame.draw.rect(tooltip_surface, bg_color, tooltip_surface.get_rect(), border_radius=6)
    pygame.draw.rect(tooltip_surface, (100, 100, 100), tooltip_surface.get_rect(), 1, border_radius=6)
    
    tooltip_surface.blit(text_surface, (padding, padding))
    return tooltip_surface

def point_in_rect(point: Tuple[int, int], rect: pygame.Rect) -> bool:
    """Check if a point is inside a rectangle"""
    return rect.collidepoint(point)

def get_move_quality_description(classification: str) -> str:
    """Get description for move quality"""
    descriptions = {
        'BRILLIANT': 'An outstanding move that demonstrates deep calculation',
        'GREAT': 'An excellent move in a critical position',
        'BEST': 'The optimal move in the position',
        'EXCELLENT': 'A very good move, close to optimal',
        'OKAY': 'A reasonable move with minor inaccuracies',
        'MISS': 'A missed opportunity to improve the position',
        'INACCURACY': 'A slightly inaccurate move that loses some advantage',
        'MISTAKE': 'A poor move that loses significant advantage',
        'BLUNDER': 'A serious error that dramatically worsens the position'
    }
    return descriptions.get(classification, 'Unknown move quality')

def calculate_performance_score(accuracy: float, mistakes: int, blunders: int, total_moves: int) -> int:
    """Calculate overall performance score (0-100)"""
    if total_moves == 0:
        return 0
    
    # Base score from accuracy
    base_score = accuracy
    
    # Penalty for mistakes and blunders
    mistake_penalty = (mistakes / total_moves) * 20
    blunder_penalty = (blunders / total_moves) * 40
    
    # Calculate final score
    performance_score = base_score - mistake_penalty - blunder_penalty
    return max(0, min(100, int(performance_score)))
