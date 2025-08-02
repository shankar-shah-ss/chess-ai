"""
Comprehensive Chess Opening Theory System
Integrates with the Chess Analysis System for real-time opening detection and exploration
"""

import chess
import chess.pgn
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import time
import threading
from pathlib import Path

@dataclass
class OpeningMove:
    """Represents a move in opening theory with statistics"""
    move: str  # UCI notation (e.g., "e2e4")
    san: str   # Standard Algebraic Notation (e.g., "e4")
    white_wins: int = 0
    draws: int = 0
    black_wins: int = 0
    total_games: int = 0
    popularity: float = 0.0  # Percentage of games where this move was played
    
    @property
    def white_win_rate(self) -> float:
        return (self.white_wins / self.total_games * 100) if self.total_games > 0 else 0.0
    
    @property
    def draw_rate(self) -> float:
        return (self.draws / self.total_games * 100) if self.total_games > 0 else 0.0
    
    @property
    def black_win_rate(self) -> float:
        return (self.black_wins / self.total_games * 100) if self.total_games > 0 else 0.0

@dataclass
class OpeningVariation:
    """Represents a chess opening variation"""
    name: str
    eco: str
    moves: List[str]  # SAN notation
    uci_moves: List[str]  # UCI notation
    fen: str
    parent_eco: Optional[str] = None
    description: str = ""
    typical_plans: List[str] = None
    key_ideas: List[str] = None
    famous_games: List[str] = None
    
    def __post_init__(self):
        if self.typical_plans is None:
            self.typical_plans = []
        if self.key_ideas is None:
            self.key_ideas = []
        if self.famous_games is None:
            self.famous_games = []

@dataclass
class OpeningPosition:
    """Represents a position in opening theory"""
    fen: str
    variation: OpeningVariation
    move_number: int
    next_moves: List[OpeningMove]
    is_main_line: bool = True
    transpositions: List[str] = None  # List of FENs that transpose to this position
    
    def __post_init__(self):
        if self.transpositions is None:
            self.transpositions = []

class OpeningPhase(Enum):
    """Phases of the game"""
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"

class OpeningTheorySystem:
    """
    Comprehensive Opening Theory System
    Provides real-time opening detection, move suggestions, and statistical analysis
    """
    
    def __init__(self):
        self.variations: Dict[str, OpeningVariation] = {}
        self.positions: Dict[str, OpeningPosition] = {}  # FEN -> OpeningPosition
        self.eco_index: Dict[str, List[str]] = {}  # ECO -> List of variation names
        self.move_tree: Dict[str, Dict[str, str]] = {}  # FEN -> {move: resulting_FEN}
        
        # Caching and performance
        self.position_cache: Dict[str, Dict] = {}
        self.cache_lock = threading.Lock()
        
        # Statistics tracking
        self.opening_stats: Dict[str, Dict] = {}
        
        # Initialize the comprehensive database
        self._initialize_comprehensive_database()
        self._build_move_tree()
        
        print(f"🎯 Opening Theory System initialized:")
        print(f"   📚 {len(self.variations)} variations loaded")
        print(f"   🎲 {len(self.positions)} positions indexed")
        print(f"   📊 {len(self.eco_index)} ECO codes catalogued")
    
    def _initialize_comprehensive_database(self):
        """Initialize comprehensive opening database with major variations"""
        
        # ==================== KING'S PAWN OPENINGS (1.e4) ====================
        
        # Basic King's Pawn
        self._add_variation(OpeningVariation(
            name="King's Pawn Opening",
            eco="B00",
            moves=["e4"],
            uci_moves=["e2e4"],
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            description="The most popular first move, controlling the center and developing pieces quickly.",
            key_ideas=["Control the center", "Quick development", "King safety"],
            typical_plans=["Develop knights before bishops", "Castle early", "Control central squares"]
        ))
        
        # King's Pawn Game
        self._add_variation(OpeningVariation(
            name="King's Pawn Game",
            eco="C20",
            moves=["e4", "e5"],
            uci_moves=["e2e4", "e7e5"],
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
            parent_eco="B00",
            description="Classical symmetric response, leading to open tactical games.",
            key_ideas=["Symmetric pawn structure", "Open center", "Tactical complications"],
            typical_plans=["Develop knights to f3 and c6", "Fight for central control", "Prepare castling"]
        ))
        
        # Italian Game
        self._add_variation(OpeningVariation(
            name="Italian Game",
            eco="C50",
            moves=["e4", "e5", "Nf3", "Nc6", "Bc4"],
            uci_moves=["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"],
            fen="r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            parent_eco="C20",
            description="One of the oldest openings, targeting the f7 square.",
            key_ideas=["Attack f7 weakness", "Quick development", "Central control"],
            typical_plans=["Castle kingside", "Develop remaining pieces", "Consider d3 and Be3"],
            famous_games=["Greco vs NN, 1620", "Morphy vs Duke of Brunswick, 1858"]
        ))
        
        # Ruy Lopez
        self._add_variation(OpeningVariation(
            name="Ruy Lopez",
            eco="C60",
            moves=["e4", "e5", "Nf3", "Nc6", "Bb5"],
            uci_moves=["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
            fen="r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
            parent_eco="C20",
            description="The Spanish Opening, one of the most analyzed openings in chess.",
            key_ideas=["Pressure on e5", "Long-term positional advantage", "Flexible pawn structure"],
            typical_plans=["Castle kingside", "Play Re1", "Consider d3 and c3"],
            famous_games=["Capablanca vs Marshall, 1909", "Kasparov vs Karpov, 1984"]
        ))
        
        # Ruy Lopez: Morphy Defense
        self._add_variation(OpeningVariation(
            name="Ruy Lopez: Morphy Defense",
            eco="C78",
            moves=["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"],
            uci_moves=["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"],
            fen="r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
            parent_eco="C60",
            description="The most popular defense to the Ruy Lopez.",
            key_ideas=["Challenge the Spanish bishop", "Maintain central tension", "Flexible development"],
            typical_plans=["Ba4 or Bxc6", "Castle kingside", "Central pawn breaks with d3 and c3"]
        ))
        
        # Sicilian Defense
        self._add_variation(OpeningVariation(
            name="Sicilian Defense",
            eco="B20",
            moves=["e4", "c5"],
            uci_moves=["e2e4", "c7c5"],
            fen="rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
            parent_eco="B00",
            description="The most popular response to 1.e4, leading to sharp tactical games.",
            key_ideas=["Asymmetric pawn structure", "Counterplay on queenside", "Sharp tactical play"],
            typical_plans=["Open Sicilian with Nf3 and d4", "Closed Sicilian with Nc3", "Control d4 square"]
        ))
        
        # Sicilian Defense: Najdorf Variation
        self._add_variation(OpeningVariation(
            name="Sicilian Defense: Najdorf Variation",
            eco="B90",
            moves=["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6"],
            uci_moves=["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"],
            fen="rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6",
            parent_eco="B20",
            description="The sharpest and most theoretical variation of the Sicilian Defense.",
            key_ideas=["Flexible pawn structure", "Kingside attack potential", "Complex middlegame positions"],
            typical_plans=["Be3 and f3", "0-0-0 and h4-h5", "Central control with e5"],
            famous_games=["Fischer vs Spassky, 1972", "Kasparov vs Topalov, 1999"]
        ))
        
        # French Defense
        self._add_variation(OpeningVariation(
            name="French Defense",
            eco="C00",
            moves=["e4", "e6"],
            uci_moves=["e2e4", "e7e6"],
            fen="rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            parent_eco="B00",
            description="A solid defense leading to strategic middlegames.",
            key_ideas=["Solid pawn structure", "Strategic complexity", "Light-squared bishop problems"],
            typical_plans=["d4 and Nc3", "Develop pieces harmoniously", "Consider f4-f5 advance"]
        ))
        
        # Caro-Kann Defense
        self._add_variation(OpeningVariation(
            name="Caro-Kann Defense",
            eco="B10",
            moves=["e4", "c6"],
            uci_moves=["e2e4", "c7c6"],
            fen="rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            parent_eco="B00",
            description="A solid defense avoiding the pawn weaknesses of the French Defense.",
            key_ideas=["Solid pawn structure", "Active light-squared bishop", "Safe king position"],
            typical_plans=["d4 and Nc3", "Develop naturally", "Consider space advantage in center"]
        ))
        
        # ==================== QUEEN'S PAWN OPENINGS (1.d4) ====================
        
        # Queen's Pawn Opening
        self._add_variation(OpeningVariation(
            name="Queen's Pawn Opening",
            eco="D00",
            moves=["d4"],
            uci_moves=["d2d4"],
            fen="rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
            description="The second most popular first move, emphasizing central control.",
            key_ideas=["Central control", "Positional play", "Gradual development"],
            typical_plans=["Support d4 with c4 or Nf3", "Develop pieces harmoniously", "Control key squares"]
        ))
        
        # Queen's Gambit
        self._add_variation(OpeningVariation(
            name="Queen's Gambit",
            eco="D06",
            moves=["d4", "d5", "c4"],
            uci_moves=["d2d4", "d7d5", "c2c4"],
            fen="rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3 0 2",
            parent_eco="D00",
            description="One of the oldest and most respected openings in chess.",
            key_ideas=["Central control", "Piece activity", "Positional pressure"],
            typical_plans=["Develop knights", "Consider Bg5 or Bf4", "Castle kingside"],
            famous_games=["Capablanca vs Alekhine, 1927", "Botvinnik vs Smyslov, 1954"]
        ))
        
        # Queen's Gambit Declined
        self._add_variation(OpeningVariation(
            name="Queen's Gambit Declined",
            eco="D30",
            moves=["d4", "d5", "c4", "e6"],
            uci_moves=["d2d4", "d7d5", "c2c4", "e7e6"],
            fen="rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3",
            parent_eco="D06",
            description="The classical response to the Queen's Gambit.",
            key_ideas=["Solid central structure", "Gradual development", "Strategic complexity"],
            typical_plans=["Nc3 and Nf3", "Develop bishops", "Consider minority attack"]
        ))
        
        # King's Indian Defense
        self._add_variation(OpeningVariation(
            name="King's Indian Defense",
            eco="E60",
            moves=["d4", "Nf6", "c4", "g6"],
            uci_moves=["d2d4", "g8f6", "c2c4", "g7g6"],
            fen="rnbqkb1r/pppppp1p/5np1/8/2PP4/8/PP2PPPP/RNBQKBNR w KQkq - 0 3",
            parent_eco="D00",
            description="A hypermodern defense allowing White central control initially.",
            key_ideas=["Fianchetto kingside bishop", "Central counterplay", "Dynamic piece play"],
            typical_plans=["Bg7 and 0-0", "Prepare ...e5 or ...c5", "Kingside attack potential"],
            famous_games=["Fischer vs Petrosian, 1971", "Kasparov vs Karpov, 1986"]
        ))
        
        # ==================== ENGLISH OPENING (1.c4) ====================
        
        # English Opening
        self._add_variation(OpeningVariation(
            name="English Opening",
            eco="A10",
            moves=["c4"],
            uci_moves=["c2c4"],
            fen="rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3 0 1",
            description="A flexible opening that can transpose to many different systems.",
            key_ideas=["Flexible development", "Control of d5", "Transposition possibilities"],
            typical_plans=["Nf3 and g3", "Nc3 and e4", "Control central squares"]
        ))
        
        # English Opening: Symmetrical Variation
        self._add_variation(OpeningVariation(
            name="English Opening: Symmetrical Variation",
            eco="A30",
            moves=["c4", "c5"],
            uci_moves=["c2c4", "c7c5"],
            fen="rnbqkbnr/pp1ppppp/8/2p5/2P5/8/PP1PPPPP/RNBQKBNR w KQkq c6 0 2",
            parent_eco="A10",
            description="The symmetrical response leading to balanced positions.",
            key_ideas=["Symmetrical pawn structure", "Flexible piece development", "Strategic complexity"],
            typical_plans=["Nc3 and g3", "Nf3 and d4", "Control key central squares"]
        ))
        
        # ==================== RÉTI OPENING (1.Nf3) ====================
        
        # Réti Opening
        self._add_variation(OpeningVariation(
            name="Réti Opening",
            eco="A04",
            moves=["Nf3"],
            uci_moves=["g1f3"],
            fen="rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1",
            description="A hypermodern opening emphasizing piece development over pawn advances.",
            key_ideas=["Hypermodern principles", "Flexible development", "Control from a distance"],
            typical_plans=["g3 and Bg2", "c4 and Nc3", "Control central squares indirectly"]
        ))
        
        # Add more variations as needed...
        
    def _add_variation(self, variation: OpeningVariation):
        """Add a variation to the database"""
        self.variations[variation.name] = variation
        
        # Add to ECO index
        if variation.eco not in self.eco_index:
            self.eco_index[variation.eco] = []
        self.eco_index[variation.eco].append(variation.name)
        
        # Create position entry
        position = OpeningPosition(
            fen=variation.fen,
            variation=variation,
            move_number=len(variation.moves),
            next_moves=[],  # Will be populated later
            is_main_line=True
        )
        self.positions[variation.fen] = position
    
    def _build_move_tree(self):
        """Build the move tree for position navigation"""
        for variation in self.variations.values():
            try:
                board = chess.Board()
                current_fen = board.fen()
                
                for i, move in enumerate(variation.uci_moves):
                    if current_fen not in self.move_tree:
                        self.move_tree[current_fen] = {}
                    
                    # Make the move
                    chess_move = chess.Move.from_uci(move)
                    board.push(chess_move)
                    next_fen = board.fen()
                    
                    # Add to move tree
                    self.move_tree[current_fen][move] = next_fen
                    current_fen = next_fen
                    
            except Exception as e:
                print(f"⚠️ Error building move tree for {variation.name}: {e}")
    
    def detect_opening(self, fen: str) -> Dict[str, Any]:
        """
        Detect opening from FEN position
        Returns comprehensive opening information
        """
        with self.cache_lock:
            if fen in self.position_cache:
                return self.position_cache[fen]
        
        try:
            # Direct position lookup
            if fen in self.positions:
                position = self.positions[fen]
                result = {
                    "name": position.variation.name,
                    "eco": position.variation.eco,
                    "moves": position.variation.moves,
                    "uci_moves": position.variation.uci_moves,
                    "move_number": position.move_number,
                    "description": position.variation.description,
                    "key_ideas": position.variation.key_ideas,
                    "typical_plans": position.variation.typical_plans,
                    "famous_games": position.variation.famous_games,
                    "phase": OpeningPhase.OPENING.value,
                    "is_theoretical": True,
                    "next_moves": [asdict(move) for move in position.next_moves]
                }
                
                with self.cache_lock:
                    self.position_cache[fen] = result
                return result
            
            # Try to find by move sequence matching
            board = chess.Board(fen)
            move_count = board.fullmove_number
            
            # Determine game phase
            if move_count <= 15:
                phase = OpeningPhase.OPENING.value
                opening_info = self._find_closest_opening(fen)
                if opening_info:
                    result = opening_info
                else:
                    result = {
                        "name": "Unknown Opening",
                        "eco": "",
                        "moves": [],
                        "uci_moves": [],
                        "move_number": move_count,
                        "description": "Position not in opening database",
                        "key_ideas": [],
                        "typical_plans": [],
                        "famous_games": [],
                        "phase": phase,
                        "is_theoretical": False,
                        "next_moves": []
                    }
            elif move_count <= 40:
                phase = OpeningPhase.MIDDLEGAME.value
                result = {
                    "name": "Middlegame",
                    "eco": "",
                    "moves": [],
                    "uci_moves": [],
                    "move_number": move_count,
                    "description": "Game has transitioned to middlegame",
                    "key_ideas": ["Improve piece positions", "Create weaknesses", "Plan strategic goals"],
                    "typical_plans": ["Centralize pieces", "Create pawn breaks", "Improve king safety"],
                    "famous_games": [],
                    "phase": phase,
                    "is_theoretical": False,
                    "next_moves": []
                }
            else:
                phase = OpeningPhase.ENDGAME.value
                result = {
                    "name": "Endgame",
                    "eco": "",
                    "moves": [],
                    "uci_moves": [],
                    "move_number": move_count,
                    "description": "Game has reached the endgame phase",
                    "key_ideas": ["Activate the king", "Create passed pawns", "Improve piece coordination"],
                    "typical_plans": ["King activity", "Pawn promotion", "Piece coordination"],
                    "famous_games": [],
                    "phase": phase,
                    "is_theoretical": False,
                    "next_moves": []
                }
            
            with self.cache_lock:
                self.position_cache[fen] = result
            return result
            
        except Exception as e:
            print(f"❌ Opening detection error: {e}")
            result = {
                "name": "Error",
                "eco": "",
                "moves": [],
                "uci_moves": [],
                "move_number": 0,
                "description": "Error detecting opening",
                "key_ideas": [],
                "typical_plans": [],
                "famous_games": [],
                "phase": OpeningPhase.OPENING.value,
                "is_theoretical": False,
                "next_moves": []
            }
            return result
    
    def _find_closest_opening(self, fen: str) -> Optional[Dict[str, Any]]:
        """Find the closest matching opening by analyzing the position"""
        try:
            board = chess.Board(fen)
            
            # Simple heuristic: find opening with similar piece placement
            best_match = None
            best_score = 0
            
            for position in self.positions.values():
                try:
                    opening_board = chess.Board(position.fen)
                    score = self._calculate_position_similarity(board, opening_board)
                    
                    if score > best_score and score > 0.7:  # Minimum similarity threshold
                        best_score = score
                        best_match = position
                        
                except:
                    continue
            
            if best_match:
                return {
                    "name": f"{best_match.variation.name} (Similar)",
                    "eco": best_match.variation.eco,
                    "moves": best_match.variation.moves,
                    "uci_moves": best_match.variation.uci_moves,
                    "move_number": best_match.move_number,
                    "description": f"Similar to {best_match.variation.description}",
                    "key_ideas": best_match.variation.key_ideas,
                    "typical_plans": best_match.variation.typical_plans,
                    "famous_games": best_match.variation.famous_games,
                    "phase": OpeningPhase.OPENING.value,
                    "is_theoretical": False,
                    "next_moves": []
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding closest opening: {e}")
            return None
    
    def _calculate_position_similarity(self, board1: chess.Board, board2: chess.Board) -> float:
        """Calculate similarity between two positions"""
        try:
            # Compare piece positions
            pieces1 = board1.piece_map()
            pieces2 = board2.piece_map()
            
            total_squares = 64
            matching_squares = 0
            
            for square in chess.SQUARES:
                piece1 = pieces1.get(square)
                piece2 = pieces2.get(square)
                
                if piece1 == piece2:  # Both None or same piece
                    matching_squares += 1
            
            return matching_squares / total_squares
            
        except:
            return 0.0
    
    def get_next_moves(self, fen: str, limit: int = 10) -> List[OpeningMove]:
        """Get popular next moves from a position"""
        try:
            if fen in self.move_tree:
                moves = []
                for uci_move, next_fen in self.move_tree[fen].items():
                    try:
                        board = chess.Board(fen)
                        chess_move = chess.Move.from_uci(uci_move)
                        san_move = board.san(chess_move)
                        
                        # Create opening move with placeholder statistics
                        opening_move = OpeningMove(
                            move=uci_move,
                            san=san_move,
                            white_wins=40,  # Placeholder
                            draws=30,       # Placeholder
                            black_wins=30,  # Placeholder
                            total_games=100, # Placeholder
                            popularity=50.0  # Placeholder
                        )
                        moves.append(opening_move)
                        
                    except:
                        continue
                
                return moves[:limit]
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting next moves: {e}")
            return []
    
    def get_opening_by_eco(self, eco: str) -> List[OpeningVariation]:
        """Get all openings with specific ECO code"""
        if eco in self.eco_index:
            return [self.variations[name] for name in self.eco_index[eco]]
        return []
    
    def search_openings(self, query: str) -> List[OpeningVariation]:
        """Search openings by name"""
        query_lower = query.lower()
        results = []
        
        for variation in self.variations.values():
            if query_lower in variation.name.lower():
                results.append(variation)
        
        return results
    
    def get_opening_statistics(self, eco: str) -> Dict[str, Any]:
        """Get statistics for an opening (placeholder for future database integration)"""
        return {
            "eco": eco,
            "popularity": 75.0,  # Placeholder
            "white_win_rate": 45.0,
            "draw_rate": 35.0,
            "black_win_rate": 20.0,
            "total_games": 50000,
            "average_rating": 2200
        }
    
    def is_theoretical_position(self, fen: str) -> bool:
        """Check if position is in opening theory"""
        return fen in self.positions
    
    def get_transpositions(self, fen: str) -> List[str]:
        """Get positions that transpose to the given position"""
        if fen in self.positions:
            return self.positions[fen].transpositions
        return []
    
    def clear_cache(self):
        """Clear position cache"""
        with self.cache_lock:
            self.position_cache.clear()
        print("🧹 Opening theory cache cleared")
    
    def export_database(self, filepath: str):
        """Export opening database to JSON file"""
        try:
            data = {
                "variations": {name: asdict(var) for name, var in self.variations.items()},
                "positions": {fen: asdict(pos) for fen, pos in self.positions.items()},
                "eco_index": self.eco_index,
                "version": "1.0",
                "created": time.time()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Opening database exported to {filepath}")
            
        except Exception as e:
            print(f"❌ Error exporting database: {e}")
    
    def import_database(self, filepath: str):
        """Import opening database from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Import variations
            for name, var_data in data.get("variations", {}).items():
                variation = OpeningVariation(**var_data)
                self.variations[name] = variation
            
            # Import positions
            for fen, pos_data in data.get("positions", {}).items():
                # Reconstruct OpeningPosition with variation reference
                var_data = pos_data["variation"]
                variation = OpeningVariation(**var_data)
                
                position = OpeningPosition(
                    fen=fen,
                    variation=variation,
                    move_number=pos_data["move_number"],
                    next_moves=[OpeningMove(**move_data) for move_data in pos_data["next_moves"]],
                    is_main_line=pos_data.get("is_main_line", True),
                    transpositions=pos_data.get("transpositions", [])
                )
                self.positions[fen] = position
            
            # Import ECO index
            self.eco_index = data.get("eco_index", {})
            
            # Rebuild move tree
            self._build_move_tree()
            
            print(f"✅ Opening database imported from {filepath}")
            
        except Exception as e:
            print(f"❌ Error importing database: {e}")

# Global instance
opening_theory_system = OpeningTheorySystem()