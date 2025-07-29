# enhanced_analysis.py
import threading
import time
from threading import Lock
from collections import namedtuple
import copy

MoveAnalysis = namedtuple('MoveAnalysis', [
    'move', 'player', 'position_before', 'position_after', 
    'eval_before', 'eval_after', 'best_moves', 'classification', 
    'eval_loss', 'move_number', 'is_sacrifice', 'position_assessment',
    'alternative_moves', 'move_quality_score'
])

class EnhancedGameAnalyzer:
    def __init__(self, engine):
        self.engine = engine
        self.game_moves = []
        self.analyzed_moves = []
        self.analysis_complete = False
        self.analysis_lock = Lock()
        self.analysis_thread = None
        self.analysis_progress = 0
        
        # Enhanced classification thresholds (in centipawns)
        self.THRESHOLDS = {
            'BLUNDER': 300,      # Loss of 3+ pawns
            'MISTAKE': 150,      # Loss of 1.5+ pawns  
            'INACCURACY': 50,    # Loss of 0.5+ pawns
            'OKAY': 25,          # Within 0.25 pawns of best
            'EXCELLENT': 15,     # Within 0.15 pawns of best
            'BEST': 10,          # Within 0.1 pawns of best
        }
        
        # Position assessment thresholds
        self.POSITION_THRESHOLDS = {
            'WINNING': 200,      # +2 pawns advantage
            'BETTER': 75,        # +0.75 pawns advantage
            'EQUAL': 25,         # Within 0.25 pawns
            'WORSE': -75,        # -0.75 pawns disadvantage
            'LOSING': -200       # -2 pawns disadvantage
        }
        
        # Classification colors for display
        self.COLORS = {
            'BRILLIANT': (0, 200, 255),     # Bright blue
            'GREAT': (0, 255, 100),         # Bright green
            'BEST': (0, 200, 0),            # Green
            'EXCELLENT': (100, 255, 100),   # Light green
            'OKAY': (150, 255, 150),        # Very light green
            'MISS': (255, 200, 0),          # Orange-yellow
            'INACCURACY': (255, 255, 100),  # Light yellow
            'MISTAKE': (255, 165, 0),       # Orange
            'BLUNDER': (255, 0, 0)          # Red
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
        """Analyze each move in the game with enhanced classification"""
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
                
                # Get multiple candidate moves with different depths
                candidate_moves = self._get_candidate_moves(move_data['position_before'])
                
                # Make the actual move and get evaluation after
                temp_board = chess.Board(move_data['position_before'])
                try:
                    actual_move_uci = self._convert_move_to_uci(move_data['move'])
                    temp_board.push(chess.Move.from_uci(actual_move_uci))
                    position_after = temp_board.fen()
                    
                    self.engine.set_position(position_after)
                    eval_after = self._flip_evaluation(self.engine.get_evaluation())
                    
                except:
                    eval_after = eval_before
                    position_after = move_data['position_before']
                
                # Check if move is a sacrifice
                is_sacrifice = self._is_sacrifice(move_data['move'], move_data['position_before'])
                
                # Assess position strength
                position_assessment = self._assess_position(eval_before)
                
                # Get move quality score
                move_quality_score = self._calculate_move_quality(
                    eval_before, eval_after, candidate_moves, actual_move_uci
                )
                
                # Enhanced classification
                classification, eval_loss = self._enhanced_classify_move(
                    move_data['move'], candidate_moves, eval_before, eval_after, 
                    move_data['position_before'], i == 0, is_sacrifice,
                    position_assessment, i, total_moves
                )
                
                # Create enhanced analysis
                analysis = MoveAnalysis(
                    move=move_data['move'],
                    player=move_data['player'],
                    position_before=move_data['position_before'],
                    position_after=position_after,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    best_moves=candidate_moves[:3],  # Top 3 moves
                    classification=classification,
                    eval_loss=eval_loss,
                    move_number=move_data['move_number'],
                    is_sacrifice=is_sacrifice,
                    position_assessment=position_assessment,
                    alternative_moves=candidate_moves[1:4],  # 2nd-4th best moves
                    move_quality_score=move_quality_score
                )
                
                with self.analysis_lock:
                    self.analyzed_moves.append(analysis)
                    self.analysis_progress = int((i + 1) / total_moves * 100)
                    
            except Exception as e:
                print(f"Error analyzing move {i}: {e}")
                continue
                
        self.analysis_complete = True
        
    def _get_candidate_moves(self, fen):
        """Get top candidate moves with multiple depths"""
        self.engine.set_position(fen)
        candidates = []
        
        # Get moves at different depths for variety
        for depth in [12, 15, 18, 20]:
            try:
                self.engine.set_depth(depth)
                best_move = self.engine.get_best_move()
                if best_move and best_move not in candidates:
                    candidates.append(best_move)
                if len(candidates) >= 5:
                    break
            except:
                continue
                
        # Reset to default depth
        self.engine.set_depth(15)
        return candidates
        
    def _is_sacrifice(self, move, position):
        """Detect if a move is a sacrifice"""
        try:
            board = chess.Board(position)
            move_uci = self._convert_move_to_uci(move)
            chess_move = chess.Move.from_uci(move_uci)
            
            # Check if piece is moving to a square attacked by opponent
            to_square = chess_move.to_square
            piece = board.piece_at(chess_move.from_square)
            
            if not piece:
                return False
                
            # Temporarily make the move
            board.push(chess_move)
            
            # Check if the moved piece can be captured
            attackers = board.attackers(not piece.color, to_square)
            
            board.pop()  # Undo the move
            
            # If there are attackers and the piece value > pawn value, it might be a sacrifice
            if attackers and piece.piece_type > chess.PAWN:
                return True
                
        except:
            pass
            
        return False
        
    def _assess_position(self, evaluation):
        """Assess the strength of the position"""
        if not evaluation or 'value' not in evaluation:
            return 'EQUAL'
            
        if evaluation['type'] == 'mate':
            return 'WINNING' if evaluation['value'] > 0 else 'LOSING'
            
        value = evaluation['value']
        
        if value >= self.POSITION_THRESHOLDS['WINNING']:
            return 'WINNING'
        elif value >= self.POSITION_THRESHOLDS['BETTER']:
            return 'BETTER'
        elif value >= self.POSITION_THRESHOLDS['EQUAL']:
            return 'EQUAL'
        elif value >= self.POSITION_THRESHOLDS['WORSE']:
            return 'WORSE'
        else:
            return 'LOSING'
            
    def _calculate_move_quality(self, eval_before, eval_after, candidates, actual_move):
        """Calculate a quality score for the move (0-100)"""
        if not candidates or actual_move not in candidates:
            return 0
            
        # Position in candidate list (0 = best move)
        try:
            position = candidates.index(actual_move)
            # Quality decreases based on position in candidate list
            base_quality = max(0, 100 - (position * 20))
            
            # Adjust based on evaluation change
            eval_change = self._calculate_eval_loss(eval_before, eval_after)
            if eval_change == 0:
                return min(100, base_quality + 10)  # Bonus for no eval loss
            elif eval_change < 25:
                return base_quality
            else:
                return max(0, base_quality - (eval_change // 10))
                
        except ValueError:
            return 0
            
    def _enhanced_classify_move(self, actual_move, candidate_moves, eval_before, eval_after, 
                              position, is_first_move, is_sacrifice, position_assessment, 
                              move_index, total_moves):
        """Enhanced move classification with Chess.com-like categories"""
        
        if is_first_move:
            return 'OKAY', 0
            
        try:
            actual_uci = self._convert_move_to_uci(actual_move)
        except:
            return 'INACCURACY', 0
            
        if not candidate_moves:
            return 'OKAY', 0
            
        # Calculate evaluation loss
        eval_loss = self._calculate_eval_loss(eval_before, eval_after)
        
        # Check if it's the best move
        if actual_uci == candidate_moves[0]:
            # Best move, but could still be BRILLIANT or GREAT
            if is_sacrifice and position_assessment in ['BETTER', 'EQUAL'] and eval_loss <= 10:
                return 'BRILLIANT', eval_loss
            elif self._is_critical_move(eval_before, eval_after, candidate_moves, move_index, total_moves):
                return 'GREAT', eval_loss
            else:
                return 'BEST', eval_loss
                
        # Check if it's in top moves
        if actual_uci in candidate_moves[:2]:
            return 'EXCELLENT', eval_loss
            
        # Check for missed opportunities (opponent's previous move was bad)
        if self._is_missed_opportunity(move_index, eval_before):
            return 'MISS', eval_loss
            
        # Standard classification based on evaluation loss
        if eval_loss >= self.THRESHOLDS['BLUNDER']:
            return 'BLUNDER', eval_loss
        elif eval_loss >= self.THRESHOLDS['MISTAKE']:
            return 'MISTAKE', eval_loss
        elif eval_loss >= self.THRESHOLDS['INACCURACY']:
            return 'INACCURACY', eval_loss
        elif eval_loss <= self.THRESHOLDS['OKAY']:
            return 'OKAY', eval_loss
        else:
            return 'OKAY', eval_loss
            
    def _is_critical_move(self, eval_before, eval_after, candidates, move_index, total_moves):
        """Determine if this is a critical move that changes the game outcome"""
        if not eval_before or not eval_after:
            return False
            
        # Critical moves are typically in the middle to late game
        if move_index < total_moves * 0.3:  # Not in opening
            return False
            
        # Check if this move significantly changes position assessment
        before_assessment = self._assess_position(eval_before)
        after_assessment = self._assess_position(eval_after)
        
        # Turning around a bad position or maintaining advantage in critical moment
        critical_changes = [
            ('LOSING', 'EQUAL'), ('LOSING', 'BETTER'), ('LOSING', 'WINNING'),
            ('WORSE', 'EQUAL'), ('WORSE', 'BETTER'), ('WORSE', 'WINNING'),
            ('EQUAL', 'BETTER'), ('EQUAL', 'WINNING')
        ]
        
        return (before_assessment, after_assessment) in critical_changes
        
    def _is_missed_opportunity(self, move_index, current_eval):
        """Check if player missed an opportunity from opponent's mistake"""
        if move_index == 0 or not hasattr(self, 'analyzed_moves'):
            return False
            
        # Look at previous move analysis if available
        with self.analysis_lock:
            if len(self.analyzed_moves) > 0:
                prev_analysis = self.analyzed_moves[-1]
                # If opponent made a mistake/blunder and current position is good,
                # but player doesn't capitalize
                if (prev_analysis.classification in ['MISTAKE', 'BLUNDER'] and
                    self._assess_position(current_eval) in ['BETTER', 'WINNING']):
                    return True
                    
        return False
        
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
            
    def _calculate_eval_loss(self, eval_before, eval_after):
        """Calculate the evaluation loss from a move"""
        if not eval_before or not eval_after:
            return 0
            
        if 'value' not in eval_before or 'value' not in eval_after:
            return 0
            
        # Handle mate scores
        if eval_before.get('type') == 'mate' or eval_after.get('type') == 'mate':
            if eval_before.get('type') == 'mate' and eval_after.get('type') == 'cp':
                return 1000  # Lost a winning position
            elif eval_before.get('type') == 'cp' and eval_after.get('type') == 'mate':
                return 1000  # Moved into mate
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
        
    def get_game_summary(self):
        """Get a summary of the game analysis"""
        if not self.analysis_complete:
            return None
            
        with self.analysis_lock:
            moves = self.analyzed_moves
            
        if not moves:
            return None
            
        # Count move classifications
        classifications = {}
        for move in moves:
            classifications[move.classification] = classifications.get(move.classification, 0) + 1
            
        # Calculate accuracy (percentage of moves that weren't mistakes/blunders)
        total_moves = len(moves)
        good_moves = sum(1 for m in moves if m.classification not in ['MISTAKE', 'BLUNDER'])
        accuracy = (good_moves / total_moves) * 100 if total_moves > 0 else 0
        
        return {
            'total_moves': total_moves,
            'classifications': classifications,
            'accuracy': accuracy,
            'brilliant_moves': classifications.get('BRILLIANT', 0),
            'great_moves': classifications.get('GREAT', 0),
            'mistakes': classifications.get('MISTAKE', 0),
            'blunders': classifications.get('BLUNDER', 0)
        }
        
    def reset(self):
        """Reset analyzer for new game"""
        self.game_moves = []
        self.analyzed_moves = []
        self.analysis_complete = False
        self.analysis_progress = 0
        if self.analysis_thread and self.analysis_thread.is_alive():
            pass  # Let it finish naturally

# Import chess library
try:
    import chess
except ImportError:
    print("Warning: python-chess library not found. Analysis features may not work.")
    chess = None