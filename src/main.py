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
        self.clock = pygame.time.Clock()  # For FPS control

    def mainloop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        # Set initial game mode
        game.set_game_mode(0)  # Start with human vs human

        while True:
            self.clock.tick(60)  # Limit to 60 FPS for consistent performance
            
            # Check for completed engine moves
            if game.engine_thread and not game.engine_thread.is_alive():
                if game.engine_thread.move:
                    game.pending_engine_move = game.engine_thread.move
                game.engine_thread = None

            # Process engine move if available
            if game.pending_engine_move:
                game.make_engine_move()
                # Force immediate redraw
                game.show_bg(screen)
                game.show_last_move(screen)
                game.show_pieces(screen)
                pygame.display.update()

            # Skip processing if game over
            if game.game_over:
                game.show_bg(screen)
                game.show_last_move(screen)
                game.show_moves(screen)
                game.show_check(screen)
                game.show_pieces(screen)
                game.show_hover(screen)
                
                if dragger.dragging:
                    dragger.update_blit(screen)
                    
                pygame.display.update()
                
                # Process events for restart
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            game.reset()
                            game = self.game
                            board = self.game.board
                            dragger = self.game.dragger
                    elif event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                continue

            # Schedule engine move if needed
            if not dragger.dragging and not game.engine_thread and not game.pending_engine_move:
                if (game.next_player == 'white' and game.engine_white) or \
                   (game.next_player == 'black' and game.engine_black):
                    game.schedule_engine_move()

            # Render game state
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_check(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            for event in pygame.event.get():
                # Mouse click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if (game.next_player == 'white' and game.engine_white) or \
                       (game.next_player == 'black' and game.engine_black):
                        continue
                    
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
                        game.hovered_sqr = None
                
                # Mouse release
                elif event.type == pygame.MOUSEBUTTONUP:
                    if (game.next_player == 'white' and game.engine_white) or \
                       (game.next_player == 'black' and game.engine_black):
                        continue
                    
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        
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
                                pygame.display.update()
                                game.next_turn()
                                game.check_game_state()
                    
                    dragger.undrag_piece()
                
                # Key press
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger
                    if event.key == pygame.K_1:
                        game.set_game_mode(0)
                    if event.key == pygame.K_2:
                        game.set_game_mode(1)
                    if event.key == pygame.K_3:
                        game.set_game_mode(2)
                    if event.key == pygame.K_e:
                        game.toggle_engine('white')
                    if event.key == pygame.K_d:
                        game.toggle_engine('black')
                    if event.key == pygame.K_UP:
                        game.set_engine_depth(min(20, game.depth + 1))
                    if event.key == pygame.K_DOWN:
                        game.set_engine_depth(max(1, game.depth - 1))
                    if event.key == pygame.K_RIGHT:
                        game.set_engine_level(min(20, game.level + 1))
                    if event.key == pygame.K_LEFT:
                        game.set_engine_level(max(0, game.level - 1))
                    if event.key == pygame.K_s:
                        game.get_engine_evaluation()
                    if event.key == pygame.K_a:
                        game.set_game_mode(2)
                    if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        game.increase_level()
                    if event.key == pygame.K_MINUS:
                        game.decrease_level()
                
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.update()

main = Main()
main.mainloop()