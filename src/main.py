# main.py - Updated with Enhanced Analysis System
import pygame
import sys

from const import *
from game import Game
from square import Square
from move import Move
from analysis_manager import AnalysisManager

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess with Enhanced Analysis')
        self.game = Game()
        self.clock = pygame.time.Clock()
        
        # Initialize enhanced analysis manager
        self.analysis_manager = AnalysisManager(self.game.config, self.game.engine)
        
        # Connect analysis manager to game
        self.game.set_analysis_manager(self.analysis_manager)

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
            
            # Check for completed engine moves
            if game.engine_thread and not game.engine_thread.is_alive():
                if game.engine_thread.move:
                    game.pending_engine_move = game.engine_thread.move
                game.engine_thread = None
                
            # Check for completed evaluations
            if game.evaluation_thread and not game.evaluation_thread.is_alive():
                with game.evaluation_lock:
                    game.evaluation = game.evaluation_thread.evaluation
                game.evaluation_thread = None

            # Process engine move if available and not in analysis mode
            if game.pending_engine_move and not analysis_manager.active:
                game.make_engine_move()
                # Force immediate redraw
                game.show_bg(screen)
                game.show_last_move(screen)
                game.show_pieces(screen)
                pygame.display.update()

            # Schedule evaluation if needed (not in analysis mode)
            if not game.evaluation_thread and not analysis_manager.active:
                game.schedule_evaluation()

            # Handle analysis mode rendering
            if analysis_manager.active:
                # Render analysis screen
                if analysis_manager.render(screen):
                    pygame.display.update()
                    
                    # Process events for analysis mode
                    for event in pygame.event.get():
                        # Handle analysis manager input first
                        if analysis_manager.handle_input(event):
                            continue
                            
                        # Handle global keys
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_r:
                                game.reset()
                                analysis_manager.reset()
                                game = self.game
                                board = self.game.board
                                dragger = self.game.dragger
                                analysis_manager = self.analysis_manager
                                game.set_analysis_manager(analysis_manager)
                        elif event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                    continue

            # Skip processing if game over (but not in analysis mode)
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
                            analysis_manager.reset()
                            game = self.game
                            board = self.game.board
                            dragger = self.game.dragger
                            analysis_manager = self.analysis_manager
                            game.set_analysis_manager(analysis_manager)
                        elif event.key == pygame.K_a:
                            analysis_manager.enter_analysis_mode()
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
                                # Record move for analysis and make the move
                                game.make_move(dragger.piece, move)
                                game.show_bg(screen)
                                game.show_last_move(screen)
                                game.show_moves(screen)
                                game.show_pieces(screen)
                                pygame.display.update()
                    
                    dragger.undrag_piece()
                
                # Key press
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    elif event.key == pygame.K_r:
                        game.reset()
                        analysis_manager.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger
                        analysis_manager = self.analysis_manager
                        game.set_analysis_manager(analysis_manager)
                    elif event.key == pygame.K_1:
                        game.set_game_mode(0)
                    elif event.key == pygame.K_2:
                        game.set_game_mode(1)
                    elif event.key == pygame.K_3:
                        game.set_game_mode(2)
                    elif event.key == pygame.K_e:
                        game.toggle_engine('white')
                    elif event.key == pygame.K_d:
                        game.toggle_engine('black')
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
                    elif event.key == pygame.K_a:
                        if game.game_over:
                            analysis_manager.enter_analysis_mode()
                
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            pygame.display.update()

main = Main()
main.mainloop()