# main.py
import pygame
from sys import exit
import os

from const import *
from game import Game
from square import Square
from move import Move


class ChessApplication:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess with Modern Analysis')
        self.game = Game()
        self.clock = pygame.time.Clock()
        
        # UI state
        self.show_game_info = True
        self.show_help = False
        self.initial_fen = None
        self.last_click_time = 0
        self.click_debounce = 100  # milliseconds - reduced for better responsiveness
        self.pgn_save_offered = False  # Track if we've offered to save PGN
        
        # Enhanced resource management
        from resource_manager import resource_manager
        from error_handling import performance_monitor
        self.resource_manager = resource_manager
        self.performance_monitor = performance_monitor
        
        # Maintenance timing
        self.last_maintenance = pygame.time.get_ticks()
        self.maintenance_interval = 30000  # 30 seconds

    def mainloop(self):
        self.game.set_game_mode(0)  # Start with human vs human
        
        while True:
            self.clock.tick(120)
            self._perform_maintenance()
            
            if self._process_engine_moves():
                continue
            
            self._process_evaluation()
            
            if self.game.game_over:
                self._handle_game_over()
                continue
            
            self._schedule_engine_move()
            self._render_game_state(self.screen, self.game, self.game.dragger)
            self._handle_events()
            pygame.display.flip()
    
    def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_maintenance > self.maintenance_interval:
            self.game.periodic_maintenance()
            self.last_maintenance = current_time
    
    def _process_engine_moves(self):
        """Process engine moves and return True if move was made"""
        if hasattr(self.game, 'engine_thread') and self.game.engine_thread:
            self.game.check_engine_timeout()
            if self.game.make_engine_move():
                self._render_game_state(self.screen, self.game, self.game.dragger)
                pygame.display.flip()
                return True
        return False
    
    def _process_evaluation(self):
        """Process engine evaluation updates"""
        if (hasattr(self.game, 'evaluation_thread') and 
            self.game.evaluation_thread and 
            not self.game.evaluation_thread.is_alive()):
            with self.game.evaluation_lock:
                self.game.evaluation = self.game.evaluation_thread.evaluation
            self.game.evaluation_thread = None
    
    def _handle_game_over(self):
        """Handle game over state"""
        if not self.pgn_save_offered and self.game.pgn.get_move_count() > 0:
            self.pgn_save_offered = True
            import threading
            threading.Thread(target=self._offer_save_pgn, args=(self.game,), daemon=True).start()
        
        self._render_game_state(self.screen, self.game, self.game.dragger)
        self._render_game_over_overlay(self.screen, self.game)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._reset_game(self.game)
                elif event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self._save_pgn(self.game)
            elif event.type == pygame.QUIT:
                self._cleanup_and_exit()
    
    def _schedule_engine_move(self):
        """Schedule engine move if needed"""
        if (not self.game.dragger.dragging and 
            (not hasattr(self.game, 'engine_thread') or not self.game.engine_thread)):
            if ((self.game.next_player == 'white' and self.game.engine_white) or 
                (self.game.next_player == 'black' and self.game.engine_black)):
                self.game.schedule_engine_move()
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            self._handle_game_event(event, self.game, self.game.board, self.game.dragger)

    def _render_game_state(self, screen, game, dragger):
        """Render the main game state with modern styling"""
        game.show_bg(screen)
        game.show_last_move(screen)
        game.show_all_moves_hint(screen)  # Show all moves hint
        game.show_move_preview(screen)  # Show move preview before selected moves
        game.show_moves(screen)
        game.show_no_moves_feedback(screen)  # Show feedback for pieces with no moves
        game.show_check(screen)
        game.show_pieces(screen)
        game.show_hover(screen)
        
        # Show modern game info panel
        if self.show_game_info:
            self._render_modern_game_info(screen, game)
        
        # Show help overlay if requested
        if self.show_help:
            self._render_help_overlay(screen)

    def _render_modern_game_info(self, screen, game):
        """Render modern game information panel"""
        panel_width, panel_height = 320, 200
        panel_x, panel_y = WIDTH - panel_width - 20, 20
        
        self._draw_panel_background(screen, panel_x, panel_y, panel_width, panel_height)
        self._draw_panel_title(screen, panel_x, panel_y)
        self._draw_game_mode_info(screen, game, panel_x, panel_y)
        self._draw_engine_settings(screen, game, panel_x, panel_y)
        self._draw_current_player(screen, game, panel_x, panel_y)
        self._draw_control_hints(screen, game, panel_x, panel_y)
        self._draw_system_info(screen, panel_x, panel_y)
    
    def _draw_panel_background(self, screen, x, y, width, height):
        """Draw panel background with shadow"""
        shadow_surface = pygame.Surface((width + 8, height + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 60), pygame.Rect(0, 0, width + 8, height + 8), border_radius=15)
        screen.blit(shadow_surface, (x + 4, y + 4))
        
        panel_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, (40, 46, 58, 220), pygame.Rect(0, 0, width, height), border_radius=15)
        pygame.draw.rect(panel_surface, (84, 92, 108, 255), pygame.Rect(0, 0, width, height), 2, border_radius=15)
        screen.blit(panel_surface, (x, y))
    
    def _draw_panel_title(self, screen, x, y):
        """Draw panel title"""
        title_font = self._get_cached_font('Segoe UI', 18, bold=True)
        title_surface = title_font.render("Game Status", True, (255, 255, 255))
        screen.blit(title_surface, (x + 20, y + 15))
    
    def _draw_game_mode_info(self, screen, game, x, y):
        """Draw game mode information"""
        mode_text = {0: "Human vs Human", 1: "Human vs Engine", 2: "Engine vs Engine"}[game.game_mode]
        
        mode_font = self._get_cached_font('Segoe UI', 14, bold=True)
        mode_label = mode_font.render("Mode:", True, (181, 181, 181))
        screen.blit(mode_label, (x + 20, y + 45))
        
        mode_value_font = self._get_cached_font('Segoe UI', 14)
        mode_value_surface = mode_value_font.render(mode_text, True, (255, 255, 255))
        screen.blit(mode_value_surface, (x + 70, y + 45))
    
    def _draw_engine_settings(self, screen, game, x, y):
        """Draw engine settings if engines are active"""
        if game.engine_white or game.engine_black:
            settings_font = self._get_cached_font('Segoe UI', 13)
            
            level_label = settings_font.render("Level:", True, (181, 181, 181))
            screen.blit(level_label, (x + 20, y + 70))
            level_value = settings_font.render(f"{game.level}/20", True, (129, 182, 76))
            screen.blit(level_value, (x + 70, y + 70))
            
            depth_label = settings_font.render("Depth:", True, (181, 181, 181))
            screen.blit(depth_label, (x + 150, y + 70))
            depth_value = settings_font.render(str(game.depth), True, (129, 182, 76))
            screen.blit(depth_value, (x + 200, y + 70))
    
    def _draw_current_player(self, screen, game, x, y):
        """Draw current player indicator"""
        player_font = self._get_cached_font('Segoe UI', 14, bold=True)
        player_label = player_font.render("Turn:", True, (181, 181, 181))
        screen.blit(player_label, (x + 20, y + 100))
        
        player_color = (255, 255, 255) if game.next_player == 'white' else (200, 200, 200)
        player_surface = player_font.render(game.next_player.title(), True, player_color)
        screen.blit(player_surface, (x + 70, y + 100))
    
    def _draw_control_hints(self, screen, game, x, y):
        """Draw control hints"""
        hint_font = self._get_cached_font('Segoe UI', 12)
        
        hint_surface = hint_font.render("Press 'H' for controls", True, (129, 182, 76))
        screen.blit(hint_surface, (x + 20, y + 130))
        
        mode_hint = hint_font.render("1/2/3: Switch modes", True, (181, 181, 181))
        screen.blit(mode_hint, (x + 20, y + 150))
        
        if game.engine_white or game.engine_black:
            engine_hint = hint_font.render("+/-: Level, Ctrl+↑/↓: Depth", True, (181, 181, 181))
            screen.blit(engine_hint, (x + 20, y + 170))
    
    def _draw_system_info(self, screen, x, y):
        """Draw system information"""
        from threading import active_count
        from os import cpu_count
        
        info_font = self._get_cached_font('Segoe UI', 11)
        thread_surface = info_font.render(f"Threads: {active_count()}", True, (100, 149, 237))
        screen.blit(thread_surface, (x + 200, y + 170))
        
        cpu_surface = info_font.render(f"Cores: {cpu_count() or 4}", True, (255, 165, 0))
        screen.blit(cpu_surface, (x + 200, y + 185))
    
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
            ("Ctrl+S", "Quick save PGN (no dialogs)"),
            ("Shift+S", "Save PGN with dialog"),
            ("", ""),
            ("Professional Draw System:", ""),
            ("Ctrl+D", "Offer draw"),
            ("Ctrl+A", "Accept draw offer"),
            ("Ctrl+X", "Decline draw offer"),
            ("Ctrl+C", "Claim available draw"),
            ("", ""),
            ("Chess.com Style Controls:", ""),
            ("Left Click", "Select piece (if has moves) / Make move"),
            ("Right Click", "Preview piece moves"),
            ("ESC", "Deselect piece"),
            ("SPACE", "Show all movable pieces"),

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
    
    def _reset_game(self, game):
        """Reset the game"""
        try:
            game.reset()
            self.pgn_save_offered = False  # Reset PGN save flag for new game
        except AttributeError as e:
            print(f"Game state error resetting: {e}")
        except Exception as e:
            print(f"Unexpected error resetting: {e}")
    
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
            
        except AttributeError as e:
            print(f"Resource cleanup error: {e}")
        except Exception as e:
            print(f"Unexpected cleanup error: {e}")
        finally:
            pygame.quit()
            sys.exit()
    
    def _handle_game_event(self, event, game, board, dragger):
        """Handle game events with enhanced click-to-move functionality"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Debounce clicks to prevent double-clicking issues
            current_time = pygame.time.get_ticks()
            if current_time - self.last_click_time < self.click_debounce:
                return False
            self.last_click_time = current_time
            
            # Only allow human moves when it's not engine's turn
            is_engine_turn = (game.next_player == 'white' and game.engine_white) or \
                           (game.next_player == 'black' and game.engine_black)
            
            if not is_engine_turn:
                clicked_row = event.pos[1] // SQSIZE
                clicked_col = event.pos[0] // SQSIZE
                
                # Check if click is within the board
                if 0 <= clicked_row < 8 and 0 <= clicked_col < 8:
                    square = board.squares[clicked_row][clicked_col]
                    
                    # Handle right-click for move preview
                    if event.button == 3:  # Right click
                        if square.has_piece() and square.piece.color == game.next_player:
                            self._show_move_preview(game, board, square, clicked_row, clicked_col)
                        return False
                    
                    # Handle left-click for selection and moves
                    elif event.button == 1:  # Left click
                        # If no piece is selected
                        if not dragger.dragging:
                            # Select piece if it belongs to current player
                            if square.has_piece() and square.piece.color == game.next_player:
                                self._select_piece(game, board, dragger, square, clicked_row, clicked_col)
                        
                        # If a piece is already selected
                        else:
                            # If clicking on same square, deselect
                            if clicked_row == dragger.initial_row and clicked_col == dragger.initial_col:
                                self._deselect_piece(dragger)
                            
                            # If clicking on another piece of same color, select it instead
                            elif square.has_piece() and square.piece.color == game.next_player:
                                self._select_piece(game, board, dragger, square, clicked_row, clicked_col)
                            
                            # If clicking on opponent piece or empty square, try to move
                            else:
                                self._attempt_move(game, board, dragger, clicked_row, clicked_col)
                
                # If clicking outside board, deselect piece
                else:
                    if dragger.dragging:
                        self._deselect_piece(dragger)
        
        elif event.type == pygame.MOUSEMOTION:
            # Handle hover effects for pieces (no dragging in chess.com style)
            motion_row = event.pos[1] // SQSIZE
            motion_col = event.pos[0] // SQSIZE
            game.set_hover(motion_row, motion_col)
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            # No action needed for click-to-move style
            pass
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                game.change_theme()
            elif event.key == pygame.K_r:
                self._reset_game(game)
            
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
            
            # Click-to-move enhancements
            elif event.key == pygame.K_ESCAPE:
                # Deselect piece with Escape key
                if dragger.dragging:
                    self._deselect_piece(dragger)
            elif event.key == pygame.K_SPACE:
                # Show all possible moves for current player's pieces
                self._show_all_moves_hint(game, board)
            
            # PGN save shortcuts
            elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+S for quick save (no dialogs)
                self._quick_save_pgn(game)
            elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LSHIFT]:
                # Shift+S for save with dialog
                self._save_pgn(game)
            
            # Draw management shortcuts
            elif event.key == pygame.K_d and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+D to offer draw
                self._offer_draw(game)
            elif event.key == pygame.K_a and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+A to accept draw
                self._accept_draw(game)
            elif event.key == pygame.K_x and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+X to decline draw
                self._decline_draw(game)
            elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                # Ctrl+C to claim draw
                self._claim_draw(game)
            
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
    
    def _select_piece(self, game, board, dragger, square, row, col):
        """Select a piece and calculate its possible moves (chess.com style)"""
        # Calculate possible moves for the piece
        board.calc_moves(square.piece, row, col, bool=True)
        
        # Only select the piece if it has valid moves (chess.com behavior)
        if square.piece.moves:
            # Select the piece using the new method
            dragger.select_piece(square.piece, row, col)
            
            # Play selection sound if available
            if hasattr(game, 'sound_manager') and game.sound_manager:
                game.sound_manager.play_select()
        else:
            # Piece has no valid moves - don't select it
            # Optionally provide visual feedback
            self._show_no_moves_feedback(row, col)
    
    def _deselect_piece(self, dragger):
        """Deselect the currently selected piece"""
        dragger.deselect_piece()
    
    def _attempt_move(self, game, board, dragger, target_row, target_col):
        """Attempt to move the selected piece to the target square"""
        try:
            initial = Square(dragger.initial_row, dragger.initial_col)
            final = Square(target_row, target_col)
            move = Move(initial, final)
            
            # Check if the move is valid
            if board.valid_move(dragger.piece, move):
                # Make the move
                game.make_move(dragger.piece, move)
                # Deselect the piece
                dragger.deselect_piece()
            else:
                # Invalid move - provide visual feedback
                self._show_invalid_move_feedback(target_row, target_col)
                # Keep piece selected for another attempt
        except (AttributeError, IndexError) as e:
            print(f"Move validation error: {e}")
            dragger.deselect_piece()
        except Exception as e:
            print(f"Unexpected move error: {e}")
            dragger.deselect_piece()
    
    def _show_invalid_move_feedback(self, row, col):
        """Show visual feedback for invalid moves"""
        if not hasattr(self.game, 'invalid_move_feedback'):
            self.game.invalid_move_feedback = {}
        
        self.game.invalid_move_feedback = {
            'row': row,
            'col': col,
            'timestamp': pygame.time.get_ticks(),
            'duration': 300
        }
    
    def _show_no_moves_feedback(self, row, col):
        """Show visual feedback when a piece has no valid moves"""
        # Store feedback state for visual rendering
        if not hasattr(self.game, 'no_moves_feedback'):
            self.game.no_moves_feedback = {}
        
        self.game.no_moves_feedback = {
            'row': row,
            'col': col,
            'timestamp': pygame.time.get_ticks(),
            'duration': 500  # Show feedback for 500ms
        }
    
    def _show_move_preview(self, game, board, square, row, col):
        """Show move preview for right-clicked piece (temporary highlight)"""
        # Calculate moves for the piece
        board.calc_moves(square.piece, row, col, bool=True)
        
        # Store the preview state temporarily
        if not hasattr(game, 'move_preview'):
            game.move_preview = {}
        
        game.move_preview = {
            'piece': square.piece,
            'row': row,
            'col': col,
            'timestamp': pygame.time.get_ticks()
        }
    
    def _show_all_moves_hint(self, game, board):
        """Show hint highlighting all pieces that can move"""
        if not hasattr(game, 'all_moves_hint'):
            game.all_moves_hint = {}
        
        # Find all pieces that can move for current player
        movable_pieces = []
        for row in range(8):
            for col in range(8):
                square = board.squares[row][col]
                if square.has_piece() and square.piece.color == game.next_player:
                    # Calculate moves for this piece
                    board.calc_moves(square.piece, row, col, bool=True)
                    if square.piece.moves:  # If piece has valid moves
                        movable_pieces.append((row, col, square.piece))
        
        game.all_moves_hint = {
            'pieces': movable_pieces,
            'timestamp': pygame.time.get_ticks()
        }
    
    def _save_pgn(self, game):
        """Save PGN with user dialog (non-blocking)"""
        try:
            if game.pgn.get_move_count() == 0:
                print("No moves to save")
                return
            
            success = game.pgn.save_game()
            if success:
                print("✅ PGN save started (background)")
            else:
                print("❌ PGN save cancelled or failed")
        except (IOError, OSError) as e:
            print(f"File error saving PGN: {e}")
        except ValueError as e:
            print(f"Invalid data error saving PGN: {e}")
        except Exception as e:
            print(f"Unexpected error saving PGN: {e}")
    
    def _quick_save_pgn(self, game):
        """Quick save PGN without dialogs (non-blocking)"""
        try:
            if game.pgn.get_move_count() == 0:
                print("No moves to save")
                return
            
            success = game.pgn.save_game_quick()
            if success:
                print("✅ Quick save started (background)")
            else:
                print("❌ Quick save failed")
        except (IOError, OSError) as e:
            print(f"File error quick saving PGN: {e}")
        except ValueError as e:
            print(f"Invalid data error quick saving PGN: {e}")
        except Exception as e:
            print(f"Unexpected error quick saving PGN: {e}")
    
    def _offer_draw(self, game):
        """Offer a draw"""
        try:
            if game.game_over:
                print("Cannot offer draw - game is over")
                return
            
            current_player = game.next_player
            success = game.offer_draw(current_player)
            if success:
                print(f"🤝 Draw offered by {current_player}")
            else:
                print("❌ Cannot offer draw at this time")
        except AttributeError as e:
            print(f"Game state error offering draw: {e}")
        except Exception as e:
            print(f"Unexpected error offering draw: {e}")
    
    def _accept_draw(self, game):
        """Accept a draw offer"""
        try:
            if not game.draw_offered:
                print("No draw offer to accept")
                return
            
            current_player = game.next_player
            success = game.accept_draw(current_player)
            if success:
                print(f"🤝 Draw accepted by {current_player}")
            else:
                print("❌ Cannot accept draw")
        except AttributeError as e:
            print(f"Game state error accepting draw: {e}")
        except Exception as e:
            print(f"Unexpected error accepting draw: {e}")
    
    def _decline_draw(self, game):
        """Decline a draw offer"""
        try:
            if not game.draw_offered:
                print("No draw offer to decline")
                return
            
            current_player = game.next_player
            success = game.decline_draw(current_player)
            if success:
                print(f"❌ Draw declined by {current_player}")
            else:
                print("Cannot decline draw")
        except AttributeError as e:
            print(f"Game state error declining draw: {e}")
        except Exception as e:
            print(f"Unexpected error declining draw: {e}")
    
    def _claim_draw(self, game):
        """Claim a draw (show available claims)"""
        try:
            claimable_draws = game.get_claimable_draws()
            if not claimable_draws:
                print("No draws available to claim")
                return
            
            print("📋 Available draw claims:")
            for i, draw in enumerate(claimable_draws):
                print(f"  {i+1}. {game.draw_manager.get_draw_description(draw)}")
            
            # For now, claim the first available draw
            # In a full UI, this would show a selection dialog
            if claimable_draws:
                from draw_manager import DrawType
                draw_type = claimable_draws[0].draw_type
                success = game.claim_draw(draw_type)
                if success:
                    print(f"⚖️ Draw claimed successfully")
                else:
                    print("❌ Failed to claim draw")
        except AttributeError as e:
            print(f"Game state error claiming draw: {e}")
        except ImportError as e:
            print(f"Module import error claiming draw: {e}")
        except Exception as e:
            print(f"Unexpected error claiming draw: {e}")
    
    def _offer_save_pgn(self, game):
        """Offer to save PGN when game ends (runs in separate thread)"""
        try:
            # Small delay to ensure game state is fully updated
            import time
            time.sleep(0.5)
            
            if game.pgn.get_move_count() > 0:
                game.pgn.save_game()
        except (IOError, OSError) as e:
            print(f"File error offering PGN save: {e}")
        except Exception as e:
            print(f"Unexpected error offering PGN save: {e}")

if __name__ == '__main__':
    app = ChessApplication()
    app.mainloop()