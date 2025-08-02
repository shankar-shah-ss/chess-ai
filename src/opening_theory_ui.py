"""
Opening Theory UI Component
Provides visual interface for opening theory exploration and analysis
"""

import pygame
import chess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from opening_theory_system import opening_theory_system, OpeningMove, OpeningPhase
import textwrap

@dataclass
class UIColors:
    """Color scheme for the opening theory UI"""
    background = (240, 240, 240)
    panel_bg = (255, 255, 255)
    border = (200, 200, 200)
    text_primary = (50, 50, 50)
    text_secondary = (100, 100, 100)
    accent = (70, 130, 180)
    success = (34, 139, 34)
    warning = (255, 140, 0)
    error = (220, 20, 60)
    hover = (230, 230, 250)
    
    # Opening phase colors
    opening_color = (34, 139, 34)
    middlegame_color = (255, 140, 0)
    endgame_color = (220, 20, 60)

class OpeningTheoryUI:
    """
    Opening Theory User Interface
    Displays opening information, move suggestions, and exploration tools
    """
    
    def __init__(self, width: int = 400, height: int = 600):
        self.width = width
        self.height = height
        self.colors = UIColors()
        
        # UI state
        self.current_fen = None
        self.current_opening = None
        self.expanded_sections = {
            "info": True,
            "moves": True,
            "plans": False,
            "games": False
        }
        
        # Fonts
        self.font_title = pygame.font.Font(None, 24)
        self.font_subtitle = pygame.font.Font(None, 20)
        self.font_body = pygame.font.Font(None, 18)
        self.font_small = pygame.font.Font(None, 16)
        
        # UI elements
        self.scroll_offset = 0
        self.max_scroll = 0
        self.hover_element = None
        
        # Panel dimensions
        self.panel_rect = pygame.Rect(0, 0, width, height)
        self.content_rect = pygame.Rect(10, 10, width - 20, height - 20)
        
        print("🎨 Opening Theory UI initialized")
    
    def update_position(self, fen: str):
        """Update the UI with a new position"""
        if fen != self.current_fen:
            self.current_fen = fen
            self.current_opening = opening_theory_system.detect_opening(fen)
            self.scroll_offset = 0  # Reset scroll when position changes
    
    def render(self, screen: pygame.Surface, x: int, y: int):
        """Render the opening theory panel"""
        # Create panel surface
        panel_surface = pygame.Surface((self.width, self.height))
        panel_surface.fill(self.colors.panel_bg)
        
        # Draw border
        pygame.draw.rect(panel_surface, self.colors.border, 
                        (0, 0, self.width, self.height), 2)
        
        if not self.current_opening:
            self._render_no_data(panel_surface)
        else:
            self._render_opening_info(panel_surface)
        
        # Blit to main screen
        screen.blit(panel_surface, (x, y))
    
    def _render_no_data(self, surface: pygame.Surface):
        """Render when no opening data is available"""
        text = "No opening data available"
        text_surface = self.font_body.render(text, True, self.colors.text_secondary)
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
        surface.blit(text_surface, text_rect)
    
    def _render_opening_info(self, surface: pygame.Surface):
        """Render comprehensive opening information"""
        y_offset = 10 - self.scroll_offset
        
        # Title section
        y_offset = self._render_title_section(surface, y_offset)
        
        # Basic info section
        if self.expanded_sections["info"]:
            y_offset = self._render_info_section(surface, y_offset)
        
        # Next moves section
        if self.expanded_sections["moves"]:
            y_offset = self._render_moves_section(surface, y_offset)
        
        # Plans and ideas section
        if self.expanded_sections["plans"]:
            y_offset = self._render_plans_section(surface, y_offset)
        
        # Famous games section
        if self.expanded_sections["games"]:
            y_offset = self._render_games_section(surface, y_offset)
        
        # Update max scroll
        self.max_scroll = max(0, y_offset - self.height + 20)
    
    def _render_title_section(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the title section with opening name and ECO"""
        opening = self.current_opening
        
        # Opening name
        name = opening["name"]
        if len(name) > 30:
            name = name[:27] + "..."
        
        name_surface = self.font_title.render(name, True, self.colors.text_primary)
        surface.blit(name_surface, (15, y_offset))
        y_offset += 30
        
        # ECO code and phase
        eco_text = f"ECO: {opening['eco']}" if opening['eco'] else "ECO: Unknown"
        phase_text = f"Phase: {opening['phase'].title()}"
        
        eco_surface = self.font_subtitle.render(eco_text, True, self.colors.accent)
        surface.blit(eco_surface, (15, y_offset))
        
        # Phase with color coding
        phase_color = self._get_phase_color(opening['phase'])
        phase_surface = self.font_subtitle.render(phase_text, True, phase_color)
        surface.blit(phase_surface, (150, y_offset))
        y_offset += 25
        
        # Move count
        move_text = f"Moves: {opening['move_number']}"
        theoretical_text = "Theoretical" if opening['is_theoretical'] else "Non-theoretical"
        
        move_surface = self.font_small.render(move_text, True, self.colors.text_secondary)
        surface.blit(move_surface, (15, y_offset))
        
        theoretical_color = self.colors.success if opening['is_theoretical'] else self.colors.warning
        theoretical_surface = self.font_small.render(theoretical_text, True, theoretical_color)
        surface.blit(theoretical_surface, (100, y_offset))
        y_offset += 25
        
        # Separator line
        pygame.draw.line(surface, self.colors.border, (10, y_offset), (self.width - 10, y_offset))
        y_offset += 15
        
        return y_offset
    
    def _render_info_section(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the basic information section"""
        opening = self.current_opening
        
        # Section header
        header_surface = self.font_subtitle.render("Information", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 25
        
        # Description
        if opening['description']:
            description_lines = textwrap.wrap(opening['description'], width=45)
            for line in description_lines:
                line_surface = self.font_body.render(line, True, self.colors.text_secondary)
                surface.blit(line_surface, (20, y_offset))
                y_offset += 20
        
        # Move sequence
        if opening['moves']:
            y_offset += 10
            moves_text = "Moves: " + " ".join(opening['moves'][:8])  # Show first 8 moves
            if len(opening['moves']) > 8:
                moves_text += "..."
            
            moves_lines = textwrap.wrap(moves_text, width=45)
            for line in moves_lines:
                line_surface = self.font_small.render(line, True, self.colors.accent)
                surface.blit(line_surface, (20, y_offset))
                y_offset += 18
        
        y_offset += 15
        return y_offset
    
    def _render_moves_section(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the next moves section"""
        # Section header
        header_surface = self.font_subtitle.render("Popular Continuations", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 25
        
        # Get next moves
        next_moves = opening_theory_system.get_next_moves(self.current_fen, limit=5)
        
        if not next_moves:
            no_moves_surface = self.font_body.render("No continuations available", True, self.colors.text_secondary)
            surface.blit(no_moves_surface, (20, y_offset))
            y_offset += 25
        else:
            for i, move in enumerate(next_moves):
                # Move notation
                move_text = f"{i+1}. {move.san}"
                move_surface = self.font_body.render(move_text, True, self.colors.text_primary)
                surface.blit(move_surface, (20, y_offset))
                
                # Statistics
                stats_text = f"W:{move.white_win_rate:.0f}% D:{move.draw_rate:.0f}% B:{move.black_win_rate:.0f}%"
                stats_surface = self.font_small.render(stats_text, True, self.colors.text_secondary)
                surface.blit(stats_surface, (120, y_offset))
                
                y_offset += 22
        
        y_offset += 15
        return y_offset
    
    def _render_plans_section(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the plans and ideas section"""
        opening = self.current_opening
        
        # Section header
        header_surface = self.font_subtitle.render("Key Ideas & Plans", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 25
        
        # Key ideas
        if opening['key_ideas']:
            ideas_header = self.font_body.render("Key Ideas:", True, self.colors.accent)
            surface.blit(ideas_header, (20, y_offset))
            y_offset += 20
            
            for idea in opening['key_ideas'][:3]:  # Show first 3 ideas
                idea_lines = textwrap.wrap(f"• {idea}", width=42)
                for line in idea_lines:
                    line_surface = self.font_small.render(line, True, self.colors.text_secondary)
                    surface.blit(line_surface, (25, y_offset))
                    y_offset += 18
        
        # Typical plans
        if opening['typical_plans']:
            y_offset += 10
            plans_header = self.font_body.render("Typical Plans:", True, self.colors.accent)
            surface.blit(plans_header, (20, y_offset))
            y_offset += 20
            
            for plan in opening['typical_plans'][:3]:  # Show first 3 plans
                plan_lines = textwrap.wrap(f"• {plan}", width=42)
                for line in plan_lines:
                    line_surface = self.font_small.render(line, True, self.colors.text_secondary)
                    surface.blit(line_surface, (25, y_offset))
                    y_offset += 18
        
        y_offset += 15
        return y_offset
    
    def _render_games_section(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the famous games section"""
        opening = self.current_opening
        
        # Section header
        header_surface = self.font_subtitle.render("Famous Games", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 25
        
        if not opening['famous_games']:
            no_games_surface = self.font_body.render("No famous games recorded", True, self.colors.text_secondary)
            surface.blit(no_games_surface, (20, y_offset))
            y_offset += 25
        else:
            for game in opening['famous_games'][:3]:  # Show first 3 games
                game_lines = textwrap.wrap(f"• {game}", width=42)
                for line in game_lines:
                    line_surface = self.font_small.render(line, True, self.colors.text_secondary)
                    surface.blit(line_surface, (25, y_offset))
                    y_offset += 18
        
        y_offset += 15
        return y_offset
    
    def _get_phase_color(self, phase: str) -> Tuple[int, int, int]:
        """Get color for game phase"""
        if phase == OpeningPhase.OPENING.value:
            return self.colors.opening_color
        elif phase == OpeningPhase.MIDDLEGAME.value:
            return self.colors.middlegame_color
        elif phase == OpeningPhase.ENDGAME.value:
            return self.colors.endgame_color
        else:
            return self.colors.text_secondary
    
    def handle_event(self, event: pygame.event.Event, panel_x: int, panel_y: int) -> bool:
        """Handle UI events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            relative_x = mouse_x - panel_x
            relative_y = mouse_y - panel_y
            
            # Check if click is within panel
            if 0 <= relative_x <= self.width and 0 <= relative_y <= self.height:
                return self._handle_click(relative_x, relative_y)
        
        elif event.type == pygame.MOUSEWHEEL:
            # Handle scrolling
            if self._is_mouse_over_panel(pygame.mouse.get_pos(), panel_x, panel_y):
                self.scroll_offset -= event.y * 20
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                return True
        
        return False
    
    def _handle_click(self, x: int, y: int) -> bool:
        """Handle mouse clicks within the panel"""
        # For now, just toggle sections (placeholder for future interactivity)
        # In a full implementation, you could add clickable elements
        return True
    
    def _is_mouse_over_panel(self, mouse_pos: Tuple[int, int], panel_x: int, panel_y: int) -> bool:
        """Check if mouse is over the panel"""
        mouse_x, mouse_y = mouse_pos
        return (panel_x <= mouse_x <= panel_x + self.width and 
                panel_y <= mouse_y <= panel_y + self.height)
    
    def toggle_section(self, section: str):
        """Toggle expansion of a section"""
        if section in self.expanded_sections:
            self.expanded_sections[section] = not self.expanded_sections[section]
    
    def reset_scroll(self):
        """Reset scroll position"""
        self.scroll_offset = 0
    
    def get_opening_info(self) -> Optional[Dict[str, Any]]:
        """Get current opening information"""
        return self.current_opening

# Create a compact version for integration with existing analysis system
class CompactOpeningDisplay:
    """
    Compact opening display for integration with existing analysis panel
    """
    
    def __init__(self):
        self.font = pygame.font.Font(None, 18)
        self.small_font = pygame.font.Font(None, 16)
        self.colors = UIColors()
        self.current_opening = None
    
    def update_position(self, fen: str):
        """Update with new position"""
        self.current_opening = opening_theory_system.detect_opening(fen)
    
    def render_compact(self, surface: pygame.Surface, x: int, y: int, width: int) -> int:
        """Render compact opening info, returns height used"""
        if not self.current_opening:
            return 0
        
        opening = self.current_opening
        y_offset = 0
        
        # Opening name and ECO
        name = opening["name"]
        if len(name) > 35:
            name = name[:32] + "..."
        
        eco_text = f" ({opening['eco']})" if opening['eco'] else ""
        full_text = name + eco_text
        
        name_surface = self.font.render(full_text, True, self.colors.text_primary)
        surface.blit(name_surface, (x, y + y_offset))
        y_offset += 22
        
        # Phase and move count
        phase_color = self._get_phase_color(opening['phase'])
        phase_text = f"Phase: {opening['phase'].title()} | Move: {opening['move_number']}"
        phase_surface = self.small_font.render(phase_text, True, phase_color)
        surface.blit(phase_surface, (x, y + y_offset))
        y_offset += 20
        
        # Description (truncated)
        if opening['description']:
            desc = opening['description']
            if len(desc) > 60:
                desc = desc[:57] + "..."
            desc_surface = self.small_font.render(desc, True, self.colors.text_secondary)
            surface.blit(desc_surface, (x, y + y_offset))
            y_offset += 18
        
        return y_offset + 10
    
    def _get_phase_color(self, phase: str) -> Tuple[int, int, int]:
        """Get color for game phase"""
        if phase == OpeningPhase.OPENING.value:
            return self.colors.opening_color
        elif phase == OpeningPhase.MIDDLEGAME.value:
            return self.colors.middlegame_color
        elif phase == OpeningPhase.ENDGAME.value:
            return self.colors.endgame_color
        else:
            return self.colors.text_secondary