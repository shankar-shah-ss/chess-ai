# unified_analysis.py - Consolidated analysis system
import pygame
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class AnalysisMode(Enum):
    MODERN = "modern"
    CHESS_COM = "chess_com"
    COMPACT = "compact"

@dataclass
class MoveEvaluation:
    """Unified move evaluation structure"""
    move: str
    notation: str
    player: str
    move_number: int
    classification: str
    eval_before: float
    eval_after: float
    eval_loss: float
    best_moves: List[str]
    position_before: str
    position_after: str
    time_spent: float = 0.0
    depth_analyzed: int = 15

class UnifiedAnalysisSystem:
    """Consolidated analysis system combining all features"""
    
    def __init__(self, config, engine):
        self.config = config
        self.engine = engine
        self.mode = AnalysisMode.MODERN
        
        # Analysis data
        self.game_moves: List[Dict] = []
        self.evaluations: List[MoveEvaluation] = []
        self.analysis_complete = False
        self.analysis_progress = 0
        
        # Threading
        self.analysis_thread: Optional[threading.Thread] = None
        self.analysis_lock = threading.Lock()
        
        # UI components
        self.active = False
        self.current_move_index = 0
        self.show_evaluation_bar = True
        self.show_move_arrows = True
        
        # Performance tracking
        self.analysis_start_time = 0
        self.moves_per_second = 0
        
    def set_mode(self, mode: AnalysisMode):
        """Switch analysis display mode"""
        self.mode = mode
        
    def record_move(self, move, player: str, position: str):
        """Record a move for analysis"""
        move_data = {
            'move': move,
            'player': player,
            'position_before': position,
            'move_number': len(self.game_moves) + 1,
            'timestamp': pygame.time.get_ticks()
        }
        self.game_moves.append(move_data)
        
    def start_analysis(self) -> bool:
        """Start comprehensive analysis"""
        if self.analysis_thread and self.analysis_thread.is_alive():
            return False
            
        self.analysis_complete = False
        self.analysis_progress = 0
        self.analysis_start_time = pygame.time.get_ticks()
        
        self.analysis_thread = threading.Thread(target=self._analyze_game)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        return True
        
    def _analyze_game(self):
        """Comprehensive game analysis"""
        total_moves = len(self.game_moves)
        if total_moves == 0:
            self.analysis_complete = True
            return
            
        with self.analysis_lock:
            self.evaluations = []
            
        for i, move_data in enumerate(self.game_moves):
            try:
                evaluation = self._analyze_single_move(move_data, i)
                
                with self.analysis_lock:
                    self.evaluations.append(evaluation)
                    self.analysis_progress = int((i + 1) / total_moves * 100)
                    
            except Exception as e:
                print(f"Error analyzing move {i}: {e}")
                continue
                
        self.analysis_complete = True
        self._calculate_performance_metrics()
        
    def _analyze_single_move(self, move_data: Dict, move_index: int) -> MoveEvaluation:
        """Analyze a single move comprehensively"""
        # Set engine position
        self.engine.set_position(move_data['position_before'])
        
        # Get evaluation before move
        eval_before = self.engine.get_evaluation()
        eval_before_numeric = self._extract_numeric_eval(eval_before)
        
        # Get best moves
        best_moves = []
        for depth in [15, 18, 20]:
            self.engine.set_depth(depth)
            best_move = self.engine.get_best_move()
            if best_move and best_move not in best_moves:
                best_moves.append(best_move)
                
        # Calculate position after move
        try:
            move_uci = self._convert_to_uci(move_data['move'])
            # Simulate move and get evaluation
            # This would need proper implementation
            eval_after_numeric = eval_before_numeric  # Placeholder
        except:
            eval_after_numeric = eval_before_numeric
            
        # Classify move
        classification = self._classify_move(
            move_data['move'], best_moves, eval_before_numeric, eval_after_numeric
        )
        
        # Calculate evaluation loss
        eval_loss = max(0, eval_before_numeric - eval_after_numeric)
        
        return MoveEvaluation(
            move=str(move_data['move']),
            notation=self._get_algebraic_notation(move_data['move']),
            player=move_data['player'],
            move_number=move_data['move_number'],
            classification=classification,
            eval_before=eval_before_numeric,
            eval_after=eval_after_numeric,
            eval_loss=eval_loss,
            best_moves=best_moves,
            position_before=move_data['position_before'],
            position_after=move_data.get('position_after', ''),
            depth_analyzed=15
        )
        
    def _classify_move(self, move, best_moves: List[str], eval_before: float, eval_after: float) -> str:
        """Classify move quality"""
        try:
            move_uci = self._convert_to_uci(move)
            if move_uci == best_moves[0]:
                return "BEST"
            elif move_uci in best_moves[:2]:
                return "EXCELLENT"
            elif move_uci in best_moves[:3]:
                return "GOOD"
        except:
            pass
            
        eval_loss = eval_before - eval_after
        if eval_loss >= 3.0:
            return "BLUNDER"
        elif eval_loss >= 1.5:
            return "MISTAKE"
        elif eval_loss >= 0.5:
            return "INACCURACY"
        else:
            return "OKAY"
            
    def _extract_numeric_eval(self, evaluation) -> float:
        """Extract numeric evaluation"""
        if not evaluation:
            return 0.0
            
        if isinstance(evaluation, dict):
            if evaluation.get('type') == 'cp':
                return evaluation.get('value', 0) / 100.0
            elif evaluation.get('type') == 'mate':
                return 20.0 if evaluation.get('value', 0) > 0 else -20.0
                
        return 0.0
        
    def _convert_to_uci(self, move) -> str:
        """Convert move to UCI format"""
        if hasattr(move, 'initial') and hasattr(move, 'final'):
            col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
            from_square = f"{col_map[move.initial.col]}{8 - move.initial.row}"
            to_square = f"{col_map[move.final.col]}{8 - move.final.row}"
            return f"{from_square}{to_square}"
        return str(move)
        
    def _get_algebraic_notation(self, move) -> str:
        """Get algebraic notation for move"""
        # Simplified - would need proper implementation
        return self._convert_to_uci(move)
        
    def _calculate_performance_metrics(self):
        """Calculate performance metrics"""
        if not self.evaluations:
            return
            
        total_time = pygame.time.get_ticks() - self.analysis_start_time
        self.moves_per_second = len(self.evaluations) / (total_time / 1000.0)
        
    def get_game_summary(self) -> Dict:
        """Get comprehensive game summary"""
        if not self.analysis_complete or not self.evaluations:
            return {}
            
        # Separate by player
        white_moves = [e for e in self.evaluations if e.player == 'white']
        black_moves = [e for e in self.evaluations if e.player == 'black']
        
        # Calculate accuracies
        def calculate_accuracy(moves):
            if not moves:
                return 0
            weights = {'BEST': 1.0, 'EXCELLENT': 0.9, 'GOOD': 0.8, 'OKAY': 0.6, 
                      'INACCURACY': 0.4, 'MISTAKE': 0.2, 'BLUNDER': 0.0}
            total_weight = sum(weights.get(m.classification, 0.5) for m in moves)
            return (total_weight / len(moves)) * 100
            
        white_accuracy = calculate_accuracy(white_moves)
        black_accuracy = calculate_accuracy(black_moves)
        
        # Count classifications
        classifications = {}
        for evaluation in self.evaluations:
            classifications[evaluation.classification] = classifications.get(evaluation.classification, 0) + 1
            
        return {
            'total_moves': len(self.evaluations),
            'white_accuracy': white_accuracy,
            'black_accuracy': black_accuracy,
            'overall_accuracy': calculate_accuracy(self.evaluations),
            'classifications': classifications,
            'analysis_time': pygame.time.get_ticks() - self.analysis_start_time,
            'moves_per_second': self.moves_per_second,
            'brilliant_moves': classifications.get('BRILLIANT', 0),
            'blunders': classifications.get('BLUNDER', 0),
            'mistakes': classifications.get('MISTAKE', 0)
        }
        
    def render(self, surface):
        """Render analysis based on current mode"""
        if not self.active:
            return
            
        if self.mode == AnalysisMode.MODERN:
            self._render_modern_analysis(surface)
        elif self.mode == AnalysisMode.CHESS_COM:
            self._render_chess_com_analysis(surface)
        else:
            self._render_compact_analysis(surface)
            
    def _render_modern_analysis(self, surface):
        """Render modern analysis interface"""
        # Implementation would go here
        pass
        
    def _render_chess_com_analysis(self, surface):
        """Render Chess.com-style analysis"""
        # Implementation would go here
        pass
        
    def _render_compact_analysis(self, surface):
        """Render compact analysis view"""
        # Implementation would go here
        pass
        
    def handle_input(self, event) -> bool:
        """Handle input events"""
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_analysis_mode()
                return True
            elif event.key == pygame.K_LEFT:
                self.previous_move()
                return True
            elif event.key == pygame.K_RIGHT:
                self.next_move()
                return True
            elif event.key == pygame.K_m:
                # Switch modes
                modes = list(AnalysisMode)
                current_index = modes.index(self.mode)
                self.mode = modes[(current_index + 1) % len(modes)]
                return True
                
        return False
        
    def enter_analysis_mode(self):
        """Enter analysis mode"""
        self.active = True
        if not self.analysis_complete and self.game_moves:
            self.start_analysis()
            
    def exit_analysis_mode(self):
        """Exit analysis mode"""
        self.active = False
        
    def next_move(self):
        """Navigate to next move"""
        if self.current_move_index < len(self.evaluations) - 1:
            self.current_move_index += 1
            
    def previous_move(self):
        """Navigate to previous move"""
        if self.current_move_index > 0:
            self.current_move_index -= 1
            
    def get_analysis_progress(self) -> int:
        """Get analysis progress percentage"""
        return self.analysis_progress
        
    def is_analysis_complete(self) -> bool:
        """Check if analysis is complete"""
        return self.analysis_complete
        
    def reset(self):
        """Reset analysis system"""
        self.game_moves = []
        self.evaluations = []
        self.analysis_complete = False
        self.analysis_progress = 0
        self.active = False
        self.current_move_index = 0