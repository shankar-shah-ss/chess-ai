# game.py - Updated with Enhanced Analysis Integration
import pygame
import time
import queue
from threading import Thread, Lock
from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square
from engine import ChessEngine
from move import Move
from piece import King

class EngineWorker(Thread):
    def __init__(self, game, fen, move_queue):
        super().__init__()
        self.game = game
        self.fen = fen
        self.move_queue = move_queue
        self.daemon = True

    def run(self):
        try:
            # Get best move from engine
            self.game.engine.set_position(self.fen)
            uci_move = self.game.engine.get_best_move()
            
            if uci_move:
                col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
                try:
                    from_col = col_map[uci_move[0]]
                    from_row = 8 - int(uci_move[1])
                    to_col = col_map[uci_move[2]]
                    to_row = 8 - int(uci_move[3])
                    
                    initial = Square(from_row, from_col)
                    final = Square(to_row, to_col)
                    self.move_queue.put(Move(initial, final))
                except (KeyError, ValueError, IndexError):
                    pass
        except Exception as e:
            print(f"Engine worker error: {e}")

class EvaluationWorker(Thread):
    def __init__(self, game, fen):
        super().__init__()
        self.game = game
        self.fen = fen
        self.evaluation = None
        self.daemon = True

    def run(self):
        try:
            # Get evaluation from engine
            self.game.engine.set_position(self.fen)
            self.evaluation = self.game.engine.get_evaluation()
        except Exception as e:
            print(f"Evaluation worker error: {e}")
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
                self.game.engine.set_depth(self.value)
                print(f"✓ Engine depth set to {self.value}")
            elif self.config_type == 'level':
                self.game.engine.set_skill_level(self.value)
                print(f"✓ Engine skill level set to {self.value}")
        except Exception as e:
            print(f"Engine config worker error: {e}")

class Game:
    def __init__(self):
        self.next_player = 'white'
        self.hovered_sqr = None
        self.board = Board()
        self.dragger = Dragger()
        self.config = Config()
        
        # Engine controls
        self.engine_white = False
        self.engine_black = False
        self.engine = ChessEngine()
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
        
        # Analysis manager (will be set by main)
        self.analysis_manager = None
        
        # Threading
        self.engine_thread = None
        self.evaluation_thread = None
        self.config_thread = None
        self.engine_move_queue = queue.Queue()
        
        # Performance tracking
        self.last_evaluation_time = 0
        self.evaluation_interval = 0.5  # Minimum time between evaluations

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

    def set_analysis_manager(self, analysis_manager):
        """Set the analysis manager"""
        self.analysis_manager = analysis_manager

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
        
        # Display game info only if not in analysis mode
        if not (self.analysis_manager and self.analysis_manager.active):
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
                    
                    # Don't draw the piece being dragged
                    if piece is not self.dragger.piece:
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
        """Show possible moves for the selected piece"""
        theme = self.config.theme

        if self.dragger.dragging:
            piece = self.dragger.piece
            for move in piece.moves:
                color = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 else theme.moves.dark
                rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        """Highlight the last move made"""
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        """Show hover effect on squares"""
        if self.hovered_sqr:
            color = (180, 180, 180)
            rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
            pygame.draw.rect(surface, color, rect, width=3)
            
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
        self.config.change_theme()

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
        self.depth = max(1, min(20, depth))
        
        # Stop any existing config thread
        if self.config_thread and self.config_thread.is_alive():
            self.config_thread.stop()
            
        # Start new config thread
        self.config_thread = EngineConfigWorker(self, 'depth', self.depth)
        self.config_thread.start()

    def set_engine_level(self, level):
        """Set engine skill level (threaded to prevent UI freezing)"""
        self.level = max(0, min(20, level))
        
        # Stop any existing config thread
        if self.config_thread and self.config_thread.is_alive():
            self.config_thread.stop()
            
        # Start new config thread
        self.config_thread = EngineConfigWorker(self, 'level', self.level)
        self.config_thread.start()

    def increase_level(self):
        """Increase engine level"""
        self.set_engine_level(self.level + 1)

    def decrease_level(self):
        """Decrease engine level"""
        self.set_engine_level(self.level - 1)

    def schedule_evaluation(self):
        """Schedule position evaluation (throttled)"""
        current_time = time.time()
        if (not self.evaluation_thread and 
            current_time - self.last_evaluation_time > self.evaluation_interval):
            
            fen = self.board.to_fen(self.next_player)
            self.evaluation_thread = EvaluationWorker(self, fen)
            self.evaluation_thread.start()
            self.last_evaluation_time = current_time

    def make_engine_move(self):
        """Process engine move from queue"""
        try:
            # Non-blocking get from queue
            move = self.engine_move_queue.get_nowait()
            piece = self.board.squares[move.initial.row][move.initial.col].piece
            
            if piece and piece.color == self.next_player:
                captured = self.board.squares[move.final.row][move.final.col].has_piece()
                
                # Make the move
                self.make_move(piece, move)
                
                self.engine_thread = None
                return True
        except queue.Empty:
            return False
        except Exception as e:
            print(f"Error making engine move: {e}")
            self.engine_thread = None
            return False

    def schedule_engine_move(self):
        """Schedule engine to calculate next move"""
        if not self.engine_thread and not self.game_over:
            fen = self.board.to_fen(self.next_player)
            self.engine_thread = EngineWorker(self, fen, self.engine_move_queue)
            self.engine_thread.start()
            
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
            
        # Check for insufficient material
        if self._is_insufficient_material():
            self.game_over = True
            self.winner = None
            
    def _is_insufficient_material(self):
        """Check for insufficient material to checkmate"""
        # Count pieces for both sides
        white_pieces = []
        black_pieces = []
        
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.squares[row][col].piece
                if piece:
                    if piece.color == 'white':
                        white_pieces.append(piece.name.lower())
                    else:
                        black_pieces.append(piece.name.lower())
        
        # Remove kings from count
        white_pieces = [p for p in white_pieces if p != 'king']
        black_pieces = [p for p in black_pieces if p != 'king']
        
        # King vs King
        if not white_pieces and not black_pieces:
            return True
            
        # King and Bishop/Knight vs King
        if (len(white_pieces) == 1 and not black_pieces and 
            white_pieces[0] in ['bishop', 'knight']):
            return True
            
        if (len(black_pieces) == 1 and not white_pieces and 
            black_pieces[0] in ['bishop', 'knight']):
            return True
            
        return False
            
    def make_move(self, piece, move):
        """Make a move and record it for analysis"""
        # Record position before move for analysis
        if self.analysis_manager:
            position_before = self.board.to_fen(piece.color)
            self.analysis_manager.record_move(move, piece.color, position_before)
        
        # Record move in history
        move_notation = self._get_move_notation(move, piece)
        self.move_history.append({
            'move': move,
            'piece': piece.name,
            'color': piece.color,
            'notation': move_notation,
            'captured': self.board.squares[move.final.row][move.final.col].has_piece()
        })
        
        # Make the actual move
        captured = self.board.squares[move.final.row][move.final.col].has_piece()
        self.board.move(piece, move)
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
            "Press 'R' to restart",
            "Press 'A' for analysis",
            "Press 'S' for summary"
        ]
        
        y_offset = HEIGHT//2 + 20
        for instruction in instructions:
            instruction_surface = instruction_font.render(instruction, True, (255, 255, 255))
            instruction_rect = instruction_surface.get_rect(center=(WIDTH//2, y_offset))
            surface.blit(instruction_surface, instruction_rect)
            y_offset += 35

    def cleanup(self):
        """Clean up resources"""
        # Wait for threads to complete
        if self.engine_thread and self.engine_thread.is_alive():
            self.engine_thread.join(timeout=1.0)
            
        if self.evaluation_thread and self.evaluation_thread.is_alive():
            self.evaluation_thread.join(timeout=1.0)
            
        # Clear queues
        try:
            while True:
                self.engine_move_queue.get_nowait()
        except queue.Empty:
            pass