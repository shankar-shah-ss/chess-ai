"""
Analysis File Manager
Handles PGN file loading, saving, and management for the analysis system
"""

import os
import pygame
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

class AnalysisFileManager:
    """
    Professional file management for chess analysis
    Handles PGN files, analysis exports, and game databases
    """
    
    def __init__(self):
        self.games_directory = "games"
        self.analysis_directory = "analysis"
        self.pgn_directory = "pgn_files"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Recent files tracking
        self.recent_files = []
        self.max_recent_files = 10
        self._load_recent_files()
        
        print("📁 Analysis File Manager initialized")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.games_directory,
            self.analysis_directory,
            self.pgn_directory,
            os.path.join(self.games_directory, "imported"),
            os.path.join(self.analysis_directory, "exports"),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _load_recent_files(self):
        """Load recent files list"""
        recent_file = "recent_files.json"
        try:
            if os.path.exists(recent_file):
                with open(recent_file, 'r') as f:
                    self.recent_files = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load recent files: {e}")
            self.recent_files = []
    
    def _save_recent_files(self):
        """Save recent files list"""
        try:
            with open("recent_files.json", 'w') as f:
                json.dump(self.recent_files, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save recent files: {e}")
    
    def _add_to_recent(self, filepath: str):
        """Add file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        
        self.recent_files.insert(0, filepath)
        
        # Keep only max_recent_files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        self._save_recent_files()
    
    def open_pgn_file_dialog(self) -> Optional[str]:
        """Open file dialog to select PGN file"""
        try:
            # Hide pygame window temporarily
            pygame.display.iconify()
            
            # Create tkinter root (hidden)
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Open file dialog
            filepath = filedialog.askopenfilename(
                title="Select PGN File",
                filetypes=[
                    ("PGN files", "*.pgn"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialdir=self.pgn_directory
            )
            
            root.destroy()
            
            # Restore pygame window
            pygame.display.set_mode(pygame.display.get_surface().get_size())
            
            if filepath:
                self._add_to_recent(filepath)
                print(f"📂 Selected PGN file: {os.path.basename(filepath)}")
                return filepath
            
            return None
            
        except Exception as e:
            print(f"❌ File dialog error: {e}")
            return None
    
    def save_pgn_file_dialog(self, pgn_content: str) -> bool:
        """Save PGN content to file"""
        try:
            # Hide pygame window temporarily
            pygame.display.iconify()
            
            # Create tkinter root (hidden)
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"chess_game_{timestamp}.pgn"
            
            # Open save dialog
            filepath = filedialog.asksaveasfilename(
                title="Save PGN File",
                defaultextension=".pgn",
                filetypes=[
                    ("PGN files", "*.pgn"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ],
                initialdir=self.pgn_directory,
                initialfile=default_name
            )
            
            root.destroy()
            
            # Restore pygame window
            pygame.display.set_mode(pygame.display.get_surface().get_size())
            
            if filepath:
                with open(filepath, 'w') as f:
                    f.write(pgn_content)
                
                self._add_to_recent(filepath)
                print(f"💾 PGN saved: {os.path.basename(filepath)}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Save PGN error: {e}")
            return False
    
    def save_analysis_export(self, analysis_data: str, game_name: str = None) -> bool:
        """Save analysis export to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if game_name:
                filename = f"analysis_{game_name}_{timestamp}.json"
            else:
                filename = f"analysis_export_{timestamp}.json"
            
            filepath = os.path.join(self.analysis_directory, "exports", filename)
            
            with open(filepath, 'w') as f:
                f.write(analysis_data)
            
            print(f"📊 Analysis exported: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Export analysis error: {e}")
            return False
    
    def load_pgn_content(self, filepath: str) -> Optional[str]:
        """Load PGN content from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📖 Loaded PGN: {os.path.basename(filepath)} ({len(content)} chars)")
            return content
            
        except Exception as e:
            print(f"❌ Load PGN error: {e}")
            return None
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files"""
        # Filter out files that no longer exist
        existing_files = []
        for filepath in self.recent_files:
            if os.path.exists(filepath):
                existing_files.append(filepath)
        
        if len(existing_files) != len(self.recent_files):
            self.recent_files = existing_files
            self._save_recent_files()
        
        return self.recent_files.copy()
    
    def get_pgn_files_in_directory(self) -> List[Dict[str, Any]]:
        """Get list of PGN files in the pgn directory"""
        pgn_files = []
        
        try:
            for filename in os.listdir(self.pgn_directory):
                if filename.lower().endswith(('.pgn', '.txt')):
                    filepath = os.path.join(self.pgn_directory, filename)
                    stat = os.stat(filepath)
                    
                    pgn_files.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'size_str': self._format_file_size(stat.st_size)
                    })
            
            # Sort by modification time (newest first)
            pgn_files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error listing PGN files: {e}")
        
        return pgn_files
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def create_sample_pgn_files(self):
        """Create sample PGN files for demonstration"""
        sample_games = [
            {
                'filename': 'immortal_game.pgn',
                'content': '''[Event "Immortal Game"]
[Site "London"]
[Date "1851.06.21"]
[Round "?"]
[White "Adolf Anderssen"]
[Black "Lionel Kieseritzky"]
[Result "1-0"]

1. e4 e5 2. f4 exf4 3. Bc4 Qh4+ 4. Kf1 b5 5. Bxb5 Nf6 6. Nf3 Qh6 7. d3 Nh5 8. Nh4 Qg5 9. Nf5 c6 10. g4 Nf6 11. Rg1 cxb5 12. h4 Qg6 13. h5 Qg5 14. Qf3 Ng8 15. Bxf4 Qf6 16. Nc3 Bc5 17. Nd5 Qxb2 18. Bd6 Bxg1 19. e5 Qxa1+ 20. Ke2 Na6 21. Nxg7+ Kd8 22. Qf6+ Nxf6 23. Be7# 1-0'''
            },
            {
                'filename': 'evergreen_game.pgn',
                'content': '''[Event "Evergreen Game"]
[Site "Berlin"]
[Date "1852.??.??"]
[Round "?"]
[White "Adolf Anderssen"]
[Black "Jean Dufresne"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 Bxb4 5. c3 Ba5 6. d4 exd4 7. O-O d3 8. Qb3 Qf6 9. e5 Qg6 10. Re1 Nge7 11. Ba3 b5 12. Qxb5 Rb8 13. Qa4 Bb6 14. Nbd2 Bb7 15. Ne4 Qf5 16. Bxd3 Qh5 17. Nf6+ gxf6 18. exf6 Rg8 19. Rad1 Qxf3 20. Rxe7+ Nxe7 21. Qxd7+ Kxd7 22. Bf5+ Ke8 23. Bd7+ Kf8 24. Bxe7# 1-0'''
            },
            {
                'filename': 'opera_game.pgn',
                'content': '''[Event "Opera Game"]
[Site "Paris Opera"]
[Date "1858.??.??"]
[Round "?"]
[White "Paul Morphy"]
[Black "Duke Karl / Count Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0'''
            }
        ]
        
        for game in sample_games:
            filepath = os.path.join(self.pgn_directory, game['filename'])
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w') as f:
                        f.write(game['content'])
                    print(f"📝 Created sample game: {game['filename']}")
                except Exception as e:
                    print(f"❌ Error creating sample game: {e}")
    
    def render_file_browser(self, screen: pygame.Surface, rect: pygame.Rect):
        """Render a simple file browser UI"""
        # Background
        pygame.draw.rect(screen, (250, 250, 250), rect)
        pygame.draw.rect(screen, (200, 200, 200), rect, 2)
        
        font = pygame.font.Font(None, 18)
        small_font = pygame.font.Font(None, 14)
        
        # Title
        title = font.render("PGN Files", True, (0, 0, 0))
        screen.blit(title, (rect.x + 5, rect.y + 5))
        
        # Get PGN files
        pgn_files = self.get_pgn_files_in_directory()
        
        y_offset = 30
        max_files = (rect.height - 60) // 20  # Space for files
        
        for i, file_info in enumerate(pgn_files[:max_files]):
            file_y = rect.y + y_offset + i * 20
            
            # File name
            name_text = small_font.render(file_info['name'][:30], True, (0, 0, 100))
            screen.blit(name_text, (rect.x + 5, file_y))
            
            # File size
            size_text = small_font.render(file_info['size_str'], True, (100, 100, 100))
            screen.blit(size_text, (rect.x + rect.width - 60, file_y))
        
        # "Open File" button
        button_rect = pygame.Rect(rect.x + 5, rect.bottom - 25, 80, 20)
        pygame.draw.rect(screen, (220, 220, 220), button_rect)
        pygame.draw.rect(screen, (100, 100, 100), button_rect, 1)
        
        button_text = small_font.render("Open File", True, (0, 0, 0))
        text_rect = button_text.get_rect(center=button_rect.center)
        screen.blit(button_text, text_rect)
        
        return button_rect  # Return button rect for click detection
    
    def handle_file_browser_click(self, pos: tuple, button_rect: pygame.Rect) -> Optional[str]:
        """Handle clicks in the file browser"""
        if button_rect.collidepoint(pos):
            return self.open_pgn_file_dialog()
        return None

# Global instance
analysis_file_manager = AnalysisFileManager()