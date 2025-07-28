# [file name]: main.py
# [file content begin]
import pygame
import sys

from const import *
from game import Game
from square import Square
from move import Move

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.game = Game()

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        # Set initial game mode
        game.set_game_mode(0)  # Start with human vs human

        while True:
            
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_pieces(screen)
            game.show_moves(screen)
            
            game.show_hover(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            # Engine move logic
            if not dragger.dragging:
                if (game.next_player == 'white' and game.engine_white) or \
                   (game.next_player == 'black' and game.engine_black):
                    game.make_engine_move()

            for event in pygame.event.get():
                # Mouse click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Skip human moves if engine is playing
                    if (game.next_player == 'white' and game.engine_white) or \
                       (game.next_player == 'black' and game.engine_black):
                        continue
                    
                    # Only process if mouse is within board boundaries
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
                                game.show_bg(screen)
                                game.show_last_move(screen)
                                game.show_moves(screen)
                                game.show_pieces(screen)
                
                # Mouse motion
                elif event.type == pygame.MOUSEMOTION:
                    # Only process if mouse is within board boundaries
                    if 0 <= event.pos[0] < WIDTH and 0 <= event.pos[1] < HEIGHT:
                        motion_row = event.pos[1] // SQSIZE
                        motion_col = event.pos[0] // SQSIZE
                        game.set_hover(motion_row, motion_col)

                        if dragger.dragging:
                            dragger.update_mouse(event.pos)
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            game.show_pieces(screen)
                            game.show_hover(screen)
                            dragger.update_blit(screen)
                    else:
                        # Clear hover when mouse leaves board
                        game.hovered_sqr = None
                
                # Mouse release
                elif event.type == pygame.MOUSEBUTTONUP:
                    # Skip human moves if engine is playing
                    if (game.next_player == 'white' and game.engine_white) or \
                       (game.next_player == 'black' and game.engine_black):
                        continue
                    
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        
                        # Only process if mouse is within board boundaries
                        if 0 <= event.pos[0] < WIDTH and 0 <= event.pos[1] < HEIGHT:
                            released_row = event.pos[1] // SQSIZE
                            released_col = event.pos[0] // SQSIZE

                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(released_row, released_col)
                            move = Move(initial, final)

                            if board.valid_move(dragger.piece, move):
                                captured = board.squares[released_row][released_col].has_piece()
                                board.move(dragger.piece, move)
                                board.set_true_en_passant(dragger.piece)
                                game.play_sound(captured)
                                game.show_bg(screen)
                                game.show_last_move(screen)
                                game.show_moves(screen)
                                game.show_pieces(screen)
                                # Force immediate screen update after human move
                                pygame.display.update()
                                game.next_turn()
                    
                    dragger.undrag_piece()
                
                # Key press
                elif event.type == pygame.KEYDOWN:
                    # Change theme
                    if event.key == pygame.K_t:
                        game.change_theme()
                    
                    # Reset game
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger
                    
                    # Game mode switching
                    if event.key == pygame.K_1:  # Human vs Human
                        game.set_game_mode(0)
                    if event.key == pygame.K_2:  # Human vs Engine
                        game.set_game_mode(1)
                    if event.key == pygame.K_3:  # Engine vs Engine
                        game.set_game_mode(2)
                    
                    # Engine controls
                    if event.key == pygame.K_e:  # Toggle white engine
                        game.toggle_engine('white')
                    if event.key == pygame.K_d:  # Toggle black engine
                        game.toggle_engine('black')
                    if event.key == pygame.K_UP:  # Increase depth
                        game.set_engine_depth(min(20, game.depth + 1))
                    if event.key == pygame.K_DOWN:  # Decrease depth
                        game.set_engine_depth(max(1, game.depth - 1))
                    if event.key == pygame.K_RIGHT:  # Increase level
                        game.set_engine_level(min(20, game.level + 1))
                    if event.key == pygame.K_LEFT:  # Decrease level
                        game.set_engine_level(max(0, game.level - 1))
                    if event.key == pygame.K_s:  # Show evaluation
                        game.get_engine_evaluation()
                    if event.key == pygame.K_a:  # Engine vs Engine
                        game.set_game_mode(2)

                    # Level adjustment
                    if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:  # + key
                        game.increase_level()
                    if event.key == pygame.K_MINUS:  # - key
                        game.decrease_level()
                
                # Quit application
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.update()

main = Main()
main.mainloop()
# [file content end]