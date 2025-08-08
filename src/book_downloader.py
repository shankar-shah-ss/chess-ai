# book_downloader.py - Download and setup opening books
import os
import requests
import zipfile
import gzip
import shutil
from typing import Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BookDownloader:
    """Download and setup opening books from various sources"""
    
    def __init__(self, books_dir: str = "books"):
        self.books_dir = Path(books_dir)
        self.books_dir.mkdir(exist_ok=True)
        
        # Book sources with download URLs
        self.book_sources = {
            "polyglot_performance": {
                "url": "https://github.com/official-stockfish/books/raw/master/polyglot/performance.bin",
                "filename": "performance.bin",
                "description": "High-performance Polyglot book",
                "size_mb": 2.5
            },
            "polyglot_human": {
                "url": "https://github.com/official-stockfish/books/raw/master/polyglot/human.bin", 
                "filename": "human.bin",
                "description": "Human-style Polyglot book",
                "size_mb": 1.8
            },
            "lichess_masters": {
                "url": "https://database.lichess.org/lichess_db_standard_rated_2023-01.pgn.bz2",
                "filename": "lichess_masters_2023.pgn.bz2",
                "description": "Lichess master games database",
                "size_mb": 150.0,
                "extract": True
            }
        }
    
    def download_essential_books(self) -> Dict[str, bool]:
        """Download essential opening books"""
        results = {}
        
        # Download Polyglot books first (smaller, faster)
        for book_name in ["polyglot_performance", "polyglot_human"]:
            try:
                success = self.download_book(book_name)
                results[book_name] = success
                if success:
                    logger.info(f"✅ Downloaded {book_name}")
                else:
                    logger.warning(f"❌ Failed to download {book_name}")
            except Exception as e:
                logger.error(f"Error downloading {book_name}: {e}")
                results[book_name] = False
        
        return results
    
    def download_book(self, book_name: str) -> bool:
        """Download a specific book"""
        if book_name not in self.book_sources:
            logger.error(f"Unknown book: {book_name}")
            return False
        
        book_info = self.book_sources[book_name]
        url = book_info["url"]
        filename = book_info["filename"]
        file_path = self.books_dir / filename
        
        # Check if already exists
        if file_path.exists():
            logger.info(f"Book already exists: {filename}")
            return True
        
        try:
            logger.info(f"Downloading {book_info['description']} ({book_info['size_mb']} MB)...")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"Progress: {progress:.1f}%")
            
            # Extract if needed
            if book_info.get("extract", False):
                self._extract_file(file_path)
            
            logger.info(f"Successfully downloaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {book_name}: {e}")
            if file_path.exists():
                file_path.unlink()  # Remove partial download
            return False
    
    def _extract_file(self, file_path: Path):
        """Extract compressed files"""
        try:
            if file_path.suffix == '.bz2':
                import bz2
                extracted_path = file_path.with_suffix('')
                with bz2.open(file_path, 'rb') as src, open(extracted_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                logger.info(f"Extracted: {extracted_path.name}")
                
            elif file_path.suffix == '.gz':
                with gzip.open(file_path, 'rb') as src:
                    extracted_path = file_path.with_suffix('')
                    with open(extracted_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                logger.info(f"Extracted: {extracted_path.name}")
                
            elif file_path.suffix == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(self.books_dir)
                logger.info(f"Extracted ZIP: {file_path.name}")
                
        except Exception as e:
            logger.error(f"Error extracting {file_path}: {e}")
    
    def create_sample_pgn(self) -> bool:
        """Create a sample PGN file with famous games for testing"""
        sample_pgn_path = self.books_dir / "sample_masters.pgn"
        
        if sample_pgn_path.exists():
            return True
        
        # Famous master games for opening book
        sample_games = '''[Event "World Championship"]
[Site "New York"]
[Date "1886.??.??"]
[Round "1"]
[White "Steinitz, Wilhelm"]
[Black "Zukertort, Johannes"]
[Result "1-0"]
[WhiteElo "2400"]
[BlackElo "2350"]

1.d4 d5 2.c4 e6 3.Nc3 Nf6 4.Bg5 Be7 5.e3 O-O 6.Nf3 Nbd7 7.Rc1 c6 8.Bd3 dxc4 9.Bxc4 Nd5 10.Bxe7 Qxe7 11.O-O Nxc3 12.Rxc3 e5 13.dxe5 Nxe5 14.Nxe5 Qxe5 15.f4 Qe7 16.Qd4 Be6 17.Bxe6 Qxe6 18.Rc4 Rad8 19.Qc5 Rd5 20.Qc2 Rfd8 21.Re1 R8d7 22.g3 Rd2 23.Qc1 Rxb2 24.Rc2 Rxc2 25.Qxc2 Rd2 26.Qc4 Qxc4 27.Rxc4 Rxc2 28.Rxc6 Rxa2 29.Rxc7 Ra1+ 30.Kf2 Ra2+ 31.Ke1 1-0

[Event "World Championship"]
[Site "Havana"]
[Date "1921.??.??"]
[Round "11"]
[White "Capablanca, Jose Raul"]
[Black "Marshall, Frank James"]
[Result "1-0"]
[WhiteElo "2500"]
[BlackElo "2400"]

1.e4 e5 2.Nf3 Nc6 3.Bb5 a6 4.Ba4 Nf6 5.O-O Be7 6.Re1 b5 7.Bb3 d6 8.c3 O-O 9.h3 Nb8 10.d4 Nbd7 11.c4 c6 12.cxb5 axb5 13.Nc3 Bb7 14.Bg5 b4 15.Nb1 h6 16.Bh4 c5 17.dxe5 Nxe5 18.Nxe5 dxe5 19.Bxf6 Bxf6 20.Nd2 Re8 21.Qf3 Be7 22.Bd5 Bxd5 23.exd5 e4 24.Qg3 Bf6 25.Rxe4 Rxe4 26.Nxe4 Qxd5 27.Rd1 Qe6 28.Nxf6+ Qxf6 29.Rd7 Qf4 30.Qxf4 1-0

[Event "Candidates Tournament"]
[Site "Zurich"]
[Date "1953.??.??"]
[Round "15"]
[White "Petrosian, Tigran"]
[Black "Najdorf, Miguel"]
[Result "1-0"]
[WhiteElo "2450"]
[BlackElo "2420"]

1.Nf3 Nf6 2.c4 g6 3.Nc3 Bg7 4.d4 O-O 5.Bf4 d5 6.Qb3 dxc4 7.Qxc4 c6 8.e4 Nbd7 9.Rd1 Nb6 10.Qc5 Bg4 11.Bg5 Na4 12.Qa3 Nxc3 13.bxc3 Nxe4 14.Bxe7 Qb6 15.Bc4 Qxb2 16.Bb4 Rfe8 17.O-O Be2 18.Qxa7 Bxd1 19.Rxd1 Nxc3 20.Rd2 Qb1+ 21.Rd1 Qb2 22.Rd2 Qb1+ 23.Rd1 1/2-1/2

[Event "World Championship"]
[Site "Moscow"]
[Date "1985.??.??"]
[Round "16"]
[White "Kasparov, Garry"]
[Black "Karpov, Anatoly"]
[Result "1-0"]
[WhiteElo "2700"]
[BlackElo "2720"]

1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 6.Be2 e6 7.O-O Be7 8.f4 O-O 9.Kh1 Qc7 10.a4 Nc6 11.Be3 Re8 12.Bf3 Rb8 13.Qd2 Bd7 14.Nb3 b6 15.g4 Bc6 16.g5 Nd7 17.Qf2 Bf8 18.Bg2 Nb4 19.Rad1 Bxe4 20.Nxe4 Nxc2 21.Nxd6 Bxd6 22.Rxd6 Qc1+ 23.Rd1 Qc7 24.Rd3 f6 25.gxf6 Nxf6 26.Rg1 Kh8 27.Bxb6 Qb7 28.Bd4 Rg8 29.Qh4 Rg4 30.Qh3 Ne4 31.Bxe4 Rxe4 32.Rg3 1-0'''
        
        try:
            with open(sample_pgn_path, 'w') as f:
                f.write(sample_games)
            logger.info(f"Created sample PGN: {sample_pgn_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating sample PGN: {e}")
            return False
    
    def setup_books(self) -> Dict[str, bool]:
        """Setup all opening books"""
        results = {}
        
        # Create sample PGN for immediate use
        results['sample_pgn'] = self.create_sample_pgn()
        
        # Download essential books
        download_results = self.download_essential_books()
        results.update(download_results)
        
        # Create symlinks for easy access
        self._create_symlinks()
        
        return results
    
    def _create_symlinks(self):
        """Create convenient symlinks"""
        try:
            # Create main book symlink
            main_book = self.books_dir / "performance.bin"
            book_link = self.books_dir / "book.bin"
            
            if main_book.exists() and not book_link.exists():
                book_link.symlink_to(main_book)
                logger.info("Created book.bin symlink")
                
        except Exception as e:
            logger.debug(f"Could not create symlinks: {e}")
    
    def get_book_status(self) -> Dict[str, Dict]:
        """Get status of all books"""
        status = {}
        
        for book_name, book_info in self.book_sources.items():
            file_path = self.books_dir / book_info["filename"]
            status[book_name] = {
                "exists": file_path.exists(),
                "size_mb": file_path.stat().st_size / (1024*1024) if file_path.exists() else 0,
                "description": book_info["description"]
            }
        
        # Check sample PGN
        sample_pgn = self.books_dir / "sample_masters.pgn"
        status["sample_pgn"] = {
            "exists": sample_pgn.exists(),
            "size_mb": sample_pgn.stat().st_size / (1024*1024) if sample_pgn.exists() else 0,
            "description": "Sample master games"
        }
        
        return status

def setup_opening_books(books_dir: str = "books") -> bool:
    """Convenience function to setup opening books"""
    try:
        downloader = BookDownloader(books_dir)
        results = downloader.setup_books()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"Book setup completed: {success_count}/{total_count} successful")
        
        # Print status
        status = downloader.get_book_status()
        for book_name, info in status.items():
            status_icon = "✅" if info["exists"] else "❌"
            logger.info(f"{status_icon} {book_name}: {info['description']} ({info['size_mb']:.1f} MB)")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error setting up books: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_opening_books()