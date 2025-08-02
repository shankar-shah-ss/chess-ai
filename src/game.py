# game.py - Enhanced with modern analysis integration and improved threading
import pygame
import time
import queue
import threading
from threading import Thread, Lock
from const import *
from board import Board
from dragger import Dragger
from square import Square
from engine import ChessEngine
from move import Move
from piece import King, Pawn
from error_handling import safe_execute, validate_game_state, ErrorRecovery, monitor_performance
from thread_manager import thread_manager
from resource_manager import resource_manager

class EngineWorker(Thread):
    def __init__(self, game, fen, move_queue, engine=None):
        super().__init__()
        self.game = game
        self.fen = fen
        self.move_queue = move_queue
        self.engine = engine or game.engine  # Use specific engine or fallback
        self.daemon = True
        self.priority = threading.THREAD_PRIORITY_ABOVE_NORMAL if hasattr(threading, 'THREAD_PRIORITY_ABOVE_NORMAL') else None

    def run(self):
        try:
            # Validate FEN before using
            if not self.fen or len(self.fen.strip()) == 0:
                print("Invalid FEN provided to engine worker")
                return
                
            # Get best move from engine
            if not self.engine.set_position(self.fen):
                print("Failed to set position in engine worker")
                return
                
            uci_move = self.engine.get_best_move()
            
            if uci_move and len(uci_move) >= 4:
                col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
                try:
                    from_col = col_map[uci_move[0]]
                    from_row = 8 - int(uci_move[1])
                    to_col = col_map[uci_move[2]]
                    to_row = 8 - int(uci_move[3])
                    
                    # Validate coordinates
                    if (0 <= from_row < 8 and 0 <= from_col < 8 and 
                        0 <= to_row < 8 and 0 <= to_col < 8):
                        initial = Square(from_row, from_col)
                        final = Square(to_row, to_col)
                        self.move_queue.put(Move(initial, final))
                    else:
                        print(f"Invalid move coordinates: {uci_move}")
                except (KeyError, ValueError, IndexError) as e:
                    print(f"Error parsing UCI move {uci_move}: {e}")
            else:
                print(f"Invalid UCI move received: {uci_move}")
        except Exception as e:
            print(f"Engine worker error: {e}")
            import traceback
            traceback.print_exc()

class EvaluationWorker(Thread):
    def __init__(self, game, fen, engine=None):
        super().__init__()
        self.game = game
        self.fen = fen
        self.engine = engine or game.engine  # Use specific engine or fallback
        self.evaluation = None
        self.daemon = True

    def run(self):
        try:
            # Validate FEN before using
            if not self.fen or len(self.fen.strip()) == 0:
                print("Invalid FEN provided to evaluation worker")
                self.evaluation = None
                return
                
            # Get evaluation from engine
            if not self.engine.set_position(self.fen):
                print("Failed to set position in evaluation worker")
                self.evaluation = None
                return
                
            self.evaluation = self.engine.get_evaluation()
            if self.evaluation is None:
                print("Engine returned None evaluation")
        except Exception as e:
            print(f"Evaluation worker error: {e}")
            import traceback
            traceback.print_exc()
            self.evaluation = None

class EngineConfigWorker(Thread):
    """
    Background thread for engine configuration to prevent UI freezing.
    
    This worker handles engine depth and skill level changes in a separate thread,
    ensuring the main UI remains responsive even when configuring high-depth engines.
    Supports cancellation for rapid setting changes.
    """
    def __init__(self, game, config_type, value):
        super().__init__()
        self.game = game
        self.config_type = config_type  # 'depth' or 'level'
        self.value = value
        self.daemon = True
        self._stop_requested = False

    def stop(self):
        """Request the worker to stop"""
        self._stop_requested = True

    def run(self):
        try:
            # Small delay to allow for rapid key presses to settle
            time.sleep(0.1)
            
            # Check if we should still proceed
            if self._stop_requested:
                return
                
            if self.config_type == 'depth':
                if self.game.engine_white_instance:
                    self.game.engine_white_instance.set_depth(self.value)
                if self.game.engine_black_instance:
                    self.game.engine_black_instance.set_depth(self.value)
                print(f"✓ Both engines depth set to {self.value}")
            elif self.config_type == 'level':
                if self.game.engine_white_instance:
                    self.game.engine_white_instance.set_skill_level(self.value)
                if self.game.engine_black_instance:
                    self.game.engine_black_instance.set_skill_level(self.value)
                print(f"✓ Both engines skill level set to {self.value}")
        except Exception as e:
            print(f"Engine config worker error: {e}")

class Game:
    def __init__(self):
        self.next_player = 'white'
        self.hovered_sqr = None
        self.board = Board()
        self.dragger = Dragger()
        # Theme system with multiple themes
        from theme import Theme
        from color import Color
        self.themes = [
            Theme(  # Classic
                light_bg=(240, 217, 181),
                dark_bg=(181, 136, 99),
                light_trace=(246, 246, 130),
                dark_trace=(186, 202, 68),
                light_moves=(249, 249, 249),
                dark_moves=(119, 154, 88)
            ),
            Theme(  # Blue
                light_bg=(222, 227, 230),
                dark_bg=(140, 162, 173),
                light_trace=(206, 210, 107),
                dark_trace=(169, 162, 58),
                light_moves=(255, 255, 255),
                dark_moves=(100, 149, 237)
            ),
            Theme(  # Green
                light_bg=(238, 238, 210),
                dark_bg=(118, 150, 86),
                light_trace=(255, 255, 104),
                dark_trace=(180, 180, 0),
                light_moves=(255, 255, 255),
                dark_moves=(34, 139, 34)
            )
        ]
        self.current_theme = 0
        self.config = type('Config', (), {
            'theme': self.themes[self.current_theme],
            'font': pygame.font.SysFont('Arial', 14),
            'move_sound': None,
            'capture_sound': None,
            'check_sound': None
        })()
        
        # Enhanced error handling and monitoring
        self._error_recovery = ErrorRecovery()
        self._last_validation = time.time()
        
        # Engine controls
        self.engine_white = False
        self.engine_black = False
        
        # Create separate engines for white and black with multi-core optimization
        self.engine_creation_lock = Lock()
        import os
        cpu_count = os.cpu_count() or 4
        try:
            # Initialize engines with optimized settings
            self.engine_white_instance = ChessEngine()
            self.engine_black_instance = ChessEngine()
            self.engine = self.engine_white_instance  # Default for compatibility
            print(f"✓ Chess engines initialized for {cpu_count} CPU cores")
        except Exception as e:
            print(f"✗ Failed to initialize chess engines: {e}")
            self.engine_white_instance = None
            self.engine_black_instance = None
            self.engine = None
        
        self.depth = 15
        self.level = 10
        self.game_mode = 0
        self.evaluation = None
        self.evaluation_lock = Lock()
        
        # Game state
        self.game_over = False
        self.winner = None
        self.check_alert = None
        self.move_history = []  # Track move history for analysis
        self.draw_offered = False  # Track if a draw has been offered
        self.draw_offer_by = None  # Track who offered the draw
        self.draw_accepted = False  # Track if draw was accepted by mutual agreement
        

        
        # Threading with proper cleanup
        self.engine_thread = None
        self.evaluation_thread = None
        self.config_thread = None
        self.engine_move_queue = queue.Queue(maxsize=10)  # Prevent unbounded growth
        self.thread_cleanup_lock = Lock()
        
        # Performance tracking
        self.last_evaluation_time = 0
        self.evaluation_interval = 5.0  # Much longer interval for smoothness

    # Game mode methods
    def set_game_mode(self, mode):
        """Set game mode and update engine settings"""
        self.game_mode = mode
        if mode == 0:  # Human vs Human
            self.engine_white = False
            self.engine_black = False
        elif mode == 1:  # Human vs Engine
            self.engine_white = False
            self.engine_black = True
        elif mode == 2:  # Engine vs Engine
            self.engine_white = True
            self.engine_black = True


    
    def _get_engine_for_player(self, player):
        """Get the correct engine instance for the given player"""
        with self.engine_creation_lock:
            if player == 'white':
                return self.engine_white_instance if self.engine_white_instance and self.engine_white_instance._is_healthy else None
            else:
                return self.engine_black_instance if self.engine_black_instance and self.engine_black_instance._is_healthy else None

    # Board rendering methods
    def show_bg(self, surface):
        """Render the chess board background with coordinates"""
        theme = self.config.theme
        
        for row in range(ROWS):
            for col in range(COLS):
                # Square color
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

                # Row coordinates (ranks)
                coord_color = (200, 200, 200)
                if col == 0:
                    lbl = self.config.font.render(str(ROWS-row), 1, coord_color)
                    lbl_pos = (5, 5 + row * SQSIZE)
                    surface.blit(lbl, lbl_pos)

                # Column coordinates (files)
                if row == 7:
                    lbl = self.config.font.render(Square.get_alphacol(col), 1, coord_color)
                    lbl_pos = (col * SQSIZE + 5, HEIGHT - 20)
                    surface.blit(lbl, lbl_pos)
        
        # Display game info
        self._render_game_status(surface)

    def _render_game_status(self, surface):
        """Render game status information"""
        display_width = WIDTH
        status_font = pygame.font.SysFont('Segoe UI', 14)
        
        # Game mode indicator
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine",
            2: "Engine vs Engine"
        }[self.game_mode]
        
        mode_surface = status_font.render(f"Mode: {mode_text}", True, (255, 255, 255))
        surface.blit(mode_surface, (display_width - 280, 10))
        
        # Engine info
        if self.engine_white or self.engine_black:
            engine_info = f"Engine Level: {self.level}/20 | Depth: {self.depth}"
            info_surface = status_font.render(engine_info, True, (200, 200, 200))
            surface.blit(info_surface, (display_width - 280, 35))
        
        # Current evaluation
        self._render_evaluation(surface, display_width - 280, 60)
        
        # Move counter
        if self.move_history:
            move_count = len(self.move_history)
            move_surface = status_font.render(f"Moves: {move_count}", True, (180, 180, 180))
            surface.blit(move_surface, (display_width - 280, 85))

    def _render_evaluation(self, surface, x, y):
        """Render current position evaluation"""
        with self.evaluation_lock:
            if self.evaluation and 'type' in self.evaluation and 'value' in self.evaluation:
                eval_font = pygame.font.SysFont('Segoe UI', 13)
                eval_type = self.evaluation['type']
                value = self.evaluation['value']
                
                if eval_type == 'cp':
                    score = value / 100.0
                    eval_text = f"Evaluation: {score:+.2f}"
                    eval_color = (100, 255, 100) if score > 0.5 else (255, 100, 100) if score < -0.5 else (255, 255, 255)
                else:  # mate
                    moves_to_mate = abs(value)
                    side = 'White' if value > 0 else 'Black'
                    eval_text = f"Mate in {moves_to_mate} for {side}"
                    eval_color = (100, 255, 100) if value > 0 else (255, 100, 100)
                
                eval_surface = eval_font.render(eval_text, True, eval_color)
                surface.blit(eval_surface, (x, y))

    def show_pieces(self, surface):
        """Render chess pieces on the board"""
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    
                    # Always draw all pieces - no hiding during selection
                    piece.set_texture(size=80)
                    try:
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)
                    except pygame.error:
                        # Fallback to simple colored circles if image loading fails
                        color = (255, 255, 255) if piece.color == 'white' else (0, 0, 0)
                        center = (col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2)
                        pygame.draw.circle(surface, color, center, SQSIZE // 3)
                        pygame.draw.circle(surface, (128, 128, 128), center, SQSIZE // 3, 2)

    def set_hover(self, row, col):
        """Set hovered square for visual feedback"""
        if 0 <= row < ROWS and 0 <= col < COLS:
            self.hovered_sqr = self.board.squares[row][col]
        else:
            self.hovered_sqr = None
    
    def show_moves(self, surface):
        """Show possible moves for the selected piece with chess.com-style highlighting"""
        if self.dragger.selected and self.dragger.piece:
            piece = self.dragger.piece
            
            # Chess.com-style selected piece highlighting
            selected_rect = (self.dragger.initial_col * SQSIZE, self.dragger.initial_row * SQSIZE, SQSIZE, SQSIZE)
            
            # Create a subtle background highlight for the selected square
            selected_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
            selected_surface.fill((255, 255, 0, 80))  # Yellow highlight
            surface.blit(selected_surface, selected_rect)
            
            # Draw a thick border around the selected piece (chess.com style)
            pygame.draw.rect(surface, (255, 255, 0), selected_rect, 4)  # Thick yellow border
            
            # Show possible moves with authentic chess.com-style indicators
            for move in piece.moves:
                move_col = move.final.col
                move_row = move.final.row
                move_rect = (move_col * SQSIZE, move_row * SQSIZE, SQSIZE, SQSIZE)
                center_x = move_col * SQSIZE + SQSIZE // 2
                center_y = move_row * SQSIZE + SQSIZE // 2
                
                # Check if target square has an opponent piece
                target_square = self.board.squares[move_row][move_col]
                has_opponent_piece = target_square.has_piece() and target_square.piece.color != piece.color
                
                if has_opponent_piece:
                    # For capture moves: draw a thick ring around the target square (chess.com style)
                    pygame.draw.circle(surface, (255, 70, 70), (center_x, center_y), SQSIZE // 2 - 3, 5)
                    # Add subtle capture highlight
                    capture_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    capture_surface.fill((255, 70, 70, 30))
                    surface.blit(capture_surface, move_rect)
                else:
                    # For regular moves: draw a solid dot in the center (chess.com style)
                    dot_radius = SQSIZE // 8
                    pygame.draw.circle(surface, (130, 130, 130), (center_x, center_y), dot_radius)
                    
                    # Add subtle move highlight
                    move_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    move_surface.fill((130, 130, 130, 25))
                    surface.blit(move_surface, move_rect)
    
    def show_no_moves_feedback(self, surface):
        """Show visual feedback for pieces with no valid moves"""
        if hasattr(self, 'no_moves_feedback') and self.no_moves_feedback:
            current_time = pygame.time.get_ticks()
            feedback = self.no_moves_feedback
            
            # Check if feedback should still be shown
            if current_time - feedback['timestamp'] < feedback['duration']:
                row, col = feedback['row'], feedback['col']
                feedback_rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                
                # Create a pulsing red effect
                elapsed = current_time - feedback['timestamp']
                alpha = int(100 * (1 - elapsed / feedback['duration']))  # Fade out
                
                feedback_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                feedback_surface.fill((255, 100, 100, alpha))
                surface.blit(feedback_surface, feedback_rect)
                
                # Red border
                pygame.draw.rect(surface, (255, 50, 50), feedback_rect, 3)
            else:
                # Clear expired feedback
                self.no_moves_feedback = None
    
    def show_move_preview(self, surface):
        """Show temporary move preview for right-clicked pieces"""
        if hasattr(self, 'move_preview') and self.move_preview:
            current_time = pygame.time.get_ticks()
            # Show preview for 2 seconds
            if current_time - self.move_preview['timestamp'] < 2000:
                piece = self.move_preview['piece']
                row = self.move_preview['row']
                col = self.move_preview['col']
                
                # Highlight the piece with a blue border
                preview_rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, (100, 150, 255), preview_rect, 3)
                
                # Show moves with a different style (more subtle)
                for move in piece.moves:
                    move_col = move.final.col
                    move_row = move.final.row
                    center_x = move_col * SQSIZE + SQSIZE // 2
                    center_y = move_row * SQSIZE + SQSIZE // 2
                    
                    # Draw smaller, more subtle dots
                    dot_radius = SQSIZE // 8
                    pygame.draw.circle(surface, (100, 150, 255, 100), (center_x, center_y), dot_radius)
            else:
                # Clear expired preview
                self.move_preview = None
    
    def show_all_moves_hint(self, surface):
        """Show hint highlighting all pieces that can move"""
        if hasattr(self, 'all_moves_hint') and self.all_moves_hint:
            current_time = pygame.time.get_ticks()
            # Show hint for 3 seconds
            if current_time - self.all_moves_hint['timestamp'] < 3000:
                for row, col, piece in self.all_moves_hint['pieces']:
                    # Pulse effect for movable pieces
                    import math
                    pulse_intensity = abs(math.sin((current_time - self.all_moves_hint['timestamp']) * 0.01))
                    alpha = int(50 + pulse_intensity * 100)
                    
                    hint_rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                    hint_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    hint_surface.fill((255, 255, 0, alpha))  # Yellow pulsing highlight
                    surface.blit(hint_surface, hint_rect)
                    
                    # Add a subtle border
                    pygame.draw.rect(surface, (255, 255, 0, 150), hint_rect, 2)
            else:
                # Clear expired hint
                self.all_moves_hint = None
    
    def draw_move_arrow(self, surface, from_pos, to_pos, color=(100, 255, 100), width=4):
        """Draw an arrow from one position to another"""
        from_x = from_pos[1] * SQSIZE + SQSIZE // 2
        from_y = from_pos[0] * SQSIZE + SQSIZE // 2
        to_x = to_pos[1] * SQSIZE + SQSIZE // 2
        to_y = to_pos[0] * SQSIZE + SQSIZE // 2
        
        # Calculate arrow components
        import math
        dx = to_x - from_x
        dy = to_y - from_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length > 0:
            # Normalize direction
            dx /= length
            dy /= length
            
            # Shorten the arrow to not overlap with pieces
            margin = SQSIZE // 4
            start_x = from_x + dx * margin
            start_y = from_y + dy * margin
            end_x = to_x - dx * margin
            end_y = to_y - dy * margin
            
            # Draw main line
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)
            
            # Draw arrowhead
            arrow_length = 15
            arrow_angle = 0.5
            
            # Calculate arrowhead points
            head_x1 = end_x - arrow_length * math.cos(math.atan2(dy, dx) - arrow_angle)
            head_y1 = end_y - arrow_length * math.sin(math.atan2(dy, dx) - arrow_angle)
            head_x2 = end_x - arrow_length * math.cos(math.atan2(dy, dx) + arrow_angle)
            head_y2 = end_y - arrow_length * math.sin(math.atan2(dy, dx) + arrow_angle)
            
            # Draw arrowhead
            pygame.draw.polygon(surface, color, [(end_x, end_y), (head_x1, head_y1), (head_x2, head_y2)])

    def show_last_move(self, surface):
        """Highlight the last move made with squares and arrow"""
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            # Highlight squares
            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)
            
            # Draw arrow for the last move
            self.draw_move_arrow(surface, (initial.row, initial.col), (final.row, final.col), 
                               color=(255, 255, 100, 180), width=3)

    def show_hover(self, surface):
        """Show hover effect on squares with enhanced visual feedback"""
        if self.hovered_sqr:
            # Different hover colors based on context
            if self.dragger.dragging:
                # If a piece is selected, show different hover for valid moves
                piece = self.dragger.piece
                hovered_move = None
                
                # Check if hovered square is a valid move
                for move in piece.moves:
                    if move.final.row == self.hovered_sqr.row and move.final.col == self.hovered_sqr.col:
                        hovered_move = move
                        break
                
                if hovered_move:
                    # Valid move hover - green tint
                    color = (100, 255, 100, 80)
                    hover_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    hover_surface.fill(color)
                    rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
                    surface.blit(hover_surface, rect)
                    pygame.draw.rect(surface, (100, 255, 100), rect, width=3)
                else:
                    # Invalid move hover - subtle red tint
                    color = (255, 100, 100, 40)
                    hover_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    hover_surface.fill(color)
                    rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
                    surface.blit(hover_surface, rect)
            else:
                # Normal hover when no piece is selected
                if self.hovered_sqr.has_piece() and self.hovered_sqr.piece.color == self.next_player:
                    # Hovering over own piece - blue tint
                    color = (100, 150, 255, 60)
                    hover_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    hover_surface.fill(color)
                    rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
                    surface.blit(hover_surface, rect)
                    pygame.draw.rect(surface, (100, 150, 255), rect, width=2)
                else:
                    # General hover
                    color = (180, 180, 180, 40)
                    hover_surface = pygame.Surface((SQSIZE, SQSIZE), pygame.SRCALPHA)
                    hover_surface.fill(color)
                    rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
                    surface.blit(hover_surface, rect)
            
    def show_check(self, surface):
        """Highlight king in check"""
        if self.check_alert:
            king_pos = self._find_king_position(self.check_alert)
            if king_pos:
                row, col = king_pos
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, (255, 0, 0), rect, 5)

    def _find_king_position(self, color):
        """Find the position of the king of given color"""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col].piece
                if isinstance(piece, King) and piece.color == color:
                    return (row, col)
        return None

    # Game state methods
    def next_turn(self):
        """Switch to the next player"""
        self.next_player = 'white' if self.next_player == 'black' else 'black'
        self.check_alert = None

    def change_theme(self):
        """Change the board theme"""
        self.current_theme = (self.current_theme + 1) % len(self.themes)
        self.config.theme = self.themes[self.current_theme]

    def play_sound(self, captured=False):
        """Play move or capture sound"""
        try:
            if captured:
                self.config.capture_sound.play()
            else:
                self.config.move_sound.play()
        except:
            pass  # Handle missing sound files gracefully

    def reset(self):
        """Reset the game to initial state"""
        # Store current settings
        current_mode = self.game_mode
        current_level = self.level
        current_depth = self.depth
        
        # Reset game state
        self.__init__()
        
        # Restore settings
        self.game_mode = current_mode
        self.level = current_level  
        self.depth = current_depth
        self.set_game_mode(current_mode)
        # Use threaded methods to restore engine settings
        self.set_engine_level(current_level)
        self.set_engine_depth(current_depth)
        


    # Engine control methods
    def toggle_engine(self, color):
        """Toggle engine for specified color"""
        if color == 'white':
            self.engine_white = not self.engine_white
        elif color == 'black':
            self.engine_black = not self.engine_black
            
        # Update game mode based on engine settings
        if not self.engine_white and not self.engine_black:
            self.game_mode = 0
        elif self.engine_white and self.engine_black:
            self.game_mode = 2
        else:
            self.game_mode = 1

    def set_engine_depth(self, depth):
        """Set engine search depth (threaded to prevent UI freezing)"""
        with self.engine_creation_lock:
            if not self.engine_white_instance or not self.engine_black_instance:
                return
                
            self.depth = max(1, min(20, depth))
            
            # Stop any existing config thread
            if self.config_thread and self.config_thread.is_alive():
                self.config_thread.stop()
                
            # Start new config thread
            try:
                self.config_thread = EngineConfigWorker(self, 'depth', self.depth)
                self.config_thread.start()
            except Exception as e:
                print(f"Error setting engine depth: {e}")

    def set_engine_level(self, level):
        """Set engine skill level (threaded to prevent UI freezing)"""
        with self.engine_creation_lock:
            if not self.engine_white_instance or not self.engine_black_instance:
                return
                
            self.level = max(0, min(20, level))
            
            # Stop any existing config thread
            if self.config_thread and self.config_thread.is_alive():
                self.config_thread.stop()
                
            # Start new config thread
            try:
                self.config_thread = EngineConfigWorker(self, 'level', self.level)
                self.config_thread.start()
            except Exception as e:
                print(f"Error setting engine level: {e}")

    def increase_level(self):
        """Increase engine level"""
        self.set_engine_level(self.level + 1)

    def decrease_level(self):
        """Decrease engine level"""
        self.set_engine_level(self.level - 1)

    def schedule_evaluation(self):
        """Schedule position evaluation (throttled)"""
        # Skip evaluation in human vs human mode for maximum performance
        if self.game_mode == 0:
            return
            
        # Use white engine for evaluation (doesn't matter which one)
        engine = self._get_engine_for_player('white')
        if not engine:
            return
            
        current_time = time.time()
        if (not self.evaluation_thread and 
            current_time - self.last_evaluation_time > self.evaluation_interval):
            
            try:
                fen = self.board.to_fen(self.next_player)
                if fen and len(fen.strip()) > 0 and self._validate_fen(fen):
                    self.evaluation_thread = EvaluationWorker(self, fen, engine)
                    self.evaluation_thread.start()
                    self.last_evaluation_time = current_time
                else:
                    print("Invalid FEN generated, cannot schedule evaluation")
            except Exception as e:
                print(f"Error scheduling evaluation: {e}")

    def make_engine_move(self):
        """Process engine move from queue"""
        try:
            # Non-blocking get from queue
            move = self.engine_move_queue.get_nowait()
            if not move or not hasattr(move, 'initial') or not hasattr(move, 'final'):
                return False
                
            piece = self.board.squares[move.initial.row][move.initial.col].piece
            
            if piece and piece.color == self.next_player:
                captured = self.board.squares[move.final.row][move.final.col].has_piece()
                
                # Make the move
                self.make_move(piece, move)
                
                with self.thread_cleanup_lock:
                    self.engine_thread = None
                return True
        except queue.Empty:
            return False
        except Exception as e:
            print(f"Error making engine move: {e}")
            with self.thread_cleanup_lock:
                self.engine_thread = None
            return False

    def schedule_engine_move(self):
        """Schedule engine to calculate next move"""
        with self.thread_cleanup_lock:
            if not self.engine_thread and not self.game_over:
                # Get the correct engine for current player
                current_engine = self._get_engine_for_player(self.next_player)
                if not current_engine:
                    return
                    
                try:
                    fen = self.board.to_fen(self.next_player)
                    if fen and len(fen.strip()) > 0 and self._validate_fen(fen):
                        self.engine_thread = EngineWorker(self, fen, self.engine_move_queue, current_engine)
                        self.engine_thread.start()
                    else:
                        print("Invalid FEN generated, cannot schedule engine move")
                except Exception as e:
                    print(f"Error scheduling engine move: {e}")
            
    def check_game_state(self):
        """Check for game over conditions"""
        if self.game_over:
            return
            
        # Check for check
        if self.board.is_king_in_check(self.next_player):
            self.check_alert = self.next_player
            try:
                if self.config.check_sound:
                    self.config.check_sound.play()
            except:
                pass
            
        # Check for checkmate
        if self.board.is_checkmate(self.next_player):
            self.game_over = True
            self.winner = 'black' if self.next_player == 'white' else 'white'
            return
            
        # Check for stalemate
        if self.board.is_stalemate(self.next_player):
            self.game_over = True
            self.winner = None
            return
            
        # Check for threefold repetition
        if self.board.is_threefold_repetition():
            self.game_over = True
            self.winner = None
            return
            
        # Check for fifty-move rule
        if self.board.is_fifty_move_rule():
            self.game_over = True
            self.winner = None
            return
            
        # Check for insufficient material
        if self._is_insufficient_material():
            self.game_over = True
            self.winner = None
            
    def _is_insufficient_material(self):
        """Check for insufficient material to checkmate"""
        # Count pieces for both sides
        white_pieces = []
        black_pieces = []
        white_bishops = []
        black_bishops = []
        
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col].piece
                if piece:
                    if piece.color == 'white':
                        if piece.name.lower() != 'king':
                            white_pieces.append(piece.name.lower())
                            if piece.name.lower() == 'bishop':
                                # Track bishop square color (light or dark)
                                square_color = 'light' if (row + col) % 2 == 0 else 'dark'
                                white_bishops.append(square_color)
                    else:
                        if piece.name.lower() != 'king':
                            black_pieces.append(piece.name.lower())
                            if piece.name.lower() == 'bishop':
                                # Track bishop square color (light or dark)
                                square_color = 'light' if (row + col) % 2 == 0 else 'dark'
                                black_bishops.append(square_color)
        
        # King vs King
        if not white_pieces and not black_pieces:
            return True
            
        # King and Bishop vs King
        if (len(white_pieces) == 1 and not black_pieces and white_pieces[0] == 'bishop'):
            return True
        if (len(black_pieces) == 1 and not white_pieces and black_pieces[0] == 'bishop'):
            return True
            
        # King and Knight vs King
        if (len(white_pieces) == 1 and not black_pieces and white_pieces[0] == 'knight'):
            return True
        if (len(black_pieces) == 1 and not white_pieces and black_pieces[0] == 'knight'):
            return True
            
        # King and Bishop vs King and Bishop (same color squares)
        if (len(white_pieces) == 1 and len(black_pieces) == 1 and 
            white_pieces[0] == 'bishop' and black_pieces[0] == 'bishop'):
            if white_bishops[0] == black_bishops[0]:  # Same color squares
                return True
                
        return False
    
    def offer_draw(self, player):
        """Offer a draw by the specified player"""
        if not self.game_over:
            self.draw_offered = True
            self.draw_offer_by = player
            return True
        return False
    
    def accept_draw(self):
        """Accept the draw offer"""
        if self.draw_offered:
            self.game_over = True
            self.winner = None  # Draw
            self.draw_offered = False
            self.draw_offer_by = None
            self.draw_accepted = True  # Flag for mutual agreement
            return True
        return False
    
    def decline_draw(self):
        """Decline the draw offer"""
        self.draw_offered = False
        self.draw_offer_by = None
        return True
    
    def can_claim_draw(self):
        """Check if current player can claim a draw (threefold repetition or fifty-move rule)"""
        return self.board.is_threefold_repetition() or self.board.is_fifty_move_rule()
    
    def claim_draw(self):
        """Claim a draw based on rules (threefold repetition or fifty-move rule)"""
        if self.can_claim_draw():
            self.game_over = True
            self.winner = None
            return True
        return False
            
    def make_move(self, piece, move):
        """Make a move and record it for analysis"""
        # Check for special conditions before move
        captured = self.board.squares[move.final.row][move.final.col].has_piece()
        is_en_passant = (isinstance(piece, Pawn) and 
                        abs(move.initial.col - move.final.col) == 1 and 
                        self.board.squares[move.final.row][move.final.col].isempty() and
                        self.board.en_passant_target)
        captured = captured or is_en_passant
        
        # Get evaluation before move (if available)
        eval_before = self.evaluation.copy() if self.evaluation else None
        

        
        # Make the actual move
        self.board.move(piece, move)
        
        # Check for check/checkmate after move
        opponent_color = 'black' if piece.color == 'white' else 'white'
        is_check = self.board.is_king_in_check(opponent_color)
        is_checkmate = self.board.is_checkmate(opponent_color) if is_check else False
        
        # Get evaluation after move (if available)
        eval_after = None
        if self.evaluation:
            # Schedule new evaluation
            self.schedule_evaluation()
            eval_after = self.evaluation.copy()
        
        # Record move in history
        self.move_history.append({
            'move': move,
            'piece': piece.name,
            'color': piece.color,
            'captured': captured
        })
        
        # Clear any pending draw offer (draw offers expire after a move)
        self.draw_offered = False
        self.draw_offer_by = None
        
        self.play_sound(captured)
        self.next_turn()
        self.check_game_state()

    def _get_move_notation(self, move, piece):
        """Generate simple algebraic notation for move"""
        col_map = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        
        from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
        to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
        
        # Basic notation (can be enhanced later)
        notation = f"{piece.name[0] if piece.name != 'pawn' else ''}{from_square}{to_square}"
        
        return notation

    # Game over display
    def show_game_over(self, surface):
        """Display game over message"""
        if not self.game_over:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Game result
        font = pygame.font.SysFont('Segoe UI', 48, bold=True)
        if self.winner:
            text = f"{self.winner.title()} Wins!"
            color = (100, 255, 100) if self.winner == 'white' else (255, 100, 100)
        else:
            text = "Draw!"
            color = (255, 255, 255)
            
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        surface.blit(text_surface, text_rect)
        
        # Instructions
        instruction_font = pygame.font.SysFont('Segoe UI', 20)
        instructions = [
            "Press 'R' to restart"
        ]
        
        y_offset = HEIGHT//2 + 20
        for instruction in instructions:
            instruction_surface = instruction_font.render(instruction, True, (255, 255, 255))
            instruction_rect = instruction_surface.get_rect(center=(WIDTH//2, y_offset))
            surface.blit(instruction_surface, instruction_rect)
            y_offset += 35


    
    def _validate_fen(self, fen):
        """Validate FEN string"""
        try:
            import chess
            board = chess.Board(fen)
            return board.is_valid()
        except:
            return False
    
    @safe_execute(fallback_value=None, context="game_cleanup")
    def cleanup(self):
        """Enhanced cleanup with proper resource management"""
        with self.thread_cleanup_lock:
            # Stop and cleanup threads using thread manager
            if hasattr(self, 'engine_thread') and self.engine_thread:
                if hasattr(self.engine_thread, 'stop'):
                    self.engine_thread.stop()
                if self.engine_thread.is_alive():
                    self.engine_thread.join(timeout=2.0)
                self.engine_thread = None
                
            if hasattr(self, 'evaluation_thread') and self.evaluation_thread:
                if hasattr(self.evaluation_thread, 'stop'):
                    self.evaluation_thread.stop()
                if self.evaluation_thread.is_alive():
                    self.evaluation_thread.join(timeout=2.0)
                self.evaluation_thread = None
                
            if hasattr(self, 'config_thread') and self.config_thread:
                if hasattr(self.config_thread, 'stop'):
                    self.config_thread.stop()
                if self.config_thread.is_alive():
                    self.config_thread.join(timeout=2.0)
                self.config_thread = None
                
            # Clear queues safely
            try:
                while not self.engine_move_queue.empty():
                    self.engine_move_queue.get_nowait()
            except queue.Empty:
                pass
            
            # Cleanup engines
            if hasattr(self, 'engine_white_instance') and self.engine_white_instance:
                self.engine_white_instance.cleanup()
            if hasattr(self, 'engine_black_instance') and self.engine_black_instance:
                self.engine_black_instance.cleanup()
            

    
    @safe_execute(fallback_value=False, context="game_validation")
    def validate_game_state(self):
        """Enhanced game state validation"""
        current_time = time.time()
        
        # Throttle validation checks
        if current_time - self._last_validation < 1.0:
            return True
        
        self._last_validation = current_time
        
        try:
            # Validate board state
            if not self.board or not hasattr(self.board, 'squares'):
                return False
            
            # Check for kings
            king_count = {'white': 0, 'black': 0}
            for row in range(8):
                for col in range(8):
                    piece = self.board.squares[row][col].piece
                    if piece and isinstance(piece, King):
                        king_count[piece.color] += 1
            
            if king_count['white'] != 1 or king_count['black'] != 1:
                return False
            
            # Validate current player
            if self.next_player not in ['white', 'black']:
                return False
            
            return True
            
        except Exception as e:
            print(f"Game state validation error: {e}")
            return False
    
    @monitor_performance()
    def periodic_maintenance(self):
        """Perform periodic maintenance tasks"""
        try:
            # Validate game state
            if not self.validate_game_state():
                print("Game state validation failed, attempting recovery...")
                self._error_recovery.recover_game_state(self)
            
            # Check engine health
            if hasattr(self, 'engine_white_instance') and self.engine_white_instance:
                if not self.engine_white_instance._is_healthy:
                    print("White engine unhealthy, attempting recovery...")
                    self._error_recovery.recover_engine(self.engine_white_instance)
            
            if hasattr(self, 'engine_black_instance') and self.engine_black_instance:
                if not self.engine_black_instance._is_healthy:
                    print("Black engine unhealthy, attempting recovery...")
                    self._error_recovery.recover_engine(self.engine_black_instance)
            
            # Cleanup resources if needed
            stats = resource_manager.get_cache_stats()
            total_cached = sum(stats.values())
            if total_cached > 100:  # Arbitrary threshold
                resource_manager.cleanup_cache("images")
            
            # Check thread count
            thread_stats = thread_manager.get_stats()
            if thread_stats['active_threads'] > 15:
                thread_manager.cancel_all_tasks()
                
        except Exception as e:
            print(f"Maintenance error: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass