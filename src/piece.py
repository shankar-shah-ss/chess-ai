# [file name]: piece.py
# [file content begin]
import os

class Piece:

    def symbol(self):
        if self.name == 'pawn': return 'p'
        if self.name == 'knight': return 'n'
        if self.name == 'bishop': return 'b'
        if self.name == 'rook': return 'r'
        if self.name == 'queen': return 'q'
        if self.name == 'king': return 'k'
        return '?'
    
    def __repr__(self):
        return self.symbol().upper() if self.color == 'white' else self.symbol().lower()

    def __init__(self, name, color, value, texture=None, texture_rect=None):
        self.name = name
        self.color = color
        value_sign = 1 if color == 'white' else -1
        self.value = value * value_sign
        self.moves = []
        self.moved = False
        self.texture = texture
        self.set_texture()
        self.texture_rect = texture_rect

    def set_texture(self, size=128):
        # Try relative path from src directory first
        texture_path = os.path.join('..', 'assets', 'images', f'imgs-{size}px', f'{self.color}_{self.name}.png')
        if os.path.exists(texture_path):
            self.texture = texture_path
        else:
            # Fallback to original path
            self.texture = os.path.join(f'assets/images/imgs-{size}px/{self.color}_{self.name}.png')

    def add_move(self, move):
        self.moves.append(move)

    def clear_moves(self):
        self.moves = []

class Pawn(Piece):

    def __init__(self, color):
        self.dir = -1 if color == 'white' else 1  # White moves up, black moves down
        # Removed en_passant flag - we now use board's en_passant_target
        super().__init__('pawn', color, 1.0)

class Knight(Piece):

    def __init__(self, color):
        super().__init__('knight', color, 3.0)

class Bishop(Piece):

    def __init__(self, color):
        super().__init__('bishop', color, 3.001)

class Rook(Piece):

    def __init__(self, color):
        super().__init__('rook', color, 5.0)

class Queen(Piece):

    def __init__(self, color):
        super().__init__('queen', color, 9.0)

class King(Piece):

    def __init__(self, color):
        self.left_rook = None
        self.right_rook = None
        super().__init__('king', color, 10000.0)
# [file content end]