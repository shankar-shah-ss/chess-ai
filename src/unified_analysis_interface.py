# unified_analysis_interface.py - Consolidated analysis interface
import pygame
import chess
import chess.svg
from typing import Optional, Dict, List, Any
import logging
from resource_manager import resource_manager
from thread_manager import thread_manager

logger = logging.getLogger(__name__)

class UnifiedAnalysisInterface:
    """Unified analysis interface combining all analysis features"""
    
    def __init__(self, config, opening_db=None):
        self.config = config
        self.opening_db = opening_db
        self.analyzer = None
        
        # UI state
        self.active = False
        self.current_move_index = 0
        self.show_evaluation_bar = True
        self.show_move_arrows = True
        self.show_best_moves = True
        self.auto_play = False
        self.auto_play_speed = 1000
        self.last_auto_play_time = 0
        
        # UI components (must be before layout setup)
        self.tabs = ['Analysis', 'Summary', 'Opening', 'Statistics']
        self.current_tab = 0
        
        # Layout configuration
        self.setup_layout()
        self.setup_colors()
        
        # Board state
        self.board = chess.Board()
        self.move_history = []
        self.analysis_data = {}
        
        # Performance optimization
        self._cached_surfaces = {}
        self._last_render_hash = None
    
    def setup_layout(self):
        """Setup UI layout dimensions"""
        self.width = getattr(self.config, 'WIDTH', 1200)
        self.height = getattr(self.config, 'HEIGHT', 800)
        
        # Board section
        self.board_size = min(self.width * 0.6, self.height * 0.8)
        self.square_size = self.board_size // 8
        self.board_x = 20
        self.board_y = (self.height - self.board_size) // 2
        
        # Sidebar
        self.sidebar_x = self.board_x + self.board_size + 20
        self.sidebar_width = self.width - self.sidebar_x - 20
        self.sidebar_height = self.height - 40
        
        # Tab bar
        self.tab_height = 40
        self.tab_width = self.sidebar_width // len(self.tabs)
    
    def setup_colors(self):
        """Setup color scheme"""
        self.colors = {
            'background': (40, 46, 58),
            'board_light': (240, 217, 181),
            'board_dark': (181, 136, 99),
            'highlight': (255, 255, 0, 100),
            'last_move': (255, 255, 0, 80),
            'best_move': (0, 255, 0, 100),
            'text_primary': (255, 255, 255),
            'text_secondary': (181, 181, 181),
            'accent': (129, 182, 76),
            'error': (255, 100, 100),
            'warning': (255, 200, 100),
            'tab_active': (60, 70, 85),
            'tab_inactive': (50, 56, 68),
            'panel': (45, 52, 65),
            'border': (84, 92, 108)
        }
    
    def set_analyzer(self, analyzer):
        """Set the game analyzer"""
        self.analyzer = analyzer
        if analyzer and analyzer.game_moves:
            self.move_history = analyzer.game_moves.copy()
            self.board = chess.Board()
            self.current_move_index = 0
    
    def activate(self, initial_fen=None):
        """Activate analysis mode"""
        self.active = True
        if initial_fen:
            try:
                self.board = chess.Board(initial_fen)
            except:
                self.board = chess.Board()
        self.update_board_position()
        logger.info("Analysis interface activated")
    
    def deactivate(self):
        """Deactivate analysis mode"""
        self.active = False
        self.auto_play = False
        self._cached_surfaces.clear()
        logger.info("Analysis interface deactivated")
    
    def render(self, surface):
        """Main render method"""
        if not self.active:
            return
        
        # Check if we need to re-render (performance optimization)
        current_hash = self._get_render_hash()
        if current_hash == self._last_render_hash and not self.auto_play:
            return
        
        self._last_render_hash = current_hash
        
        # Clear background
        surface.fill(self.colors['background'])
        
        # Render components
        self._render_board(surface)
        self._render_sidebar(surface)
        
        # Handle auto-play
        if self.auto_play and self.analyzer and self.analyzer.is_analysis_complete():
            current_time = pygame.time.get_ticks()
            if current_time - self.last_auto_play_time >= self.auto_play_speed:
                self.next_move()
                self.last_auto_play_time = current_time
    
    def _get_render_hash(self):
        """Get hash for render state (for caching)"""
        return hash((
            self.current_move_index,
            self.current_tab,
            self.show_evaluation_bar,
            self.show_move_arrows,
            self.auto_play
        ))
    
    def _render_board(self, surface):
        """Render the chess board"""
        # Board background
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(surface, self.colors['border'], board_rect, 2)
        
        # Squares
        for row in range(8):
            for col in range(8):
                self._render_square(surface, row, col)
        
        # Coordinates
        self._render_coordinates(surface)
        
        # Pieces
        self._render_pieces(surface)
        
        # Highlights and arrows
        self._render_highlights(surface)
        if self.show_move_arrows:
            self._render_move_arrows(surface)
    
    def _render_square(self, surface, row, col):
        """Render a single square"""
        x = self.board_x + col * self.square_size
        y = self.board_y + row * self.square_size
        
        # Square color
        is_light = (row + col) % 2 == 0
        color = self.colors['board_light'] if is_light else self.colors['board_dark']
        
        square_rect = pygame.Rect(x, y, self.square_size, self.square_size)
        pygame.draw.rect(surface, color, square_rect)
    
    def _render_coordinates(self, surface):
        """Render board coordinates"""
        font = resource_manager.get_font('Arial', 12)
        
        # Files (a-h)
        for col in range(8):
            file_char = chr(ord('a') + col)
            text = font.render(file_char, True, self.colors['text_secondary'])
            x = self.board_x + col * self.square_size + self.square_size - 15
            y = self.board_y + self.board_size + 5
            surface.blit(text, (x, y))
        
        # Ranks (1-8)
        for row in range(8):
            rank_char = str(8 - row)
            text = font.render(rank_char, True, self.colors['text_secondary'])
            x = self.board_x - 15
            y = self.board_y + row * self.square_size + 5
            surface.blit(text, (x, y))
    
    def _render_pieces(self, surface):
        """Render pieces on the board"""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - (square // 8)
                col = square % 8
                
                x = self.board_x + col * self.square_size
                y = self.board_y + row * self.square_size
                
                # Get piece image
                color_name = 'white' if piece.color else 'black'
                piece_name = piece.symbol().lower()
                if piece_name == 'p':
                    piece_name = 'pawn'
                elif piece_name == 'r':
                    piece_name = 'rook'
                elif piece_name == 'n':
                    piece_name = 'knight'
                elif piece_name == 'b':
                    piece_name = 'bishop'
                elif piece_name == 'q':
                    piece_name = 'queen'
                elif piece_name == 'k':
                    piece_name = 'king'
                
                piece_image = resource_manager.get_piece_image(piece_name, color_name, self.square_size)
                if piece_image:
                    surface.blit(piece_image, (x, y))
                else:
                    # Fallback text rendering
                    font = resource_manager.get_font('Arial', self.square_size // 2, bold=True)
                    text = font.render(piece.symbol(), True, self.colors['text_primary'])
                    text_rect = text.get_rect(center=(x + self.square_size // 2, y + self.square_size // 2))
                    surface.blit(text, text_rect)
    
    def _render_highlights(self, surface):
        """Render move highlights"""
        if not self.move_history or self.current_move_index >= len(self.move_history):
            return
        
        # Get current move
        move_data = self.move_history[self.current_move_index]
        if 'move' in move_data:
            move = move_data['move']
            
            # Highlight last move
            from_square = move.from_square
            to_square = move.to_square
            
            # From square
            from_row = 7 - (from_square // 8)
            from_col = from_square % 8
            from_x = self.board_x + from_col * self.square_size
            from_y = self.board_y + from_row * self.square_size
            
            highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight_surface.fill(self.colors['last_move'])
            surface.blit(highlight_surface, (from_x, from_y))
            
            # To square
            to_row = 7 - (to_square // 8)
            to_col = to_square % 8
            to_x = self.board_x + to_col * self.square_size
            to_y = self.board_y + to_row * self.square_size
            
            surface.blit(highlight_surface, (to_x, to_y))
    
    def _render_move_arrows(self, surface):
        """Render move arrows"""
        if not self.analyzer or not self.analyzer.is_analysis_complete():
            return
        
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves):
            return
        
        move_analysis = analyzed_moves[self.current_move_index]
        if 'best_moves' in move_analysis:
            for i, best_move in enumerate(move_analysis['best_moves'][:3]):
                if 'move' in best_move:
                    self._draw_move_arrow(surface, best_move['move'], i)
    
    def _draw_move_arrow(self, surface, move, index):
        """Draw an arrow for a move"""
        from_square = move.from_square
        to_square = move.to_square
        
        # Calculate positions
        from_row = 7 - (from_square // 8)
        from_col = from_square % 8
        from_x = self.board_x + from_col * self.square_size + self.square_size // 2
        from_y = self.board_y + from_row * self.square_size + self.square_size // 2
        
        to_row = 7 - (to_square // 8)
        to_col = to_square % 8
        to_x = self.board_x + to_col * self.square_size + self.square_size // 2
        to_y = self.board_y + to_row * self.square_size + self.square_size // 2
        
        # Arrow color based on ranking
        colors = [self.colors['best_move'], (255, 255, 0, 100), (255, 165, 0, 100)]
        color = colors[min(index, len(colors) - 1)]
        
        # Draw arrow (simplified)
        pygame.draw.line(surface, color[:3], (from_x, from_y), (to_x, to_y), 3)
    
    def _render_sidebar(self, surface):
        """Render the analysis sidebar"""
        # Tab bar
        self._render_tab_bar(surface)
        
        # Tab content
        content_y = self.board_y + self.tab_height
        content_height = self.sidebar_height - self.tab_height
        
        if self.current_tab == 0:  # Analysis
            self._render_analysis_tab(surface, content_y, content_height)
        elif self.current_tab == 1:  # Summary
            self._render_summary_tab(surface, content_y, content_height)
        elif self.current_tab == 2:  # Opening
            self._render_opening_tab(surface, content_y, content_height)
        elif self.current_tab == 3:  # Statistics
            self._render_statistics_tab(surface, content_y, content_height)
    
    def _render_tab_bar(self, surface):
        """Render tab bar"""
        for i, tab_name in enumerate(self.tabs):
            x = self.sidebar_x + i * self.tab_width
            y = self.board_y
            
            # Tab background
            is_active = i == self.current_tab
            color = self.colors['tab_active'] if is_active else self.colors['tab_inactive']
            
            tab_rect = pygame.Rect(x, y, self.tab_width, self.tab_height)
            pygame.draw.rect(surface, color, tab_rect)
            pygame.draw.rect(surface, self.colors['border'], tab_rect, 1)
            
            # Tab text
            font = resource_manager.get_font('Arial', 14, bold=is_active)
            text_color = self.colors['text_primary'] if is_active else self.colors['text_secondary']
            text = font.render(tab_name, True, text_color)
            text_rect = text.get_rect(center=tab_rect.center)
            surface.blit(text, text_rect)
    
    def _render_analysis_tab(self, surface, y, height):
        """Render analysis tab content"""
        panel_rect = pygame.Rect(self.sidebar_x, y, self.sidebar_width, height)
        pygame.draw.rect(surface, self.colors['panel'], panel_rect)
        pygame.draw.rect(surface, self.colors['border'], panel_rect, 1)
        
        if not self.analyzer:
            font = resource_manager.get_font('Arial', 16)
            text = font.render("No analysis data available", True, self.colors['text_secondary'])
            text_rect = text.get_rect(center=panel_rect.center)
            surface.blit(text, text_rect)
            return
        
        # Analysis progress
        current_y = y + 20
        if not self.analyzer.is_analysis_complete():
            progress = self.analyzer.get_analysis_progress()
            self._render_progress_bar(surface, self.sidebar_x + 20, current_y, 
                                    self.sidebar_width - 40, 20, progress)
            current_y += 40
        
        # Current move analysis
        if self.analyzer.is_analysis_complete():
            self._render_current_move_analysis(surface, current_y)
    
    def _render_progress_bar(self, surface, x, y, width, height, progress):
        """Render progress bar"""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.colors['tab_inactive'], bg_rect)
        pygame.draw.rect(surface, self.colors['border'], bg_rect, 1)
        
        # Progress
        if progress > 0:
            progress_width = int(width * progress / 100)
            progress_rect = pygame.Rect(x, y, progress_width, height)
            pygame.draw.rect(surface, self.colors['accent'], progress_rect)
        
        # Text
        font = resource_manager.get_font('Arial', 12)
        text = font.render(f"Analysis: {progress:.1f}%", True, self.colors['text_primary'])
        text_rect = text.get_rect(center=bg_rect.center)
        surface.blit(text, text_rect)
    
    def _render_current_move_analysis(self, surface, y):
        """Render current move analysis"""
        analyzed_moves = self.analyzer.get_analyzed_moves()
        if self.current_move_index >= len(analyzed_moves):
            return
        
        move_analysis = analyzed_moves[self.current_move_index]
        font = resource_manager.get_font('Arial', 14)
        
        current_y = y
        
        # Move notation
        if 'notation' in move_analysis:
            text = font.render(f"Move: {move_analysis['notation']}", True, self.colors['text_primary'])
            surface.blit(text, (self.sidebar_x + 20, current_y))
            current_y += 25
        
        # Classification
        if 'classification' in move_analysis:
            classification = move_analysis['classification']
            color = self._get_classification_color(classification)
            text = font.render(f"Quality: {classification}", True, color)
            surface.blit(text, (self.sidebar_x + 20, current_y))
            current_y += 25
        
        # Evaluation
        if 'evaluation_after' in move_analysis:
            eval_text = self._format_evaluation(move_analysis['evaluation_after'])
            text = font.render(f"Evaluation: {eval_text}", True, self.colors['text_primary'])
            surface.blit(text, (self.sidebar_x + 20, current_y))
            current_y += 25
    
    def _get_classification_color(self, classification):
        """Get color for move classification"""
        colors = {
            'BRILLIANT': (255, 215, 0),
            'GREAT': (129, 182, 76),
            'BEST': (129, 182, 76),
            'EXCELLENT': (129, 182, 76),
            'GOOD': (129, 182, 76),
            'OKAY': (255, 255, 255),
            'INACCURACY': (255, 200, 100),
            'MISTAKE': (255, 165, 0),
            'BLUNDER': (255, 100, 100)
        }
        return colors.get(classification, self.colors['text_primary'])
    
    def _format_evaluation(self, evaluation):
        """Format evaluation for display"""
        if evaluation is None:
            return "N/A"
        
        if isinstance(evaluation, dict):
            if evaluation.get('type') == 'mate':
                mate_in = evaluation.get('value', 0)
                return f"Mate in {abs(mate_in)}"
            elif evaluation.get('type') == 'cp':
                cp_value = evaluation.get('value', 0)
                return f"{cp_value/100:.2f}"
        
        return str(evaluation)
    
    def _render_summary_tab(self, surface, y, height):
        """Render summary tab content"""
        panel_rect = pygame.Rect(self.sidebar_x, y, self.sidebar_width, height)
        pygame.draw.rect(surface, self.colors['panel'], panel_rect)
        pygame.draw.rect(surface, self.colors['border'], panel_rect, 1)
        
        if not self.analyzer or not self.analyzer.is_analysis_complete():
            font = resource_manager.get_font('Arial', 16)
            text = font.render("Analysis not complete", True, self.colors['text_secondary'])
            text_rect = text.get_rect(center=panel_rect.center)
            surface.blit(text, text_rect)
            return
        
        # Get summary data
        summary = self.analyzer.get_game_summary()
        if not summary:
            return
        
        font = resource_manager.get_font('Arial', 14)
        current_y = y + 20
        
        # Accuracy
        text = font.render(f"Overall Accuracy: {summary.get('accuracy', 0):.1f}%", 
                          True, self.colors['text_primary'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        # Player accuracies
        text = font.render(f"White: {summary.get('white_accuracy', 0):.1f}%", 
                          True, self.colors['text_primary'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        text = font.render(f"Black: {summary.get('black_accuracy', 0):.1f}%", 
                          True, self.colors['text_primary'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        # Move counts
        current_y += 10
        text = font.render("Move Quality:", True, self.colors['accent'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        for quality in ['brilliant_moves', 'great_moves', 'best_moves', 'mistakes', 'blunders']:
            count = summary.get(quality, 0)
            quality_name = quality.replace('_', ' ').title()
            text = font.render(f"{quality_name}: {count}", True, self.colors['text_primary'])
            surface.blit(text, (self.sidebar_x + 40, current_y))
            current_y += 20
    
    def _render_opening_tab(self, surface, y, height):
        """Render opening tab content"""
        panel_rect = pygame.Rect(self.sidebar_x, y, self.sidebar_width, height)
        pygame.draw.rect(surface, self.colors['panel'], panel_rect)
        pygame.draw.rect(surface, self.colors['border'], panel_rect, 1)
        
        font = resource_manager.get_font('Arial', 14)
        current_y = y + 20
        
        if self.opening_db:
            opening = self.opening_db.detect_opening(self.board)
            if opening:
                text = font.render(f"Opening: {opening['name']}", True, self.colors['text_primary'])
                surface.blit(text, (self.sidebar_x + 20, current_y))
                current_y += 25
                
                text = font.render(f"ECO: {opening['eco']}", True, self.colors['text_secondary'])
                surface.blit(text, (self.sidebar_x + 20, current_y))
                current_y += 25
            else:
                text = font.render("Opening: Unknown", True, self.colors['text_secondary'])
                surface.blit(text, (self.sidebar_x + 20, current_y))
        else:
            text = font.render("Opening database not available", True, self.colors['text_secondary'])
            surface.blit(text, (self.sidebar_x + 20, current_y))
    
    def _render_statistics_tab(self, surface, y, height):
        """Render statistics tab content"""
        panel_rect = pygame.Rect(self.sidebar_x, y, self.sidebar_width, height)
        pygame.draw.rect(surface, self.colors['panel'], panel_rect)
        pygame.draw.rect(surface, self.colors['border'], panel_rect, 1)
        
        font = resource_manager.get_font('Arial', 14)
        current_y = y + 20
        
        # Resource manager stats
        stats = resource_manager.get_cache_stats()
        text = font.render("Resource Usage:", True, self.colors['accent'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        for key, value in stats.items():
            text = font.render(f"{key.title()}: {value}", True, self.colors['text_primary'])
            surface.blit(text, (self.sidebar_x + 40, current_y))
            current_y += 20
        
        # Thread manager stats
        current_y += 10
        thread_stats = thread_manager.get_stats()
        text = font.render("Thread Usage:", True, self.colors['accent'])
        surface.blit(text, (self.sidebar_x + 20, current_y))
        current_y += 25
        
        for key, value in thread_stats.items():
            text = font.render(f"{key.replace('_', ' ').title()}: {value}", 
                              True, self.colors['text_primary'])
            surface.blit(text, (self.sidebar_x + 40, current_y))
            current_y += 20
    
    def handle_input(self, event):
        """Handle input events"""
        if not self.active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                self.previous_move()
                return True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                self.next_move()
                return True
            elif event.key == pygame.K_HOME:
                self.jump_to_move(0)
                return True
            elif event.key == pygame.K_END:
                self.jump_to_move(len(self.move_history) - 1)
                return True
            elif event.key == pygame.K_SPACE:
                self.toggle_auto_play()
                return True
            elif event.key == pygame.K_e:
                self.show_evaluation_bar = not self.show_evaluation_bar
                return True
            elif event.key == pygame.K_a:
                self.show_move_arrows = not self.show_move_arrows
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check tab clicks
                if self._handle_tab_click(event.pos):
                    return True
        
        return False
    
    def _handle_tab_click(self, pos):
        """Handle tab bar clicks"""
        x, y = pos
        if (self.sidebar_x <= x <= self.sidebar_x + self.sidebar_width and
            self.board_y <= y <= self.board_y + self.tab_height):
            
            tab_index = (x - self.sidebar_x) // self.tab_width
            if 0 <= tab_index < len(self.tabs):
                self.current_tab = tab_index
                return True
        return False
    
    def next_move(self):
        """Navigate to next move"""
        if self.current_move_index < len(self.move_history) - 1:
            self.current_move_index += 1
            self.update_board_position()
    
    def previous_move(self):
        """Navigate to previous move"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self.update_board_position()
    
    def jump_to_move(self, move_index):
        """Jump to specific move"""
        if 0 <= move_index < len(self.move_history):
            self.current_move_index = move_index
            self.update_board_position()
    
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.last_auto_play_time = pygame.time.get_ticks()
        logger.info(f"Auto-play {'enabled' if self.auto_play else 'disabled'}")
    
    def update_board_position(self):
        """Update board position based on current move"""
        if not self.move_history:
            return
        
        # Reset board and replay moves up to current index
        self.board = chess.Board()
        for i in range(min(self.current_move_index + 1, len(self.move_history))):
            move_data = self.move_history[i]
            if 'move' in move_data:
                try:
                    self.board.push(move_data['move'])
                except:
                    logger.warning(f"Invalid move at index {i}")
                    break
    
    def get_current_move(self):
        """Get current move data"""
        if 0 <= self.current_move_index < len(self.move_history):
            return self.move_history[self.current_move_index]
        return None