"""
Game Setup Screen - Mode Selection and Engine Configuration
"""

import pygame
import sys
from typing import Optional, Tuple, Dict

class GameSetup:
    """Game setup screen for mode selection and engine configuration"""
    
    def __init__(self, screen_width=900, screen_height=900):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = None
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (200, 200, 200)
        self.DARK_GRAY = (64, 64, 64)
        self.BLUE = (0, 100, 200)
        self.LIGHT_BLUE = (100, 150, 255)
        self.GREEN = (0, 150, 0)
        self.RED = (200, 0, 0)
        
        # Game modes
        self.game_modes = [
            {"name": "Human vs Human", "mode": 0, "desc": "Two human players"},
            {"name": "Human vs Engine", "mode": 1, "desc": "Human plays against AI"},
            {"name": "Engine vs Engine", "mode": 2, "desc": "Watch AI vs AI battle"}
        ]
        
        # Engine strength settings
        self.white_engine_elo = 2000
        self.black_engine_elo = 2000
        self.min_elo = 800
        self.max_elo = 3600
        
        # UI state
        self.selected_mode = 1  # Default to Human vs Engine
        self.setup_complete = False
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        # Button states
        self.buttons = {}
        self.sliders = {}
        
    def initialize(self, screen):
        """Initialize the setup screen"""
        try:
            self.screen = screen
            
            # Initialize fonts
            pygame.font.init()
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
            
            # Create UI elements
            self._create_buttons()
            self._create_sliders()
            
            print("✓ Game setup screen initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing game setup screen: {e}")
            # Fallback to minimal setup
            self.font_large = pygame.font.Font(None, 36)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
        
    def _create_buttons(self):
        """Create interactive buttons"""
        button_width = 300
        button_height = 60
        start_y = 200
        
        for i, mode in enumerate(self.game_modes):
            y = start_y + i * 80
            self.buttons[f"mode_{mode['mode']}"] = {
                'rect': pygame.Rect(self.screen_width // 2 - button_width // 2, y, button_width, button_height),
                'text': mode['name'],
                'mode': mode['mode'],
                'selected': mode['mode'] == self.selected_mode
            }
        
        # Start game button
        self.buttons['start'] = {
            'rect': pygame.Rect(self.screen_width // 2 - 100, self.screen_height - 100, 200, 50),
            'text': 'Start Game',
            'action': 'start'
        }
        
        # ELO adjustment buttons
        if self.selected_mode in [1, 2]:  # Engine modes
            self._create_elo_buttons()
    
    def _create_elo_buttons(self):
        """Create ELO adjustment buttons"""
        # White engine controls (if applicable)
        if self.selected_mode == 2:  # Engine vs Engine
            # White engine
            self.buttons['white_elo_down'] = {
                'rect': pygame.Rect(150, 500, 30, 30),
                'text': '-',
                'action': 'white_elo_down'
            }
            self.buttons['white_elo_up'] = {
                'rect': pygame.Rect(320, 500, 30, 30),
                'text': '+',
                'action': 'white_elo_up'
            }
            
            # Black engine
            self.buttons['black_elo_down'] = {
                'rect': pygame.Rect(550, 500, 30, 30),
                'text': '-',
                'action': 'black_elo_down'
            }
            self.buttons['black_elo_up'] = {
                'rect': pygame.Rect(720, 500, 30, 30),
                'text': '+',
                'action': 'black_elo_up'
            }
        
        elif self.selected_mode == 1:  # Human vs Engine
            # Black engine only
            self.buttons['black_elo_down'] = {
                'rect': pygame.Rect(self.screen_width // 2 - 100, 500, 30, 30),
                'text': '-',
                'action': 'black_elo_down'
            }
            self.buttons['black_elo_up'] = {
                'rect': pygame.Rect(self.screen_width // 2 + 70, 500, 30, 30),
                'text': '+',
                'action': 'black_elo_up'
            }
    
    def _create_sliders(self):
        """Create ELO sliders"""
        if self.selected_mode == 2:  # Engine vs Engine
            # White engine slider
            self.sliders['white_elo'] = {
                'rect': pygame.Rect(180, 505, 140, 20),
                'min_val': self.min_elo,
                'max_val': self.max_elo,
                'current_val': self.white_engine_elo,
                'dragging': False
            }
            
            # Black engine slider
            self.sliders['black_elo'] = {
                'rect': pygame.Rect(580, 505, 140, 20),
                'min_val': self.min_elo,
                'max_val': self.max_elo,
                'current_val': self.black_engine_elo,
                'dragging': False
            }
        
        elif self.selected_mode == 1:  # Human vs Engine
            # Black engine slider only
            self.sliders['black_elo'] = {
                'rect': pygame.Rect(self.screen_width // 2 - 70, 505, 140, 20),
                'min_val': self.min_elo,
                'max_val': self.max_elo,
                'current_val': self.black_engine_elo,
                'dragging': False
            }
    
    def handle_event(self, event) -> bool:
        """Handle pygame events. Returns True if setup is complete."""
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._handle_click(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left click release
                self._handle_click_release(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.setup_complete = True
                return True
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        
        return self.setup_complete
    
    def _handle_click(self, pos):
        """Handle mouse click"""
        # Check mode buttons - create a copy of items to avoid RuntimeError
        buttons_copy = list(self.buttons.items())
        for button_id, button in buttons_copy:
            if button['rect'].collidepoint(pos):
                if button_id.startswith('mode_'):
                    self.selected_mode = button['mode']
                    self._update_ui_for_mode()
                elif button_id == 'start':
                    self.setup_complete = True
                elif button_id.endswith('_elo_up'):
                    self._adjust_elo(button_id, 100)
                elif button_id.endswith('_elo_down'):
                    self._adjust_elo(button_id, -100)
        
        # Check sliders
        sliders_copy = list(self.sliders.items())
        for slider_id, slider in sliders_copy:
            if slider['rect'].collidepoint(pos):
                slider['dragging'] = True
                self._update_slider_value(slider_id, pos)
    
    def _handle_click_release(self, pos):
        """Handle mouse click release"""
        for slider in self.sliders.values():
            slider['dragging'] = False
    
    def _handle_mouse_motion(self, pos):
        """Handle mouse motion"""
        sliders_copy = list(self.sliders.items())
        for slider_id, slider in sliders_copy:
            if slider['dragging']:
                self._update_slider_value(slider_id, pos)
    
    def _adjust_elo(self, button_id, delta):
        """Adjust ELO rating"""
        if 'white' in button_id:
            self.white_engine_elo = max(self.min_elo, min(self.max_elo, self.white_engine_elo + delta))
            if 'white_elo' in self.sliders:
                self.sliders['white_elo']['current_val'] = self.white_engine_elo
        elif 'black' in button_id:
            self.black_engine_elo = max(self.min_elo, min(self.max_elo, self.black_engine_elo + delta))
            if 'black_elo' in self.sliders:
                self.sliders['black_elo']['current_val'] = self.black_engine_elo
    
    def _update_slider_value(self, slider_id, pos):
        """Update slider value based on mouse position"""
        slider = self.sliders[slider_id]
        rect = slider['rect']
        
        # Calculate relative position
        rel_x = max(0, min(rect.width, pos[0] - rect.x))
        ratio = rel_x / rect.width
        
        # Calculate new value
        value_range = slider['max_val'] - slider['min_val']
        new_value = slider['min_val'] + int(ratio * value_range)
        
        # Round to nearest 50
        new_value = round(new_value / 50) * 50
        
        slider['current_val'] = new_value
        
        # Update corresponding ELO
        if slider_id == 'white_elo':
            self.white_engine_elo = new_value
        elif slider_id == 'black_elo':
            self.black_engine_elo = new_value
    
    def _update_ui_for_mode(self):
        """Update UI elements when mode changes"""
        # Clear existing ELO buttons and sliders
        keys_to_remove = [k for k in list(self.buttons.keys()) if 'elo' in k]
        for key in keys_to_remove:
            del self.buttons[key]
        self.sliders.clear()
        
        # Update button selection
        buttons_copy = list(self.buttons.items())
        for button_id, button in buttons_copy:
            if button_id.startswith('mode_'):
                button['selected'] = button['mode'] == self.selected_mode
        
        # Recreate ELO controls
        self._create_elo_buttons()
        self._create_sliders()
    
    def draw(self):
        """Draw the setup screen"""
        try:
            self.screen.fill(self.WHITE)
            
            # Title
            if self.font_large:
                title = self.font_large.render("Chess AI - Game Setup", True, self.BLACK)
                title_rect = title.get_rect(center=(self.screen_width // 2, 80))
                self.screen.blit(title, title_rect)
        except Exception as e:
            print(f"Error drawing setup screen: {e}")
            # Fallback drawing
            self.screen.fill(self.WHITE)
        
        # Mode selection
        mode_title = self.font_medium.render("Select Game Mode:", True, self.BLACK)
        self.screen.blit(mode_title, (self.screen_width // 2 - 100, 150))
        
        # Draw mode buttons
        buttons_copy = list(self.buttons.items())
        for button_id, button in buttons_copy:
            if button_id.startswith('mode_'):
                self._draw_mode_button(button)
        
        # Draw engine strength controls
        if self.selected_mode in [1, 2]:
            self._draw_engine_controls()
        
        # Draw start button
        if 'start' in self.buttons:
            self._draw_start_button()
        
        # Instructions
        instructions = [
            "Use mouse to select options",
            "Press ENTER to start game",
            "Press ESC to exit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, self.GRAY)
            self.screen.blit(text, (20, self.screen_height - 80 + i * 25))
    
    def _draw_mode_button(self, button):
        """Draw a mode selection button"""
        rect = button['rect']
        color = self.LIGHT_BLUE if button.get('selected', False) else self.LIGHT_GRAY
        border_color = self.BLUE if button.get('selected', False) else self.GRAY
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)
        
        # Button text
        text = self.font_medium.render(button['text'], True, self.BLACK)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)
        
        # Description
        mode_info = next(m for m in self.game_modes if m['mode'] == button['mode'])
        desc_text = self.font_small.render(mode_info['desc'], True, self.GRAY)
        desc_rect = desc_text.get_rect(center=(rect.centerx, rect.bottom + 15))
        self.screen.blit(desc_text, desc_rect)
    
    def _draw_engine_controls(self):
        """Draw engine strength controls"""
        controls_y = 450
        
        # Title
        title = self.font_medium.render("Engine Strength Settings:", True, self.BLACK)
        self.screen.blit(title, (self.screen_width // 2 - 120, controls_y))
        
        if self.selected_mode == 2:  # Engine vs Engine
            # White engine
            white_label = self.font_small.render("White Engine ELO:", True, self.BLACK)
            self.screen.blit(white_label, (150, controls_y + 40))
            
            # Black engine
            black_label = self.font_small.render("Black Engine ELO:", True, self.BLACK)
            self.screen.blit(black_label, (550, controls_y + 40))
            
            # Draw sliders and values
            self._draw_elo_control('white_elo', self.white_engine_elo, 150)
            self._draw_elo_control('black_elo', self.black_engine_elo, 550)
            
        elif self.selected_mode == 1:  # Human vs Engine
            # Black engine only
            engine_label = self.font_small.render("AI Engine ELO:", True, self.BLACK)
            self.screen.blit(engine_label, (self.screen_width // 2 - 70, controls_y + 40))
            
            self._draw_elo_control('black_elo', self.black_engine_elo, self.screen_width // 2 - 70)
    
    def _draw_elo_control(self, slider_id, elo_value, x_pos):
        """Draw ELO control (slider + buttons + value)"""
        y_pos = 500
        
        # Draw buttons
        if f"{slider_id.split('_')[0]}_elo_down" in self.buttons:
            down_button = self.buttons[f"{slider_id.split('_')[0]}_elo_down"]
            up_button = self.buttons[f"{slider_id.split('_')[0]}_elo_up"]
            
            pygame.draw.rect(self.screen, self.LIGHT_GRAY, down_button['rect'])
            pygame.draw.rect(self.screen, self.GRAY, down_button['rect'], 1)
            pygame.draw.rect(self.screen, self.LIGHT_GRAY, up_button['rect'])
            pygame.draw.rect(self.screen, self.GRAY, up_button['rect'], 1)
            
            # Button text
            down_text = self.font_small.render("-", True, self.BLACK)
            up_text = self.font_small.render("+", True, self.BLACK)
            
            down_rect = down_text.get_rect(center=down_button['rect'].center)
            up_rect = up_text.get_rect(center=up_button['rect'].center)
            
            self.screen.blit(down_text, down_rect)
            self.screen.blit(up_text, up_rect)
        
        # Draw slider
        if slider_id in self.sliders:
            slider = self.sliders[slider_id]
            slider_rect = slider['rect']
            
            # Slider track
            pygame.draw.rect(self.screen, self.GRAY, slider_rect)
            
            # Slider handle
            value_ratio = (slider['current_val'] - slider['min_val']) / (slider['max_val'] - slider['min_val'])
            handle_x = slider_rect.x + int(value_ratio * slider_rect.width)
            handle_rect = pygame.Rect(handle_x - 5, slider_rect.y - 2, 10, slider_rect.height + 4)
            pygame.draw.rect(self.screen, self.BLUE, handle_rect)
        
        # ELO value and category
        elo_text = self.font_small.render(f"{elo_value}", True, self.BLACK)
        category = self._get_elo_category(elo_value)
        category_text = self.font_small.render(f"({category})", True, self.GRAY)
        
        self.screen.blit(elo_text, (x_pos + 75, y_pos + 30))
        self.screen.blit(category_text, (x_pos + 75, y_pos + 50))
    
    def _draw_start_button(self):
        """Draw the start game button"""
        button = self.buttons['start']
        rect = button['rect']
        
        pygame.draw.rect(self.screen, self.GREEN, rect)
        pygame.draw.rect(self.screen, self.DARK_GRAY, rect, 2)
        
        text = self.font_medium.render(button['text'], True, self.WHITE)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)
    
    def _get_elo_category(self, elo):
        """Get ELO category name"""
        if elo <= 1200: return "Beginner"
        elif elo <= 1600: return "Casual"
        elif elo <= 2000: return "Club Player"
        elif elo <= 2200: return "Expert"
        elif elo <= 2400: return "Master"
        elif elo <= 2500: return "International Master"
        elif elo <= 2700: return "Grandmaster"
        elif elo <= 2800: return "Super GM"
        else: return "Engine Max"  # 2800-3600
    
    def get_game_config(self) -> Dict:
        """Get the configured game settings"""
        return {
            'game_mode': self.selected_mode,
            'white_engine_elo': self.white_engine_elo if self.selected_mode == 2 else None,
            'black_engine_elo': self.black_engine_elo if self.selected_mode in [1, 2] else None
        }