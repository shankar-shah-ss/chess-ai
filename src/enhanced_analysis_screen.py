# enhanced_analysis_screen.py - Interactive Chess.com-style Analysis Screen
import pygame
import chess
from utils_analysis_complete import draw_arrow, draw_classification_badge, draw_progress_bar

class EnhancedAnalysisScreen:
    def __init__(self, config, opening_db=None):
        self.config = config
        self.opening_db = opening_db
        self.analyzer = None
        self.current_move_index = 0
        self.board_display = chess.Board()
        self.active = False
        
        # Screen dimensions (match main game)
        self.width = 900
        self.height = 900
        self.board_size = 480
        self.board_x = 50
        self.board_y = 50
        
        # Analysis panel
        self.panel_x = self.board_x + self.board_size + 30
        self.panel_width = 300
        
        # Colors (Chess.com style)
        self.colors = {
            'bg': (40, 46, 58),
            'panel': (49, 56, 70),
            'text': (255, 255, 255),
            'accent': (129, 182, 76),
            'brilliant': (28, 158, 255),
            'great': (96, 169, 23),
            'best': (96, 169, 23),
            'excellent': (96, 169, 23),
            'okay': (115, 192, 67),
            'miss': (255, 167, 38),
            'inaccuracy': (255, 167, 38),
            'mistake': (255, 146, 146),
            'blunder': (242, 113, 102)
        }
        
        # Fonts
        self.title_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
        self.header_font = pygame.font.SysFont('Segoe UI', 18, bold=True)
        self.text_font = pygame.font.SysFont('Segoe UI', 14)
        self.small_font = pygame.font.SysFont('Segoe UI', 12)
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        
    def activate(self, initial_fen=None):
        """Activate the analysis screen"""
        self.active = True
        self.current_move_index = 0
        # Initialize with starting position or provided FEN
        if initial_fen:
            self.board_display = chess.Board(initial_fen)
        else:
            self.board_display = chess.Board()
        self.update_board_position()
        
    def deactivate(self):
        """Deactivate the analysis screen"""
        self.active = False
        
    def update_board_position(self):
        """Update board to show position at current move"""
        if not self.analyzer:
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            self.board_display = chess.Board()
            return
            
        # Replay moves up to current index with error handling
        try:
            self.board_display = chess.Board()
            valid_moves = 0
            
            for i in range(min(self.current_move_index + 1, len(analyzed_moves))):
                move_analysis = analyzed_moves[i]
                try:
                    uci_move = self._convert_to_uci(move_analysis.move)
                    chess_move = chess.Move.from_uci(uci_move)
                    
                    # Validate move before pushing
                    if chess_move in self.board_display.legal_moves:
                        self.board_display.push(chess_move)
                        valid_moves += 1
                    else:
                        print(f"Invalid move at index {i}: {uci_move}")
                        break
                except Exception as e:
                    print(f"Error processing move {i}: {e}")
                    break
                    
            # Ensure current_move_index doesn't exceed valid moves
            if self.current_move_index >= valid_moves:
                self.current_move_index = max(0, valid_moves - 1)
                
        except Exception as e:
            print(f"Board update error: {e}")
            self.board_display = chess.Board()
                
    def _convert_to_uci(self, internal_move):
        """Convert internal move format to UCI"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_col = col_map[internal_move.initial.col]
        from_row = str(8 - internal_move.initial.row)
        to_col = col_map[internal_move.final.col]
        to_row = str(8 - internal_move.final.row)
        
        return f"{from_col}{from_row}{to_col}{to_row}"
        
    def render(self, surface):
        """Render the analysis screen"""
        if not self.active:
            return
            
        # Clear background
        surface.fill(self.colors['bg'])
        
        # Render board
        self._render_board(surface)
        
        # Render analysis panel
        self._render_analysis_panel(surface)
        
        # Render move list
        self._render_move_list(surface)
        
        # Render controls
        self._render_controls(surface)
        
    def _render_board(self, surface):
        """Render the chess board"""
        square_size = self.board_size // 8
        
        # Board background
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(surface, (240, 217, 181), board_rect)
        
        # Squares
        for row in range(8):
            for col in range(8):
                x = self.board_x + col * square_size
                y = self.board_y + row * square_size
                
                # Square color
                if (row + col) % 2 == 0:
                    color = (240, 217, 181)  # Light squares
                else:
                    color = (181, 136, 99)   # Dark squares
                    
                pygame.draw.rect(surface, color, (x, y, square_size, square_size))
                
                # Coordinates
                if col == 0:  # Ranks
                    rank_text = self.small_font.render(str(8-row), True, (100, 100, 100))
                    surface.blit(rank_text, (x + 2, y + 2))
                if row == 7:  # Files
                    file_text = self.small_font.render(chr(97+col), True, (100, 100, 100))
                    surface.blit(file_text, (x + square_size - 12, y + square_size - 15))
        
        # Pieces
        self._render_pieces(surface, square_size)
        
        # Highlight last move
        self._highlight_last_move(surface, square_size)
        
    def _render_pieces(self, surface, square_size):
        """Render pieces on the board"""
        import os
        
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7-row)
                piece = self.board_display.piece_at(square)
                
                if piece:
                    # Map chess piece to file name
                    piece_names = {
                        'p': 'pawn', 'r': 'rook', 'n': 'knight', 
                        'b': 'bishop', 'q': 'queen', 'k': 'king'
                    }
                    
                    piece_name = piece_names.get(piece.symbol().lower(), 'pawn')
                    piece_color = 'white' if piece.color else 'black'
                    
                    # Try to load piece image
                    image_paths = [
                        os.path.join('..', 'assets', 'images', 'imgs-80px', f'{piece_color}_{piece_name}.png'),
                        os.path.join('assets', 'images', 'imgs-80px', f'{piece_color}_{piece_name}.png')
                    ]
                    
                    piece_surface = None
                    for path in image_paths:
                        if os.path.exists(path):
                            try:
                                piece_surface = pygame.image.load(path)
                                # Scale to fit square
                                piece_surface = pygame.transform.scale(piece_surface, (int(square_size * 0.8), int(square_size * 0.8)))
                                break
                            except:
                                continue
                    
                    # Fallback to text if image not found
                    if piece_surface is None:
                        piece_symbols = {
                            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
                            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
                        }
                        piece_font = pygame.font.SysFont('Segoe UI Symbol', int(square_size * 0.6))
                        symbol = piece_symbols.get(piece.symbol(), piece.symbol())
                        color = (255, 255, 255) if piece.color else (50, 50, 50)
                        piece_surface = piece_font.render(symbol, True, color)
                    
                    # Center the piece in the square
                    piece_rect = piece_surface.get_rect()
                    piece_rect.center = (
                        self.board_x + col * square_size + square_size // 2,
                        self.board_y + row * square_size + square_size // 2
                    )
                    surface.blit(piece_surface, piece_rect)
                    
    def _highlight_last_move(self, surface, square_size):
        """Highlight the last move played"""
        if not self.analyzer or self.current_move_index < 0:
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves):
            return
            
        move_analysis = analyzed_moves[self.current_move_index]
        move = move_analysis.move
        
        # Highlight from and to squares
        for square_pos in [move.initial, move.final]:
            x = self.board_x + square_pos.col * square_size
            y = self.board_y + square_pos.row * square_size
            
            highlight_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
            highlight_surface.fill((255, 255, 0, 100))
            surface.blit(highlight_surface, (x, y))
            
    def _render_analysis_panel(self, surface):
        """Render the analysis information panel"""
        panel_rect = pygame.Rect(self.panel_x, self.board_y, self.panel_width, 400)
        pygame.draw.rect(surface, self.colors['panel'], panel_rect, border_radius=10)
        
        y_offset = self.board_y + 20
        
        # Title
        title_surface = self.title_font.render("Analysis", True, self.colors['text'])
        surface.blit(title_surface, (self.panel_x + 20, y_offset))
        y_offset += 40
        
        if not self.analyzer or not self.analyzer.is_analysis_complete():
            # Show progress
            progress = self.analyzer.get_analysis_progress() if self.analyzer else 0
            
            if progress == 0 and self.analyzer and self.analyzer.analysis_thread and self.analyzer.analysis_thread.is_alive():
                progress_text = self.text_font.render("Starting analysis...", True, self.colors['text'])
            else:
                progress_text = self.text_font.render(f"Analyzing... {progress}%", True, self.colors['text'])
            
            surface.blit(progress_text, (self.panel_x + 20, y_offset))
            
            # Progress bar
            draw_progress_bar(surface, self.panel_x + 20, y_offset + 30, self.panel_width - 40, 20, progress)
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves or self.current_move_index >= len(analyzed_moves):
            return
            
        current_move = analyzed_moves[self.current_move_index]
        
        # Move info
        move_text = f"Move {self.current_move_index + 1}: {current_move.player.title()}"
        move_surface = self.header_font.render(move_text, True, self.colors['text'])
        surface.blit(move_surface, (self.panel_x + 20, y_offset))
        y_offset += 30
        
        # Classification badge
        classification_color = self.colors.get(current_move.classification.lower(), self.colors['text'])
        draw_classification_badge(surface, self.panel_x + 20, y_offset, current_move.classification, classification_color)
        y_offset += 40
        
        # Evaluation
        eval_text = f"Evaluation: {self._format_evaluation(current_move.eval_after)}"
        eval_surface = self.text_font.render(eval_text, True, self.colors['text'])
        surface.blit(eval_surface, (self.panel_x + 20, y_offset))
        y_offset += 25
        
        # Evaluation loss
        if current_move.eval_loss > 0:
            loss_text = f"Evaluation Loss: -{current_move.eval_loss}"
            loss_surface = self.text_font.render(loss_text, True, (255, 100, 100))
            surface.blit(loss_surface, (self.panel_x + 20, y_offset))
        y_offset += 25
        
        # Position assessment
        assessment_text = f"Position: {current_move.position_assessment}"
        assessment_surface = self.text_font.render(assessment_text, True, self.colors['accent'])
        surface.blit(assessment_surface, (self.panel_x + 20, y_offset))
        y_offset += 30
        
        # Best moves
        if current_move.best_moves:
            best_text = self.header_font.render("Best Moves:", True, self.colors['text'])
            surface.blit(best_text, (self.panel_x + 20, y_offset))
            y_offset += 25
            
            for i, move in enumerate(current_move.best_moves[:3]):
                move_text = f"{i+1}. {move}"
                move_surface = self.small_font.render(move_text, True, self.colors['text'])
                surface.blit(move_surface, (self.panel_x + 30, y_offset))
                y_offset += 20
                
        # Opening information
        if self.opening_db:
            opening_info = self.opening_db.detect_opening(self.board_display)
            if opening_info:
                y_offset += 10
                opening_text = self.header_font.render("Opening:", True, self.colors['text'])
                surface.blit(opening_text, (self.panel_x + 20, y_offset))
                y_offset += 25
                
                name_surface = self.text_font.render(opening_info['name'], True, self.colors['accent'])
                surface.blit(name_surface, (self.panel_x + 20, y_offset))
                y_offset += 20
                
                eco_surface = self.small_font.render(f"ECO: {opening_info['eco']}", True, self.colors['text'])
                surface.blit(eco_surface, (self.panel_x + 20, y_offset))
                
    def _render_move_list(self, surface):
        """Render the move list with classifications"""
        if not self.analyzer or not self.analyzer.is_analysis_complete():
            return
            
        # Adjust move list position based on surface height
        available_height = surface.get_height() - (self.board_y + 420) - 80
        move_list_height = min(300, max(150, available_height))
        move_list_rect = pygame.Rect(self.panel_x, self.board_y + 420, self.panel_width, move_list_height)
        pygame.draw.rect(surface, self.colors['panel'], move_list_rect, border_radius=10)
        
        # Title
        title_surface = self.header_font.render("Move List", True, self.colors['text'])
        surface.blit(title_surface, (self.panel_x + 20, move_list_rect.y + 20))
        
        analyzed_moves = self.analyzer.get_analyzed_moves()
        y_offset = move_list_rect.y + 50
        
        # Show moves around current position
        start_index = max(0, self.current_move_index - 5)
        max_moves = (move_list_height - 60) // 22  # Calculate how many moves fit
        end_index = min(len(analyzed_moves), start_index + max_moves)
        
        for i in range(start_index, end_index):
            if y_offset + 22 > move_list_rect.bottom - 10:
                break
                
            move_analysis = analyzed_moves[i]
            
            # Highlight current move
            if i == self.current_move_index:
                highlight_rect = pygame.Rect(self.panel_x + 10, y_offset - 2, self.panel_width - 20, 22)
                pygame.draw.rect(surface, (100, 100, 100, 100), highlight_rect, border_radius=5)
            
            # Move number and player
            move_text = f"{i+1}. {move_analysis.player[0].upper()}"
            move_surface = self.text_font.render(move_text, True, self.colors['text'])
            surface.blit(move_surface, (self.panel_x + 20, y_offset))
            
            # Classification
            class_color = self.colors.get(move_analysis.classification.lower(), self.colors['text'])
            class_surface = self.small_font.render(move_analysis.classification, True, class_color)
            surface.blit(class_surface, (self.panel_x + 80, y_offset))
            
            # Evaluation loss
            if hasattr(move_analysis, 'eval_loss') and move_analysis.eval_loss > 0:
                loss_surface = self.small_font.render(f"-{move_analysis.eval_loss}", True, (255, 100, 100))
                surface.blit(loss_surface, (self.panel_x + 200, y_offset))
            
            y_offset += 22
            
    def _render_controls(self, surface):
        """Render control instructions"""
        controls_y = surface.get_height() - 60
        
        controls = [
            "← → Navigate moves",
            "Space: Auto-play", 
            "S: Summary",
            "ESC: Exit"
        ]
        
        for i, control in enumerate(controls):
            control_surface = self.small_font.render(control, True, self.colors['text'])
            x_pos = 50 + i * min(150, (surface.get_width() - 100) // len(controls))
            surface.blit(control_surface, (x_pos, controls_y))
            
    def _format_evaluation(self, evaluation):
        """Format evaluation for display"""
        if not evaluation or 'value' not in evaluation:
            return "0.00"
            
        if evaluation['type'] == 'cp':
            return f"{evaluation['value'] / 100:.2f}"
        elif evaluation['type'] == 'mate':
            return f"Mate in {abs(evaluation['value'])}"
        
        return "0.00"
        
    def handle_input(self, event):
        """Handle input events"""
        if not self.active or not self.analyzer:
            return False
            
        if event.type == pygame.KEYDOWN:
            analyzed_moves = self.analyzer.get_analyzed_moves()
            if not analyzed_moves:
                return False
                
            old_index = self.current_move_index
            
            if event.key == pygame.K_LEFT:
                self.current_move_index = max(0, self.current_move_index - 1)
            elif event.key == pygame.K_RIGHT:
                self.current_move_index = min(len(analyzed_moves) - 1, self.current_move_index + 1)
            elif event.key == pygame.K_HOME:
                self.current_move_index = 0
            elif event.key == pygame.K_END:
                self.current_move_index = max(0, len(analyzed_moves) - 1)
            else:
                return False
                
            # Only update if index changed
            if self.current_move_index != old_index:
                self.update_board_position()
            return True
                
        return False
        
    def next_move(self):
        """Go to next move"""
        if not self.analyzer:
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        old_index = self.current_move_index
        self.current_move_index = min(len(analyzed_moves) - 1, self.current_move_index + 1)
        
        if self.current_move_index != old_index:
            self.update_board_position()
            
    def previous_move(self):
        """Go to previous move"""
        old_index = self.current_move_index
        self.current_move_index = max(0, self.current_move_index - 1)
        
        if self.current_move_index != old_index:
            self.update_board_position()
        
    def jump_to_move(self, move_index):
        """Jump to specific move"""
        if not self.analyzer:
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        old_index = self.current_move_index
        self.current_move_index = max(0, min(len(analyzed_moves) - 1, move_index))
        
        if self.current_move_index != old_index:
            self.update_board_position()
    
