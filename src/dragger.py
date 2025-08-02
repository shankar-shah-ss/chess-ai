# [file name]: dragger.py
import pygame

from const import *

class Dragger:
    """
    Chess.com-style piece selector - handles piece selection and move highlighting
    instead of drag-and-drop functionality
    """

    def __init__(self):
        self.piece = None
        self.selected = False  # Changed from 'dragging' to 'selected'
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0

    # Legacy compatibility - keeping dragging property for existing code
    @property
    def dragging(self):
        return self.selected
    
    @dragging.setter
    def dragging(self, value):
        self.selected = value

    def update_mouse(self, pos):
        """Update mouse position (kept for compatibility)"""
        self.mouseX, self.mouseY = pos

    def save_initial(self, pos):
        """Save initial click position"""
        self.initial_row = pos[1] // SQSIZE
        self.initial_col = pos[0] // SQSIZE

    def select_piece(self, piece, row, col):
        """Select a piece at the given position (chess.com style)"""
        self.piece = piece
        self.selected = True
        self.initial_row = row
        self.initial_col = col

    def deselect_piece(self):
        """Deselect the currently selected piece"""
        self.piece = None
        self.selected = False
        self.initial_row = 0
        self.initial_col = 0

    # Legacy methods for compatibility
    def drag_piece(self, piece):
        """Legacy method - now just selects the piece"""
        if hasattr(piece, 'moves') and piece.moves:
            self.piece = piece
            self.selected = True

    def undrag_piece(self):
        """Legacy method - now deselects the piece"""
        self.deselect_piece()
        
    def get_selected_square(self):
        """Get the currently selected square coordinates"""
        if self.selected:
            return (self.initial_row, self.initial_col)
        return None

    def is_piece_selected(self):
        """Check if a piece is currently selected"""
        return self.selected and self.piece is not None

    def get_selected_piece(self):
        """Get the currently selected piece"""
        return self.piece if self.selected else None
# [file content end]