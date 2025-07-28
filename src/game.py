# [file name]: game.py
# [file content begin]
import pygame
from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square
from engine import ChessEngine
from move import Move

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
        self.game_mode = 0  # 0: human vs human, 1: human vs engine, 2: engine vs engine
        self.evaluation = None  # Store the last evaluation

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
                    lbl_pos = (col * SQSIZE + 5, HEIGHT - 20)  # Left-aligned
                    # blit
                    surface.blit(lbl, lbl_pos)
        
        # Display game mode
        mode_text = {
            0: "Human vs Human",
            1: "Human vs Engine",
            2: "Engine vs Engine"
        }[self.game_mode]
        
        # Change text color to white and adjust position left
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
                # Convert centipawns to pawn advantage
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

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                # piece ?
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    
                    # all pieces except dragger piece
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

            # loop all valid moves
            for move in piece.moves:
                # color
                color = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 else theme.moves.dark
                # rect
                rect = (move.final.col * SQSIZE, move.final.row * SQSIZE, SQSIZE, SQSIZE)
                # blit
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                # color
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                # rect
                rect = (pos.col * SQSIZE, pos.row * SQSIZE, SQSIZE, SQSIZE)
                # blit
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        if self.hovered_sqr:
            # color
            color = (180, 180, 180)
            # rect
            rect = (self.hovered_sqr.col * SQSIZE, self.hovered_sqr.row * SQSIZE, SQSIZE, SQSIZE)
            # blit
            pygame.draw.rect(surface, color, rect, width=3)

    # other methods

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

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
        # Update game mode based on engine states
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
        # Set the current position to the engine
        fen = self.board.to_fen(self.next_player)
        self.engine.set_position(fen)
        
        # Get the evaluation
        self.evaluation = self.engine.get_evaluation()
        return self.evaluation

    def make_engine_move(self):
        # Convert board to FEN with next player
        fen = self.board.to_fen(self.next_player)
        self.engine.set_position(fen)
        
        # Skip if game is over
        if self.engine.is_game_over():
            return
        
        # Get best move from engine
        uci_move = self.engine.get_best_move()
        
        # Handle case where engine returns no move
        if uci_move is None or len(uci_move) < 4:
            return
        
        # Convert UCI to our move format
        col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        try:
            from_col = col_map[uci_move[0]]
            from_row = 8 - int(uci_move[1])
            to_col = col_map[uci_move[2]]
            to_row = 8 - int(uci_move[3])
        except (KeyError, ValueError):
            return
        
        # Create move object
        initial = Square(from_row, from_col)
        final = Square(to_row, to_col)
        move = Move(initial, final)
        
        # Execute move
        piece = self.board.squares[from_row][from_col].piece
        captured = self.board.squares[to_row][to_col].has_piece()
        self.board.move(piece, move)
        self.board.set_true_en_passant(piece)
        self.play_sound(captured)
        self.next_turn()

    def increase_level(self):
        self.level = min(20, self.level + 1)
        self.engine.set_skill_level(self.level)

    def decrease_level(self):
        self.level = max(0, self.level - 1)
        self.engine.set_skill_level(self.level)
# [file content end]