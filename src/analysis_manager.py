# analysis_manager.py
import pygame
from enhanced_analysis import EnhancedGameAnalyzer
from analysis_screen import AnalysisScreen
from game_summary import GameSummaryWidget

class AnalysisManager:
    def __init__(self, config, engine):
        self.config = config
        self.engine = engine
        
        # Analysis components
        self.analyzer = EnhancedGameAnalyzer(engine)
        self.analysis_screen = AnalysisScreen(config)
        self.summary_widget = GameSummaryWidget(config)
        
        # Connect components
        self.analysis_screen.set_analyzer(self.analyzer)
        self.summary_widget.set_analyzer(self.analyzer)
        
        # State
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
        
    def record_move(self, move, player, position):
        """Record a move for analysis"""
        if not self.active:
            self.analyzer.record_move(move, player, position)
            
    def start_analysis(self):
        """Start the analysis process"""
        if not self.analysis_started and len(self.analyzer.game_moves) > 0:
            self.analysis_started = True
            self.analyzer.start_analysis()
            return True
        return False
        
    def enter_analysis_mode(self):
        """Enter analysis mode"""
        if len(self.analyzer.game_moves) > 0:
            self.active = True
            self.current_screen = self.SCREEN_ANALYSIS
            self.analysis_screen.activate()
            
            # Start analysis if not already started
            if not self.analysis_started:
                self.start_analysis()
            return True
        return False
        
    def exit_analysis_mode(self):
        """Exit analysis mode"""
        self.active = False
        self.current_screen = self.SCREEN_GAME
        self.analysis_screen.deactivate()
        self.show_summary = False
        self.auto_play = False
        
    def toggle_summary(self):
        """Toggle game summary widget"""
        if self.active and self.analyzer.is_analysis_complete():
            self.show_summary = not self.show_summary
            if self.show_summary:
                # Position summary widget
                self.summary_widget.set_position(50, 50)
                self.summary_widget.show()
            else:
                self.summary_widget.hide()
                
    def toggle_auto_play(self):
        """Toggle auto-play mode"""
        if self.active:
            self.auto_play = not self.auto_play
            self.last_auto_play_time = pygame.time.get_ticks()
            
    def set_auto_play_speed(self, speed):
        """Set auto-play speed in milliseconds"""
        self.auto_play_speed = max(100, min(5000, speed))
        
    def update(self):
        """Update analysis manager (call this in main loop)"""
        if not self.active:
            return
            
        # Handle auto-play
        if self.auto_play and self.analyzer.is_analysis_complete():
            current_time = pygame.time.get_ticks()
            if current_time - self.last_auto_play_time >= self.auto_play_speed:
                self.analysis_screen.next_move()
                self.last_auto_play_time = current_time
                
    def render(self, surface):
        """Render analysis components"""
        if not self.active:
            return False
            
        if self.current_screen == self.SCREEN_ANALYSIS:
            # Render analysis screen
            self.analysis_screen.render(surface)
            
            # Render summary widget if active
            if self.show_summary:
                self.summary_widget.render(surface)
                
            return True
            
        return False
        
    def handle_input(self, event):
        """Handle input events"""
        if not self.active:
            return False
            
        # Handle summary widget input first
        if self.show_summary and self.summary_widget.handle_input(event):
            return True
            
        # Handle screen-specific input
        if self.current_screen == self.SCREEN_ANALYSIS:
            if self.analysis_screen.handle_input(event):
                return True
                
        # Handle manager-specific input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                self.toggle_summary()
                return True
            elif event.key == pygame.K_SPACE:
                self.toggle_auto_play()
                return True
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.set_auto_play_speed(self.auto_play_speed - 200)
                return True
            elif event.key == pygame.K_MINUS:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.set_auto_play_speed(self.auto_play_speed + 200)
                return True
            elif event.key == pygame.K_ESCAPE:
                if self.show_summary:
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
            return self.analysis_screen.get_current_move()
        return None
        
    def get_game_summary(self):
        """Get game analysis summary"""
        return self.analyzer.get_game_summary()
        
    def jump_to_move(self, move_number):
        """Jump to specific move in analysis"""
        if self.active and self.current_screen == self.SCREEN_ANALYSIS:
            self.analysis_screen.jump_to_move(move_number)
            
    def get_analysis_stats(self):
        """Get analysis statistics for display"""
        if not self.analyzer.is_analysis_complete():
            return {
                'progress': self.analyzer.get_analysis_progress(),
                'total_moves': len(self.analyzer.game_moves),
                'analyzed_moves': len(self.analyzer.get_analyzed_moves())
            }
            
        summary = self.analyzer.get_game_summary()
        if summary:
            return {
                'progress': 100,
                'total_moves': summary['total_moves'],
                'analyzed_moves': summary['total_moves'],
                'accuracy': summary['accuracy'],
                'brilliant_moves': summary['brilliant_moves'],
                'great_moves': summary['great_moves'],
                'mistakes': summary['mistakes'],
                'blunders': summary['blunders']
            }
        return None
        
    def export_analysis(self, filename):
        """Export analysis to file (future feature)"""
        # This could export the analysis to PGN with annotations
        pass
        
    def reset(self):
        """Reset analysis manager"""
        self.analyzer.reset()
        self.active = False
        self.show_summary = False
        self.analysis_started = False
        self.current_screen = self.SCREEN_GAME
        self.auto_play = False
        self.summary_widget.hide()
        self.analysis_screen.deactivate()