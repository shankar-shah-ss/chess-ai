# main.py - Updated with Modern Analysis System Integration
import pygame
import sys
import os

from const import *
from game import Game
from square import Square
from move import Move
from analysis_manager import AnalysisManager
from chess_com_analysis import ChessComAnalysis

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

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger
        analysis_manager = self.analysis_manager

        # Set initial game mode
        game.set_game_mode(0)  # Start with human vs human

        while True:
            self.clock.tick(60)  # Limit to 60 FPS
            
            # Update analysis manager
            analysis_manager.update()
            
            # Process engine moves from queue
            if game.engine_thread:
                if game.make_engine_move():
                    # Force immediate redraw
                    self._render_game_state(screen, game, dragger, analysis_manager)
                    pygame.display.update()

            # Check for completed evaluations
            if game.evaluation_thread and not game.evaluation_thread.is_alive():
                with game.evaluation_lock:
                    game.evaluation = game.evaluation_thread.evaluation
                game.evaluation_thread = None

            # Schedule evaluation if needed (not in analysis mode)
            if not game.evaluation_thread and not analysis_manager.active:
                game.schedule_evaluation()

            # Handle analysis mode rendering
            if analysis_manager.active:
                # Render using the analysis manager (which uses AnalysisScreen)
                analysis_manager.render(screen)
                pygame.display.update()
                    
                # Process events for analysis mode
                for event in pygame.event.get():
                    # Handle analysis manager input
                    if analysis_manager.handle_input(event):
                        # If analysis was deactivated, we don't need to do anything special because the loop condition will break next time
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
                        pygame.quit()
                        sys.exit()
                continue

            # Handle game over state
            if game.game_over:
                self._render_game_state(screen, game, dragger, analysis_manager)
                self._render_game_over_overlay(screen, game)
                pygame.display.update()
                
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
                        pygame.quit()
                        sys.exit()
                continue

            # Schedule engine move if needed
            if not dragger.dragging and not game.engine_thread:
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
            
            pygame.display.update()

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

    def _render_modern_game_info(self, screen, game, analysis_manager):
        """Render modern game information panel"""
        # Info panel background
        panel_width = 320
        panel_height = 240
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
        title_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Game Status", True, (255, 255, 255))
        screen.blit(title_surface, (panel_x + 20, panel_y + 15))

        # Game mode section
        mode_font = pygame.font.SysFont('Segoe UI', 14, bold=True)
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine", 
            2: "Engine vs Engine"
        }[game.game_mode]
        
        mode_label = mode_font.render("Mode:", True, (181, 181, 181))
        screen.blit(mode_label, (panel_x + 20, panel_y + 45))
        
        mode_value_font = pygame.font.SysFont('Segoe UI', 14)
        mode_value_surface = mode_value_font.render(mode_text, True, (255, 255, 255))
        screen.blit(mode_value_surface, (panel_x + 70, panel_y + 45))
        
        # Engine settings
        if game.engine_white or game.engine_black:
            settings_font = pygame.font.SysFont('Segoe UI', 13)
            
            level_label = settings_font.render("Level:", True, (181, 181, 181))
            screen.blit(level_label, (panel_x + 20, panel_y + 70))
            
            level_value = settings_font.render(f"{game.level}/20", True, (129, 182, 76))
            screen.blit(level_value, (panel_x + 70, panel_y + 70))
            
            depth_label = settings_font.render("Depth:", True, (181, 181, 181))
            screen.blit(depth_label, (panel_x + 150, panel_y + 70))
            
            depth_value = settings_font.render(str(game.depth), True, (129, 182, 76))
            screen.blit(depth_value, (panel_x + 200, panel_y + 70))
            
            # Show configuration status with animation
            if hasattr(game, 'config_thread') and game.config_thread and game.config_thread.is_alive():
                # Animated dots for visual feedback
                dots = "." * (int(pygame.time.get_ticks() / 300) % 4)
                config_status = settings_font.render(f"Configuring{dots}", True, (255, 193, 7))
                screen.blit(config_status, (panel_x + 250, panel_y + 70))
        
        # Current player indicator with visual circle
        player_font = pygame.font.SysFont('Segoe UI', 14, bold=True)
        player_label = player_font.render("Turn:", True, (181, 181, 181))
        screen.blit(player_label, (panel_x + 20, panel_y + 100))
        
        # Player indicator circle
        circle_color = (255, 255, 255) if game.next_player == 'white' else (100, 100, 100)
        pygame.draw.circle(screen, circle_color, (panel_x + 70, panel_y + 107), 8)
        pygame.draw.circle(screen, (181, 181, 181), (panel_x + 70, panel_y + 107), 8, 2)
        
        player_text = game.next_player.title()
        player_surface = player_font.render(player_text, True, (255, 255, 255))
        screen.blit(player_surface, (panel_x + 90, panel_y + 100))
        
        # Evaluation display with bar
        with game.evaluation_lock:
            if game.evaluation and 'type' in game.evaluation and 'value' in game.evaluation:
                eval_font = pygame.font.SysFont('Segoe UI', 13)
                eval_type = game.evaluation['type']
                value = game.evaluation['value']
                
                eval_label = eval_font.render("Eval:", True, (181, 181, 181))
                screen.blit(eval_label, (panel_x + 20, panel_y + 130))
                
                if eval_type == 'cp':
                    score = value / 100.0
                    eval_text = f"{score:+.2f}"
                    eval_color = (129, 182, 76) if score > 0 else (242, 113, 102) if score < -0.5 else (181, 181, 181)
                    
                    # Evaluation bar
                    bar_width = 120
                    bar_height = 6
                    bar_x = panel_x + 70
                    bar_y = panel_y + 135
                    
                    # Background bar
                    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
                    
                    # Fill bar based on evaluation
                    normalized_score = max(-2, min(2, score))  # Clamp between -2 and +2
                    fill_position = (normalized_score + 2) / 4  # Normalize to 0-1
                    fill_width = int(bar_width * fill_position)
                    
                    fill_color = (129, 182, 76) if score > 0 else (242, 113, 102)
                    if fill_width > 0:
                        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height), border_radius=3)
                    
                else:  # mate
                    moves_to_mate = abs(value)
                    side = 'W' if value > 0 else 'B'
                    eval_text = f"M{moves_to_mate} {side}"
                    eval_color = (129, 182, 76) if value > 0 else (242, 113, 102)
                
                eval_surface = eval_font.render(eval_text, True, eval_color)
                screen.blit(eval_surface, (panel_x + 200, panel_y + 130))
        
        # Game progress
        moves_recorded = len(analysis_manager.analyzer.game_moves)
        if moves_recorded > 0:
            progress_font = pygame.font.SysFont('Segoe UI', 12)
            progress_text = f"Moves recorded: {moves_recorded}"
            progress_surface = progress_font.render(progress_text, True, (181, 181, 181))
            screen.blit(progress_surface, (panel_x + 20, panel_y + 160))
        
        # Controls info
        controls_font = pygame.font.SysFont('Segoe UI', 11)
        controls = [
            "Press 'A' for Analysis",
            "Press 'S' for Summary"
        ]
        
        y_offset = 180
        for control in controls:
            control_surface = controls_font.render(control, True, (129, 182, 76))
            screen.blit(control_surface, (panel_x + 20, panel_y + y_offset))
            y_offset += 18

    def _render_game_over_overlay(self, screen, game):
        """Render modern game over overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Game over panel with shadow
        panel_width = 450
        panel_height = 250
        panel_x = (WIDTH - panel_width) // 2
        panel_y = (HEIGHT - panel_height) // 2
        
        # Shadow
        shadow_surface = pygame.Surface((panel_width + 16, panel_height + 16), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 100), pygame.Rect(0, 0, panel_width + 16, panel_height + 16), border_radius=25)
        screen.blit(shadow_surface, (panel_x + 8, panel_y + 8))
        
        # Main panel
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 46, 58), panel_rect, border_radius=20)
        pygame.draw.rect(screen, (84, 92, 108), panel_rect, 3, border_radius=20)
        
        # Game result
        result_font = pygame.font.SysFont('Segoe UI', 36, bold=True)
        if game.winner:
            result_text = f"{game.winner.title()} Wins!"
            result_color = (129, 182, 76)
        else:
            result_text = "Draw!"
            result_color = (181, 181, 181)
            
        result_surface = result_font.render(result_text, True, result_color)
        result_rect = result_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 60))
        screen.blit(result_surface, result_rect)
        
        # Separator line
        pygame.draw.line(screen, (84, 92, 108), (panel_x + 50, panel_y + 100), (panel_x + panel_width - 50, panel_y + 100), 2)
        
        # Options with modern styling
        options_font = pygame.font.SysFont('Segoe UI', 16)
        option_descriptions = pygame.font.SysFont('Segoe UI', 12)
        
        options = [
            ("R", "Restart Game", "Start a new game"),
            ("A", "Analysis Mode", "Review game with engine analysis"),
            ("S", "Game Summary", "View performance statistics")
        ]
        
        y_offset = 130
        for key, title, desc in options:
            # Key badge
            key_rect = pygame.Rect(panel_x + 50, panel_y + y_offset - 5, 30, 25)
            pygame.draw.rect(screen, (129, 182, 76), key_rect, border_radius=5)
            
            key_surface = pygame.font.SysFont('Segoe UI', 14, bold=True).render(key, True, (40, 46, 58))
            key_text_rect = key_surface.get_rect(center=key_rect.center)
            screen.blit(key_surface, key_text_rect)
            
            # Option title
            title_surface = options_font.render(title, True, (255, 255, 255))
            screen.blit(title_surface, (panel_x + 95, panel_y + y_offset - 2))
            
            # Option description
            desc_surface = option_descriptions.render(desc, True, (181, 181, 181))
            screen.blit(desc_surface, (panel_x + 95, panel_y + y_offset + 18))
            
            y_offset += 45

    def _handle_game_event(self, event, game, board, dragger, analysis_manager):
        """Handle game events with modern controls"""
        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (game.next_player == 'white' and game.engine_white) or \
               (game.next_player == 'black' and game.engine_black):
                return True
            
            if 0 <= event.pos[0] < WIDTH and 0 <= event.pos[1] < HEIGHT:
                dragger.update_mouse(event.pos)
                clicked_row = event.pos[1] // SQSIZE
                clicked_col = event.pos[0] // SQSIZE

                if board.squares[clicked_row][clicked_col].has_piece():
                    piece = board.squares[clicked_row][clicked_col].piece
                    if piece.color == game.next_player:
                        board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                        dragger.save_initial(event.pos)
                        dragger.drag_piece(piece)
                        self._render_game_state(self.screen, game, dragger, analysis_manager)
            return True
        
        # Mouse motion
        elif event.type == pygame.MOUSEMOTION:
            if 0 <= event.pos[0] < WIDTH and 0 <= event.pos[1] < HEIGHT:
                motion_row = event.pos[1] // SQSIZE
                motion_col = event.pos[0] // SQSIZE
                game.set_hover(motion_row, motion_col)

                if dragger.dragging:
                    dragger.update_mouse(event.pos)
                    self._render_game_state(self.screen, game, dragger, analysis_manager)
                    dragger.update_blit(self.screen)
            else:
                game.hovered_sqr = None
            return True
        
        # Mouse release
        elif event.type == pygame.MOUSEBUTTONUP:
            if (game.next_player == 'white' and game.engine_white) or \
               (game.next_player == 'black' and game.engine_black):
                return True
            
            if dragger.dragging:
                dragger.update_mouse(event.pos)
                
                if 0 <= event.pos[0] < WIDTH and 0 <= event.pos[1] < HEIGHT:
                    released_row = event.pos[1] // SQSIZE
                    released_col = event.pos[0] // SQSIZE

                    initial = Square(dragger.initial_row, dragger.initial_col)
                    final = Square(released_row, released_col)
                    move = Move(initial, final)

                    if board.valid_move(dragger.piece, move):
                        # Record move for analysis and make the move
                        game.make_move(dragger.piece, move)
                        self._render_game_state(self.screen, game, dragger, analysis_manager)
                        pygame.display.update()
            
            dragger.undrag_piece()
            return True
        
        # Key press
        elif event.type == pygame.KEYDOWN:
            # Theme and reset
            if event.key == pygame.K_t:
                game.change_theme()
            elif event.key == pygame.K_r:
                self._reset_game(game, analysis_manager)
                
            # Game mode controls
            elif event.key == pygame.K_1:
                game.set_game_mode(0)
            elif event.key == pygame.K_2:
                game.set_game_mode(1)
            elif event.key == pygame.K_3:
                game.set_game_mode(2)
                
            # Engine controls
            elif event.key == pygame.K_e:
                game.toggle_engine('white')
            elif event.key == pygame.K_d:
                game.toggle_engine('black')
                
            # Engine settings
            elif event.key == pygame.K_UP:
                game.set_engine_depth(min(20, game.depth + 1))
            elif event.key == pygame.K_DOWN:
                game.set_engine_depth(max(1, game.depth - 1))
            elif event.key == pygame.K_RIGHT:
                game.set_engine_level(min(20, game.level + 1))
            elif event.key == pygame.K_LEFT:
                game.set_engine_level(max(0, game.level - 1))
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                game.increase_level()
            elif event.key == pygame.K_MINUS:
                game.decrease_level()
                
            # Analysis controls
            elif event.key == pygame.K_a:
                if game.game_over or len(analysis_manager.analyzer.game_moves) > 0:
                    analysis_manager.enter_analysis_mode()
            elif event.key == pygame.K_s:
                if analysis_manager.is_analysis_complete():
                    analysis_manager.toggle_summary()
                    
            # UI controls
            elif event.key == pygame.K_i:
                self.show_game_info = not self.show_game_info
            elif event.key == pygame.K_F11:
                self._toggle_fullscreen()
                
            return True
        
        elif event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        return False

    def _reset_game(self, game, analysis_manager):
        """Reset game and analysis with proper cleanup"""
        game.reset()
        analysis_manager.reset()
        
        # Reconnect references after reset
        game.set_analysis_manager(analysis_manager)

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        pygame.display.toggle_fullscreen()

    def show_startup_screen(self):
        """Show modern startup screen"""
        startup_font = pygame.font.SysFont('Segoe UI', 48, bold=True)
        subtitle_font = pygame.font.SysFont('Segoe UI', 24)
        info_font = pygame.font.SysFont('Segoe UI', 16)
        
        # Gradient background
        for y in range(HEIGHT):
            color_intensity = int(40 + (y / HEIGHT) * 20)
            color = (color_intensity, color_intensity + 6, color_intensity + 18)
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))
        
        # Title with shadow
        title_text = "Modern Chess"
        title_surface = startup_font.render(title_text, True, (255, 255, 255))
        title_shadow = startup_font.render(title_text, True, (0, 0, 0))
        
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = subtitle_font.render("with Advanced Analysis", True, (129, 182, 76))
        subtitle_rect = subtitle_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Instructions panel
        panel_width = 600
        panel_height = 200
        panel_x = (WIDTH - panel_width) // 2
        panel_y = HEIGHT // 2 - 10
        
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (0, 0, 0, 100), pygame.Rect(0, 0, panel_width, panel_height), border_radius=15)
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        instructions = [
            "Game Modes: 1 (Human vs Human) | 2 (Human vs Engine) | 3 (Engine vs Engine)",
            "Engine: E/D (Toggle) | ↑/↓ (Depth) | ←/→ (Level) | +/- (Quick Level) [Non-blocking]",
            "Analysis: A (Enter Analysis) | S (Summary) | ESC (Exit Analysis)",
            "Other: T (Theme) | R (Reset) | I (Info Panel) | F11 (Fullscreen)"
        ]
        
        y_offset = panel_y + 30
        for instruction in instructions:
            instruction_surface = info_font.render(instruction, True, (255, 255, 255))
            instruction_rect = instruction_surface.get_rect(center=(WIDTH // 2, y_offset))
            self.screen.blit(instruction_surface, instruction_rect)
            y_offset += 30
            
        # Start prompt with animation effect
        start_font = pygame.font.SysFont('Segoe UI', 20, bold=True)
        start_surface = start_font.render("Click anywhere to start", True, (129, 182, 76))
        start_rect = start_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 160))
        self.screen.blit(start_surface, start_rect)
        
        pygame.display.update()
        
        # Wait for click
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    waiting = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

if __name__ == "__main__":
    main = Main()
    main.show_startup_screen()
    main.mainloop()