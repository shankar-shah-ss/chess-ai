"""
Comprehensive Chess AI Control Panel
Integrates all game features including opening theory, analysis, and engine controls
"""

import pygame
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import chess

class PanelSection(Enum):
    """Control panel sections"""
    GAME_STATUS = "game_status"
    ENGINE_CONTROLS = "engine_controls"
    OPENING_THEORY = "opening_theory"
    ANALYSIS_TOOLS = "analysis_tools"
    GAME_CONTROLS = "game_controls"
    STATISTICS = "statistics"

@dataclass
class PanelColors:
    """Color scheme for the control panel"""
    background = (40, 46, 58, 240)
    border = (84, 92, 108, 255)
    section_bg = (50, 56, 68, 200)
    text_primary = (255, 255, 255)
    text_secondary = (181, 181, 181)
    text_accent = (129, 182, 76)
    button_bg = (70, 76, 88)
    button_hover = (90, 96, 108)
    button_active = (129, 182, 76)
    status_good = (34, 139, 34)
    status_warning = (255, 140, 0)
    status_error = (220, 20, 60)

class ChessControlPanel:
    """
    Comprehensive control panel for chess AI features
    """
    
    def __init__(self, width: int = 400, height: int = 800):
        self.width = width
        self.height = height
        self.colors = PanelColors()
        
        # Panel state
        self.expanded_sections = {
            PanelSection.GAME_STATUS: True,
            PanelSection.ENGINE_CONTROLS: True,
            PanelSection.OPENING_THEORY: True,
            PanelSection.ANALYSIS_TOOLS: False,
            PanelSection.GAME_CONTROLS: False,
            PanelSection.STATISTICS: False
        }
        
        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        
        # Interactive elements
        self.buttons = {}  # button_id -> rect
        self.toggles = {}  # toggle_id -> rect
        self.sliders = {}  # slider_id -> rect
        
        # Fonts (initialize lazily to avoid pygame init issues)
        self.font_title = None
        self.font_section = None
        self.font_body = None
        self.font_small = None
        
        # Panel positioning
        self.panel_rect = pygame.Rect(0, 0, width, height)
        self.content_rect = pygame.Rect(10, 10, width - 20, height - 20)
        
        print("🎛️ Chess Control Panel initialized")
    
    def _init_fonts(self):
        """Initialize fonts lazily"""
        if self.font_title is None:
            self.font_title = pygame.font.Font(None, 24)
            self.font_section = pygame.font.Font(None, 20)
            self.font_body = pygame.font.Font(None, 18)
            self.font_small = pygame.font.Font(None, 16)
    
    def render(self, screen: pygame.Surface, x: int, y: int, game, analysis_system, opening_explorer):
        """Render the complete control panel"""
        # Initialize fonts if needed
        self._init_fonts()
        
        # Create panel surface
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Background with shadow
        shadow_surface = pygame.Surface((self.width + 8, self.height + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 60), 
                        pygame.Rect(0, 0, self.width + 8, self.height + 8), border_radius=15)
        screen.blit(shadow_surface, (x + 4, y + 4))
        
        # Main panel background
        pygame.draw.rect(panel_surface, self.colors.background, 
                        pygame.Rect(0, 0, self.width, self.height), border_radius=15)
        pygame.draw.rect(panel_surface, self.colors.border, 
                        pygame.Rect(0, 0, self.width, self.height), 2, border_radius=15)
        
        # Clear interactive elements
        self.buttons.clear()
        self.toggles.clear()
        self.sliders.clear()
        
        # Panel title
        title_surface = self.font_title.render("Chess AI Control Center", True, self.colors.text_primary)
        panel_surface.blit(title_surface, (20, 15))
        
        # Render sections
        y_offset = 50 - self.scroll_offset
        
        # Game Status Section
        if self.expanded_sections[PanelSection.GAME_STATUS]:
            y_offset = self._render_game_status_section(panel_surface, y_offset, game)
        
        # Engine Controls Section
        if self.expanded_sections[PanelSection.ENGINE_CONTROLS]:
            y_offset = self._render_engine_controls_section(panel_surface, y_offset, game)
        
        # Opening Theory Section
        if self.expanded_sections[PanelSection.OPENING_THEORY]:
            y_offset = self._render_opening_theory_section(panel_surface, y_offset, game, analysis_system)
        
        # Analysis Tools Section
        if self.expanded_sections[PanelSection.ANALYSIS_TOOLS]:
            y_offset = self._render_analysis_tools_section(panel_surface, y_offset, analysis_system)
        
        # Game Controls Section
        if self.expanded_sections[PanelSection.GAME_CONTROLS]:
            y_offset = self._render_game_controls_section(panel_surface, y_offset, game)
        
        # Statistics Section
        if self.expanded_sections[PanelSection.STATISTICS]:
            y_offset = self._render_statistics_section(panel_surface, y_offset, game)
        
        # Section toggles (always visible)
        self._render_section_toggles(panel_surface)
        
        # Update max scroll
        self.max_scroll = max(0, y_offset - self.height + 100)
        
        # Blit to main screen
        screen.blit(panel_surface, (x, y))
    
    def _render_section_header(self, surface: pygame.Surface, y_offset: int, title: str, 
                              section: PanelSection) -> int:
        """Render a collapsible section header"""
        header_rect = pygame.Rect(15, y_offset, self.width - 30, 25)
        
        # Header background
        pygame.draw.rect(surface, self.colors.section_bg, header_rect, border_radius=5)
        
        # Expand/collapse indicator
        indicator = "▼" if self.expanded_sections[section] else "▶"
        indicator_surface = self.font_section.render(indicator, True, self.colors.text_accent)
        surface.blit(indicator_surface, (25, y_offset + 3))
        
        # Section title
        title_surface = self.font_section.render(title, True, self.colors.text_primary)
        surface.blit(title_surface, (45, y_offset + 3))
        
        # Store toggle area
        self.toggles[f"section_{section.value}"] = header_rect
        
        return y_offset + 35
    
    def _render_game_status_section(self, surface: pygame.Surface, y_offset: int, game) -> int:
        """Render game status information"""
        y_offset = self._render_section_header(surface, y_offset, "Game Status", PanelSection.GAME_STATUS)
        
        # Game mode
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine", 
            2: "Engine vs Engine"
        }.get(game.game_mode, "Unknown")
        
        self._render_info_line(surface, y_offset, "Mode:", mode_text)
        y_offset += 25
        
        # Current player
        current_player = game.next_player.title()
        player_color = self.colors.text_primary if not game.game_over else self.colors.text_secondary
        self._render_info_line(surface, y_offset, "Turn:", current_player, value_color=player_color)
        y_offset += 25
        
        # Game status
        if game.game_over:
            if hasattr(game, 'game_result'):
                status_text = f"Game Over: {game.game_result}"
                status_color = self.colors.status_warning
            else:
                status_text = "Game Over"
                status_color = self.colors.status_warning
        else:
            status_text = "In Progress"
            status_color = self.colors.status_good
        
        self._render_info_line(surface, y_offset, "Status:", status_text, value_color=status_color)
        y_offset += 25
        
        # Move count
        move_count = getattr(game, 'move_count', 0)
        self._render_info_line(surface, y_offset, "Moves:", str(move_count))
        y_offset += 35
        
        return y_offset
    
    def _render_engine_controls_section(self, surface: pygame.Surface, y_offset: int, game) -> int:
        """Render engine control options"""
        y_offset = self._render_section_header(surface, y_offset, "Engine Controls", PanelSection.ENGINE_CONTROLS)
        
        # Engine status
        white_engine = "ON" if getattr(game, 'engine_white', False) else "OFF"
        black_engine = "ON" if getattr(game, 'engine_black', False) else "OFF"
        
        white_color = self.colors.status_good if white_engine == "ON" else self.colors.text_secondary
        black_color = self.colors.status_good if black_engine == "ON" else self.colors.text_secondary
        
        self._render_info_line(surface, y_offset, "White Engine:", white_engine, value_color=white_color)
        y_offset += 25
        
        self._render_info_line(surface, y_offset, "Black Engine:", black_engine, value_color=black_color)
        y_offset += 25
        
        # Engine level and depth
        engine_level = getattr(game, 'level', 1)
        engine_depth = getattr(game, 'depth', 10)
        
        self._render_info_line(surface, y_offset, "Level:", f"{engine_level}/20")
        y_offset += 25
        
        self._render_info_line(surface, y_offset, "Depth:", f"{engine_depth}")
        y_offset += 25
        
        # Engine control buttons
        button_width = 80
        button_height = 25
        button_y = y_offset + 10
        
        # White engine toggle
        white_btn_rect = pygame.Rect(25, button_y, button_width, button_height)
        self._render_button(surface, white_btn_rect, "White", "toggle_white_engine")
        
        # Black engine toggle
        black_btn_rect = pygame.Rect(115, button_y, button_width, button_height)
        self._render_button(surface, black_btn_rect, "Black", "toggle_black_engine")
        
        # Level controls
        level_up_rect = pygame.Rect(205, button_y, 35, button_height)
        self._render_button(surface, level_up_rect, "+", "level_up")
        
        level_down_rect = pygame.Rect(245, button_y, 35, button_height)
        self._render_button(surface, level_down_rect, "-", "level_down")
        
        y_offset += 45
        
        return y_offset
    
    def _render_opening_theory_section(self, surface: pygame.Surface, y_offset: int, 
                                     game, analysis_system) -> int:
        """Render opening theory information"""
        y_offset = self._render_section_header(surface, y_offset, "Opening Theory", PanelSection.OPENING_THEORY)
        
        # Get current opening info
        try:
            current_fen = game.board.to_fen(game.next_player)
            opening_info = analysis_system.detect_opening(current_fen)
        except:
            opening_info = {"name": "Unknown", "eco": "", "phase": "opening"}
        
        # Opening name
        opening_name = opening_info.get("name", "Unknown")
        if len(opening_name) > 30:
            opening_name = opening_name[:27] + "..."
        
        self._render_info_line(surface, y_offset, "Opening:", opening_name)
        y_offset += 25
        
        # ECO code and phase
        eco_code = opening_info.get("eco", "")
        phase = opening_info.get("phase", "opening").title()
        
        if eco_code:
            self._render_info_line(surface, y_offset, "ECO:", eco_code)
            y_offset += 25
        
        # Phase with color coding
        phase_color = self._get_phase_color(phase.lower())
        self._render_info_line(surface, y_offset, "Phase:", phase, value_color=phase_color)
        y_offset += 25
        
        # Theoretical status
        is_theoretical = opening_info.get("is_theoretical", False)
        theory_text = "Yes" if is_theoretical else "No"
        theory_color = self.colors.status_good if is_theoretical else self.colors.status_warning
        self._render_info_line(surface, y_offset, "Theoretical:", theory_text, value_color=theory_color)
        y_offset += 25
        
        # Opening theory controls
        button_width = 100
        button_height = 25
        button_y = y_offset + 10
        
        # Opening explorer toggle
        explorer_btn_rect = pygame.Rect(25, button_y, button_width, button_height)
        self._render_button(surface, explorer_btn_rect, "Explorer", "toggle_explorer")
        
        # Analysis panel toggle
        analysis_btn_rect = pygame.Rect(135, button_y, button_width, button_height)
        self._render_button(surface, analysis_btn_rect, "Analysis", "toggle_analysis")
        
        y_offset += 45
        
        return y_offset
    
    def _render_analysis_tools_section(self, surface: pygame.Surface, y_offset: int, 
                                     analysis_system) -> int:
        """Render analysis tools and options"""
        y_offset = self._render_section_header(surface, y_offset, "Analysis Tools", PanelSection.ANALYSIS_TOOLS)
        
        # Analysis mode
        current_mode = getattr(analysis_system, 'current_mode', None)
        mode_text = current_mode.value.title() if current_mode else "None"
        self._render_info_line(surface, y_offset, "Mode:", mode_text)
        y_offset += 25
        
        # Engine analysis status
        engine_status = "Active" if getattr(analysis_system, 'analysis_engine', None) else "Inactive"
        engine_color = self.colors.status_good if engine_status == "Active" else self.colors.status_error
        self._render_info_line(surface, y_offset, "Engine:", engine_status, value_color=engine_color)
        y_offset += 25
        
        # Analysis controls
        button_width = 80
        button_height = 25
        button_y = y_offset + 10
        
        # Mode buttons
        modes = [("Review", "mode_review"), ("Engine", "mode_engine"), 
                ("Classify", "mode_classify"), ("Explore", "mode_explore")]
        
        for i, (label, button_id) in enumerate(modes):
            btn_x = 25 + (i % 2) * 90
            btn_y = button_y + (i // 2) * 30
            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
            self._render_button(surface, btn_rect, label, button_id)
        
        y_offset += 80
        
        return y_offset
    
    def _render_game_controls_section(self, surface: pygame.Surface, y_offset: int, game) -> int:
        """Render game control options"""
        y_offset = self._render_section_header(surface, y_offset, "Game Controls", PanelSection.GAME_CONTROLS)
        
        # Game control buttons
        button_width = 80
        button_height = 25
        button_y = y_offset + 10
        
        controls = [
            ("New Game", "new_game"),
            ("Reset", "reset_game"),
            ("Save PGN", "save_pgn"),
            ("Load PGN", "load_pgn"),
            ("Undo", "undo_move"),
            ("Theme", "change_theme")
        ]
        
        for i, (label, button_id) in enumerate(controls):
            btn_x = 25 + (i % 2) * 90
            btn_y = button_y + (i // 2) * 30
            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)
            self._render_button(surface, btn_rect, label, button_id)
        
        y_offset += 100
        
        return y_offset
    
    def _render_statistics_section(self, surface: pygame.Surface, y_offset: int, game) -> int:
        """Render game statistics"""
        y_offset = self._render_section_header(surface, y_offset, "Statistics", PanelSection.STATISTICS)
        
        # Game statistics
        total_games = getattr(game, 'total_games', 0)
        wins = getattr(game, 'wins', 0)
        draws = getattr(game, 'draws', 0)
        losses = getattr(game, 'losses', 0)
        
        self._render_info_line(surface, y_offset, "Total Games:", str(total_games))
        y_offset += 25
        
        self._render_info_line(surface, y_offset, "Wins:", str(wins), value_color=self.colors.status_good)
        y_offset += 25
        
        self._render_info_line(surface, y_offset, "Draws:", str(draws), value_color=self.colors.text_accent)
        y_offset += 25
        
        self._render_info_line(surface, y_offset, "Losses:", str(losses), value_color=self.colors.status_error)
        y_offset += 35
        
        return y_offset
    
    def _render_section_toggles(self, surface: pygame.Surface):
        """Render section toggle buttons at the bottom"""
        toggle_y = self.height - 40
        toggle_width = 50
        toggle_height = 20
        
        sections = [
            ("Game", PanelSection.GAME_STATUS),
            ("Engine", PanelSection.ENGINE_CONTROLS),
            ("Opening", PanelSection.OPENING_THEORY),
            ("Analysis", PanelSection.ANALYSIS_TOOLS),
            ("Controls", PanelSection.GAME_CONTROLS),
            ("Stats", PanelSection.STATISTICS)
        ]
        
        for i, (label, section) in enumerate(sections):
            toggle_x = 15 + i * 60
            toggle_rect = pygame.Rect(toggle_x, toggle_y, toggle_width, toggle_height)
            
            # Button color based on expansion state
            bg_color = self.colors.button_active if self.expanded_sections[section] else self.colors.button_bg
            
            pygame.draw.rect(surface, bg_color, toggle_rect, border_radius=3)
            pygame.draw.rect(surface, self.colors.border, toggle_rect, 1, border_radius=3)
            
            # Button text
            text_surface = self.font_small.render(label, True, self.colors.text_primary)
            text_rect = text_surface.get_rect(center=toggle_rect.center)
            surface.blit(text_surface, text_rect)
            
            # Store toggle
            self.toggles[f"section_{section.value}"] = toggle_rect
    
    def _render_info_line(self, surface: pygame.Surface, y: int, label: str, value: str, 
                         value_color=None):
        """Render an information line with label and value"""
        if value_color is None:
            value_color = self.colors.text_primary
        
        label_surface = self.font_body.render(label, True, self.colors.text_secondary)
        surface.blit(label_surface, (25, y))
        
        value_surface = self.font_body.render(value, True, value_color)
        surface.blit(value_surface, (120, y))
    
    def _render_button(self, surface: pygame.Surface, rect: pygame.Rect, text: str, button_id: str):
        """Render a clickable button"""
        # Button background
        pygame.draw.rect(surface, self.colors.button_bg, rect, border_radius=3)
        pygame.draw.rect(surface, self.colors.border, rect, 1, border_radius=3)
        
        # Button text
        text_surface = self.font_small.render(text, True, self.colors.text_primary)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
        
        # Store button
        self.buttons[button_id] = rect
    
    def _get_phase_color(self, phase: str) -> Tuple[int, int, int]:
        """Get color for game phase"""
        if phase == "opening":
            return self.colors.status_good
        elif phase == "middlegame":
            return self.colors.status_warning
        elif phase == "endgame":
            return self.colors.status_error
        else:
            return self.colors.text_secondary
    
    def handle_click(self, x: int, y: int, game, analysis_system, main_app) -> bool:
        """Handle mouse clicks on the control panel"""
        # Check section toggles
        for toggle_id, rect in self.toggles.items():
            if rect.collidepoint(x, y):
                if toggle_id.startswith("section_"):
                    section_name = toggle_id.replace("section_", "")
                    section = PanelSection(section_name)
                    self.expanded_sections[section] = not self.expanded_sections[section]
                    return True
        
        # Check buttons
        for button_id, rect in self.buttons.items():
            if rect.collidepoint(x, y):
                return self._handle_button_click(button_id, game, analysis_system, main_app)
        
        return False
    
    def _handle_button_click(self, button_id: str, game, analysis_system, main_app) -> bool:
        """Handle button click actions"""
        try:
            # Engine controls
            if button_id == "toggle_white_engine":
                game.toggle_engine('white')
                return True
            elif button_id == "toggle_black_engine":
                game.toggle_engine('black')
                return True
            elif button_id == "level_up":
                game.increase_level()
                return True
            elif button_id == "level_down":
                game.decrease_level()
                return True
            
            # Opening theory controls
            elif button_id == "toggle_explorer":
                main_app.show_opening_explorer = not main_app.show_opening_explorer
                return True
            elif button_id == "toggle_analysis":
                main_app.show_analysis = not main_app.show_analysis
                return True
            
            # Analysis mode controls
            elif button_id == "mode_review":
                from chess_analysis_system import AnalysisMode
                analysis_system.set_mode(AnalysisMode.REVIEW)
                return True
            elif button_id == "mode_engine":
                from chess_analysis_system import AnalysisMode
                analysis_system.set_mode(AnalysisMode.ENGINE)
                return True
            elif button_id == "mode_classify":
                from chess_analysis_system import AnalysisMode
                analysis_system.set_mode(AnalysisMode.CLASSIFICATION)
                return True
            elif button_id == "mode_explore":
                from chess_analysis_system import AnalysisMode
                analysis_system.set_mode(AnalysisMode.EXPLORATION)
                return True
            
            # Game controls
            elif button_id == "new_game":
                game.reset()
                return True
            elif button_id == "reset_game":
                game.reset()
                return True
            elif button_id == "save_pgn":
                # Trigger PGN save
                if hasattr(main_app, '_save_pgn'):
                    main_app._save_pgn(game)
                return True
            elif button_id == "change_theme":
                game.change_theme()
                return True
            
        except Exception as e:
            print(f"⚠️ Error handling button click {button_id}: {e}")
        
        return False
    
    def handle_scroll(self, delta: int) -> bool:
        """Handle mouse wheel scrolling"""
        self.scroll_offset -= delta * 20
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        return True

# Global instance
chess_control_panel = ChessControlPanel()