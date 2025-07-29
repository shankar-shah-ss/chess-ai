# analysis.py
import threading
import time
from threading import Lock
from collections import namedtuple
import copy

MoveAnalysis = namedtuple('MoveAnalysis', [
    'move', 'player', 'position_before', 'position_after', 
    'eval_before', 'eval_after', 'best_moves', 'classification', 
    'eval_loss', 'move_number'
])

class GameAnalyzer:
    def __init__(self, engine):
        self.engine = engine
        self.game_moves = []
        self.analyzed_moves = []
        self.analysis_complete = False
        self.analysis_lock = Lock()
        self.analysis_thread = None
        self.analysis_progress = 0
        
        # Classification thresholds (in centipawns)
        self.THRESHOLDS = {
            'BLUNDER': 300,      # Loss of 3+ pawns
            'MISTAKE': 150,      # Loss of 1.5+ pawns  
            'INACCURACY': 50,    # Loss of 0.5+ pawns
            'EXCELLENT': 25,     # Within 0.25 pawns of best
            'BEST': 10,          # Within 0.1 pawns of best
        }
        
        # Classification colors for display
        self.COLORS = {
            'GREAT': (0, 100, 255),      # Blue
            'BEST': (0, 200, 0),         # Green
            'EXCELLENT': (100, 255, 100), # Light green
            'GOOD': (150, 255, 150),     # Very light green
            'INACCURACY': (255, 255, 100), # Light yellow
            'MISTAKE': (255, 165, 0),    # Orange
            'BLUNDER': (255, 0, 0)       # Red
        }
        
    def record_move(self, move, player, position_before):
        """Record a move for later analysis"""
        self.game_moves.append({
            'move': move,
            'player': player,
            'position_before': position_before,
            'move_number': len(self.game_moves) + 1
        })
        
    def start_analysis(self):
        """Start analyzing the recorded game"""
        if self.analysis_thread and self.analysis_thread.is_alive():
            return False
            
        self.analysis_complete = False
        self.analyzed_moves = []
        self.analysis_progress = 0
        self.analysis_thread = threading.Thread(target=self._analyze_game)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        return True
        
    def _analyze_game(self):
        """Analyze each move in the game"""
        total_moves = len(self.game_moves)
        if total_moves == 0:
            self.analysis_complete = True
            return
            
        for i, move_data in enumerate(self.game_moves):
            try:
                # Set position before the move
                self.engine.set_position(move_data['position_before'])
                
                # Get evaluation before move
                eval_before = self.engine.get_evaluation()
                
                # Get best moves in position
                best_moves = []
                original_depth = 15
                self.engine.set_depth(original_depth)
                
                # Get top 3 moves
                for depth in [12, 15, 18]:  # Different depths for variety
                    self.engine.set_depth(depth)
                    best_move = self.engine.get_best_move()
                    if best_move and best_move not in best_moves:
                        best_moves.append(best_move)
                    if len(best_moves) >= 3:
                        break
                
                # Reset depth
                self.engine.set_depth(original_depth)
                
                # Make the actual move and get evaluation after
                temp_board = chess.Board(move_data['position_before'])
                try:
                    actual_move_uci = self._convert_move_to_uci(move_data['move'])
                    temp_board.push(chess.Move.from_uci(actual_move_uci))
                    position_after = temp_board.fen()
                    
                    self.engine.set_position(position_after)
                    eval_after = self._flip_evaluation(self.engine.get_evaluation())
                    
                except:
                    # If move conversion fails, skip this move
                    eval_after = eval_before
                    position_after = move_data['position_before']
                
                # Classify the move
                classification, eval_loss = self._classify_move(
                    move_data['move'], best_moves, eval_before, eval_after, 
                    move_data['position_before'], i == 0
                )
                
                # Create analysis
                analysis = MoveAnalysis(
                    move=move_data['move'],
                    player=move_data['player'],
                    position_before=move_data['position_before'],
                    position_after=position_after,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    best_moves=best_moves,
                    classification=classification,
                    eval_loss=eval_loss,
                    move_number=move_data['move_number']
                )
                
                with self.analysis_lock:
                    self.analyzed_moves.append(analysis)
                    self.analysis_progress = int((i + 1) / total_moves * 100)
                    
            except Exception as e:
                print(f"Error analyzing move {i}: {e}")
                continue
                
        self.analysis_complete = True
        
    def _convert_move_to_uci(self, move):
        """Convert internal move format to UCI"""
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        
        from_col = col_map[move.initial.col]
        from_row = str(8 - move.initial.row)
        to_col = col_map[move.final.col]
        to_row = str(8 - move.final.row)
        
        return f"{from_col}{from_row}{to_col}{to_row}"
        
    def _flip_evaluation(self, evaluation):
        """Flip evaluation perspective for the opponent"""
        if not evaluation or 'value' not in evaluation:
            return evaluation
            
        flipped = evaluation.copy()
        if evaluation['type'] == 'cp':
            flipped['value'] = -evaluation['value']
        elif evaluation['type'] == 'mate':
            flipped['value'] = -evaluation['value']
            
        return flipped
        
    def _classify_move(self, actual_move, best_moves, eval_before, eval_after, position, is_first_move):
        """Classify a move based on evaluation loss and position"""
        if is_first_move:
            return 'GOOD', 0
            
        # Convert actual move to UCI for comparison
        try:
            actual_uci = self._convert_move_to_uci(actual_move)
        except:
            return 'INACCURACY', 0
            
        # Check if it's the best move
        if best_moves and actual_uci == best_moves[0]:
            return 'BEST', 0
            
        # Check if it's an excellent alternative
        if best_moves and actual_uci in best_moves[:2]:
            return 'EXCELLENT', 0
            
        # Calculate evaluation loss
        eval_loss = self._calculate_eval_loss(eval_before, eval_after)
        
        # Classify based on evaluation loss
        if eval_loss >= self.THRESHOLDS['BLUNDER']:
            return 'BLUNDER', eval_loss
        elif eval_loss >= self.THRESHOLDS['MISTAKE']:
            return 'MISTAKE', eval_loss
        elif eval_loss >= self.THRESHOLDS['INACCURACY']:
            return 'INACCURACY', eval_loss
        elif eval_loss <= self.THRESHOLDS['EXCELLENT']:
            return 'EXCELLENT', eval_loss
        elif eval_loss <= self.THRESHOLDS['BEST']:
            return 'GOOD', eval_loss
        else:
            return 'GOOD', eval_loss
            
    def _calculate_eval_loss(self, eval_before, eval_after):
        """Calculate the evaluation loss from a move"""
        if not eval_before or not eval_after:
            return 0
            
        if 'value' not in eval_before or 'value' not in eval_after:
            return 0
            
        # Handle mate scores
        if eval_before.get('type') == 'mate' or eval_after.get('type') == 'mate':
            if eval_before.get('type') == 'mate' and eval_after.get('type') == 'cp':
                # Lost a winning position
                return 1000
            elif eval_before.get('type') == 'cp' and eval_after.get('type') == 'mate':
                # Moved into mate
                return 1000
            else:
                return 0
                
        # Both are centipawn evaluations
        before_cp = eval_before['value']
        after_cp = eval_after['value']
        
        # Loss is decrease in evaluation
        loss = before_cp - after_cp
        return max(0, loss)
        
    def get_analysis_progress(self):
        """Get current analysis progress"""
        with self.analysis_lock:
            return self.analysis_progress
            
    def get_analyzed_moves(self):
        """Get all analyzed moves"""
        with self.analysis_lock:
            return self.analyzed_moves.copy()
            
    def is_analysis_complete(self):
        """Check if analysis is complete"""
        return self.analysis_complete
        
    def reset(self):
        """Reset analyzer for new game"""
        self.game_moves = []
        self.analyzed_moves = []
        self.analysis_complete = False
        self.analysis_progress = 0
        if self.analysis_thread and self.analysis_thread.is_alive():
            # Note: In a real implementation, you'd want to properly cancel the thread
            pass

# Import chess library at the top
try:
    import chess
except ImportError:
    print("Warning: python-chess library not found. Some analysis features may not work.")
    chess = None