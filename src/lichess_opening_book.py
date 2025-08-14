# lichess_opening_book.py - Pure Lichess Masters Opening Book
import json
import time
import requests
from typing import Dict, List, Optional, Any
from threading import Lock
from dataclasses import dataclass
import logging
import random
import sqlite3
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Import opening variety manager
try:
    from opening_variety_manager import get_opening_variety_manager
    VARIETY_MANAGER_AVAILABLE = True
except ImportError:
    VARIETY_MANAGER_AVAILABLE = False
    logger.warning("Opening variety manager not available")

@dataclass
class LichessMove:
    """Represents a move from Lichess masters database"""
    move: str  # UCI format (e.g., "e2e4")
    games: int  # Total number of games
    wins: int  # Number of wins (for white)
    draws: int  # Number of draws
    losses: int  # Number of losses (for white)
    avg_rating: float  # Average rating of players
    
    @property
    def score(self) -> float:
        """Calculate move score based on results"""
        if self.games == 0:
            return 0.5
        return (self.wins + 0.5 * self.draws) / self.games
    
    @property
    def popularity(self) -> float:
        """Normalized popularity score"""
        return min(self.games / 1000.0, 1.0)

class LichessOpeningBook:
    """Pure Lichess masters database opening book with intelligent variety management"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.lock = Lock()
        
        # Configuration
        self.max_book_depth = self.config.get('max_depth', 20)
        self.min_games_threshold = self.config.get('min_games', 10)
        self.request_delay = self.config.get('request_delay', 1.0)
        self.cache_ttl = self.config.get('cache_ttl_minutes', 30) * 60
        self.move_selection = self.config.get('move_selection', 'intelligent_random')  # 'best', 'popular', 'random', 'intelligent_random'
        self.variety_enabled = self.config.get('variety_enabled', True)
        self.min_games_gap = self.config.get('min_games_gap', 10)
        
        # Network resilience settings
        self.max_retries = self.config.get('max_retries', 3)
        self.base_retry_delay = self.config.get('base_retry_delay', 1.0)
        self.connection_timeout = self.config.get('connection_timeout', 15)
        self.fallback_enabled = self.config.get('fallback_enabled', True)
        
        # Initialize variety manager if available
        self.variety_manager = None
        if VARIETY_MANAGER_AVAILABLE and self.variety_enabled:
            try:
                self.variety_manager = get_opening_variety_manager(min_games_gap=self.min_games_gap)
                logger.info("🎯 Opening variety manager integrated")
            except Exception as e:
                logger.warning(f"Failed to initialize variety manager: {e}")
        
        # Track current game moves for variety management
        self.current_game_moves = []
        self.current_elo = None
        
        # Lichess API setup
        self.base_url = "https://explorer.lichess.ovh"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ChessAI-LichessOpening/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Caching and rate limiting
        self.cache = {}  # fen -> (data, timestamp)
        self.last_request_time = 0
        self.enabled = True
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'api_requests': 0,
            'successful_moves': 0,
            'failed_requests': 0,
            'total_requests': 0,
            'fallback_requests': 0
        }
        
        # Network status tracking
        self.network_available = True
        self.last_network_check = 0
        self.network_check_interval = 300  # Check every 5 minutes
        
        # Fallback database setup
        self.fallback_db_path = self.config.get('fallback_db_path', 'books/openings.db')
        self.fallback_available = False
        self._init_fallback_database()
        
        logger.debug("Pure Lichess opening book initialized")
    
    def _init_fallback_database(self):
        """Initialize fallback local database"""
        try:
            if os.path.exists(self.fallback_db_path):
                # Test database connection
                conn = sqlite3.connect(self.fallback_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if tables:
                    self.fallback_available = True
                    logger.info(f"📚 Fallback opening database available: {self.fallback_db_path}")
                else:
                    logger.warning(f"Fallback database exists but has no tables: {self.fallback_db_path}")
            else:
                logger.warning(f"Fallback database not found: {self.fallback_db_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize fallback database: {e}")
            self.fallback_available = False
    
    def _rate_limit(self):
        """Ensure respectful rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _check_network_connectivity(self) -> bool:
        """Check if network connectivity is available"""
        current_time = time.time()
        
        # Only check periodically to avoid overhead
        if current_time - self.last_network_check < self.network_check_interval:
            return self.network_available
        
        try:
            # Quick connectivity test to a reliable endpoint
            response = self.session.head("https://www.google.com", timeout=5)
            self.network_available = response.status_code == 200
            logger.debug(f"Network connectivity check: {'Available' if self.network_available else 'Unavailable'}")
        except Exception:
            self.network_available = False
            logger.debug("Network connectivity check: Unavailable")
        
        self.last_network_check = current_time
        return self.network_available
    
    def _fetch_fallback_data(self, fen: str) -> Optional[Dict]:
        """Fetch position data from local fallback database"""
        if not self.fallback_available:
            return None
        
        try:
            conn = sqlite3.connect(self.fallback_db_path)
            cursor = conn.cursor()
            
            # Query for the position
            cursor.execute("SELECT moves FROM opening_moves WHERE fen = ?", (fen,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                moves_json = result[0]
                moves_data = json.loads(moves_json)
                
                # Convert to Lichess API format
                lichess_format = {
                    'moves': []
                }
                
                for move_data in moves_data:
                    # Convert from local format to Lichess format
                    lichess_move = {
                        'uci': move_data['move'],
                        'white': move_data['wins'],
                        'draws': move_data['draws'],
                        'black': move_data['losses'],
                        'averageRating': move_data.get('avg_rating', 2400)
                    }
                    lichess_format['moves'].append(lichess_move)
                
                logger.debug(f"📚 Fallback data found for position: {len(lichess_format['moves'])} moves")
                self.stats['fallback_requests'] += 1
                return lichess_format
            
            return None
            
        except Exception as e:
            logger.warning(f"Error querying fallback database: {e}")
            return None
    
    def _fetch_position_data(self, fen: str) -> Optional[Dict]:
        """Fetch position data from Lichess masters database with robust error handling"""
        if not self.enabled:
            return None
        
        # Check cache first
        cache_key = fen
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.stats['cache_hits'] += 1
                return cached_data
        
        # Check network connectivity before making requests
        if not self._check_network_connectivity():
            logger.warning("Network connectivity unavailable, trying fallback database")
            if self.fallback_enabled and self.fallback_available:
                fallback_data = self._fetch_fallback_data(fen)
                if fallback_data:
                    logger.info("📚 Using fallback database for opening move")
                    return fallback_data
            self.stats['failed_requests'] += 1
            return None
        
        # Rate limit requests
        self._rate_limit()
        
        # Retry logic with exponential backoff
        max_retries = self.max_retries
        base_delay = self.base_retry_delay
        
        for attempt in range(max_retries):
            try:
                # Prepare request parameters
                params = {}
                if fen != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
                    params['fen'] = fen
                
                # Make request to Lichess
                url = f"{self.base_url}/masters"
                logger.debug(f"Making request (attempt {attempt + 1}/{max_retries}): {url} with params: {params}")
                
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.connection_timeout,
                    stream=False  # Don't stream to avoid connection issues
                )
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Received data: {data}")
                
                # Cache the result
                self.cache[cache_key] = (data, time.time())
                self.stats['api_requests'] += 1
                
                return data
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for connection error - marking network as unavailable")
                    self.network_available = False
                    self.last_network_check = time.time()
                    
                    # Try fallback database
                    if self.fallback_enabled and self.fallback_available:
                        logger.info("🔄 Attempting fallback database after connection failure")
                        fallback_data = self._fetch_fallback_data(fen)
                        if fallback_data:
                            logger.info("📚 Successfully using fallback database")
                            return fallback_data
                    
                    self.stats['failed_requests'] += 1
                    return None
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for timeout")
                    
                    # Try fallback database
                    if self.fallback_enabled and self.fallback_available:
                        logger.info("🔄 Attempting fallback database after timeout")
                        fallback_data = self._fetch_fallback_data(fen)
                        if fallback_data:
                            logger.info("📚 Successfully using fallback database")
                            return fallback_data
                    
                    self.stats['failed_requests'] += 1
                    return None
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    logger.warning(f"HTTP error {e.response.status_code} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                        logger.info(f"Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Max retries reached for HTTP error {e.response.status_code}")
                        self.stats['failed_requests'] += 1
                        return None
                else:
                    logger.error(f"Non-retryable HTTP error: {e}")
                    self.stats['failed_requests'] += 1
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for request error")
                    self.stats['failed_requests'] += 1
                    return None
                    
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed: {e}")
                self.stats['failed_requests'] += 1
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.stats['failed_requests'] += 1
                return None
        
        # Should not reach here, but just in case
        self.stats['failed_requests'] += 1
        return None
    
    def _convert_lichess_moves(self, lichess_data: Dict) -> List[LichessMove]:
        """Convert Lichess API response to LichessMove objects"""
        if not lichess_data or 'moves' not in lichess_data:
            return []
        
        moves = []
        for move_data in lichess_data['moves']:
            try:
                total_games = move_data['white'] + move_data['draws'] + move_data['black']
                
                # Filter out moves with too few games
                if total_games < self.min_games_threshold:
                    continue
                
                lichess_move = LichessMove(
                    move=move_data['uci'],
                    games=total_games,
                    wins=move_data['white'],
                    draws=move_data['draws'],
                    losses=move_data['black'],
                    avg_rating=move_data.get('averageRating', 2400)
                )
                moves.append(lichess_move)
                
            except (KeyError, Exception):
                continue
        
        return moves
    
    def _select_best_move(self, moves: List[LichessMove]) -> Optional[LichessMove]:
        """Select the best move based on ELO-aware strategy and variety constraints"""
        if not moves:
            return None
        
        # Extract move strings for variety checking
        available_moves = [move.move for move in moves]
        
        # Use ELO-aware selection if ELO is available
        if self.current_elo:
            return self._select_elo_aware_move(moves, available_moves)
        
        # Fallback to original selection methods
        if self.move_selection == 'best':
            # Select move with best score, with popularity as tiebreaker
            return max(moves, key=lambda m: (m.score, m.popularity))
        
        elif self.move_selection == 'popular':
            # Select most popular move
            return max(moves, key=lambda m: m.games)
        
        elif self.move_selection == 'random':
            # Weighted random selection based on games played
            total_weight = sum(m.games for m in moves)
            if total_weight == 0:
                return random.choice(moves)
            
            rand_val = random.uniform(0, total_weight)
            current_weight = 0
            for move in moves:
                current_weight += move.games
                if rand_val <= current_weight:
                    return move
            return moves[-1]  # Fallback
        
        elif self.move_selection == 'intelligent_random':
            # Intelligent random selection with variety management
            if self.variety_manager and self.current_elo:
                # Get allowed moves from variety manager
                allowed_moves = self.variety_manager.get_allowed_moves(
                    available_moves, self.current_game_moves, self.current_elo
                )
                
                # Filter moves to only allowed ones
                allowed_lichess_moves = [m for m in moves if m.move in allowed_moves]
                
                if allowed_lichess_moves:
                    # Select randomly from allowed moves with quality weighting
                    return self._weighted_random_selection(allowed_lichess_moves)
                else:
                    logger.warning("No allowed moves found, falling back to quality-based selection")
            
            # Fallback to weighted random selection
            return self._weighted_random_selection(moves)
        
        else:
            # Default to best move
            return max(moves, key=lambda m: (m.score, m.popularity))
    
    def _weighted_random_selection(self, moves: List[LichessMove]) -> LichessMove:
        """Perform weighted random selection based on move quality and popularity"""
        if len(moves) == 1:
            return moves[0]
        
        # Calculate weights based on score and popularity
        weights = []
        for move in moves:
            # Base weight from score (0.0 to 1.0)
            score_weight = move.score
            
            # Popularity weight (normalized)
            popularity_weight = move.popularity
            
            # Games weight (more games = more reliable)
            games_weight = min(move.games / 100.0, 1.0)
            
            # Combined weight (emphasize quality but allow variety)
            combined_weight = (score_weight * 0.5 + popularity_weight * 0.3 + games_weight * 0.2)
            weights.append(max(combined_weight, 0.1))  # Minimum weight to ensure all moves have a chance
        
        # Random selection with weights
        return random.choices(moves, weights=weights, k=1)[0]
    
    def _select_elo_aware_move(self, moves: List[LichessMove], available_moves: List[str]) -> Optional[LichessMove]:
        """Select move based on ELO-aware strategy"""
        if not moves:
            return None
        
        elo = self.current_elo
        
        # Define ELO categories and their selection strategies
        if elo < 1000:  # Beginner (800-999)
            return self._select_beginner_move(moves)
        elif elo < 1200:  # Amateur (1000-1199)
            return self._select_amateur_move(moves)
        elif elo < 1500:  # Club Player (1200-1499)
            return self._select_club_move(moves)
        elif elo < 1800:  # Tournament Player (1500-1799)
            return self._select_tournament_move(moves)
        elif elo < 2000:  # Expert (1800-1999)
            return self._select_expert_move(moves)
        elif elo < 2200:  # Master (2000-2199)
            return self._select_master_move(moves)
        elif elo < 2400:  # International Master (2200-2399)
            return self._select_im_move(moves)
        elif elo < 2600:  # Grandmaster (2400-2599)
            return self._select_gm_move(moves)
        elif elo < 2800:  # Super GM (2600-2799)
            return self._select_super_gm_move(moves)
        else:  # Engine Strength (2800+)
            return self._select_engine_move(moves)
    
    def _select_beginner_move(self, moves: List[LichessMove]) -> LichessMove:
        """Beginner: Very random, can play suboptimal moves, prefers simple/popular moves"""
        # Filter out moves with very few games (less reliable for beginners)
        reliable_moves = [m for m in moves if m.games >= 100]
        if not reliable_moves:
            reliable_moves = moves
        
        # 60% chance to play a random move, 40% chance to play popular move
        if random.random() < 0.6:
            return random.choice(reliable_moves)
        else:
            return max(reliable_moves, key=lambda m: m.games)
    
    def _select_amateur_move(self, moves: List[LichessMove]) -> LichessMove:
        """Amateur: Mostly random but slightly better, avoids worst moves"""
        # Remove moves with very poor scores (< 0.4)
        decent_moves = [m for m in moves if m.score >= 0.4]
        if not decent_moves:
            decent_moves = moves
        
        # 50% random, 30% popular, 20% best
        rand = random.random()
        if rand < 0.5:
            return random.choice(decent_moves)
        elif rand < 0.8:
            return max(decent_moves, key=lambda m: m.games)
        else:
            return max(decent_moves, key=lambda m: m.score)
    
    def _select_club_move(self, moves: List[LichessMove]) -> LichessMove:
        """Club Player: Balanced approach, prefers sound moves but allows variety"""
        # Filter moves with reasonable scores (>= 0.45)
        sound_moves = [m for m in moves if m.score >= 0.45]
        if not sound_moves:
            sound_moves = moves
        
        # 30% random, 40% popular, 30% best
        rand = random.random()
        if rand < 0.3:
            return random.choice(sound_moves)
        elif rand < 0.7:
            return max(sound_moves, key=lambda m: m.games)
        else:
            return max(sound_moves, key=lambda m: m.score)
    
    def _select_tournament_move(self, moves: List[LichessMove]) -> LichessMove:
        """Tournament Player: Prefers good moves, some variety for surprise"""
        # Filter moves with good scores (>= 0.48)
        good_moves = [m for m in moves if m.score >= 0.48]
        if not good_moves:
            good_moves = moves
        
        # 20% random, 30% popular, 50% best
        rand = random.random()
        if rand < 0.2:
            return random.choice(good_moves)
        elif rand < 0.5:
            return max(good_moves, key=lambda m: m.games)
        else:
            return max(good_moves, key=lambda m: m.score)
    
    def _select_expert_move(self, moves: List[LichessMove]) -> LichessMove:
        """Expert: Mostly plays strong moves, occasional variety"""
        # Filter moves with strong scores (>= 0.5)
        strong_moves = [m for m in moves if m.score >= 0.5]
        if not strong_moves:
            strong_moves = moves
        
        # 10% random, 25% popular, 65% best
        rand = random.random()
        if rand < 0.1:
            return random.choice(strong_moves)
        elif rand < 0.35:
            return max(strong_moves, key=lambda m: m.games)
        else:
            return max(strong_moves, key=lambda m: m.score)
    
    def _select_master_move(self, moves: List[LichessMove]) -> LichessMove:
        """Master: Strongly prefers best moves, minimal randomness"""
        # Filter moves with very strong scores (>= 0.52)
        excellent_moves = [m for m in moves if m.score >= 0.52]
        if not excellent_moves:
            excellent_moves = moves
        
        # 5% random, 15% popular, 80% best
        rand = random.random()
        if rand < 0.05:
            return random.choice(excellent_moves)
        elif rand < 0.2:
            return max(excellent_moves, key=lambda m: m.games)
        else:
            return max(excellent_moves, key=lambda m: m.score)
    
    def _select_im_move(self, moves: List[LichessMove]) -> LichessMove:
        """International Master: Almost always plays objectively best moves"""
        # Filter top-tier moves (>= 0.53)
        top_moves = [m for m in moves if m.score >= 0.53]
        if not top_moves:
            top_moves = moves
        
        # 2% random, 8% popular, 90% best
        rand = random.random()
        if rand < 0.02:
            return random.choice(top_moves)
        elif rand < 0.1:
            return max(top_moves, key=lambda m: m.games)
        else:
            return max(top_moves, key=lambda m: m.score)
    
    def _select_gm_move(self, moves: List[LichessMove]) -> LichessMove:
        """Grandmaster: Plays best moves with occasional popular alternatives"""
        # Only consider excellent moves (>= 0.54)
        elite_moves = [m for m in moves if m.score >= 0.54]
        if not elite_moves:
            elite_moves = moves
        
        # 1% random, 4% popular, 95% best
        rand = random.random()
        if rand < 0.01:
            return random.choice(elite_moves)
        elif rand < 0.05:
            return max(elite_moves, key=lambda m: m.games)
        else:
            return max(elite_moves, key=lambda m: m.score)
    
    def _select_super_gm_move(self, moves: List[LichessMove]) -> LichessMove:
        """Super GM: Almost purely objective, considers only top moves"""
        # Only elite moves (>= 0.55)
        super_elite_moves = [m for m in moves if m.score >= 0.55]
        if not super_elite_moves:
            super_elite_moves = moves
        
        # 0.5% random, 2% popular, 97.5% best
        rand = random.random()
        if rand < 0.005:
            return random.choice(super_elite_moves)
        elif rand < 0.025:
            return max(super_elite_moves, key=lambda m: m.games)
        else:
            return max(super_elite_moves, key=lambda m: m.score)
    
    def _select_engine_move(self, moves: List[LichessMove]) -> LichessMove:
        """Engine: Pure objectivity, always plays the best move"""
        # Always play the objectively best move
        return max(moves, key=lambda m: (m.score, m.games, m.popularity))
    
    def get_book_move(self, fen: str, move_number: int = 1) -> Optional[str]:
        """Get best book move for position from Lichess masters"""
        with self.lock:
            try:
                self.stats['total_requests'] += 1
                
                # Check depth limit
                if move_number > self.max_book_depth:
                    return None
                
                # Fetch data from Lichess
                lichess_data = self._fetch_position_data(fen)
                if not lichess_data:
                    return None
                
                # Convert to move objects
                moves = self._convert_lichess_moves(lichess_data)
                if not moves:
                    return None
                
                # Select best move
                selected_move = self._select_best_move(moves)
                if selected_move:
                    self.stats['successful_moves'] += 1
                    return selected_move.move
                
                return None
                
            except Exception as e:
                logger.error(f"Error getting book move: {e}")
                return None
    
    def get_position_analysis(self, fen: str) -> Dict[str, Any]:
        """Get detailed analysis of a position"""
        lichess_data = self._fetch_position_data(fen)
        if not lichess_data:
            return {}
        
        moves = self._convert_lichess_moves(lichess_data)
        
        analysis = {
            'total_games': sum(m.games for m in moves),
            'move_count': len(moves),
            'moves': []
        }
        
        for move in sorted(moves, key=lambda m: m.games, reverse=True):
            analysis['moves'].append({
                'move': move.move,
                'games': move.games,
                'score': move.score,
                'wins': move.wins,
                'draws': move.draws,
                'losses': move.losses,
                'avg_rating': move.avg_rating
            })
        
        return analysis
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_requests = self.stats['total_requests']
        stats = self.stats.copy()
        
        if total_requests > 0:
            stats['cache_hit_rate'] = (self.stats['cache_hits'] / total_requests) * 100
            stats['success_rate'] = (self.stats['successful_moves'] / total_requests) * 100
            stats['api_request_rate'] = (self.stats['api_requests'] / total_requests) * 100
        
        stats['cache_size'] = len(self.cache)
        stats['enabled'] = self.enabled
        stats['network_available'] = self.network_available
        stats['last_network_check'] = self.last_network_check
        stats['fallback_available'] = self.fallback_available
        
        if total_requests > 0:
            stats['fallback_usage_rate'] = (self.stats['fallback_requests'] / total_requests) * 100
        
        return stats
    
    def clear_cache(self):
        """Clear the position cache"""
        with self.lock:
            self.cache.clear()
    
    def disable(self):
        """Disable the opening book"""
        self.enabled = False
    
    def enable(self):
        """Enable the opening book"""
        self.enabled = True
    
    def force_network_check(self) -> bool:
        """Force a network connectivity check"""
        self.last_network_check = 0  # Reset to force check
        return self._check_network_connectivity()
    
    def start_new_game(self, elo_level: int, game_id: str = None):
        """Start tracking a new game for variety management"""
        self.current_game_moves = []
        self.current_elo = elo_level
        
        if self.variety_manager:
            logger.info(f"🎮 Started new game tracking (ELO: {elo_level})")
    
    def record_move_played(self, move: str):
        """Record a move that was played in the current game"""
        if move:
            self.current_game_moves.append(move)
            logger.debug(f"📝 Recorded move: {move} (total: {len(self.current_game_moves)})")
    
    def finish_game(self, game_id: str = None, result: str = None):
        """Finish the current game and record opening for variety tracking"""
        if self.variety_manager and self.current_game_moves and self.current_elo:
            self.variety_manager.record_opening_played(
                self.current_game_moves,
                self.current_elo,
                game_id or f"game_{int(time.time())}",
                result
            )
            logger.info(f"🏁 Game finished, opening recorded for variety tracking")
        
        # Reset game state
        self.current_game_moves = []
        self.current_elo = None
    
    def get_variety_stats(self) -> Dict[str, Any]:
        """Get opening variety statistics"""
        if self.variety_manager:
            return self.variety_manager.get_variety_stats(self.current_elo)
        return {'variety_manager': 'not_available'}
    
    def cleanup(self):
        """Cleanup resources"""
        # Save any pending variety data
        if self.variety_manager:
            self.variety_manager.force_save()
        
        self.session.close()

# Global instance management
_lichess_book = None
_book_lock = Lock()

def get_lichess_opening_book(config: Dict[str, Any] = None) -> LichessOpeningBook:
    """Get global Lichess opening book instance (singleton)"""
    global _lichess_book
    with _book_lock:
        if _lichess_book is None:
            _lichess_book = LichessOpeningBook(config)
        return _lichess_book

def cleanup_lichess_opening_book():
    """Cleanup global opening book"""
    global _lichess_book
    with _book_lock:
        if _lichess_book:
            _lichess_book.cleanup()
            _lichess_book = None