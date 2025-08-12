# opening_variety_manager.py - Intelligent Opening Variety System
import json
import time
import random
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from threading import Lock
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class OpeningRecord:
    """Record of a played opening"""
    opening_signature: str
    moves: List[str]
    elo_level: int
    timestamp: float
    game_id: str
    result: Optional[str] = None  # 'win', 'loss', 'draw'

@dataclass
class OpeningStats:
    """Statistics for an opening"""
    times_played: int
    last_played: float
    success_rate: float
    avg_game_length: float
    elo_levels: List[int]

class OpeningVarietyManager:
    """Intelligent system to ensure opening variety and prevent repetition"""
    
    def __init__(self, data_dir: str = "data", min_games_gap: int = 10):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.min_games_gap = min_games_gap  # Minimum games before repeating opening
        self.lock = Lock()
        
        # Storage files
        self.history_file = self.data_dir / "opening_variety_history.json"
        self.stats_file = self.data_dir / "opening_variety_stats.json"
        
        # In-memory data structures
        self.opening_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=50))  # Last 50 games per ELO
        self.opening_stats: Dict[str, OpeningStats] = {}
        self.blocked_openings: Dict[int, set] = defaultdict(set)  # ELO -> blocked opening signatures
        
        # Load existing data
        self._load_data()
        
        logger.info(f"🎯 Opening Variety Manager initialized")
        logger.info(f"   Min games gap: {self.min_games_gap}")
        logger.info(f"   Data directory: {self.data_dir}")
    
    def _generate_opening_signature(self, moves: List[str], depth: int = 4) -> str:
        """Generate a unique signature for an opening sequence"""
        # Use first N moves to create signature (default 4 moves = 2 full moves)
        opening_moves = moves[:depth]
        signature = "_".join(opening_moves)
        return hashlib.md5(signature.encode()).hexdigest()[:12]  # Short hash
    
    def _load_data(self):
        """Load opening history and stats from disk"""
        try:
            # Load history
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    
                for elo_str, records in data.get('history', {}).items():
                    elo = int(elo_str)
                    for record_data in records:
                        record = OpeningRecord(**record_data)
                        self.opening_history[elo].append(record)
                
                logger.info(f"📚 Loaded {sum(len(h) for h in self.opening_history.values())} opening records")
            
            # Load stats
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    
                for sig, stats_data in data.get('stats', {}).items():
                    self.opening_stats[sig] = OpeningStats(**stats_data)
                
                logger.info(f"📊 Loaded stats for {len(self.opening_stats)} openings")
            
            # Update blocked openings based on recent history
            self._update_blocked_openings()
            
        except Exception as e:
            logger.warning(f"Error loading opening variety data: {e}")
    
    def _save_data(self):
        """Save opening history and stats to disk"""
        try:
            # Save history
            history_data = {
                'history': {
                    str(elo): [asdict(record) for record in records]
                    for elo, records in self.opening_history.items()
                },
                'last_updated': time.time()
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            # Save stats
            stats_data = {
                'stats': {
                    sig: asdict(stats) for sig, stats in self.opening_stats.items()
                },
                'last_updated': time.time()
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving opening variety data: {e}")
    
    def _update_blocked_openings(self):
        """Update the list of blocked openings based on recent play"""
        current_time = time.time()
        
        for elo, history in self.opening_history.items():
            blocked = set()
            
            # Check last N games for this ELO level
            recent_games = list(history)[-self.min_games_gap:]
            
            for record in recent_games:
                # Block openings played within the gap period
                blocked.add(record.opening_signature)
            
            self.blocked_openings[elo] = blocked
            
            if blocked:
                logger.debug(f"🚫 ELO {elo}: {len(blocked)} openings blocked")
    
    def is_opening_allowed(self, moves: List[str], elo_level: int) -> bool:
        """Check if an opening is allowed (not recently played)"""
        with self.lock:
            signature = self._generate_opening_signature(moves)
            return signature not in self.blocked_openings.get(elo_level, set())
    
    def get_allowed_moves(self, available_moves: List[str], current_moves: List[str], elo_level: int) -> List[str]:
        """Filter available moves to only include those that lead to allowed openings"""
        if not available_moves:
            return []
        
        with self.lock:
            allowed_moves = []
            
            for move in available_moves:
                # Test the opening sequence with this move added
                test_moves = current_moves + [move]
                
                if self.is_opening_allowed(test_moves, elo_level):
                    allowed_moves.append(move)
            
            # If no moves are allowed (all lead to blocked openings), allow all
            # This prevents the system from getting stuck
            if not allowed_moves:
                logger.warning(f"⚠️ All moves blocked for ELO {elo_level}, allowing all moves")
                return available_moves
            
            return allowed_moves
    
    def select_random_move(self, available_moves: List[str], current_moves: List[str], elo_level: int) -> Optional[str]:
        """Select a random move from available moves, considering variety constraints"""
        allowed_moves = self.get_allowed_moves(available_moves, current_moves, elo_level)
        
        if not allowed_moves:
            return None
        
        # Weighted random selection based on how long ago each opening was played
        move_weights = {}
        current_time = time.time()
        
        for move in allowed_moves:
            test_moves = current_moves + [move]
            signature = self._generate_opening_signature(test_moves)
            
            # Base weight
            weight = 1.0
            
            # Bonus for never-played openings
            if signature not in self.opening_stats:
                weight *= 2.0
            else:
                # Bonus based on time since last played
                stats = self.opening_stats[signature]
                time_since_played = current_time - stats.last_played
                hours_since = time_since_played / 3600
                
                # More weight for openings not played recently
                weight *= (1.0 + min(hours_since / 24, 2.0))  # Up to 3x weight after 48 hours
            
            move_weights[move] = weight
        
        # Weighted random selection
        moves = list(move_weights.keys())
        weights = list(move_weights.values())
        
        selected_move = random.choices(moves, weights=weights, k=1)[0]
        
        logger.debug(f"🎲 Selected move {selected_move} from {len(allowed_moves)} allowed moves")
        return selected_move
    
    def record_opening_played(self, moves: List[str], elo_level: int, game_id: str, result: Optional[str] = None):
        """Record that an opening was played"""
        with self.lock:
            signature = self._generate_opening_signature(moves)
            current_time = time.time()
            
            # Create opening record
            record = OpeningRecord(
                opening_signature=signature,
                moves=moves.copy(),
                elo_level=elo_level,
                timestamp=current_time,
                game_id=game_id,
                result=result
            )
            
            # Add to history
            self.opening_history[elo_level].append(record)
            
            # Update stats
            if signature not in self.opening_stats:
                self.opening_stats[signature] = OpeningStats(
                    times_played=0,
                    last_played=0,
                    success_rate=0.5,
                    avg_game_length=0,
                    elo_levels=[]
                )
            
            stats = self.opening_stats[signature]
            stats.times_played += 1
            stats.last_played = current_time
            
            if elo_level not in stats.elo_levels:
                stats.elo_levels.append(elo_level)
            
            # Update blocked openings
            self._update_blocked_openings()
            
            # Save data periodically
            if random.random() < 0.1:  # 10% chance to save
                self._save_data()
            
            logger.info(f"📝 Recorded opening: {signature[:8]}... (ELO {elo_level})")
    
    def get_variety_stats(self, elo_level: Optional[int] = None) -> Dict[str, Any]:
        """Get opening variety statistics"""
        with self.lock:
            stats = {
                'total_openings_tracked': len(self.opening_stats),
                'total_games_recorded': sum(len(h) for h in self.opening_history.values()),
                'min_games_gap': self.min_games_gap
            }
            
            if elo_level:
                history = self.opening_history.get(elo_level, deque())
                blocked = self.blocked_openings.get(elo_level, set())
                
                stats.update({
                    'elo_level': elo_level,
                    'games_at_elo': len(history),
                    'blocked_openings': len(blocked),
                    'recent_openings': [r.opening_signature[:8] for r in list(history)[-5:]]
                })
            else:
                # Overall stats
                stats.update({
                    'elo_levels_tracked': list(self.opening_history.keys()),
                    'most_played_openings': self._get_most_played_openings(5),
                    'diversity_score': self._calculate_diversity_score()
                })
            
            return stats
    
    def _get_most_played_openings(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most frequently played openings"""
        sorted_openings = sorted(
            self.opening_stats.items(),
            key=lambda x: x[1].times_played,
            reverse=True
        )
        
        return [
            {
                'signature': sig[:8],
                'times_played': stats.times_played,
                'elo_levels': stats.elo_levels
            }
            for sig, stats in sorted_openings[:limit]
        ]
    
    def _calculate_diversity_score(self) -> float:
        """Calculate overall opening diversity score (0-1)"""
        if not self.opening_stats:
            return 1.0
        
        total_games = sum(stats.times_played for stats in self.opening_stats.values())
        if total_games == 0:
            return 1.0
        
        # Calculate entropy-based diversity score
        import math
        probabilities = [stats.times_played / total_games for stats in self.opening_stats.values()]
        entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probabilities)
        max_entropy = math.log(len(self.opening_stats)) if len(self.opening_stats) > 1 else 1
        
        return min(entropy / max_entropy, 1.0) if max_entropy > 0 else 1.0
    
    def force_save(self):
        """Force save all data to disk"""
        with self.lock:
            self._save_data()
            logger.info("💾 Opening variety data saved to disk")
    
    def clear_history(self, elo_level: Optional[int] = None):
        """Clear opening history (for testing or reset)"""
        with self.lock:
            if elo_level:
                self.opening_history[elo_level].clear()
                self.blocked_openings[elo_level].clear()
                logger.info(f"🗑️ Cleared opening history for ELO {elo_level}")
            else:
                self.opening_history.clear()
                self.opening_stats.clear()
                self.blocked_openings.clear()
                logger.info("🗑️ Cleared all opening history")
            
            self._save_data()

# Global instance
_variety_manager = None
_manager_lock = Lock()

def get_opening_variety_manager(data_dir: str = "data", min_games_gap: int = 10) -> OpeningVarietyManager:
    """Get global opening variety manager instance (singleton)"""
    global _variety_manager
    with _manager_lock:
        if _variety_manager is None:
            _variety_manager = OpeningVarietyManager(data_dir, min_games_gap)
        return _variety_manager

def cleanup_opening_variety_manager():
    """Cleanup global opening variety manager"""
    global _variety_manager
    with _manager_lock:
        if _variety_manager:
            _variety_manager.force_save()
            _variety_manager = None