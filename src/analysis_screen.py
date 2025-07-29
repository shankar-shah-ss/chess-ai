# analysis_screen.py - Enhanced with pieces and cleaner UI
import pygame
import os
from const import *

class AnalysisScreen:
    def __init__(self, config):
        self.config = config
        self.analyzer = None
        self.current_move_index = 0
        self.show_analysis = False
        self.scroll_offset = 0
        self.active = False
        
        # Screen dimensions
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        
        # Layout constants - optimized for cleaner look
        self.board_size = min(self.screen_width * 0.55, self.screen_height * 0.85)
        self.board_square_size = self.board_size // 8
        self.board_x = 40
        self.board_y = (self.screen_height - self.board_size) // 2
        
        # Move list panel - made wider and cleaner
        self.moves_panel_x = self.board_x + self.board_size + 20
        self.moves_panel_width = self.screen_width - self.moves_panel_x - 15
        self.moves_panel_height = self.screen_height - 120
        
        # Modern color scheme
        self.bg_color = (25, 25, 30)           # Darker background
        self.panel_color = (35, 35, 45)        # Darker panel
        self.selected_color = (55, 55, 70)     # Selected item
        self.text_color = (240, 240, 245)      # Lighter text
        self.header_color = (220, 220, 230)    # Headers
        self.border_color = (70, 70, 80)       # Borders
        self.accent_color = (100, 150, 255)    # Accent blue
        
        # Board colors - warmer, more premium look
        self.light_square = (240, 217, 181)
        self.dark_square = (181, 136, 99)
        
        # Move classification colors (Chess.com style with better contrast)
        self.classification_colors = {
            'BRILLIANT': (30, 175, 255),       # Bright blue
            'GREAT': (120, 210, 150),          # Green
            'BEST': (130, 200, 140),           # Light green
            'EXCELLENT': (150, 220, 160),      # Very light green
            'OKAY': (200, 200, 205),           # Light gray
            'MISS': (255, 193, 87),            # Orange
            'INACCURACY': (255, 193, 87),      # Orange
            'MISTAKE': (255, 162, 132),        # Light red
            'BLUNDER': (255, 74, 74)           # Red
        }
        
        # Analysis state
        self.selected_move = None
        self.show_evaluation_bar = True
        self.show_best_moves = True
        self.evaluation_history = []
        
        # Current position for piece rendering
        self.current_position = None
        
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        self.current_move_index = 0
        self.scroll_offset = 0
        self.evaluation_history = []
        self.current_position = None
        
    def activate(self):
        """Activate the analysis screen"""
        self.active = True
        self.show_analysis = True
        
    def deactivate(self):
        """Deactivate the analysis screen"""
        self.active = False
        self.show_analysis = False
        
    def render(self, surface):
        """Render the analysis screen"""
        if not self.active or not self.analyzer:
            return
            
        # Fill background with modern dark color
        surface.fill(self.bg_color)
        
        # Draw header
        self._draw_header(surface)
        
        # Draw board with pieces
        self._draw_analysis_board(surface)
        
        # Draw moves panel
        self._draw_moves_panel(surface)
        
        # Draw evaluation bar
        if self.show_evaluation_bar:
            self._draw_evaluation_bar(surface)
            
        # Draw analysis info
        self._draw_analysis_info(surface)
        
        # Draw controls
        self._draw_controls(surface)
        
    def _draw_header(self, surface):
        """Draw the header with game analysis title"""
        # Main title with modern styling
        title_font = pygame.font.SysFont('Segoe UI', 32, bold=True)
        title_text = "Game Analysis"
        title_surface = title_font.render(title_text, True, self.header_color)
        surface.blit(title_surface, (30, 15))
        
        # Analysis status with better visual feedback
        status_font = pygame.font.SysFont('Segoe UI', 16)
        if not self.analyzer.is_analysis_complete():
            progress = self.analyzer.get_analysis_progress()
            status_text = f"Analyzing moves... {progress}%"
            status_color = self.accent_color
            
            # Progress bar
            bar_x, bar_y = 30, 55
            bar_width, bar_height = 200, 6
            
            # Background bar
            pygame.draw.rect(surface, (50, 50, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
            
            # Progress fill
            fill_width = int(bar_width * progress / 100)
            if fill_width > 0:
                pygame.draw.rect(surface, self.accent_color, (bar_x, bar_y, fill_width, bar_height), border_radius=3)
        else:
            status_text = "Analysis Complete ✓"
            status_color = (100, 255, 150)
            
        status_surface = status_font.render(status_text, True, status_color)
        surface.blit(status_surface, (30, 70))
        
    def _draw_analysis_board(self, surface):
        """Draw the chess board with pieces and analysis overlay"""
        # Board background with subtle shadow
        shadow_offset = 3
        shadow_rect = pygame.Rect(self.board_x + shadow_offset, self.board_y + shadow_offset, 
                                 self.board_size, self.board_size)
        pygame.draw.rect(surface, (15, 15, 20), shadow_rect, border_radius=8)
        
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(surface, self.border_color, board_rect, 3, border_radius=8)
        
        # Draw squares
        for row in range(8):
            for col in range(8):
                square_x = self.board_x + col * self.board_square_size
                square_y = self.board_y + row * self.board_square_size
                
                # Square color
                color = self.light_square if (row + col) % 2 == 0 else self.dark_square
                square_rect = pygame.Rect(square_x, square_y, self.board_square_size, self.board_square_size)
                pygame.draw.rect(surface, color, square_rect)
        
        # Draw coordinate labels with better styling
        self._draw_board_coordinates(surface)
        
        # Draw current move highlight
        self._draw_move_highlight(surface)
        
        # Draw pieces on the board
        self._draw_pieces(surface)
        
    def _draw_pieces(self, surface):
        """Draw chess pieces on the analysis board"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves or self.current_move_index < 0:
            return
            
        # Get the position after the current move
        if self.current_move_index < len(analyzed_moves):
            current_analysis = analyzed_moves[self.current_move_index]
            position_fen = current_analysis.position_after
        else:
            return
            
        # Parse FEN to get piece positions
        try:
            board_part = position_fen.split()[0]
            self._render_pieces_from_fen(surface, board_part)
        except:
            pass
            
    def _render_pieces_from_fen(self, surface, board_fen):
        """Render pieces from FEN string"""
        # Piece to filename mapping
        piece_files = {
            'K': 'white_king.png', 'Q': 'white_queen.png', 'R': 'white_rook.png',
            'B': 'white_bishop.png', 'N': 'white_knight.png', 'P': 'white_pawn.png',
            'k': 'black_king.png', 'q': 'black_queen.png', 'r': 'black_rook.png', 
            'b': 'black_bishop.png', 'n': 'black_knight.png', 'p': 'black_pawn.png'
        }
        
        row = 0
        col = 0
        
        for char in board_fen:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            elif char in piece_files:
                # Calculate screen position
                screen_x = self.board_x + col * self.board_square_size
                screen_y = self.board_y + row * self.board_square_size
                
                try:
                    # Load and display piece image
                    piece_file = os.path.join('assets', 'images', 'imgs-80px', piece_files[char])
                    if os.path.exists(piece_file):
                        piece_img = pygame.image.load(piece_file)
                        # Scale to fit square
                        piece_size = int(self.board_square_size * 0.8)
                        piece_img = pygame.transform.scale(piece_img, (piece_size, piece_size))
                        
                        # Center piece in square
                        piece_rect = piece_img.get_rect()
                        piece_rect.center = (screen_x + self.board_square_size // 2, 
                                           screen_y + self.board_square_size // 2)
                        surface.blit(piece_img, piece_rect)
                except:
                    # Fallback: draw simple colored circles for pieces
                    color = (255, 255, 255) if char.isupper() else (50, 50, 50)
                    center = (screen_x + self.board_square_size // 2, 
                             screen_y + self.board_square_size // 2)
                    radius = self.board_square_size // 4
                    pygame.draw.circle(surface, color, center, radius)
                    pygame.draw.circle(surface, (100, 100, 100), center, radius, 2)
                    
                    # Draw piece symbol
                    font = pygame.font.SysFont('Arial', self.board_square_size // 6, bold=True)
                    text_color = (0, 0, 0) if char.isupper() else (255, 255, 255)
                    symbol_surface = font.render(char.upper(), True, text_color)
                    symbol_rect = symbol_surface.get_rect(center=center)
                    surface.blit(symbol_surface, symbol_rect)
                
                col += 1
                
    def _draw_board_coordinates(self, surface):
        """Draw coordinate labels on the board"""
        coord_font = pygame.font.SysFont('Segoe UI', 12, bold=True)
        coord_color = (120, 120, 130)
        
        # File labels (a-h)
        for col in range(8):
            file_label = chr(ord('a') + col)
            label_surface = coord_font.render(file_label, True, coord_color)
            x = self.board_x + col * self.board_square_size + self.board_square_size - 18
            y = self.board_y + self.board_size - 18
            surface.blit(label_surface, (x, y))
            
        # Rank labels (1-8)
        for row in range(8):
            rank_label = str(8 - row)
            label_surface = coord_font.render(rank_label, True, coord_color)
            x = self.board_x + 6
            y = self.board_y + row * self.board_square_size + 6
            surface.blit(label_surface, (x, y))
            
    def _draw_move_highlight(self, surface):
        """Highlight the current move on the board"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if (self.current_move_index >= len(analyzed_moves) or 
            self.current_move_index < 0):
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        move = current_analysis.move
        
        # Get classification color
        color = self.classification_colors.get(current_analysis.classification, (255, 255, 255))
        
        # Highlight from square with rounded corners
        from_x = self.board_x + move.initial.col * self.board_square_size
        from_y = self.board_y + move.initial.row * self.board_square_size
        from_rect = pygame.Rect(from_x + 2, from_y + 2, 
                               self.board_square_size - 4, self.board_square_size - 4)
        pygame.draw.rect(surface, color, from_rect, 4, border_radius=6)
        
        # Highlight to square
        to_x = self.board_x + move.final.col * self.board_square_size
        to_y = self.board_y + move.final.row * self.board_square_size
        to_rect = pygame.Rect(to_x + 2, to_y + 2, 
                             self.board_square_size - 4, self.board_square_size - 4)
        pygame.draw.rect(surface, color, to_rect, 4, border_radius=6)
        
        # Draw arrow with better styling
        self._draw_move_arrow(surface, 
                            (from_x + self.board_square_size//2, from_y + self.board_square_size//2),
                            (to_x + self.board_square_size//2, to_y + self.board_square_size//2),
                            color)
        
    def _draw_move_arrow(self, surface, start_pos, end_pos, color):
        """Draw an arrow showing the move"""
        # Draw arrow line with thickness
        pygame.draw.line(surface, color, start_pos, end_pos, 4)
        
        # Calculate arrow head
        import math
        angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
        arrow_length = 15
        arrow_angle = math.pi / 6
        
        # Arrow head points
        point1 = (end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                 end_pos[1] - arrow_length * math.sin(angle - arrow_angle))
        point2 = (end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
                 end_pos[1] - arrow_length * math.sin(angle + arrow_angle))
        
        # Draw arrow head
        pygame.draw.polygon(surface, color, [end_pos, point1, point2])
        
    def _draw_moves_panel(self, surface):
        """Draw the moves list panel with modern styling"""
        # Panel background with rounded corners
        panel_rect = pygame.Rect(self.moves_panel_x, 100, 
                                self.moves_panel_width, self.moves_panel_height - 100)
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=12)
        pygame.draw.rect(surface, self.border_color, panel_rect, 2, border_radius=12)
        
        # Panel header with better styling
        header_font = pygame.font.SysFont('Segoe UI', 20, bold=True)
        header_text = "Move Analysis"
        header_surface = header_font.render(header_text, True, self.header_color)
        surface.blit(header_surface, (self.moves_panel_x + 15, 115))
        
        if not self.analyzer.is_analysis_complete():
            # Show progress with better formatting
            progress_font = pygame.font.SysFont('Segoe UI', 14)
            progress_text = f"Analyzing moves... {self.analyzer.get_analysis_progress()}%"
            progress_surface = progress_font.render(progress_text, True, self.accent_color)
            surface.blit(progress_surface, (self.moves_panel_x + 15, 150))
            return
            
        # Draw move list
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        # Calculate visible area
        start_y = 150
        move_height = 50  # Increased for better spacing
        visible_moves = min(len(analyzed_moves), (self.moves_panel_height - 160) // move_height)
        
        # Draw moves with modern styling
        for i in range(visible_moves):
            move_index = i + self.scroll_offset
            if move_index >= len(analyzed_moves):
                break
                
            move_analysis = analyzed_moves[move_index]
            y = start_y + i * move_height
            
            # Highlight current move with modern selection
            if move_index == self.current_move_index:
                highlight_rect = pygame.Rect(self.moves_panel_x + 8, y - 3, 
                                           self.moves_panel_width - 16, move_height - 4)
                pygame.draw.rect(surface, self.selected_color, highlight_rect, border_radius=8)
                
            self._draw_move_entry(surface, move_analysis, move_index, y)
            
    def _draw_move_entry(self, surface, move_analysis, move_index, y):
        """Draw a single move analysis entry with improved styling"""
        x_base = self.moves_panel_x + 15
        
        # Move number and player with better typography
        move_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        player_color = "W" if move_analysis.player == 'white' else "B"
        move_text = f"{move_analysis.move_number}.{player_color}"
        move_surface = move_font.render(move_text, True, self.text_color)
        surface.blit(move_surface, (x_base, y + 2))
        
        # Move notation with better font
        notation_font = pygame.font.SysFont('Segoe UI', 15)
        move_notation = self._get_move_notation(move_analysis.move)
        notation_surface = notation_font.render(move_notation, True, self.text_color)
        surface.blit(notation_surface, (x_base + 70, y + 2))
        
        # Classification badge with modern design
        classification = move_analysis.classification
        class_color = self.classification_colors.get(classification, self.text_color)
        
        # Modern badge design
        badge_width = 90
        badge_height = 20
        badge_rect = pygame.Rect(x_base + 170, y + 1, badge_width, badge_height)
        pygame.draw.rect(surface, class_color, badge_rect, border_radius=10)
        
        # Classification text
        class_font = pygame.font.SysFont('Segoe UI', 11, bold=True)
        class_surface = class_font.render(classification, True, (255, 255, 255))
        text_rect = class_surface.get_rect(center=badge_rect.center)
        surface.blit(class_surface, text_rect)
        
        # Evaluation change with better styling
        if move_analysis.eval_loss > 0:
            eval_text = f"-{move_analysis.eval_loss}"
            eval_color = (255, 120, 120) if move_analysis.eval_loss > 100 else (255, 200, 120)
            eval_font = pygame.font.SysFont('Segoe UI', 13, bold=True)
            eval_surface = eval_font.render(eval_text, True, eval_color)
            surface.blit(eval_surface, (x_base + 280, y + 3))
            
        # Best move suggestion with improved formatting
        if (move_analysis.classification not in ['BEST', 'BRILLIANT', 'GREAT'] and 
            move_analysis.best_moves):
            best_notation = self._uci_to_notation(move_analysis.best_moves[0])
            best_text = f"Best: {best_notation}"
            best_font = pygame.font.SysFont('Segoe UI', 12)
            best_surface = best_font.render(best_text, True, (140, 255, 140))
            surface.blit(best_surface, (x_base, y + 25))
            
    def _draw_evaluation_bar(self, surface):
        """Draw evaluation bar with modern styling"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if not analyzed_moves:
            return
            
        # Evaluation bar dimensions
        bar_x = self.board_x + self.board_size + 8
        bar_y = self.board_y
        bar_width = 8
        bar_height = self.board_size
        
        # Modern background with rounded corners
        pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        pygame.draw.rect(surface, self.border_color, (bar_x, bar_y, bar_width, bar_height), 1, border_radius=4)
        
        # Get current evaluation
        if self.current_move_index < len(analyzed_moves):
            current_analysis = analyzed_moves[self.current_move_index]
            evaluation = current_analysis.eval_after
            
            if evaluation and 'value' in evaluation:
                if evaluation['type'] == 'cp':
                    # Convert centipawns to bar position (-500 to +500 cp range)
                    eval_cp = max(-500, min(500, evaluation['value']))
                    bar_position = (eval_cp + 500) / 1000  # 0 to 1
                else:  # mate
                    bar_position = 1.0 if evaluation['value'] > 0 else 0.0
                    
                # Calculate bar fill
                white_height = int(bar_height * bar_position)
                black_height = bar_height - white_height
                
                # Draw white advantage (bottom)
                if white_height > 0:
                    white_rect = pygame.Rect(bar_x, bar_y + black_height, bar_width, white_height)
                    pygame.draw.rect(surface, (250, 250, 250), white_rect, border_radius=4)
                    
                # Draw black advantage (top)
                if black_height > 0:
                    black_rect = pygame.Rect(bar_x, bar_y, bar_width, black_height)
                    pygame.draw.rect(surface, (60, 60, 60), black_rect, border_radius=4)
                    
                # Draw center line
                center_y = bar_y + bar_height // 2
                pygame.draw.line(surface, (120, 120, 130), 
                               (bar_x, center_y), (bar_x + bar_width, center_y), 2)
                
    def _draw_analysis_info(self, surface):
        """Draw detailed analysis information with modern styling"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if (self.current_move_index >= len(analyzed_moves) or 
            self.current_move_index < 0):
            return
            
        current_analysis = analyzed_moves[self.current_move_index]
        
        # Info panel with modern design
        info_x = 30
        info_y = self.screen_height - 140
        info_width = self.moves_panel_x - 50
        info_height = 110
        
        panel_rect = pygame.Rect(info_x, info_y, info_width, info_height)
        pygame.draw.rect(surface, self.panel_color, panel_rect, border_radius=12)
        pygame.draw.rect(surface, self.border_color, panel_rect, 2, border_radius=12)
        
        # Info header
        header_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        header_text = f"Move {current_analysis.move_number} Analysis"
        header_surface = header_font.render(header_text, True, self.header_color)
        surface.blit(header_surface, (info_x + 15, info_y + 12))
        
        # Evaluation info with better formatting
        if current_analysis.eval_after:
            eval_info = self._format_evaluation(current_analysis.eval_after)
            eval_font = pygame.font.SysFont('Segoe UI', 14)
            eval_surface = eval_font.render(f"Position: {eval_info}", True, self.text_color)
            surface.blit(eval_surface, (info_x + 15, info_y + 40))
            
        # Alternative moves with modern styling
        if (hasattr(current_analysis, 'alternative_moves') and 
            current_analysis.alternative_moves):
            alt_text = "Alternatives: " + ", ".join([
                self._uci_to_notation(move) for move in current_analysis.alternative_moves[:2]
            ])
            alt_font = pygame.font.SysFont('Segoe UI', 13)
            alt_surface = alt_font.render(alt_text, True, (180, 180, 190))
            surface.blit(alt_surface, (info_x + 15, info_y + 65))
            
    def _draw_controls(self, surface):
        """Draw control information with modern styling"""
        controls_y = self.screen_height - 22
        controls_font = pygame.font.SysFont('Segoe UI', 12)
        
        controls = [
            "← → Navigate",
            "Space: Auto-play",
            "Ctrl+S: Summary", 
            "E: Eval bar",
            "Esc: Exit"
        ]
        
        x = 30
        for i, control in enumerate(controls):
            color = self.accent_color if i == 0 else (160, 160, 170)
            control_surface = controls_font.render(control, True, color)
            surface.blit(control_surface, (x, controls_y))
            x += control_surface.get_width() + 25
            
    def _get_move_notation(self, move):
        """Convert move to algebraic notation"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
        to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
        
        return f"{from_square}{to_square}"
        
    def _uci_to_notation(self, uci_move):
        """Convert UCI move to readable notation"""
        if len(uci_move) >= 4:
            return f"{uci_move[:2]}{uci_move[2:4]}"
        return uci_move
        
    def _format_evaluation(self, evaluation):
        """Format evaluation for display"""
        if not evaluation or 'value' not in evaluation:
            return "N/A"
            
        if evaluation['type'] == 'cp':
            score = evaluation['value'] / 100.0
            return f"{score:+.2f}"
        else:  # mate
            moves_to_mate = abs(evaluation['value'])
            side = "White" if evaluation['value'] > 0 else "Black"
            return f"Mate in {moves_to_mate} for {side}"
            
    def handle_input(self, event):
        """Handle input events for analysis screen"""
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            analyzed_moves = self.analyzer.get_analyzed_moves()
            
            if event.key == pygame.K_LEFT:
                if self.current_move_index > 0:
                    self.current_move_index -= 1
                    self._update_scroll()
                return True
                
            elif event.key == pygame.K_RIGHT:
                if self.current_move_index < len(analyzed_moves) - 1:
                    self.current_move_index += 1
                    self._update_scroll()
                return True
                
            elif event.key == pygame.K_HOME:
                self.current_move_index = 0
                self._update_scroll()
                return True
                
            elif event.key == pygame.K_END:
                if analyzed_moves:
                    self.current_move_index = len(analyzed_moves) - 1
                    self._update_scroll()
                return True
                
            elif event.key == pygame.K_e:
                self.show_evaluation_bar = not self.show_evaluation_bar
                return True
                
            elif event.key == pygame.K_ESCAPE:
                self.deactivate()
                return True
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.active:
                # Check if click is in moves panel
                panel_start_y = 150
                if (self.moves_panel_x <= event.pos[0] <= self.moves_panel_x + self.moves_panel_width and
                    panel_start_y <= event.pos[1] <= panel_start_y + self.moves_panel_height - 160):
                    
                    # Calculate which move was clicked
                    relative_y = event.pos[1] - panel_start_y
                    move_index = (relative_y // 50) + self.scroll_offset  # Updated move height
                    
                    analyzed_moves = self.analyzer.get_analyzed_moves()
                    if 0 <= move_index < len(analyzed_moves):
                        self.current_move_index = move_index
                        return True
                        
        return False
        
    def _update_scroll(self):
        """Update scroll offset to keep current move visible"""
        move_height = 50
        visible_moves = (self.moves_panel_height - 160) // move_height
        
        if self.current_move_index < self.scroll_offset:
            self.scroll_offset = self.current_move_index
        elif self.current_move_index >= self.scroll_offset + visible_moves:
            self.scroll_offset = self.current_move_index - visible_moves + 1
            
        self.scroll_offset = max(0, self.scroll_offset)
        
    def get_current_move(self):
        """Get the currently selected move analysis"""
        if not self.analyzer.is_analysis_complete():
            return None
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if 0 <= self.current_move_index < len(analyzed_moves):
            return analyzed_moves[self.current_move_index]
        return None

    def next_move(self):
        """Move to the next move in analysis"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index < len(analyzed_moves) - 1:
            self.current_move_index += 1
            self._update_scroll()

    def previous_move(self):
        """Move to the previous move in analysis"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self._update_scroll()

    def jump_to_move(self, move_number):
        """Jump to a specific move number"""
        if not self.analyzer.is_analysis_complete():
            return
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        for i, move_analysis in enumerate(analyzed_moves):
            if move_analysis.move_number == move_number:
                self.current_move_index = i
                self._update_scroll()
                break

    def get_position_at_move(self, move_index):
        """Get the board position at a specific move"""
        if not self.analyzer.is_analysis_complete():
            return None
            
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if 0 <= move_index < len(analyzed_moves):
            return analyzed_moves[move_index].position_after
        return None

    def toggle_evaluation_display(self):
        """Toggle the evaluation display mode"""
        self.show_evaluation_bar = not self.show_evaluation_bar

    def set_analysis_depth(self, depth):
        """Set analysis depth for future analysis"""
        if hasattr(self.analyzer, 'set_analysis_depth'):
            self.analyzer.set_analysis_depth(depth)