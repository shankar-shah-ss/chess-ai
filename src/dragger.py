# [file name]: dragger.py
# [file content begin]
import pygame

from const import *

class Dragger:

    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0

    # blit method

    def update_blit(self, surface):
        # texture
        self.piece.set_texture(size=128)
        texture = self.piece.texture
        try:
            # img
            img = pygame.image.load(texture)
            # rect
            img_center = (self.mouseX, self.mouseY)
            self.piece.texture_rect = img.get_rect(center=img_center)
            # blit
            surface.blit(img, self.piece.texture_rect)
        except pygame.error:
            # Fallback to simple colored circle if image loading fails
            color = (255, 255, 255) if self.piece.color == 'white' else (0, 0, 0)
            pygame.draw.circle(surface, color, (self.mouseX, self.mouseY), SQSIZE // 3)
            pygame.draw.circle(surface, (128, 128, 128), (self.mouseX, self.mouseY), SQSIZE // 3, 2)

    # other methods

    def update_mouse(self, pos):
        self.mouseX, self.mouseY = pos # (xcor, ycor)

    def save_initial(self, pos):
        self.initial_row = pos[1] // SQSIZE
        self.initial_col = pos[0] // SQSIZE

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = True

    def undrag_piece(self):
        self.piece = None
        self.dragging = False
        
    def get_selected_square(self):
        """Get the currently selected square coordinates"""
        if self.dragging:
            return (self.initial_row, self.initial_col)
        return None
# [file content end]