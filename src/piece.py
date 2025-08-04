# [file name]: piece.py
# [file content begin]
from os.path import join, exists, normpath, abspath
from os import sep

class Piece:
    # Class-level constant for better performance
    SYMBOLS = {
        'pawn': 'p',
        'knight': 'n', 
        'bishop': 'b',
        'rook': 'r',
        'queen': 'q',
        'king': 'k'
    }

    def symbol(self):
        return self.SYMBOLS.get(self.name, '?')
    
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
        self.texture_rect = texture_rect
        self._texture_loaded = False

    def set_texture(self, size=128):
        # Skip if already loaded with same size
        if self._texture_loaded and hasattr(self, '_last_size') and self._last_size == size:
            return
            
        # Validate inputs to prevent path traversal
        if not isinstance(size, int) or size <= 0:
            size = 128
        
        self._last_size = size
        
        # Sanitize filename components
        safe_color = self.color.replace('..', '').replace(sep, '')
        safe_name = self.name.replace('..', '').replace(sep, '')
        
        # Define allowed base paths
        base_paths = [
            join('..', 'assets', 'images', f'imgs-{size}px'),
            join('assets', 'images', f'imgs-{size}px')
        ]
        
        filename = f'{safe_color}_{safe_name}.png'
        
        for base_path in base_paths:
            # Normalize and validate path
            texture_path = normpath(join(base_path, filename))
            
            # Ensure path doesn't escape intended directory
            abs_base = abspath(base_path)
            abs_texture = abspath(texture_path)
            
            if abs_texture.startswith(abs_base) and exists(texture_path):
                self.texture = texture_path
                self._texture_loaded = True
                return
        
        # Fallback to safe default
        self.texture = join('assets', 'images', f'imgs-{size}px', f'{safe_color}_{safe_name}.png')
        self._texture_loaded = True

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