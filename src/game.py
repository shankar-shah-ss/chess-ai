# [file name]: game.py
# [file content begin]
import pygame
import time
from threading import Thread
from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square
from engine import ChessEngine
from move import Move
from piece import King

class EngineWorker(Thread):
    def __init__(self, game, fen):
        super().__init__()
        self.game = game
        self.fen = fen
        self.move = None

    def run(self):
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
                self.move = Move(initial, final)
            except (KeyError, ValueError):
                pass

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
        
        # Game state
        self.game_over = False
        self.winner = None
        self.check_alert = None
        
        # Threading
        self.engine_thread = None
        self.pending_engine_move = None

    # Game mode methods
    def set_game_mode(self, mode):
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

    # blit methods
    def show_bg(self, surface):
        theme = self.config.theme
        
        for row in range(ROWS):
            for col in range(COLS):
                # color
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                # rect
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                # blit
                pygame.draw.rect(surface, color, rect)

                # row coordinates
                coord_color = (200, 200, 200)  # Light gray
                if col == 0:
                    # label
                    lbl = self.config.font.render(str(ROWS-row), 1, coord_color)
                    lbl_pos = (5, 5 + row * SQSIZE)
                    # blit
                    surface.blit(lbl, lbl_pos)

                # col coordinates
                if row == 7:
                    # label
                    lbl = self.config.font.render(Square.get_alphacol(col), 1, coord_color)
                    lbl_pos = (col * SQSIZE + 5, HEIGHT - 20)
                    # blit
                    surface.blit(lbl, lbl_pos)
        
        # Display game mode
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine",
            2: "Engine vs Engine"
        }[self.game_mode]
        
        mode_surface = self.config.font.render(mode_text, True, (255, 255, 255))
        surface.blit(mode_surface, (WIDTH - 250, 10))
        
        # Display controls info
        controls = "1: HvH, 2: HvE, 3: EvE"
        ctrl_surface = self.config.font.render(controls, True, (255, 255, 255))
        surface.blit(ctrl_surface, (WIDTH - 250, 40))
        
        # Display engine info
        engine_info = f"Level: {self.level}, Depth: {self.depth}"
        info_surface = self.config.font.render(engine_info, True, (255, 255, 255))
        surface.blit(info_surface, (WIDTH - 250, 70))
        
        # Display evaluation if available
        if self.evaluation and 'type' in self.evaluation and 'value' in self.evaluation:
            eval_type = self.evaluation['type']
            value = self.evaluation['value']
            
            if eval_type == 'cp':
                score = value / 100.0
                eval_text = f"Eval: {score:+.2f}"
            else:  # mate
                moves_to_mate = abs(value)
                eval_text = f"Mate in {moves_to_mate} for {'white' if value > 0 else 'black'}"
            
            eval_surface = self.config.font.render(eval_text, True, (255, 255, 255))
            surface.blit(eval_surface, (WIDTH - 250, 100))

        # Display level info
        level_info = f"Level: {self.level}"
        level_surface = self.config.font.render(level_info, True, (255, 255, 255))
        surface.blit(level_surface, (WIDTH - 150, 40))
        
        # Display game over message
        if self.game_over:
            font = pygame.font.SysFont('monospace', 40, bold=True)
            if self.winner:
                text = f"{self.winner.capitalize()} wins!"
            else:
                text = "Draw!"
            text_surface = font.render(text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            surface.blit(text_surface, text_rect)
            
            restart_font = pygame.font.SysFont('monospace', 24)
            restart_text = "Press 'R' to restart"
            restart_surface = restart_font.render(restart_text, True, (255, 255, 255))
            restart_rect = restart_surface.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            surface.blit(restart_surface, restart_rect)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    
                    if piece is not self.dragger.piece:
                        piece.set_texture(size=80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def set_hover(self, row, col):
        if 0 <= row < ROWS and 0 <= col < COLS:
            self.hovered_sqr = self.board.squares[row][col]
        else:
            self.hovered_sqr = None
    
    def show_moves(self, surface):
        theme = self.config.theme

        if self.dragger.dragging:
            piece = self.dragger.piece

            for move in piece.moves:
                color = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 else theme.moves.dark
                rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        if self.hovered_sqr:
            color = (180, 180, 180)
            rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
            pygame.draw.rect(surface, color, rect, width=3)
            
    def show_check(self, surface):
        if self.check_alert:
            king_pos = None
            for row in range(ROWS):
                for col in range(COLS):
                    piece = self.board.squares[row][col].piece
                    if isinstance(piece, King) and piece.color == self.check_alert:
                        king_pos = (row, col)
                        break
                if king_pos:
                    break
                    
            if king_pos:
                row, col = king_pos
                rect = (col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE)
                pygame.draw.rect(surface, (255, 0, 0), rect, 5)

    # other methods
    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'
        self.check_alert = None

    def change_theme(self):
        self.config.change_theme()

    def play_sound(self, captured=False):
        if captured:
            self.config.capture_sound.play()
        else:
            self.config.move_sound.play()

    def reset(self):
        self.__init__()

    # Engine control methods
    def toggle_engine(self, color):
        if color == 'white':
            self.engine_white = not self.engine_white
        elif color == 'black':
            self.engine_black = not self.engine_black
        if not self.engine_white and not self.engine_black:
            self.game_mode = 0
        elif self.engine_white and self.engine_black:
            self.game_mode = 2
        else:
            self.game_mode = 1

    def set_engine_depth(self, depth):
        self.depth = depth
        self.engine.set_depth(depth)

    def set_engine_level(self, level):
        self.level = level
        self.engine.set_skill_level(level)

    def get_engine_evaluation(self):
        fen = self.board.to_fen(self.next_player)
        self.engine.set_position(fen)
        self.evaluation = self.engine.get_evaluation()
        return self.evaluation

    def make_engine_move(self):
        if self.pending_engine_move:
            move = self.pending_engine_move
            piece = self.board.squares[move.initial.row][move.initial.col].piece
            captured = self.board.squares[move.final.row][move.final.col].has_piece()
            
            self.board.move(piece, move)
            self.board.set_true_en_passant(piece)
            self.play_sound(captured)
            self.next_turn()
            self.check_game_state()
            
            self.pending_engine_move = None
            self.engine_thread = None
            return True
        return False

    def schedule_engine_move(self):
        if not self.engine_thread and not self.pending_engine_move:
            fen = self.board.to_fen(self.next_player)
            self.engine_thread = EngineWorker(self, fen)
            self.engine_thread.start()

    def increase_level(self):
        self.level = min(20, self.level + 1)
        self.engine.set_skill_level(self.level)

    def decrease_level(self):
        self.level = max(0, self.level - 1)
        self.engine.set_skill_level(self.level)
        
    def check_game_state(self):
        if self.game_over:
            return
            
        if self.board.is_king_in_check(self.next_player):
            self.check_alert = self.next_player
            if self.config.check_sound:
                self.config.check_sound.play()
            
        if self.board.is_checkmate(self.next_player):
            self.game_over = True
            self.winner = 'black' if self.next_player == 'white' else 'white'
            return
            
        if self.board.is_stalemate(self.next_player):
            self.game_over = True
            self.winner = None
            return
            
        if self.board.is_threefold_repetition():
            self.game_over = True
            self.winner = None
# [file content end]