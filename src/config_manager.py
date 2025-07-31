# config_manager.py - Centralized configuration management
import json
import os
import pygame
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from sound import Sound
from theme import Theme

@dataclass
class EngineConfig:
    """Engine configuration"""
    stockfish_path: str = "stockfish"
    default_depth: int = 15
    default_skill_level: int = 10
    max_depth: int = 20
    max_skill_level: int = 20
    timeout_seconds: int = 30

@dataclass
class UIConfig:
    """UI configuration"""
    window_width: int = 900
    window_height: int = 900
    fullscreen: bool = False
    theme_index: int = 0
    show_coordinates: bool = True
    show_move_history: bool = True
    show_evaluation_bar: bool = True
    animation_speed: float = 1.0

@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    auto_analyze: bool = False
    analysis_depth: int = 18
    max_analysis_time: int = 300  # seconds
    show_best_moves: int = 3
    classification_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.classification_thresholds is None:
            self.classification_thresholds = {
                'BLUNDER': 3.0,
                'MISTAKE': 1.5,
                'INACCURACY': 0.5,
                'OKAY': 0.25
            }

@dataclass
class GameConfig:
    """Game configuration"""
    default_game_mode: int = 0  # 0: Human vs Human
    auto_save_pgn: bool = True
    pgn_directory: str = "games"
    sound_enabled: bool = True
    move_validation: bool = True
    font_size: int = 18
    font_bold: bool = True

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_file: str = "chess_ai_config.json"):
        # Ensure pygame is fully initialized
        if not pygame.get_init():
            pygame.init()
        else:
            pygame.mixer.init()  # Initialize mixer first
            pygame.font.init()   # Initialize font system
        
        self.config_file = Path(config_file)
        self.engine = EngineConfig()
        self.ui = UIConfig()
        self.analysis = AnalysisConfig()
        self.game = GameConfig()
        
        # Theme and sound management (from old config.py)
        self.themes = []
        self._add_themes()
        self.theme = self.themes[self.ui.theme_index]
        self.font = pygame.font.SysFont('monospace', self.game.font_size, bold=self.game.font_bold)
        
        self.load_config()
        
        # Load sounds after config is loaded
        self._load_sounds()
        
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                # Update configurations
                if 'engine' in data:
                    self._update_dataclass(self.engine, data['engine'])
                if 'ui' in data:
                    self._update_dataclass(self.ui, data['ui'])
                    # Update theme after loading UI config
                    self.ui.theme_index = max(0, min(self.ui.theme_index, len(self.themes) - 1))
                    self.theme = self.themes[self.ui.theme_index]
                if 'analysis' in data:
                    self._update_dataclass(self.analysis, data['analysis'])
                if 'game' in data:
                    self._update_dataclass(self.game, data['game'])
                    # Update font after loading game config
                    self.font = pygame.font.SysFont('monospace', self.game.font_size, bold=self.game.font_bold)
                    
                print(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"Error loading config: {e}")
                self.create_default_config()
        else:
            self.create_default_config()
            
    def save_config(self):
        """Save configuration to file"""
        try:
            config_data = {
                'engine': asdict(self.engine),
                'ui': asdict(self.ui),
                'analysis': asdict(self.analysis),
                'game': asdict(self.game)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def create_default_config(self):
        """Create default configuration file"""
        self.save_config()
        print("Default configuration created")
        
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """Update dataclass with dictionary data"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
                
    def get_stockfish_path(self) -> str:
        """Get Stockfish path with fallbacks"""
        paths_to_try = [
            self.engine.stockfish_path,
            "stockfish",
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
            os.path.expanduser("~/stockfish/stockfish")
        ]
        
        for path in paths_to_try:
            if os.path.exists(path) or self._is_in_path(path):
                return path
                
        raise FileNotFoundError("Stockfish not found. Please install Stockfish or set STOCKFISH_PATH")
        
    def _is_in_path(self, program: str) -> bool:
        """Check if program is in system PATH"""
        try:
            import subprocess
            subprocess.run([program, "--version"], 
                         capture_output=True, timeout=5)
            return True
        except:
            return False
            
    def update_engine_config(self, **kwargs):
        """Update engine configuration"""
        for key, value in kwargs.items():
            if hasattr(self.engine, key):
                setattr(self.engine, key, value)
        self.save_config()
        
    def update_ui_config(self, **kwargs):
        """Update UI configuration"""
        for key, value in kwargs.items():
            if hasattr(self.ui, key):
                setattr(self.ui, key, value)
        self.save_config()
        
    def update_analysis_config(self, **kwargs):
        """Update analysis configuration"""
        for key, value in kwargs.items():
            if hasattr(self.analysis, key):
                setattr(self.analysis, key, value)
        self.save_config()
        
    def reset_to_defaults(self):
        """Reset all configurations to defaults"""
        self.engine = EngineConfig()
        self.ui = UIConfig()
        self.analysis = AnalysisConfig()
        self.game = GameConfig()
        self.save_config()
        
    def export_config(self, filename: str):
        """Export configuration to specified file"""
        config_data = {
            'engine': asdict(self.engine),
            'ui': asdict(self.ui),
            'analysis': asdict(self.analysis),
            'game': asdict(self.game)
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    def import_config(self, filename: str):
        """Import configuration from specified file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            
        if 'engine' in data:
            self._update_dataclass(self.engine, data['engine'])
        if 'ui' in data:
            self._update_dataclass(self.ui, data['ui'])
        if 'analysis' in data:
            self._update_dataclass(self.analysis, data['analysis'])
        if 'game' in data:
            self._update_dataclass(self.game, data['game'])
            
        self.save_config()
        
    def _add_themes(self):
        """Add predefined themes"""
        green = Theme((234, 235, 200), (119, 154, 88), (244, 247, 116), (172, 195, 51), '#C86464', '#C84646')
        brown = Theme((235, 209, 166), (165, 117, 80), (245, 234, 100), (209, 185, 59), '#C86464', '#C84646')
        blue = Theme((229, 228, 200), (60, 95, 135), (123, 187, 227), (43, 119, 191), '#C86464', '#C84646')
        gray = Theme((120, 119, 118), (86, 85, 84), (99, 126, 143), (82, 102, 128), '#C86464', '#C84646')
        self.themes = [green, brown, blue, gray]
        
    def _load_sounds(self):
        """Load sound files"""
        if self.game.sound_enabled:
            self.move_sound = self._load_sound('move.wav')
            self.capture_sound = self._load_sound('capture.wav')
            self.check_sound = self._load_sound('check.wav')
        else:
            self.move_sound = None
            self.capture_sound = None
            self.check_sound = None
            
    def _load_sound(self, filename):
        """Load a sound file"""
        paths = [
            os.path.join('..', 'assets', 'sounds', filename),
            os.path.join('assets', 'sounds', filename)
        ]
        
        for path in paths:
            if os.path.exists(path):
                return Sound(path)
        print(f"Warning: Sound file not found - {filename}")
        return None
        
    def change_theme(self):
        """Change to next theme"""
        self.ui.theme_index = (self.ui.theme_index + 1) % len(self.themes)
        self.theme = self.themes[self.ui.theme_index]
        self.save_config()
        
    def update_game_config(self, **kwargs):
        """Update game configuration"""
        for key, value in kwargs.items():
            if hasattr(self.game, key):
                setattr(self.game, key, value)
        self.save_config()
        
        # Reload sounds if sound_enabled changed
        if 'sound_enabled' in kwargs:
            self._load_sounds()
            
        # Reload font if font settings changed
        if 'font_size' in kwargs or 'font_bold' in kwargs:
            self.font = pygame.font.SysFont('monospace', self.game.font_size, bold=self.game.font_bold)

# Global configuration instance
config_manager = ConfigManager()