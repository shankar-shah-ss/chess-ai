# analysis_manager.py - Updated with unified interface and enhanced features
import pygame
from enhanced_analysis import EnhancedGameAnalyzer
from unified_analysis_interface import UnifiedAnalysisInterface
from game_summary import GameSummaryWidget
from error_handling import safe_execute, logger
from resource_manager import resource_manager

class AnalysisManager:
    def __init__(self, config, engine):
        self.config = config
        self.engine = engine
        
        # Analysis components with enhanced Chess.com-style interface
        from opening_database import OpeningDatabase
        self.opening_db = OpeningDatabase()
        
        self.analyzer = EnhancedGameAnalyzer(engine)
        self.analysis_interface = UnifiedAnalysisInterface(config, self.opening_db)
        self.summary_widget = GameSummaryWidget(config)
        
        # Connect components
        self.analysis_interface.set_analyzer(self.analyzer)
        self.summary_widget.set_analyzer(self.analyzer)
        
        # State management
        self.active = False
        self.show_summary = False
        self.analysis_started = False
        
        # Screen modes
        self.SCREEN_GAME = 0
        self.SCREEN_ANALYSIS = 1
        self.current_screen = self.SCREEN_GAME
        
        # Auto-play settings
        self.auto_play = False
        self.auto_play_speed = 1000  # milliseconds
        self.last_auto_play_time = 0
        
        # UI state
        self.show_controls_help = False
        
    @safe_execute(fallback_value=None, context="record_move")
    def record_move(self, move, player, position):
        """Record a move for analysis"""
        if not self.active:
            self.analyzer.record_move(move, player, position)
            
    @safe_execute(fallback_value=False, context="start_analysis", retry_count=2)
    def start_analysis(self):
        """Start the analysis process"""
        if not self.analysis_started and len(self.analyzer.game_moves) > 0:
            # Check if engine is healthy before starting
            if not self.engine or not hasattr(self.engine, '_is_healthy') or not self.engine._is_healthy:
                logger.warning("Engine not healthy, cannot start analysis")
                return False
                
            self.analysis_started = True
            logger.info("Starting game analysis...")
            return self.analyzer.start_analysis()
        return False
        
    def enter_analysis_mode(self, initial_fen=None):
        """Enter modern analysis mode"""
        try:
            if len(self.analyzer.game_moves) > 0:
                self.active = True
                self.current_screen = self.SCREEN_ANALYSIS
                # Pass initial FEN to analysis screen
                if hasattr(self.analysis_interface, 'activate'):
                    self.analysis_interface.activate(initial_fen)
                
                # Start analysis if not already started
                if not self.analysis_started:
                    self.start_analysis()
                return True
        except Exception as e:
            print(f"Error entering analysis mode: {e}")
        return False
    
    def exit_analysis_mode(self):
        """Exit analysis mode"""
        self.active = False
        self.current_screen = self.SCREEN_GAME
        self.analysis_interface.deactivate()
        self.show_summary = False
        self.auto_play = False
        self.show_controls_help = False
        
    def toggle_summary(self):
        """Toggle game summary widget"""
        if self.active and self.analyzer.is_analysis_complete():
            self.show_summary = not self.show_summary
            if self.show_summary:
                # Position summary widget in center
                screen_center_x = self.config.WIDTH // 2 if hasattr(self.config, 'WIDTH') else 400
                screen_center_y = self.config.HEIGHT // 2 if hasattr(self.config, 'HEIGHT') else 300
                
                self.summary_widget.set_position(
                    screen_center_x - self.summary_widget.width // 2,
                    screen_center_y - self.summary_widget.height // 2
                )
                self.summary_widget.show()
            else:
                self.summary_widget.hide()
                
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        if self.active and self.analyzer.is_analysis_complete():
            self.auto_play = not self.auto_play
            self.last_auto_play_time = pygame.time.get_ticks()
            
    def set_auto_play_speed(self, speed):
        """Set auto-play speed in milliseconds"""
        self.auto_play_speed = max(100, min(5000, speed))
        
    def toggle_controls_help(self):
        """Toggle controls help display"""
        self.show_controls_help = not self.show_controls_help
        
    def update(self):
        """Update analysis manager (call this in main loop)"""
        if not self.active:
            return
            
        # Handle auto-play
        if self.auto_play and self.analyzer.is_analysis_complete():
            current_time = pygame.time.get_ticks()
            if current_time - self.last_auto_play_time >= self.auto_play_speed:
                self.analysis_interface.next_move()
                self.last_auto_play_time = current_time
                
    def render(self, surface):
        """Render analysis components with modern styling"""
        if not self.active:
            return False
            
        if self.current_screen == self.SCREEN_ANALYSIS:
            # Render modern analysis screen
            self.analysis_interface.render(surface)
            
            # Render summary widget if active
            if self.show_summary:
                self.summary_widget.render(surface)
                
            # Render controls help if active
            if self.show_controls_help:
                self._render_controls_help(surface)
                
            # Render status indicators
            self._render_status_indicators(surface)
                
            return True
            
        return False
        
    def _render_controls_help(self, surface):
        """Render modern controls help overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Help panel
        panel_width = 400
        panel_height = 300
        panel_x = (surface.get_width() - panel_width) // 2
        panel_y = (surface.get_height() - panel_height) // 2
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, (40, 46, 58), panel_rect, border_radius=20)
        pygame.draw.rect(surface, (84, 92, 108), panel_rect, 3, border_radius=20)
        
        # Title
        title_font = pygame.font.SysFont('Segoe UI', 24, bold=True)
        title_surface = title_font.render("Controls", True, (255, 255, 255))
        surface.blit(title_surface, (panel_x + 20, panel_y + 20))
        
        # Controls list
        controls_font = pygame.font.SysFont('Segoe UI', 14)
        controls = [
            ("←/→ or ↑/↓", "Navigate moves"),
            ("Space", "Toggle auto-play"),
            ("Ctrl+S", "Show/hide summary"),
            ("E", "Toggle evaluation bar"),
            ("H", "Show/hide this help"),
            ("Escape", "Exit analysis"),
            ("Home/End", "First/last move"),
            ("Click", "Jump to move")
        ]
        
        y_offset = 70
        for key, description in controls:
            # Key
            key_surface = controls_font.render(key, True, (129, 182, 76))
            surface.blit(key_surface, (panel_x + 30, panel_y + y_offset))
            
            # Description
            desc_surface = controls_font.render(description, True, (181, 181, 181))
            surface.blit(desc_surface, (panel_x + 150, panel_y + y_offset))
            
            y_offset += 25
            
        # Close instruction
        close_font = pygame.font.SysFont('Segoe UI', 12)
        close_surface = close_font.render("Press 'H' again to close", True, (129, 182, 76))
        close_rect = close_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + panel_height - 20))
        surface.blit(close_surface, close_rect)
        
    def _render_status_indicators(self, surface):
        """Render status indicators"""
        if not self.analyzer.is_analysis_complete():
            return
            
        # Auto-play indicator
        if self.auto_play:
            indicator_font = pygame.font.SysFont('Segoe UI', 12, bold=True)
            indicator_surface = indicator_font.render("AUTO-PLAY ON", True, (129, 182, 76))
            surface.blit(indicator_surface, (20, surface.get_height() - 40))
            
            # Speed indicator
            speed_text = f"Speed: {2000 - self.auto_play_speed}ms"
            speed_surface = indicator_font.render(speed_text, True, (181, 181, 181))
            surface.blit(speed_surface, (20, surface.get_height() - 20))
        
    def handle_input(self, event):
        """Handle input events with modern key bindings"""
        if not self.active:
            return False
            
        # Handle summary widget input first
        if self.show_summary and self.summary_widget.handle_input(event):
            return True
            
        # Handle screen-specific input
        if self.current_screen == self.SCREEN_ANALYSIS:
            if self.analysis_interface.handle_input(event):
                return True
                
        # Handle manager-specific input
        if event.type == pygame.KEYDOWN:
            # Summary toggle
            if event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.toggle_summary()
                return True
                
            # Auto-play controls
            elif event.key == pygame.K_SPACE:
                self.toggle_auto_play()
                return True
                
            # Speed controls
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.set_auto_play_speed(max(100, self.auto_play_speed - 200))
                return True
                
            elif event.key == pygame.K_MINUS:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.set_auto_play_speed(min(5000, self.auto_play_speed + 200))
                return True
                
            # Help toggle
            elif event.key == pygame.K_h:
                self.toggle_controls_help()
                return True
                
            # Exit controls
            elif event.key == pygame.K_ESCAPE:
                if self.show_controls_help:
                    self.toggle_controls_help()
                elif self.show_summary:
                    self.toggle_summary()
                else:
                    self.exit_analysis_mode()
                return True
                
        return False
        
    def get_analysis_progress(self):
        """Get analysis progress percentage"""
        return self.analyzer.get_analysis_progress()
        
    def is_analysis_complete(self):
        """Check if analysis is complete"""
        return self.analyzer.is_analysis_complete()
        
    def get_current_move_analysis(self):
        """Get current move analysis"""
        if self.current_screen == self.SCREEN_ANALYSIS:
            return self.analysis_interface.get_current_move()
        return None
        
    def get_game_summary(self):
        """Get comprehensive game analysis summary"""
        return self.analyzer.get_game_summary()
        
    def jump_to_move(self, move_number):
        """Jump to specific move in analysis"""
        if self.active and self.current_screen == self.SCREEN_ANALYSIS:
            self.analysis_interface.jump_to_move(move_number)
            
    def get_analysis_stats(self):
        """Get detailed analysis statistics for display"""
        if not self.analyzer.is_analysis_complete():
            return {
                'progress': self.analyzer.get_analysis_progress(),
                'total_moves': len(self.analyzer.game_moves),
                'analyzed_moves': len(self.analyzer.get_analyzed_moves()),
                'status': 'analyzing'
            }
            
        summary = self.analyzer.get_game_summary()
        if summary:
            return {
                'progress': 100,
                'status': 'complete',
                'total_moves': summary['total_moves'],
                'analyzed_moves': summary['total_moves'],
                
                # Accuracy metrics
                'overall_accuracy': summary['accuracy'],
                'white_accuracy': summary['white_accuracy'],
                'black_accuracy': summary['black_accuracy'],
                
                # ELO estimates
                'white_elo': summary['white_elo'],
                'black_elo': summary['black_elo'],
                
                # Key move counts
                'brilliant_moves': summary['brilliant_moves'],
                'great_moves': summary['great_moves'],
                'best_moves': summary['best_moves'],
                'mistakes': summary['mistakes'],
                'blunders': summary['blunders'],
                
                # Phase analysis
                'opening_accuracy': summary.get('opening_accuracy', 0),
                'middlegame_accuracy': summary.get('middlegame_accuracy', 0),
                'endgame_accuracy': summary.get('endgame_accuracy', 0),
                
                # Additional metrics
                'total_eval_loss': summary.get('total_eval_loss', 0),
                'average_eval_loss': summary.get('average_eval_loss', 0),
                'sacrifices_made': summary.get('sacrifices_made', 0)
            }
        return None
        
    def export_analysis(self, filename):
        """Export analysis to file (future feature)"""
        # This could export the analysis to PGN with annotations
        summary = self.get_game_summary()
        if summary:
            try:
                with open(filename, 'w') as f:
                    f.write("# Chess Game Analysis Export\n")
                    f.write(f"Total Moves: {summary['total_moves']}\n")
                    f.write(f"White Accuracy: {summary['white_accuracy']:.1f}%\n")
                    f.write(f"Black Accuracy: {summary['black_accuracy']:.1f}%\n")
                    f.write(f"White ELO: {summary['white_elo']}\n")
                    f.write(f"Black ELO: {summary['black_elo']}\n")
                    f.write(f"Brilliant Moves: {summary['brilliant_moves']}\n")
                    f.write(f"Blunders: {summary['blunders']}\n")
                    f.write("\n# Move Details:\n")
                    
                    for move in self.analyzer.get_analyzed_moves():
                        f.write(f"Move {move.move_number} ({move.player}): ")
                        f.write(f"{move.classification} - Loss: {move.eval_loss}\n")
                        
                return True
            except Exception as e:
                print(f"Error exporting analysis: {e}")
                return False
        return False
        
    def reset(self):
        """Reset analysis manager"""
        try:
            # Stop any ongoing analysis
            if hasattr(self.analyzer, 'stop_analysis'):
                self.analyzer.stop_analysis()
            
            self.analyzer.reset()
            self.active = False
            self.show_summary = False
            self.analysis_started = False
            self.current_screen = self.SCREEN_GAME
            self.auto_play = False
            self.show_controls_help = False
            
            if hasattr(self.summary_widget, 'hide'):
                self.summary_widget.hide()
            if hasattr(self.analysis_interface, 'deactivate'):
                self.analysis_interface.deactivate()
        except Exception as e:
            print(f"Error resetting analysis manager: {e}")
    
