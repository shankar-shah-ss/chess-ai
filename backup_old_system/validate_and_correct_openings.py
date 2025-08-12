#!/usr/bin/env python3
"""
Chess Opening Validation and Correction Tool
Validates all chess openings and variations against Lichess master database
Corrects any inaccuracies found in the opening book
"""

import requests
import json
import sqlite3
import time
import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
import concurrent.futures
from threading import Lock

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))
from opening_book import BookMove, PGNDatabase, OpeningBook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('opening_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of opening validation"""
    position_fen: str
    current_moves: List[BookMove]
    lichess_moves: List[BookMove]
    discrepancies: List[str]
    needs_correction: bool
    opening_name: str = ""

class OpeningValidator:
    """Validates and corrects chess openings against Lichess master database"""
    
    def __init__(self, db_path: str = "src/books/openings.db"):
        self.db_path = db_path
        self.base_url = "https://explorer.lichess.ovh"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Chess-AI Opening Validator 1.0'
        })
        
        # Rate limiting
        self.request_delay = 1.0  # Respectful rate limiting
        self.last_request_time = 0
        self.request_lock = Lock()
        
        # Date range for filtering (last 10 years for comprehensive data)
        current_date = datetime.now()
        ten_years_ago = current_date - timedelta(days=10*365)
        self.since_date = f"{ten_years_ago.year}-{ten_years_ago.month:02d}"
        self.until_date = f"{current_date.year}-{current_date.month:02d}"
        
        # Initialize database and opening book
        self.pgn_db = PGNDatabase(db_path)
        self.opening_book = OpeningBook()
        
        # Validation results
        self.validation_results: List[ValidationResult] = []
        self.corrections_made = 0
        
        # Comprehensive opening positions to validate
        self.critical_positions = self._get_critical_positions()
    
    def _get_critical_positions(self) -> Dict[str, str]:
        """Get critical opening positions that must be validated"""
        positions = {}
        
        # Starting position
        positions[chess.STARTING_FEN] = "Starting Position"
        
        # Create a board to generate positions
        board = chess.Board()
        
        # === CRITICAL FIRST MOVES ===
        first_moves = [
            ("e2e4", "King's Pawn"),
            ("d2d4", "Queen's Pawn"), 
            ("g1f3", "Reti Opening"),
            ("c2c4", "English Opening"),
            ("b1c3", "Van't Kruijs Opening"),
            ("f2f4", "Bird's Opening"),
            ("g2g3", "Benko's Opening"),
            ("b2b3", "Nimzowitsch-Larsen Attack")
        ]
        
        for move_uci, name in first_moves:
            board.reset()
            move = chess.Move.from_uci(move_uci)
            board.push(move)
            positions[board.fen()] = f"After 1.{name}"
        
        # === CRITICAL SECOND MOVES ===
        
        # After 1.e4
        board.reset()
        board.push(chess.Move.from_uci("e2e4"))
        base_fen = board.fen()
        positions[base_fen] = "After 1.e4"
        
        e4_responses = [
            ("e7e5", "King's Pawn Game"),
            ("c7c5", "Sicilian Defense"),
            ("e7e6", "French Defense"),
            ("c7c6", "Caro-Kann Defense"),
            ("d7d6", "Pirc Defense"),
            ("g8f6", "Alekhine's Defense"),
            ("d7d5", "Scandinavian Defense")
        ]
        
        for move_uci, name in e4_responses:
            board.reset()
            board.push(chess.Move.from_uci("e2e4"))
            board.push(chess.Move.from_uci(move_uci))
            positions[board.fen()] = f"1.e4 {name}"
        
        # After 1.d4
        board.reset()
        board.push(chess.Move.from_uci("d2d4"))
        base_fen = board.fen()
        positions[base_fen] = "After 1.d4"
        
        d4_responses = [
            ("d7d5", "Queen's Gambit"),
            ("g8f6", "Indian Defenses"),
            ("e7e6", "Queen's Pawn Game"),
            ("c7c5", "Benoni Defense"),
            ("f7f5", "Dutch Defense"),
            ("g7g6", "King's Indian Defense")
        ]
        
        for move_uci, name in d4_responses:
            board.reset()
            board.push(chess.Move.from_uci("d2d4"))
            board.push(chess.Move.from_uci(move_uci))
            positions[board.fen()] = f"1.d4 {name}"
        
        # === MAJOR OPENING LINES ===
        
        major_lines = [
            # Ruy Lopez
            (["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"], "Ruy Lopez"),
            (["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"], "Ruy Lopez Morphy Defense"),
            
            # Italian Game
            (["e2e4", "e7e5", "g1f3", "b8c6", "f1c4"], "Italian Game"),
            (["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"], "Italian Game Classical"),
            
            # Sicilian Defense
            (["e2e4", "c7c5", "g1f3"], "Sicilian Defense Open"),
            (["e2e4", "c7c5", "g1f3", "d7d6"], "Sicilian Defense Najdorf Setup"),
            (["e2e4", "c7c5", "g1f3", "b8c6"], "Sicilian Defense Accelerated Dragon Setup"),
            
            # French Defense
            (["e2e4", "e7e6", "d2d4"], "French Defense"),
            (["e2e4", "e7e6", "d2d4", "d7d5"], "French Defense Main Line"),
            (["e2e4", "e7e6", "d2d4", "d7d5", "e4e5"], "French Defense Advance"),
            
            # Queen's Gambit
            (["d2d4", "d7d5", "c2c4"], "Queen's Gambit"),
            (["d2d4", "d7d5", "c2c4", "e7e6"], "Queen's Gambit Declined"),
            (["d2d4", "d7d5", "c2c4", "d5c4"], "Queen's Gambit Accepted"),
            
            # King's Indian Defense
            (["d2d4", "g8f6", "c2c4", "g7g6"], "King's Indian Defense"),
            (["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7"], "King's Indian Defense Main Line"),
            
            # English Opening
            (["c2c4", "e7e5"], "English Opening Reversed Sicilian"),
            (["c2c4", "g8f6"], "English Opening Anglo-Indian"),
            (["c2c4", "c7c5"], "English Opening Symmetrical"),
        ]
        
        for moves, name in major_lines:
            board.reset()
            for move_uci in moves:
                board.push(chess.Move.from_uci(move_uci))
            positions[board.fen()] = name
        
        logger.info(f"Generated {len(positions)} critical positions for validation")
        return positions
    
    def _rate_limit(self):
        """Enforce rate limiting for API requests"""
        with self.request_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                sleep_time = self.request_delay - time_since_last
                time.sleep(sleep_time)
            self.last_request_time = time.time()
    
    def fetch_lichess_data(self, fen: str) -> Optional[Dict]:
        """Fetch opening data from Lichess masters database"""
        self._rate_limit()
        
        try:
            params = {}
            if fen != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1":
                params['fen'] = fen
            
            response = self.session.get(f"{self.base_url}/masters", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Fetched Lichess data for position: {fen[:50]}...")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Lichess data for {fen}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Lichess JSON for {fen}: {e}")
            return None
    
    def convert_lichess_moves(self, lichess_data: Dict) -> List[BookMove]:
        """Convert Lichess move data to BookMove objects"""
        book_moves = []
        
        if not lichess_data or 'moves' not in lichess_data:
            return book_moves
        
        for move_data in lichess_data['moves']:
            try:
                uci_move = move_data['uci']
                white_wins = move_data.get('white', 0)
                draws = move_data.get('draws', 0)
                black_wins = move_data.get('black', 0)
                total_games = white_wins + draws + black_wins
                
                if total_games < 5:  # Skip moves with very few games
                    continue
                
                # Calculate average rating (estimate based on masters database)
                # Masters database typically has high-rated players
                avg_rating = 2400
                
                book_move = BookMove(
                    move=uci_move,
                    weight=total_games,
                    wins=white_wins,
                    draws=draws,
                    losses=black_wins,
                    avg_rating=avg_rating,
                    last_played=0
                )
                
                book_moves.append(book_move)
                
            except (KeyError, ValueError) as e:
                logger.warning(f"Error processing Lichess move data: {e}")
                continue
        
        # Sort by total games (weight) descending
        book_moves.sort(key=lambda x: x.weight, reverse=True)
        return book_moves
    
    def _get_current_moves(self, fen: str) -> List[BookMove]:
        """Get current moves from our opening book system"""
        try:
            # Try to get moves from PGN database first
            moves = self.pgn_db.get_moves(fen)
            if moves:
                return moves
            
            # Try to get moves from the built-in JSON book
            if hasattr(self.opening_book, 'json_book') and fen in self.opening_book.json_book:
                return self.opening_book.json_book[fen]
            
            # Try using the opening book's get_book_move method
            move_uci = self.opening_book.get_book_move(fen)
            if move_uci:
                # Convert single move to BookMove list
                return [BookMove(move_uci, 100, 40, 30, 30, 2200, 0)]
            
            return []
        except Exception as e:
            logger.warning(f"Error getting current moves for {fen}: {e}")
            return []
    
    def validate_position(self, fen: str, opening_name: str = "") -> ValidationResult:
        """Validate a single position against Lichess data"""
        logger.info(f"Validating position: {opening_name or fen[:50]}")
        
        # Get current moves from our opening book
        current_moves = self._get_current_moves(fen)
        
        # Get Lichess data
        lichess_data = self.fetch_lichess_data(fen)
        lichess_moves = self.convert_lichess_moves(lichess_data) if lichess_data else []
        
        # Compare and find discrepancies
        discrepancies = []
        needs_correction = False
        
        if not lichess_moves:
            if current_moves:
                discrepancies.append("No Lichess data available, but we have moves")
            return ValidationResult(fen, current_moves, lichess_moves, discrepancies, False, opening_name)
        
        if not current_moves:
            discrepancies.append("Missing position in our database")
            needs_correction = True
        else:
            # Check for missing popular moves
            lichess_move_set = {move.move for move in lichess_moves[:10]}  # Top 10 Lichess moves
            current_move_set = {move.move for move in current_moves}
            
            missing_moves = lichess_move_set - current_move_set
            if missing_moves:
                discrepancies.append(f"Missing popular moves: {', '.join(missing_moves)}")
                needs_correction = True
            
            # Check for incorrect weights/statistics
            for lichess_move in lichess_moves[:5]:  # Check top 5 moves
                current_move = next((m for m in current_moves if m.move == lichess_move.move), None)
                if current_move:
                    # Check if weights are significantly different (more than 50% off)
                    weight_ratio = abs(current_move.weight - lichess_move.weight) / max(lichess_move.weight, 1)
                    if weight_ratio > 0.5:
                        discrepancies.append(f"Move {lichess_move.move}: weight mismatch (ours: {current_move.weight}, Lichess: {lichess_move.weight})")
                        needs_correction = True
        
        return ValidationResult(fen, current_moves, lichess_moves, discrepancies, needs_correction, opening_name)
    
    def correct_position(self, validation_result: ValidationResult) -> bool:
        """Correct a position based on validation results"""
        if not validation_result.needs_correction:
            return False
        
        logger.info(f"Correcting position: {validation_result.opening_name}")
        
        try:
            # Use Lichess data as the authoritative source
            corrected_moves = validation_result.lichess_moves
            
            if corrected_moves:
                # Calculate depth from FEN
                board = chess.Board(validation_result.position_fen)
                depth = board.fullmove_number * 2 - (2 if board.turn == chess.WHITE else 1)
                
                # Add corrected position to database
                self.pgn_db.add_position(validation_result.position_fen, corrected_moves, depth)
                
                logger.info(f"Corrected position with {len(corrected_moves)} moves")
                self.corrections_made += 1
                return True
            
        except Exception as e:
            logger.error(f"Error correcting position {validation_result.opening_name}: {e}")
        
        return False
    
    def validate_all_openings(self) -> List[ValidationResult]:
        """Validate all critical opening positions"""
        logger.info("Starting comprehensive opening validation...")
        
        results = []
        total_positions = len(self.critical_positions)
        
        for i, (fen, opening_name) in enumerate(self.critical_positions.items(), 1):
            logger.info(f"Progress: {i}/{total_positions} - Validating {opening_name}")
            
            try:
                result = self.validate_position(fen, opening_name)
                results.append(result)
                
                # Auto-correct if needed
                if result.needs_correction:
                    self.correct_position(result)
                
                # Progress update
                if i % 10 == 0:
                    logger.info(f"Validated {i}/{total_positions} positions, {self.corrections_made} corrections made")
                
            except Exception as e:
                logger.error(f"Error validating {opening_name}: {e}")
                continue
        
        self.validation_results = results
        return results
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report"""
        if not self.validation_results:
            return "No validation results available"
        
        report = []
        report.append("=" * 80)
        report.append("CHESS OPENING VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total positions validated: {len(self.validation_results)}")
        report.append(f"Positions needing correction: {sum(1 for r in self.validation_results if r.needs_correction)}")
        report.append(f"Corrections made: {self.corrections_made}")
        report.append("")
        
        # Summary by category
        needs_correction = [r for r in self.validation_results if r.needs_correction]
        no_issues = [r for r in self.validation_results if not r.needs_correction and not r.discrepancies]
        minor_issues = [r for r in self.validation_results if r.discrepancies and not r.needs_correction]
        
        report.append("SUMMARY:")
        report.append(f"✅ Perfect matches: {len(no_issues)}")
        report.append(f"⚠️  Minor discrepancies: {len(minor_issues)}")
        report.append(f"❌ Major corrections needed: {len(needs_correction)}")
        report.append("")
        
        # Detailed issues
        if needs_correction:
            report.append("POSITIONS REQUIRING CORRECTION:")
            report.append("-" * 50)
            for result in needs_correction:
                report.append(f"Opening: {result.opening_name}")
                report.append(f"FEN: {result.position_fen}")
                for discrepancy in result.discrepancies:
                    report.append(f"  - {discrepancy}")
                report.append("")
        
        # Minor issues
        if minor_issues:
            report.append("MINOR DISCREPANCIES (No correction needed):")
            report.append("-" * 50)
            for result in minor_issues:
                report.append(f"Opening: {result.opening_name}")
                for discrepancy in result.discrepancies:
                    report.append(f"  - {discrepancy}")
                report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def save_validation_report(self, filename: str = "opening_validation_report.txt"):
        """Save validation report to file"""
        report = self.generate_validation_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Validation report saved to {filename}")
        return filename

def main():
    """Main validation and correction process"""
    print("🔍 Chess Opening Validation and Correction Tool")
    print("=" * 60)
    
    try:
        # Initialize validator
        validator = OpeningValidator()
        
        # Run validation
        print("📊 Validating all critical opening positions...")
        results = validator.validate_all_openings()
        
        # Generate and save report
        print("📝 Generating validation report...")
        report_file = validator.save_validation_report()
        
        # Print summary
        print("\n✅ VALIDATION COMPLETE!")
        print(f"📊 Total positions validated: {len(results)}")
        print(f"🔧 Corrections made: {validator.corrections_made}")
        print(f"📄 Report saved to: {report_file}")
        
        # Show critical issues
        critical_issues = [r for r in results if r.needs_correction]
        if critical_issues:
            print(f"\n⚠️  Found {len(critical_issues)} positions with critical issues:")
            for result in critical_issues[:5]:  # Show first 5
                print(f"  - {result.opening_name}")
            if len(critical_issues) > 5:
                print(f"  ... and {len(critical_issues) - 5} more (see report for details)")
        else:
            print("\n🎉 All openings are accurate according to Lichess masters database!")
        
        print(f"\n📝 Check opening_validation.log for detailed logs")
        
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())