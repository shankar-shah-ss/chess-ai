"""
Interactive Opening Explorer
Provides comprehensive opening exploration with move trees, statistics, and analysis
"""

import pygame
import chess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from opening_theory_system import opening_theory_system, OpeningMove, OpeningPhase
from opening_theory_ui import UIColors
import textwrap

@dataclass
class ExplorerState:
    """State management for the opening explorer"""
    current_fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move_history: List[str] = None
    selected_move: Optional[str] = None
    scroll_offset: int = 0
    show_statistics: bool = True
    show_plans: bool = True
    
    def __post_init__(self):
        if self.move_history is None:
            self.move_history = []

class OpeningExplorer:
    """
    Interactive Opening Explorer
    Allows users to explore opening variations, see statistics, and navigate move trees
    """
    
    def __init__(self, width: int = 500, height: int = 700):
        self.width = width
        self.height = height
        self.colors = UIColors()
        
        # State management
        self.state = ExplorerState()
        self.board = chess.Board()
        
        # UI elements
        self.font_title = pygame.font.Font(None, 28)
        self.font_subtitle = pygame.font.Font(None, 22)
        self.font_body = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 18)
        self.font_tiny = pygame.font.Font(None, 16)
        
        # Layout
        self.header_height = 80
        self.move_tree_height = 300
        self.info_panel_height = 200
        self.controls_height = 120
        
        # Interactive elements
        self.clickable_moves = {}  # move_uci -> rect
        self.buttons = {}  # button_name -> rect
        
        print("🔍 Opening Explorer initialized")
    
    def reset_to_starting_position(self):
        """Reset explorer to starting position"""
        self.state = ExplorerState()
        self.board = chess.Board()
        self.clickable_moves.clear()
    
    def make_move(self, move_uci: str) -> bool:
        """Make a move in the explorer"""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                # Update board
                san_move = self.board.san(move)
                self.board.push(move)
                
                # Update state
                self.state.current_fen = self.board.fen()
                self.state.move_history.append(san_move)
                self.state.selected_move = None
                self.state.scroll_offset = 0
                
                return True
        except Exception as e:
            print(f"❌ Error making move in explorer: {e}")
        
        return False
    
    def undo_move(self) -> bool:
        """Undo the last move"""
        try:
            if self.board.move_stack:
                self.board.pop()
                self.state.current_fen = self.board.fen()
                if self.state.move_history:
                    self.state.move_history.pop()
                self.state.selected_move = None
                return True
        except Exception as e:
            print(f"❌ Error undoing move: {e}")
        
        return False
    
    def render(self, screen: pygame.Surface, x: int, y: int):
        """Render the opening explorer"""
        # Create explorer surface
        explorer_surface = pygame.Surface((self.width, self.height))
        explorer_surface.fill(self.colors.panel_bg)
        
        # Draw border
        pygame.draw.rect(explorer_surface, self.colors.border, 
                        (0, 0, self.width, self.height), 2)
        
        # Clear clickable elements
        self.clickable_moves.clear()
        self.buttons.clear()
        
        y_offset = 10
        
        # Header section
        y_offset = self._render_header(explorer_surface, y_offset)
        
        # Move history
        y_offset = self._render_move_history(explorer_surface, y_offset)
        
        # Current position info
        y_offset = self._render_position_info(explorer_surface, y_offset)
        
        # Move tree
        y_offset = self._render_move_tree(explorer_surface, y_offset)
        
        # Statistics and plans
        if self.state.show_statistics:
            y_offset = self._render_statistics(explorer_surface, y_offset)
        
        if self.state.show_plans:
            y_offset = self._render_plans(explorer_surface, y_offset)
        
        # Controls
        self._render_controls(explorer_surface, self.height - self.controls_height)
        
        # Blit to main screen
        screen.blit(explorer_surface, (x, y))
    
    def _render_header(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the header section"""
        # Title
        title_surface = self.font_title.render("Opening Explorer", True, self.colors.text_primary)
        surface.blit(title_surface, (15, y_offset))
        y_offset += 35
        
        # Current opening info
        opening_info = opening_theory_system.detect_opening(self.state.current_fen)
        opening_name = opening_info.get("name", "Unknown")
        eco_code = opening_info.get("eco", "")
        
        if len(opening_name) > 40:
            opening_name = opening_name[:37] + "..."
        
        opening_text = f"{opening_name}"
        if eco_code:
            opening_text += f" ({eco_code})"
        
        opening_surface = self.font_subtitle.render(opening_text, True, self.colors.accent)
        surface.blit(opening_surface, (15, y_offset))
        y_offset += 30
        
        return y_offset
    
    def _render_move_history(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the move history"""
        if not self.state.move_history:
            return y_offset
        
        # Move history header
        history_header = self.font_body.render("Moves:", True, self.colors.text_primary)
        surface.blit(history_header, (15, y_offset))
        y_offset += 25
        
        # Format moves in pairs
        move_pairs = []
        for i in range(0, len(self.state.move_history), 2):
            move_num = (i // 2) + 1
            white_move = self.state.move_history[i]
            black_move = self.state.move_history[i + 1] if i + 1 < len(self.state.move_history) else ""
            
            if black_move:
                move_pairs.append(f"{move_num}.{white_move} {black_move}")
            else:
                move_pairs.append(f"{move_num}.{white_move}")
        
        # Display moves
        moves_text = " ".join(move_pairs)
        if len(moves_text) > 60:
            moves_text = moves_text[:57] + "..."
        
        moves_lines = textwrap.wrap(moves_text, width=55)
        for line in moves_lines[:2]:  # Show max 2 lines
            line_surface = self.font_small.render(line, True, self.colors.text_secondary)
            surface.blit(line_surface, (20, y_offset))
            y_offset += 20
        
        y_offset += 10
        return y_offset
    
    def _render_position_info(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render current position information"""
        opening_info = opening_theory_system.detect_opening(self.state.current_fen)
        
        # Phase indicator
        phase = opening_info.get("phase", "opening")
        phase_color = self._get_phase_color(phase)
        phase_text = f"Phase: {phase.title()}"
        phase_surface = self.font_body.render(phase_text, True, phase_color)
        surface.blit(phase_surface, (15, y_offset))
        
        # Move number
        move_num = opening_info.get("move_number", 1)
        move_text = f"Move: {move_num}"
        move_surface = self.font_body.render(move_text, True, self.colors.text_secondary)
        surface.blit(move_surface, (150, y_offset))
        
        # Theoretical indicator
        is_theoretical = opening_info.get("is_theoretical", False)
        theory_text = "Theoretical" if is_theoretical else "Non-theoretical"
        theory_color = self.colors.success if is_theoretical else self.colors.warning
        theory_surface = self.font_body.render(theory_text, True, theory_color)
        surface.blit(theory_surface, (220, y_offset))
        
        y_offset += 30
        
        # Description
        description = opening_info.get("description", "")
        if description:
            desc_lines = textwrap.wrap(description, width=55)
            for line in desc_lines[:2]:  # Show max 2 lines
                line_surface = self.font_small.render(line, True, self.colors.text_secondary)
                surface.blit(line_surface, (15, y_offset))
                y_offset += 18
        
        y_offset += 15
        return y_offset
    
    def _render_move_tree(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render the move tree with clickable moves"""
        # Section header
        header_surface = self.font_subtitle.render("Popular Continuations", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 30
        
        # Get next moves
        next_moves = opening_theory_system.get_next_moves(self.state.current_fen, limit=8)
        
        if not next_moves:
            no_moves_surface = self.font_body.render("No continuations available", True, self.colors.text_secondary)
            surface.blit(no_moves_surface, (20, y_offset))
            return y_offset + 30
        
        # Render moves
        for i, move in enumerate(next_moves):
            move_y = y_offset + (i * 35)
            
            # Move button background
            button_rect = pygame.Rect(15, move_y, self.width - 30, 30)
            
            # Highlight if selected
            if self.state.selected_move == move.move:
                pygame.draw.rect(surface, self.colors.hover, button_rect)
            
            pygame.draw.rect(surface, self.colors.border, button_rect, 1)
            
            # Store clickable area
            self.clickable_moves[move.move] = button_rect
            
            # Move notation
            move_text = f"{i+1}. {move.san}"
            move_surface = self.font_body.render(move_text, True, self.colors.text_primary)
            surface.blit(move_surface, (25, move_y + 5))
            
            # Statistics
            stats_text = f"W:{move.white_win_rate:.0f}% D:{move.draw_rate:.0f}% B:{move.black_win_rate:.0f}%"
            stats_surface = self.font_small.render(stats_text, True, self.colors.text_secondary)
            surface.blit(stats_surface, (150, move_y + 8))
            
            # Games count
            games_text = f"({move.total_games} games)"
            games_surface = self.font_tiny.render(games_text, True, self.colors.text_secondary)
            surface.blit(games_surface, (350, move_y + 8))
        
        return y_offset + (len(next_moves) * 35) + 20
    
    def _render_statistics(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render opening statistics"""
        # Section header
        header_surface = self.font_subtitle.render("Statistics", True, self.colors.text_primary)
        surface.blit(header_surface, (15, y_offset))
        y_offset += 25
        
        # Get opening statistics
        opening_info = opening_theory_system.detect_opening(self.state.current_fen)
        eco_code = opening_info.get("eco", "")
        
        if eco_code:
            stats = opening_theory_system.get_opening_statistics(eco_code)
            
            # Win rates
            white_rate = stats.get("white_win_rate", 0)
            draw_rate = stats.get("draw_rate", 0)
            black_rate = stats.get("black_win_rate", 0)
            
            rates_text = f"White: {white_rate:.1f}%  Draw: {draw_rate:.1f}%  Black: {black_rate:.1f}%"
            rates_surface = self.font_small.render(rates_text, True, self.colors.text_secondary)
            surface.blit(rates_surface, (20, y_offset))
            y_offset += 20
            
            # Games and popularity
            total_games = stats.get("total_games", 0)
            popularity = stats.get("popularity", 0)
            
            games_text = f"Games: {total_games:,}  Popularity: {popularity:.1f}%"
            games_surface = self.font_small.render(games_text, True, self.colors.text_secondary)
            surface.blit(games_surface, (20, y_offset))
            y_offset += 25
        else:
            no_stats_surface = self.font_small.render("No statistics available", True, self.colors.text_secondary)
            surface.blit(no_stats_surface, (20, y_offset))
            y_offset += 25
        
        return y_offset
    
    def _render_plans(self, surface: pygame.Surface, y_offset: int) -> int:
        """Render typical plans and ideas"""
        opening_info = opening_theory_system.detect_opening(self.state.current_fen)
        
        # Key ideas
        key_ideas = opening_info.get("key_ideas", [])
        if key_ideas:
            ideas_header = self.font_subtitle.render("Key Ideas", True, self.colors.text_primary)
            surface.blit(ideas_header, (15, y_offset))
            y_offset += 25
            
            for idea in key_ideas[:2]:  # Show first 2 ideas
                idea_lines = textwrap.wrap(f"• {idea}", width=55)
                for line in idea_lines:
                    line_surface = self.font_small.render(line, True, self.colors.text_secondary)
                    surface.blit(line_surface, (20, y_offset))
                    y_offset += 18
            
            y_offset += 10
        
        return y_offset
    
    def _render_controls(self, surface: pygame.Surface, y_offset: int):
        """Render control buttons"""
        button_width = 80
        button_height = 25
        button_spacing = 10
        
        buttons = [
            ("Reset", self._reset_position),
            ("Undo", self.undo_move),
            ("Stats", self._toggle_statistics),
            ("Plans", self._toggle_plans)
        ]
        
        x_start = 15
        for i, (label, callback) in enumerate(buttons):
            button_x = x_start + i * (button_width + button_spacing)
            button_rect = pygame.Rect(button_x, y_offset, button_width, button_height)
            
            # Store button
            self.buttons[label.lower()] = button_rect
            
            # Draw button
            pygame.draw.rect(surface, self.colors.background, button_rect)
            pygame.draw.rect(surface, self.colors.border, button_rect, 1)
            
            # Button text
            text_surface = self.font_small.render(label, True, self.colors.text_primary)
            text_rect = text_surface.get_rect(center=button_rect.center)
            surface.blit(text_surface, text_rect)
    
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
    
    def handle_click(self, x: int, y: int) -> bool:
        """Handle mouse clicks"""
        # Check move clicks
        for move_uci, rect in self.clickable_moves.items():
            if rect.collidepoint(x, y):
                if self.state.selected_move == move_uci:
                    # Double click - make the move
                    return self.make_move(move_uci)
                else:
                    # Single click - select the move
                    self.state.selected_move = move_uci
                    return True
        
        # Check button clicks
        for button_name, rect in self.buttons.items():
            if rect.collidepoint(x, y):
                if button_name == "reset":
                    self._reset_position()
                elif button_name == "undo":
                    self.undo_move()
                elif button_name == "stats":
                    self._toggle_statistics()
                elif button_name == "plans":
                    self._toggle_plans()
                return True
        
        return False
    
    def _reset_position(self):
        """Reset to starting position"""
        self.reset_to_starting_position()
    
    def _toggle_statistics(self):
        """Toggle statistics display"""
        self.state.show_statistics = not self.state.show_statistics
    
    def _toggle_plans(self):
        """Toggle plans display"""
        self.state.show_plans = not self.state.show_plans
    
    def get_current_opening(self) -> Dict[str, Any]:
        """Get current opening information"""
        return opening_theory_system.detect_opening(self.state.current_fen)

# Global instance for easy access
opening_explorer = OpeningExplorer()