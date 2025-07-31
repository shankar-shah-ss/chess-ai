# move_display.py - Real-time move display with algebraic notation
import pygame
from notation import ChessNotation

class MoveDisplay:
    def __init__(self, config, board):
        self.config = config
        self.board = board
        self.notation = ChessNotation(board)
        self.move_history = []
        self.visible = True
        self.scroll_offset = 0
        self.max_visible_moves = 10
        
        # Display settings
        self.width = 300
        self.height = 400
        self.x = 20  # Position on screen (top left)
        self.y = 20
        
        # Fonts
        self.title_font = pygame.font.SysFont('Segoe UI', 16, bold=True)
        self.move_font = pygame.font.SysFont('Consolas', 14)  # Monospace for alignment
        self.small_font = pygame.font.SysFont('Segoe UI', 12)
        
        # Colors
        self.bg_color = (40, 46, 58, 180)  # Semi-transparent
        self.border_color = (84, 92, 108, 200)
        self.text_color = (255, 255, 255)
        self.move_color = (181, 181, 181)
        self.highlight_color = (129, 182, 76)
        self.white_move_bg = (50, 56, 68)
        self.black_move_bg = (45, 51, 63)
        
    def add_move(self, move, piece, captured=False, check=False, checkmate=False, 
                 promotion_piece=None, eval_before=None, eval_after=None):
        """Add a move to the display"""
        # Generate algebraic notation
        algebraic = self.notation.move_to_algebraic(
            move, piece, captured, check, checkmate,
            promotion_piece is not None, promotion_piece
        )
        
        # Calculate move number
        move_number = (len(self.move_history) // 2) + 1
        is_white = len(self.move_history) % 2 == 0
        
        # Store move data
        move_data = {
            'number': move_number,
            'notation': algebraic,
            'is_white': is_white,
            'piece': piece.name,
            'captured': captured,
            'check': check,
            'checkmate': checkmate,
            'eval_before': eval_before,
            'eval_after': eval_after,
            'eval_change': None
        }
        
        # Calculate evaluation change
        if eval_before is not None and eval_after is not None:
            if eval_before.get('type') == 'cp' and eval_after.get('type') == 'cp':
                change = eval_after['value'] - eval_before['value']
                # Adjust for player perspective
                if not is_white:
                    change = -change
                move_data['eval_change'] = change
        
        self.move_history.append(move_data)
        
        # Auto-scroll to bottom
        self._auto_scroll()
        
        return algebraic
    
    def render(self, surface, analysis_active=False):
        """Render the move display"""
        if not self.visible or analysis_active:
            return
        
        # Background panel with transparency
        panel_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, self.bg_color, pygame.Rect(0, 0, self.width, self.height), border_radius=10)
        pygame.draw.rect(panel_surface, self.border_color, pygame.Rect(0, 0, self.width, self.height), 2, border_radius=10)
        surface.blit(panel_surface, (self.x, self.y))
        
        # Title
        title_surface = self.title_font.render("Move History", True, self.text_color)
        surface.blit(title_surface, (self.x + 15, self.y + 15))
        
        # Move count
        total_moves = len([m for m in self.move_history if m['is_white']])
        if len(self.move_history) % 2 == 1:
            total_moves += 1
        
        count_text = f"Moves: {total_moves}"
        count_surface = self.small_font.render(count_text, True, self.move_color)
        surface.blit(count_surface, (self.x + self.width - 80, self.y + 18))
        
        # Moves list
        self._render_moves(surface)
        
        # Scroll indicators
        if self.scroll_offset > 0:
            # Up arrow
            pygame.draw.polygon(surface, self.highlight_color, [
                (self.x + self.width - 20, self.y + 50),
                (self.x + self.width - 15, self.y + 45),
                (self.x + self.width - 10, self.y + 50)
            ])
        
        if self.scroll_offset + self.max_visible_moves < len(self.move_history):
            # Down arrow
            pygame.draw.polygon(surface, self.highlight_color, [
                (self.x + self.width - 20, self.y + self.height - 30),
                (self.x + self.width - 15, self.y + self.height - 25),
                (self.x + self.width - 10, self.y + self.height - 30)
            ])
    
    def _render_moves(self, surface):
        """Render the moves list"""
        start_y = self.y + 50
        line_height = 25
        
        # Calculate visible range
        start_idx = max(0, self.scroll_offset)
        end_idx = min(len(self.move_history), start_idx + self.max_visible_moves)
        
        current_y = start_y
        current_move_num = None
        
        for i in range(start_idx, end_idx):
            move = self.move_history[i]
            
            # Alternate background for move pairs
            if move['is_white']:
                bg_color = self.white_move_bg
                current_move_num = move['number']
            else:
                bg_color = self.black_move_bg
            
            # Background for move
            move_rect = pygame.Rect(self.x + 5, current_y - 2, self.width - 10, line_height)
            pygame.draw.rect(surface, bg_color, move_rect, border_radius=3)
            
            # Move number (only for white moves)
            x_offset = self.x + 15
            if move['is_white']:
                num_text = f"{move['number']}."
                num_surface = self.move_font.render(num_text, True, self.move_color)
                surface.blit(num_surface, (x_offset, current_y))
                x_offset += 35
            else:
                x_offset += 35  # Align with white moves
            
            # Move notation
            notation_color = self.text_color
            
            # Color code based on special moves
            if move['checkmate']:
                notation_color = (242, 113, 102)  # Red for checkmate
            elif move['check']:
                notation_color = (255, 193, 7)   # Yellow for check
            elif move['captured']:
                notation_color = (129, 182, 76)  # Green for captures
            
            notation_surface = self.move_font.render(move['notation'], True, notation_color)
            surface.blit(notation_surface, (x_offset, current_y))
            
            # Evaluation change indicator
            if move['eval_change'] is not None:
                self._render_eval_change(surface, move['eval_change'], 
                                       self.x + self.width - 60, current_y)
            
            current_y += line_height
    
    def _render_eval_change(self, surface, eval_change, x, y):
        """Render evaluation change indicator"""
        if abs(eval_change) < 10:  # Ignore small changes
            return
        
        # Determine color and symbol
        if eval_change > 50:
            color = (129, 182, 76)  # Green for good moves
            symbol = "↑"
        elif eval_change < -50:
            color = (242, 113, 102)  # Red for bad moves
            symbol = "↓"
        else:
            return  # Don't show small changes
        
        # Render indicator
        indicator_surface = self.small_font.render(symbol, True, color)
        surface.blit(indicator_surface, (x, y + 2))
        
        # Show actual change on hover (simplified)
        if abs(eval_change) > 100:
            change_text = f"{eval_change:+d}"
            change_surface = pygame.font.SysFont('Segoe UI', 10).render(
                change_text, True, color
            )
            surface.blit(change_surface, (x + 15, y + 4))
    
    def scroll_up(self):
        """Scroll up in move history"""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1
    
    def scroll_down(self):
        """Scroll down in move history"""
        max_scroll = max(0, len(self.move_history) - self.max_visible_moves)
        if self.scroll_offset < max_scroll:
            self.scroll_offset += 1
    
    def _auto_scroll(self):
        """Auto-scroll to show latest moves"""
        if len(self.move_history) > self.max_visible_moves:
            self.scroll_offset = len(self.move_history) - self.max_visible_moves
    
    def handle_click(self, pos):
        """Handle mouse clicks on move display"""
        if not self.visible:
            return None
        
        # Check if click is within panel
        if (self.x <= pos[0] <= self.x + self.width and 
            self.y <= pos[1] <= self.y + self.height):
            
            # Calculate which move was clicked
            click_y = pos[1] - (self.y + 50)
            if click_y >= 0:
                line_height = 25
                move_index = self.scroll_offset + (click_y // line_height)
                
                if 0 <= move_index < len(self.move_history):
                    return move_index
        
        return None
    
    def handle_scroll(self, event):
        """Handle mouse wheel scrolling"""
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.scroll_up()
            elif event.y < 0:
                self.scroll_down()
            return True
        return False
    
    def toggle_visibility(self):
        """Toggle move display visibility"""
        self.visible = not self.visible
    
    def clear_history(self):
        """Clear move history"""
        self.move_history = []
        self.scroll_offset = 0
    
    def get_pgn_moves(self):
        """Get moves in PGN format"""
        pgn_moves = []
        for i, move in enumerate(self.move_history):
            if move['is_white']:
                pgn_moves.append(f"{move['number']}. {move['notation']}")
            else:
                if pgn_moves:
                    pgn_moves[-1] += f" {move['notation']}"
                else:
                    pgn_moves.append(f"{move['number']}... {move['notation']}")
        
        return " ".join(pgn_moves)
    
    def export_moves(self, filename):
        """Export moves to text file"""
        try:
            with open(filename, 'w') as f:
                f.write("Chess Game Move History\n")
                f.write("=" * 30 + "\n\n")
                
                for move in self.move_history:
                    if move['is_white']:
                        f.write(f"{move['number']}. {move['notation']}")
                    else:
                        f.write(f" {move['notation']}\n")
                
                f.write(f"\n\nTotal moves: {len(self.move_history)}")
            return True
        except Exception as e:
            print(f"Error exporting moves: {e}")
            return False