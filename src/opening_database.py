"""
Comprehensive Chess Opening Database
For Phase 3 of the Analysis System
"""

import chess
from typing import Dict, List, Optional, Tuple, Any

class OpeningDatabase:
    """
    Professional chess opening database with ECO codes
    Supports opening detection and classification
    """
    
    def __init__(self):
        self.openings = {}
        self.position_cache = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize comprehensive opening database"""
        
        # King's Pawn Openings (1.e4)
        self.openings.update({
            # Italian Game
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3": {
                "name": "King's Pawn Opening",
                "eco": "B00",
                "moves": ["e4"]
            },
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6": {
                "name": "King's Pawn Game",
                "eco": "C20",
                "moves": ["e4", "e5"]
            },
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": {
                "name": "King's Knight Opening",
                "eco": "C40",
                "moves": ["e4", "e5", "Nf3"]
            },
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq -": {
                "name": "Italian Game",
                "eco": "C50",
                "moves": ["e4", "e5", "Nf3", "Nc6"]
            },
            "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq -": {
                "name": "Italian Game",
                "eco": "C50",
                "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4"]
            },
            
            # Ruy Lopez
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq -": {
                "name": "Ruy Lopez",
                "eco": "C60",
                "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"]
            },
            "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQ1RK1 b kq -": {
                "name": "Ruy Lopez: Morphy Defense",
                "eco": "C78",
                "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"]
            },
            
            # Sicilian Defense
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6": {
                "name": "Sicilian Defense",
                "eco": "B20",
                "moves": ["e4", "c5"]
            },
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": {
                "name": "Sicilian Defense: Open",
                "eco": "B20",
                "moves": ["e4", "c5", "Nf3"]
            },
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq -": {
                "name": "Sicilian Defense: Closed",
                "eco": "B23",
                "moves": ["e4", "c5", "Nc3"]
            },
            
            # French Defense
            "rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": {
                "name": "French Defense",
                "eco": "C00",
                "moves": ["e4", "e6"]
            },
            "rnbqkbnr/pppp1ppp/4p3/8/4PP2/8/PPPP2PP/RNBQKBNR b KQkq f3": {
                "name": "French Defense: Advance Variation",
                "eco": "C02",
                "moves": ["e4", "e6", "d4", "d5", "e5"]
            },
            
            # Caro-Kann Defense
            "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": {
                "name": "Caro-Kann Defense",
                "eco": "B10",
                "moves": ["e4", "c6"]
            },
            
            # Alekhine's Defense
            "rnbqkb1r/pppppppp/5n2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": {
                "name": "Alekhine's Defense",
                "eco": "B02",
                "moves": ["e4", "Nf6"]
            },
            
            # Pirc Defense
            "rnbqkbnr/ppp1pppp/3p4/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": {
                "name": "Pirc Defense",
                "eco": "B07",
                "moves": ["e4", "d6"]
            }
        })
        
        # Queen's Pawn Openings (1.d4)
        self.openings.update({
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3": {
                "name": "Queen's Pawn Opening",
                "eco": "D00",
                "moves": ["d4"]
            },
            "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6": {
                "name": "Queen's Pawn Game",
                "eco": "D00",
                "moves": ["d4", "d5"]
            },
            "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3": {
                "name": "Queen's Gambit",
                "eco": "D06",
                "moves": ["d4", "d5", "c4"]
            },
            "rnbqkbnr/ppp2ppp/4p3/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq -": {
                "name": "Queen's Gambit Declined",
                "eco": "D30",
                "moves": ["d4", "d5", "c4", "e6"]
            },
            "rnbqkbnr/pp2pppp/2p5/3p4/2PP4/8/PP2PPPP/RNBQKBNR w KQkq -": {
                "name": "Queen's Gambit Declined: Slav Defense",
                "eco": "D10",
                "moves": ["d4", "d5", "c4", "c6"]
            },
            "rnbqkbnr/ppp2ppp/8/3pp3/2PP4/8/PP2PPPP/RNBQKBNR w KQkq e6": {
                "name": "Queen's Gambit Accepted",
                "eco": "D20",
                "moves": ["d4", "d5", "c4", "dxc4"]
            },
            
            # King's Indian Defense
            "rnbqkb1r/pppppp1p/5np1/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq -": {
                "name": "King's Indian Defense",
                "eco": "E60",
                "moves": ["d4", "Nf6", "c4", "g6"]
            },
            
            # Nimzo-Indian Defense
            "rnbqk2r/pppp1ppp/4pn2/8/1bPP4/2N5/PP2PPPP/R1BQKBNR w KQkq -": {
                "name": "Nimzo-Indian Defense",
                "eco": "E20",
                "moves": ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4"]
            },
            
            # Grünfeld Defense
            "rnbqkb1r/ppp1pp1p/5np1/3p4/2PP4/2N5/PP2PPPP/R1BQKBNR w KQkq -": {
                "name": "Grünfeld Defense",
                "eco": "D80",
                "moves": ["d4", "Nf6", "c4", "g6", "Nc3", "d5"]
            }
        })
        
        # English Opening (1.c4)
        self.openings.update({
            "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq c3": {
                "name": "English Opening",
                "eco": "A10",
                "moves": ["c4"]
            },
            "rnbqkbnr/ppp1pppp/8/3p4/2P5/8/PP1PPPPP/RNBQKBNR w KQkq d6": {
                "name": "English Opening: Symmetrical Variation",
                "eco": "A30",
                "moves": ["c4", "c5"]
            },
            "rnbqkb1r/pppppppp/5n2/8/2P5/8/PP1PPPPP/RNBQKBNR w KQkq -": {
                "name": "English Opening: Anglo-Indian Defense",
                "eco": "A15",
                "moves": ["c4", "Nf6"]
            }
        })
        
        # Réti Opening (1.Nf3)
        self.openings.update({
            "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq -": {
                "name": "Réti Opening",
                "eco": "A04",
                "moves": ["Nf3"]
            },
            "rnbqkb1r/pppppppp/5n2/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq -": {
                "name": "Réti Opening: King's Indian Attack",
                "eco": "A07",
                "moves": ["Nf3", "Nf6"]
            }
        })
        
        # Bird's Opening (1.f4)
        self.openings.update({
            "rnbqkbnr/pppppppp/8/8/5P2/8/PPPPP1PP/RNBQKBNR b KQkq f3": {
                "name": "Bird's Opening",
                "eco": "A02",
                "moves": ["f4"]
            }
        })
        
        # Uncommon first moves
        self.openings.update({
            "rnbqkbnr/pppppppp/8/8/1P6/8/P1PPPPPP/RNBQKBNR b KQkq b3": {
                "name": "Larsen's Opening",
                "eco": "A01",
                "moves": ["b3"]
            },
            "rnbqkbnr/pppppppp/8/8/8/2N5/PPPPPPPP/R1BQKBNR b KQkq -": {
                "name": "Van't Kruijs Opening",
                "eco": "A00",
                "moves": ["Nc3"]
            }
        })
        
        print(f"✅ Opening database initialized with {len(self.openings)} positions")
    
    def detect_opening(self, fen: str) -> Dict[str, str]:
        """
        Detect opening from FEN position
        Returns opening name, ECO code, and move sequence
        """
        # Check cache first
        if fen in self.position_cache:
            return self.position_cache[fen]
        
        # Direct lookup
        if fen in self.openings:
            result = self.openings[fen].copy()
            self.position_cache[fen] = result
            return result
        
        # Try to match by position similarity (simplified)
        # In production, use more sophisticated matching
        try:
            board = chess.Board(fen)
            
            # Check if it's still in opening phase (< 10 moves)
            if board.fullmove_number > 10:
                result = {
                    "name": "Middle Game",
                    "eco": "",
                    "moves": []
                }
                self.position_cache[fen] = result
                return result
            
            # Try to find closest match by piece positions
            best_match = self._find_closest_opening(board)
            if best_match:
                self.position_cache[fen] = best_match
                return best_match
            
        except Exception as e:
            print(f"❌ Opening detection error: {e}")
        
        # Default unknown opening
        result = {
            "name": "Unknown Opening",
            "eco": "",
            "moves": []
        }
        self.position_cache[fen] = result
        return result
    
    def _find_closest_opening(self, board: chess.Board) -> Optional[Dict[str, str]]:
        """Find closest matching opening by piece similarity"""
        try:
            current_pieces = set(board.piece_map().values())
            
            # Look for openings with similar piece counts
            for opening_fen, opening_data in self.openings.items():
                try:
                    opening_board = chess.Board(opening_fen)
                    opening_pieces = set(opening_board.piece_map().values())
                    
                    # Simple similarity check
                    if len(current_pieces.intersection(opening_pieces)) >= len(opening_pieces) * 0.8:
                        return opening_data.copy()
                        
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Opening matching error: {e}")
            return None
    
    def get_opening_statistics(self, eco_code: str) -> Dict[str, Any]:
        """Get statistics for an opening (placeholder for future implementation)"""
        # In production, this would return win rates, popularity, etc.
        return {
            "eco": eco_code,
            "popularity": "Unknown",
            "white_win_rate": 0.0,
            "black_win_rate": 0.0,
            "draw_rate": 0.0,
            "games_played": 0
        }
    
    def get_opening_moves(self, fen: str) -> List[str]:
        """Get the move sequence that led to this opening"""
        opening_data = self.detect_opening(fen)
        return opening_data.get("moves", [])
    
    def is_theoretical_position(self, fen: str) -> bool:
        """Check if position is in opening theory"""
        return fen in self.openings
    
    def get_all_openings_by_eco(self, eco_prefix: str) -> List[Dict[str, str]]:
        """Get all openings starting with ECO prefix (e.g., 'C' for King's Pawn)"""
        result = []
        for opening_data in self.openings.values():
            if opening_data["eco"].startswith(eco_prefix):
                result.append(opening_data.copy())
        return result
    
    def clear_cache(self):
        """Clear position cache"""
        self.position_cache.clear()
        print("🧹 Opening database cache cleared")

# Global instance
opening_database = OpeningDatabase()