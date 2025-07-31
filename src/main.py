# main.py - Updated with Modern Analysis System Integration
import pygame
import sys
import os

from const import *
from game import Game
from square import Square
from move import Move
from analysis_manager import AnalysisManager

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess with Modern Analysis')
        self.game = Game()
        self.clock = pygame.time.Clock()
        
        # Initialize modern analysis manager
        self.analysis_manager = AnalysisManager(self.game.config, self.game.engine)
        
        # Connect analysis manager to game
        self.game.set_analysis_manager(self.analysis_manager)
        
        # UI state
        self.show_game_info = True
        self.show_help = False
        self.initial_fen = None
        
        # Enhanced resource management
        from resource_manager import resource_manager
        from error_handling import performance_monitor
        self.resource_manager = resource_manager
        self.performance_monitor = performance_monitor
        
        # Maintenance timing
        self.last_maintenance = pygame.time.get_ticks()
        self.maintenance_interval = 30000  # 30 seconds

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger
        analysis_manager = self.analysis_manager

        # Set initial game mode
        game.set_game_mode(0)  # Start with human vs human

        while True:
            self.clock.tick(120)  # Higher FPS for smoother experience
            
            # Periodic maintenance
            current_time = pygame.time.get_ticks()
            if current_time - self.last_maintenance > self.maintenance_interval:
                self.game.periodic_maintenance()
                self.last_maintenance = current_time
            
            # Process engine moves (highest priority)
            if hasattr(game, 'engine_thread') and game.engine_thread:
                if game.make_engine_move():
                    self._render_game_state(screen, game, dragger, analysis_manager)
                    pygame.display.flip()  # Faster than update()
                    continue

            # Minimal evaluation processing
            if hasattr(game, 'evaluation_thread') and game.evaluation_thread and not game.evaluation_thread.is_alive():
                with game.evaluation_lock:
                    game.evaluation = game.evaluation_thread.evaluation
                game.evaluation_thread = None

            # Handle analysis mode rendering
            if analysis_manager.active:
                # Render using the analysis manager
                analysis_manager.render(screen)
                pygame.display.flip()
                    
                # Process events for analysis mode
                for event in pygame.event.get():
                    # Handle analysis manager input
                    if analysis_manager.handle_input(event):
                        continue
                        
                    # Handle global keys
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._reset_game(game, analysis_manager)
                        elif event.key == pygame.K_F11:
                            self._toggle_fullscreen()
                        elif event.key == pygame.K_ESCAPE:
                            analysis_manager.exit_analysis_mode()
                        elif event.key == pygame.K_s:
                            if analysis_manager.is_analysis_complete():
                                analysis_manager.toggle_summary()
                    elif event.type == pygame.QUIT:
                        self._cleanup_and_exit()
                continue

            # Handle game over state
            if game.game_over:
                self._render_game_state(screen, game, dragger, analysis_manager)
                self._render_game_over_overlay(screen, game)
                pygame.display.flip()
                
                # Process events for restart
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self._reset_game(game, analysis_manager)
                        elif event.key == pygame.K_a:
                            analysis_manager.enter_analysis_mode()
                        elif event.key == pygame.K_s:
                            if analysis_manager.is_analysis_complete():
                                analysis_manager.toggle_summary()
                        elif event.key == pygame.K_F11:
                            self._toggle_fullscreen()
                    elif event.type == pygame.QUIT:
                        self._cleanup_and_exit()
                continue

            # Schedule engine move if needed
            if not dragger.dragging and (not hasattr(game, 'engine_thread') or not game.engine_thread):
                if (game.next_player == 'white' and game.engine_white) or \
                   (game.next_player == 'black' and game.engine_black):
                    game.schedule_engine_move()

            # Render normal game state
            self._render_game_state(screen, game, dragger, analysis_manager)

            if dragger.dragging:
                dragger.update_blit(screen)

            # Handle game events
            for event in pygame.event.get():
                if self._handle_game_event(event, game, board, dragger, analysis_manager):
                    continue
            
            pygame.display.flip()

    def _render_game_state(self, screen, game, dragger, analysis_manager):
        """Render the main game state with modern styling"""
        game.show_bg(screen)
        game.show_last_move(screen)
        game.show_moves(screen)
        game.show_check(screen)
        game.show_pieces(screen)
        game.show_hover(screen)
        
        # Show modern game info panel if not in analysis mode
        if not analysis_manager.active and self.show_game_info:
            self._render_modern_game_info(screen, game, analysis_manager)
        
        # Show help overlay if requested
        if self.show_help:
            self._render_help_overlay(screen)

    def _render_modern_game_info(self, screen, game, analysis_manager):
        """Render modern game information panel"""
        # Info panel background
        panel_width = 320
        panel_height = 200
        panel_x = WIDTH - panel_width - 20
        panel_y = 20
        
        # Modern panel styling with shadow
        shadow_surface = pygame.Surface((panel_width + 8, panel_height + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 60), pygame.Rect(0, 0, panel_width + 8, panel_height + 8), border_radius=15)
        screen.blit(shadow_surface, (panel_x + 4, panel_y + 4))
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_bg_color = (40, 46, 58, 220)  # Semi-transparent
        pygame.draw.rect(panel_surface, panel_bg_color, pygame.Rect(0, 0, panel_width, panel_height), border_radius=15)
        pygame.draw.rect(panel_surface, (84, 92, 108, 255), pygame.Rect(0, 0, panel_width, panel_height), 2, border_radius=15)
        screen.blit(panel_surface, (panel_x, panel_y))

        # Title
        title_font = self._get_cached_font('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Game Status", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))

        # Game mode section
        mode_font = self._get_cached_font('Segoe UI', 14, bold=True)
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine", 
            2: "Engine vs Engine"
        }[game.game_mode]
        
        mode_label = mode_font.render("Mode:", True, (181, 181, 181))
        screen.blit(mode_label, (panel_x + 20, panel_y + 45))
        
        mode_value_font = self._get_cached_font('Segoe UI', 14)
        mode_value_surface = mode_value_font.render(mode_text, True, (255, 255, 255))
        screen.blit(mode_value_surface, (panel_x + 70, panel_y + 45))
        
        # Engine settings
        if game.engine_white or game.engine_black:
            settings_font = self._get_cached_font('Segoe UI', 13)
            
            level_label = settings_font.render("Level:", True, (181, 181, 181))
            screen.blit(level_label, (panel_x + 20, panel_y + 70))
            
            level_value = settings_font.render(f"{game.level}/20", True, (129, 182, 76))
            screen.blit(level_value, (panel_x + 70, panel_y + 70))
            
            depth_label = settings_font.render("Depth:", True, (181, 181, 181))
            screen.blit(depth_label, (panel_x + 150, panel_y + 70))
            
            depth_value = settings_font.render(str(game.depth), True, (129, 182, 76))
            screen.blit(depth_value, (panel_x + 200, panel_y + 70))
        
        # Current player indicator
        player_font = self._get_cached_font('Segoe UI', 14, bold=True)
        player_label = player_font.render("Turn:", True, (181, 181, 181))
        screen.blit(player_label, (panel_x + 20, panel_y + 100))
        
        player_color = (255, 255, 255) if game.next_player == 'white' else (200, 200, 200)
        player_value = game.next_player.title()
        player_surface = player_font.render(player_value, True, player_color)
        screen.blit(player_surface, (panel_x + 70, panel_y + 100))
        
        # Controls hint
        hint_font = self._get_cached_font('Segoe UI', 12)
        hint_surface = hint_font.render("Press 'H' for controls", True, (129, 182, 76))
        screen.blit(hint_surface, (panel_x + 20, panel_y + 130))
        
        # Quick mode switch hint
        mode_hint = hint_font.render("1/2/3: Switch modes", True, (181, 181, 181))
        screen.blit(mode_hint, (panel_x + 20, panel_y + 150))
        
        # Engine controls hint
        if game.engine_white or game.engine_black:
            engine_hint = hint_font.render("+/-: Level, Ctrl+↑/↓: Depth", True, (181, 181, 181))
            screen.blit(engine_hint, (panel_x + 20, panel_y + 170))
    
    def _render_help_overlay(self, screen):
        """Render help overlay with all controls"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Help panel
        panel_width = 600
        panel_height = 500
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2
        
        # Panel background
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (40, 46, 58, 240), pygame.Rect(0, 0, panel_width, panel_height), border_radius=20)
        pygame.draw.rect(panel_surface, (84, 92, 108, 255), pygame.Rect(0, 0, panel_width, panel_height), 3, border_radius=20)
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Title
        title_font = self._get_cached_font('Segoe UI', 24, bold=True)
        title_surface = title_font.render("Chess AI Controls", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(panel_x + panel_width//2, panel_y + 30))
        screen.blit(title_surface, title_rect)
        
        # Controls list
        controls_font = self._get_cached_font('Segoe UI', 14)
        key_font = self._get_cached_font('Segoe UI', 14, bold=True)
        
        controls = [
            ("Game Modes:", ""),
            ("1", "Human vs Human"),
            ("2", "Human vs Engine"),
            ("3", "Engine vs Engine"),
            ("", ""),
            ("Engine Controls:", ""),
            ("+/-", "Increase/Decrease engine level"),
            ("Ctrl+↑/↓", "Increase/Decrease engine depth"),
            ("W", "Toggle white engine"),
            ("B", "Toggle black engine"),
            ("", ""),
            ("Game Controls:", ""),
            ("T", "Change theme"),
            ("R", "Reset game"),
            ("I", "Toggle info panel"),
            ("H", "Show/hide this help"),
            ("F11", "Toggle fullscreen"),
            ("", ""),
            ("Analysis (after game):", ""),
            ("A", "Enter analysis mode"),
            ("S", "Show summary"),
            ("←/→", "Navigate moves"),
            ("Space", "Auto-play moves")
        ]
        
        y_offset = panel_y + 70
        for key, description in controls:
            if key == "" and description == "":
                y_offset += 10
                continue
                
            if description == "":  # Section header
                header_surface = key_font.render(key, True, (129, 182, 76))
                screen.blit(header_surface, (panel_x + 30, y_offset))
                y_offset += 25
            else:
                # Key
                if key:
                    key_surface = key_font.render(key, True, (255, 255, 255))
                    screen.blit(key_surface, (panel_x + 50, y_offset))
                
                # Description
                desc_surface = controls_font.render(description, True, (200, 200, 200))
                screen.blit(desc_surface, (panel_x + 150, y_offset))
                y_offset += 22
        
        # Close instruction
        close_font = self._get_cached_font('Segoe UI', 12)
        close_surface = close_font.render("Press 'H' again to close", True, (129, 182, 76))
        close_rect = close_surface.get_rect(center=(panel_x + panel_width//2, panel_y + panel_height - 20))
        screen.blit(close_surface, close_rect)
    
    def _render_game_over_overlay(self, screen, game):
        """Render game over overlay"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        font = self._get_cached_font('Segoe UI', 48, bold=True)
        if game.winner:
            text = f"{game.winner.title()} Wins!"
            color = (100, 255, 100) if game.winner == 'white' else (255, 100, 100)
        else:
            text = "Draw!"
            color = (255, 255, 255)
            
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(text_surface, text_rect)
    
    def _reset_game(self, game, analysis_manager):
        """Reset the game"""
        try:
            analysis_manager.reset()
            game.reset()
        except Exception as e:
            print(f"Error resetting: {e}")
    
    def _get_cached_font(self, name, size, bold=False):
        """Get cached font using resource manager"""
        return self.resource_manager.get_font(name, size, bold)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen"""
        pygame.display.toggle_fullscreen()
    
    def _cleanup_and_exit(self):
        """Cleanup resources and exit gracefully"""
        try:
            print("Cleaning up resources...")
            
            # Cleanup game resources
            if hasattr(self, 'game'):
                self.game.cleanup()
            
            # Cleanup analysis manager
            if hasattr(self, 'analysis_manager'):
                if hasattr(self.analysis_manager, 'cleanup'):
                    self.analysis_manager.cleanup()
            
            # Cleanup resource manager
            if hasattr(self, 'resource_manager'):
                self.resource_manager.cleanup_all()
            
            # Cleanup thread manager
            from thread_manager import thread_manager
            thread_manager.cleanup_all()
            
            # Cleanup engine pool
            from engine import EnginePool
            EnginePool().cleanup_all()
            
            print("Cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            pygame.quit()
            sys.exit()
    
    def _handle_game_event(self, event, game, board, dragger, analysis_manager):
        """Handle game events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            dragger.update_mouse(event.pos)
            clicked_row = dragger.mouseY // SQSIZE
            clicked_col = dragger.mouseX // SQSIZE
            
            if 0 <= clicked_row < 8 and 0 <= clicked_col < 8:
                square = board.squares[clicked_row][clicked_col]
                if square.has_piece():
                    piece = square.piece
                    if piece.color == game.next_player:
                        board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                        dragger.save_initial(event.pos)
                        dragger.drag_piece(piece)
        
        elif event.type == pygame.MOUSEMOTION:
            if dragger.dragging:
                dragger.update_mouse(event.pos)
            else:
                motion_row = event.pos[1] // SQSIZE
                motion_col = event.pos[0] // SQSIZE
                game.set_hover(motion_row, motion_col)
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragger.dragging:
                dragger.update_mouse(event.pos)
                released_row = dragger.mouseY // SQSIZE
                released_col = dragger.mouseX // SQSIZE
                
                if 0 <= released_row < 8 and 0 <= released_col < 8:
                    initial = Square(dragger.initial_row, dragger.initial_col)
                    final = Square(released_row, released_col)
                    move = Move(initial, final)
                    
                    if board.valid_move(dragger.piece, move):
                        game.make_move(dragger.piece, move)
                    
            dragger.undrag_piece()
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                game.change_theme()
            elif event.key == pygame.K_r:
                self._reset_game(game, analysis_manager)
            elif event.key == pygame.K_a and game.game_over:
                analysis_manager.enter_analysis_mode()
            
            # Game mode switching
            elif event.key == pygame.K_1:
                game.set_game_mode(0)  # Human vs Human
            elif event.key == pygame.K_2:
                game.set_game_mode(1)  # Human vs Engine
            elif event.key == pygame.K_3:
                game.set_game_mode(2)  # Engine vs Engine
            
            # Engine level controls
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                game.increase_level()
            elif event.key == pygame.K_MINUS:
                game.decrease_level()
            
            # Engine depth controls
            elif event.key == pygame.K_UP:
                game.set_engine_depth(game.depth + 1)
            elif event.key == pygame.K_DOWN:
                game.set_engine_depth(game.depth - 1)
            
            # Toggle engines
            elif event.key == pygame.K_w:
                game.toggle_engine('white')
            elif event.key == pygame.K_b:
                game.toggle_engine('black')
            
            # Other features
            elif event.key == pygame.K_F11:
                self._toggle_fullscreen()
            elif event.key == pygame.K_i:
                self.show_game_info = not self.show_game_info
            elif event.key == pygame.K_h:
                self.show_help = not self.show_help
                
        elif event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        return False

if __name__ == '__main__':
    main = Main()
    main.mainloop()