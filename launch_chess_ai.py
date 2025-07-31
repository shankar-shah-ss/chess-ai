#!/usr/bin/env python3
"""
Enhanced Chess AI Launcher
Comprehensive launcher with system checks and optimizations
"""
import sys
import os
import time
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

class ChessAILauncher:
    """Enhanced launcher for Chess AI with comprehensive system checks"""
    
    def __init__(self):
        self.startup_time = time.time()
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        
    def print_banner(self):
        """Print startup banner"""
        print("=" * 60)
        print("🏁 ENHANCED CHESS AI - COMPREHENSIVE EDITION")
        print("=" * 60)
        print("🚀 Starting system checks and initialization...")
        print()
    
    def check_python_version(self):
        """Check Python version compatibility"""
        print("🐍 Checking Python version...")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"❌ Python {version.major}.{version.minor} is too old. Requires Python 3.8+")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    
    def check_dependencies(self):
        """Check required dependencies"""
        print("📦 Checking dependencies...")
        
        required_modules = [
            ('pygame', 'pygame'),
            ('chess', 'python-chess'),
            ('sqlite3', 'sqlite3 (built-in)'),
            ('json', 'json (built-in)'),
            ('threading', 'threading (built-in)'),
            ('pathlib', 'pathlib (built-in)')
        ]
        
        missing = []
        for module, package in required_modules:
            try:
                __import__(module)
                print(f"  ✅ {module}")
            except ImportError:
                print(f"  ❌ {module} - Install with: pip install {package}")
                missing.append(package)
        
        if missing:
            print(f"\n🚨 Missing dependencies: {', '.join(missing)}")
            print("Run: pip install pygame python-chess")
            return False
        
        return True
    
    def check_system_resources(self):
        """Check system resources"""
        print("💻 Checking system resources...")
        
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb < 0.5:
                self.warnings.append(f"Low memory: {available_gb:.1f}GB available")
                print(f"  ⚠️  Memory: {available_gb:.1f}GB available (low)")
            else:
                print(f"  ✅ Memory: {available_gb:.1f}GB available")
            
            # CPU check
            cpu_count = psutil.cpu_count()
            print(f"  ✅ CPU cores: {cpu_count}")
            
        except ImportError:
            print("  ⚠️  psutil not available - skipping detailed resource check")
            self.warnings.append("Install psutil for detailed system monitoring")
        
        return True
    
    def check_stockfish(self):
        """Check Stockfish engine availability"""
        print("♟️  Checking Stockfish engine...")
        
        # Try to import and test engine
        try:
            from engine import ChessEngine
            
            # Test engine creation
            engine = ChessEngine(skill_level=1, depth=1)
            
            if engine._is_healthy:
                print("  ✅ Stockfish engine available and healthy")
                engine.cleanup()
                return True
            else:
                print("  ⚠️  Stockfish engine not responding properly")
                self.warnings.append("Stockfish may not be properly installed")
                return True  # Don't fail, game can run without engine
                
        except Exception as e:
            print(f"  ⚠️  Engine check failed: {e}")
            self.warnings.append("Engine functionality may be limited")
            return True  # Don't fail completely
    
    def initialize_systems(self):
        """Initialize all game systems"""
        print("🔧 Initializing game systems...")
        
        try:
            # Initialize pygame
            import pygame
            pygame.init()
            print("  ✅ Pygame initialized")
            
            # Initialize resource manager
            from resource_manager import resource_manager
            print("  ✅ Resource manager initialized")
            
            # Initialize thread manager
            from thread_manager import thread_manager
            print("  ✅ Thread manager initialized")
            
            # Initialize error handling
            from error_handling import logger
            logger.info("Chess AI launcher started")
            print("  ✅ Error handling system initialized")
            
            # Initialize configuration
            from config_manager import config_manager
            print("  ✅ Configuration manager initialized")
            
            # Initialize opening database
            from enhanced_opening_database import enhanced_opening_db
            stats = enhanced_opening_db.get_cache_stats()
            print(f"  ✅ Opening database initialized ({stats['total_openings']} openings)")
            
            return True
            
        except Exception as e:
            print(f"  ❌ System initialization failed: {e}")
            traceback.print_exc()
            return False
    
    def run_quick_test(self):
        """Run quick functionality test"""
        print("🧪 Running quick functionality test...")
        
        try:
            # Test game creation
            from game import Game
            game = Game()
            
            # Test basic validation
            if game.validate_game_state():
                print("  ✅ Game state validation working")
            else:
                print("  ⚠️  Game state validation issues")
                self.warnings.append("Game state validation may have issues")
            
            # Cleanup
            game.cleanup()
            print("  ✅ Game cleanup working")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Quick test failed: {e}")
            return False
    
    def optimize_performance(self):
        """Apply performance optimizations"""
        print("⚡ Applying performance optimizations...")
        
        try:
            # Set thread priorities if possible
            import threading
            current_thread = threading.current_thread()
            print(f"  ✅ Main thread: {current_thread.name}")
            
            # Optimize pygame
            import pygame
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            print("  ✅ Audio optimizations applied")
            
            # Set environment variables for better performance
            os.environ['SDL_VIDEO_CENTERED'] = '1'
            print("  ✅ Display optimizations applied")
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  Performance optimization warning: {e}")
            return True  # Don't fail on optimization issues
    
    def launch_game(self):
        """Launch the main game"""
        print("🎮 Launching Chess AI...")
        print()
        
        try:
            from main import Main
            
            # Create and run main game
            main = Main()
            
            # Show final startup info
            startup_duration = time.time() - self.startup_time
            print(f"🚀 Chess AI started successfully in {startup_duration:.2f} seconds!")
            
            if self.warnings:
                print("\n⚠️  Warnings:")
                for warning in self.warnings:
                    print(f"  • {warning}")
            
            print("\n🎯 Game Controls:")
            print("  • H - Show help")
            print("  • 1/2/3 - Switch game modes")
            print("  • T - Change theme")
            print("  • R - Reset game")
            print("  • A - Analysis mode (after game)")
            print("  • F11 - Toggle fullscreen")
            print("  • ESC - Exit")
            print()
            print("🎉 Enjoy your enhanced chess experience!")
            print("=" * 60)
            
            # Start main game loop
            main.mainloop()
            
        except KeyboardInterrupt:
            print("\n👋 Chess AI interrupted by user")
            self.cleanup_and_exit()
        except Exception as e:
            print(f"\n💥 Fatal error launching game: {e}")
            traceback.print_exc()
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Cleanup and exit gracefully"""
        print("\n🧹 Cleaning up resources...")
        
        try:
            # Cleanup resource manager
            from resource_manager import resource_manager
            resource_manager.cleanup_all()
            
            # Cleanup thread manager
            from thread_manager import thread_manager
            thread_manager.cleanup_all()
            
            # Cleanup engine pool
            from engine import EnginePool
            EnginePool().cleanup_all()
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        print("👋 Goodbye!")
        sys.exit(0)
    
    def run_all_checks(self):
        """Run all system checks"""
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("System Resources", self.check_system_resources),
            ("Stockfish Engine", self.check_stockfish),
            ("System Initialization", self.initialize_systems),
            ("Quick Test", self.run_quick_test),
            ("Performance Optimization", self.optimize_performance),
        ]
        
        for check_name, check_func in checks:
            try:
                if check_func():
                    self.checks_passed += 1
                else:
                    self.checks_failed += 1
                    if check_name in ["Python Version", "Dependencies", "System Initialization"]:
                        print(f"\n🚨 Critical check failed: {check_name}")
                        print("Cannot continue. Please fix the issues above.")
                        return False
            except Exception as e:
                print(f"💥 Check '{check_name}' crashed: {e}")
                self.checks_failed += 1
        
        # Summary
        total_checks = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n📊 System Check Summary:")
        print(f"  ✅ Passed: {self.checks_passed}")
        print(f"  ❌ Failed: {self.checks_failed}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 85:
            print("🎉 System ready for optimal chess experience!")
            return True
        elif success_rate >= 70:
            print("✅ System ready with minor issues")
            return True
        else:
            print("🚨 Too many issues detected. Please review and fix.")
            return False
    
    def run(self):
        """Main launcher entry point"""
        self.print_banner()
        
        if self.run_all_checks():
            self.launch_game()
        else:
            print("\n❌ Launch aborted due to critical issues")
            sys.exit(1)

def main():
    """Main entry point"""
    try:
        launcher = ChessAILauncher()
        launcher.run()
    except KeyboardInterrupt:
        print("\n👋 Launch interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Launcher crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()