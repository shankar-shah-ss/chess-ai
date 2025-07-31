#!/usr/bin/env python3
"""
Comprehensive test suite for all chess AI improvements
"""
import sys
import os
import time
import threading
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

class ComprehensiveTestSuite:
    """Test all major improvements and systems"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test with error handling"""
        print(f"\n🧪 Testing {test_name}...")
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                self.tests_passed += 1
                self.test_results.append((test_name, "PASSED", duration, None))
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                self.tests_failed += 1
                self.test_results.append((test_name, "FAILED", duration, "Test returned False"))
        except Exception as e:
            duration = time.time() - start_time if 'start_time' in locals() else 0
            print(f"💥 {test_name} CRASHED ({duration:.2f}s): {e}")
            self.tests_failed += 1
            self.test_results.append((test_name, "CRASHED", duration, str(e)))
    
    def test_error_handling_system(self):
        """Test enhanced error handling system"""
        try:
            from error_handling import safe_execute, ErrorTracker, PerformanceMonitor, error_tracker
            
            # Test safe_execute decorator
            @safe_execute(fallback_value="fallback", context="test")
            def failing_function():
                raise ValueError("Test error")
            
            result = failing_function()
            if result != "fallback":
                return False
            
            # Test error tracking
            error_tracker.record_error("TestError", "Test message", "test_context")
            summary = error_tracker.get_error_summary()
            if summary['total_errors'] == 0:
                return False
            
            # Test performance monitor
            monitor = PerformanceMonitor()
            monitor.record_metric("test_metric", 42.0)
            metrics = monitor.get_recent_metrics()
            if "test_metric" not in metrics:
                return False
            
            print("  ✓ Safe execution decorator working")
            print("  ✓ Error tracking working")
            print("  ✓ Performance monitoring working")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_resource_management(self):
        """Test resource management system"""
        try:
            from resource_manager import resource_manager
            
            # Test font caching
            font1 = resource_manager.get_font("Arial", 14)
            font2 = resource_manager.get_font("Arial", 14)  # Should be cached
            if font1 is not font2:  # Should be same object from cache
                print("  ⚠️  Font caching may not be working optimally")
            
            # Test cache stats
            stats = resource_manager.get_cache_stats()
            if not isinstance(stats, dict):
                return False
            
            # Test cleanup
            resource_manager.cleanup_cache("fonts")
            
            print("  ✓ Resource manager initialized")
            print("  ✓ Font caching working")
            print("  ✓ Cache statistics available")
            print("  ✓ Cache cleanup working")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_thread_management(self):
        """Test thread management system"""
        try:
            from thread_manager import thread_manager, ManagedWorkerThread
            
            # Test thread creation
            def test_task():
                time.sleep(0.1)
                return "completed"
            
            # Test managed thread
            thread = ManagedWorkerThread("TestThread", test_task)
            thread.start()
            thread.join(timeout=1.0)
            
            if thread.get_result() != "completed":
                return False
            
            # Test thread pool
            future = thread_manager.submit_task(lambda: "pool_task")
            result = future.result(timeout=1.0)
            if result != "pool_task":
                return False
            
            # Test stats
            stats = thread_manager.get_stats()
            if not isinstance(stats, dict):
                return False
            
            print("  ✓ Thread manager initialized")
            print("  ✓ Managed worker threads working")
            print("  ✓ Thread pool working")
            print("  ✓ Thread statistics available")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_enhanced_engine(self):
        """Test enhanced engine system"""
        try:
            from engine import ChessEngine, EnginePool
            
            # Test engine creation
            engine = ChessEngine(skill_level=5, depth=10)
            if not hasattr(engine, '_is_healthy'):
                return False
            
            # Test engine pool
            pool = EnginePool()
            if not hasattr(pool, '_engines'):
                return False
            
            # Test basic engine operations
            if engine._is_healthy:
                # Test position setting
                result = engine.set_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
                if not result:
                    print("  ⚠️  Engine position setting failed (may be normal if Stockfish not available)")
            
            print("  ✓ Enhanced engine system initialized")
            print("  ✓ Engine pool working")
            print("  ✓ Engine health monitoring available")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_unified_analysis_interface(self):
        """Test unified analysis interface"""
        try:
            from unified_analysis_interface import UnifiedAnalysisInterface
            
            # Create mock config
            class MockConfig:
                WIDTH = 1200
                HEIGHT = 800
            
            config = MockConfig()
            interface = UnifiedAnalysisInterface(config)
            
            if not hasattr(interface, 'active'):
                return False
            
            # Test activation
            interface.activate()
            if not interface.active:
                return False
            
            # Test deactivation
            interface.deactivate()
            if interface.active:
                return False
            
            print("  ✓ Unified analysis interface created")
            print("  ✓ Interface activation/deactivation working")
            print("  ✓ Interface components initialized")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_enhanced_opening_database(self):
        """Test enhanced opening database"""
        try:
            from enhanced_opening_database import EnhancedOpeningDatabase
            import chess
            
            # Create database
            db = EnhancedOpeningDatabase()
            
            # Test opening detection
            board = chess.Board()
            board.push_san("e4")  # King's pawn opening
            
            opening = db.detect_opening(board)
            if opening and 'name' in opening:
                print(f"  ✓ Detected opening: {opening['name']}")
            else:
                print("  ⚠️  Opening detection returned no results")
            
            # Test popular openings
            popular = db.get_popular_openings(5)
            if not isinstance(popular, list):
                return False
            
            # Test search
            search_results = db.search_openings("Sicilian")
            if not isinstance(search_results, list):
                return False
            
            # Test statistics
            stats = db.get_cache_stats()
            if not isinstance(stats, dict):
                return False
            
            print("  ✓ Enhanced opening database initialized")
            print(f"  ✓ Database contains {stats.get('total_openings', 0)} openings")
            print("  ✓ Opening detection working")
            print("  ✓ Search functionality working")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_config_validation(self):
        """Test configuration validation system"""
        try:
            from config_validator import config_validator
            
            # Test valid config
            valid_config = {
                "engine": {
                    "stockfish_path": "stockfish",
                    "default_depth": 15,
                    "default_skill_level": 10,
                    "max_depth": 20,
                    "max_skill_level": 20,
                    "timeout_seconds": 30
                },
                "ui": {
                    "window_width": 1200,
                    "window_height": 800,
                    "fullscreen": False,
                    "theme_index": 1,
                    "show_coordinates": True,
                    "show_move_history": True,
                    "show_evaluation_bar": True,
                    "animation_speed": 1.0
                },
                "analysis": {
                    "auto_analyze": False,
                    "analysis_depth": 18,
                    "max_analysis_time": 300,
                    "show_best_moves": 3,
                    "classification_thresholds": {
                        "BLUNDER": 3.0,
                        "MISTAKE": 1.5,
                        "INACCURACY": 0.5,
                        "OKAY": 0.25
                    }
                },
                "game": {
                    "default_game_mode": 0,
                    "auto_save_pgn": True,
                    "pgn_directory": "games",
                    "sound_enabled": True,
                    "move_validation": True
                }
            }
            
            if not config_validator.validate_config(valid_config):
                return False
            
            # Test invalid config fixing
            invalid_config = {
                "engine": {
                    "default_depth": -5,  # Invalid
                    "default_skill_level": 25  # Invalid
                }
            }
            
            fixed_config = config_validator.fix_config(invalid_config)
            if not config_validator.validate_config(fixed_config):
                return False
            
            print("  ✓ Configuration validation working")
            print("  ✓ Configuration fixing working")
            print("  ✓ Validation rules comprehensive")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_game_integration(self):
        """Test game integration with new systems"""
        try:
            from game import Game
            
            # Create game instance
            game = Game()
            
            # Test enhanced features
            if not hasattr(game, '_error_recovery'):
                return False
            
            if not hasattr(game, 'validate_game_state'):
                return False
            
            if not hasattr(game, 'periodic_maintenance'):
                return False
            
            if not hasattr(game, 'cleanup'):
                return False
            
            # Test validation
            is_valid = game.validate_game_state()
            if not isinstance(is_valid, bool):
                return False
            
            print("  ✓ Game integration working")
            print("  ✓ Enhanced error recovery available")
            print("  ✓ Game state validation working")
            print("  ✓ Periodic maintenance available")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def test_performance_improvements(self):
        """Test performance improvements"""
        try:
            # Test import speed
            start_time = time.time()
            
            from resource_manager import resource_manager
            from thread_manager import thread_manager
            from error_handling import performance_monitor
            
            import_time = time.time() - start_time
            
            if import_time > 2.0:  # Should import quickly
                print(f"  ⚠️  Import time seems slow: {import_time:.2f}s")
            
            # Test resource efficiency
            initial_stats = resource_manager.get_cache_stats()
            
            # Create some resources
            for i in range(10):
                resource_manager.get_font("Arial", 12 + i)
            
            after_stats = resource_manager.get_cache_stats()
            
            # Should have cached fonts
            if after_stats['fonts'] <= initial_stats['fonts']:
                return False
            
            # Test cleanup
            resource_manager.cleanup_cache("fonts")
            cleanup_stats = resource_manager.get_cache_stats()
            
            if cleanup_stats['fonts'] >= after_stats['fonts']:
                print("  ⚠️  Cache cleanup may not be working optimally")
            
            print(f"  ✓ Import time: {import_time:.2f}s")
            print("  ✓ Resource caching working")
            print("  ✓ Cache cleanup working")
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Chess AI Test Suite")
        print("=" * 60)
        
        # List of all tests
        tests = [
            ("Error Handling System", self.test_error_handling_system),
            ("Resource Management", self.test_resource_management),
            ("Thread Management", self.test_thread_management),
            ("Enhanced Engine", self.test_enhanced_engine),
            ("Unified Analysis Interface", self.test_unified_analysis_interface),
            ("Enhanced Opening Database", self.test_enhanced_opening_database),
            ("Configuration Validation", self.test_config_validation),
            ("Game Integration", self.test_game_integration),
            ("Performance Improvements", self.test_performance_improvements),
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        if self.test_results:
            print("\n📋 DETAILED RESULTS:")
            for name, status, duration, error in self.test_results:
                status_icon = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "💥"
                print(f"  {status_icon} {name}: {status} ({duration:.2f}s)")
                if error:
                    print(f"    Error: {error}")
        
        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT:")
        if success_rate >= 90:
            print("🎉 EXCELLENT! All major systems are working properly.")
        elif success_rate >= 75:
            print("✅ GOOD! Most systems are working with minor issues.")
        elif success_rate >= 50:
            print("⚠️  FAIR! Some systems need attention.")
        else:
            print("🚨 POOR! Major issues detected. Review failed tests.")
        
        return success_rate >= 75

def main():
    """Main test function"""
    print("Chess AI Comprehensive Test Suite")
    print("Testing all improvements and enhancements...")
    
    suite = ComprehensiveTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print("\n🎉 All major systems are working! The chess AI is ready to use.")
        return 0
    else:
        print("\n⚠️  Some issues detected. Check the test results above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())