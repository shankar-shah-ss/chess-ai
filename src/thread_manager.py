# thread_manager.py - Comprehensive thread management system
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class ThreadManager:
    """Singleton thread manager for better resource management"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.active_threads = weakref.WeakSet()
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ChessAI")
        self.futures = []
        self._shutdown = False
        self._initialized = True
        
        # Register cleanup
        import atexit
        atexit.register(self.cleanup_all)
    
    def submit_task(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a task to the thread pool"""
        if self._shutdown:
            raise RuntimeError("ThreadManager is shutting down")
        
        try:
            future = self.thread_pool.submit(func, *args, **kwargs)
            self.futures.append(future)
            
            # Clean up completed futures
            self.futures = [f for f in self.futures if not f.done()]
            
            return future
        except RuntimeError as e:
            logger.error(f"Failed to submit task to thread pool: {e}")
            raise
    
    def create_thread(self, target: Callable, name: str = None, daemon: bool = True, *args, **kwargs) -> threading.Thread:
        """Create and register a managed thread"""
        if self._shutdown:
            raise RuntimeError("ThreadManager is shutting down")
        
        thread = threading.Thread(target=target, name=name, daemon=daemon, args=args, kwargs=kwargs)
        self.active_threads.add(thread)
        return thread
    
    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """Wait for all tasks to complete"""
        try:
            # Wait for thread pool tasks
            for future in self.futures:
                try:
                    future.result(timeout=timeout)
                except TimeoutError:
                    logger.warning(f"Task timed out after {timeout} seconds")
                except Exception as e:
                    logger.warning(f"Task failed: {e}")
            
            # Wait for individual threads
            for thread in list(self.active_threads):
                if thread.is_alive():
                    try:
                        thread.join(timeout=1.0)
                        if thread.is_alive():
                            logger.warning(f"Thread {thread.name} did not terminate gracefully")
                    except Exception as e:
                        logger.error(f"Error joining thread {thread.name}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error waiting for thread completion: {e}")
            return False
    
    def cancel_all_tasks(self):
        """Cancel all pending tasks"""
        cancelled_count = 0
        for future in self.futures:
            if future.cancel():
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} pending tasks")
        self.futures.clear()
    
    def get_active_thread_count(self) -> int:
        """Get count of active threads"""
        return len([t for t in self.active_threads if t.is_alive()])
    
    def get_pending_task_count(self) -> int:
        """Get count of pending tasks"""
        return len([f for f in self.futures if not f.done()])
    
    def cleanup_all(self):
        """Cleanup all threads and resources"""
        if self._shutdown:
            return
        
        self._shutdown = True
        logger.info("Starting thread manager cleanup...")
        
        # Cancel pending tasks
        self.cancel_all_tasks()
        
        # Shutdown thread pool
        try:
            self.thread_pool.shutdown(wait=True)
            logger.info("Thread pool shutdown completed")
        except Exception as e:
            logger.error(f"Error shutting down thread pool: {e}")
        
        # Log remaining active threads (Python threads cannot be forcibly terminated)
        self._log_remaining_threads()
        
        logger.info("Thread manager cleanup completed")
    
    def _log_remaining_threads(self):
        """Log any remaining active threads for debugging"""
        remaining_threads = [t for t in self.active_threads if t.is_alive()]
        if remaining_threads:
            logger.warning(f"Found {len(remaining_threads)} threads still active after cleanup")
            for thread in remaining_threads:
                logger.warning(f"Active thread: {thread.name} (daemon: {thread.daemon})")
        else:
            logger.info("All threads cleaned up successfully")
    
    def get_stats(self) -> dict:
        """Get thread manager statistics"""
        return {
            'active_threads': self.get_active_thread_count(),
            'pending_tasks': self.get_pending_task_count(),
            'total_futures': len(self.futures),
            'shutdown': self._shutdown
        }

# Enhanced worker classes with proper cleanup
class ManagedWorkerThread(threading.Thread):
    """Base class for managed worker threads"""
    
    def __init__(self, name: str, target: Callable = None, daemon: bool = True):
        super().__init__(name=name, daemon=daemon)
        self.target = target
        self._stop_event = threading.Event()
        self._result = None
        self._error = None
        
        # Register with thread manager
        ThreadManager().active_threads.add(self)
    
    def run(self):
        """Run the worker thread"""
        try:
            if self.target:
                self._result = self.target()
        except Exception as e:
            self._error = e
            logger.error(f"Worker thread {self.name} failed: {e}")
    
    def stop(self):
        """Signal the thread to stop"""
        self._stop_event.set()
    
    def is_stopped(self) -> bool:
        """Check if stop was requested"""
        return self._stop_event.is_set()
    
    def get_result(self):
        """Get the result (blocks until complete)"""
        self.join()
        if self._error:
            raise self._error
        return self._result

class EngineWorkerThread(ManagedWorkerThread):
    """Enhanced engine worker with proper cleanup"""
    
    def __init__(self, game, fen: str, move_queue, engine=None):
        super().__init__(name="EngineWorker", daemon=True)
        self.game = game
        self.fen = fen
        self.move_queue = move_queue
        self.engine = engine or game.engine
        self.move = None
    
    def run(self):
        """Run engine calculation"""
        try:
            if self._should_skip_calculation():
                return
            
            self._calculate_and_queue_move()
            
        except Exception as e:
            logger.error(f"Engine worker error: {e}")
            self._error = e
    
    def _should_skip_calculation(self):
        """Check if calculation should be skipped"""
        if self.is_stopped():
            return True
        
        if not self.engine or not self.engine._is_healthy:
            logger.warning("Engine not healthy, skipping move calculation")
            return True
        
        return False
    
    def _calculate_and_queue_move(self):
        """Calculate move and add to queue if valid"""
        if not self.engine.set_position(self.fen):
            return
        
        if self.is_stopped():
            return
        
        self.move = self.engine.get_best_move()
        if self.move and not self.is_stopped():
            self.move_queue.put(self.move)
            logger.info(f"Engine move calculated: {self.move}")

class EvaluationWorkerThread(ManagedWorkerThread):
    """Enhanced evaluation worker with proper cleanup"""
    
    def __init__(self, game, fen: str, engine=None):
        super().__init__(name="EvaluationWorker", daemon=True)
        self.game = game
        self.fen = fen
        self.engine = engine or game.engine
        self.evaluation = None
    
    def run(self):
        """Run position evaluation"""
        try:
            if self._should_skip_evaluation():
                return
            
            self._calculate_evaluation()
            
        except Exception as e:
            logger.error(f"Evaluation worker error: {e}")
            self._error = e
    
    def _should_skip_evaluation(self):
        """Check if evaluation should be skipped"""
        if self.is_stopped():
            return True
        
        if not self.engine or not self.engine._is_healthy:
            logger.warning("Engine not healthy, skipping evaluation")
            return True
        
        return False
    
    def _calculate_evaluation(self):
        """Calculate position evaluation"""
        if not self.engine.set_position(self.fen):
            return
        
        if self.is_stopped():
            return
        
        self.evaluation = self.engine.get_evaluation()
        logger.debug(f"Position evaluated: {self.evaluation}")

# Global thread manager instance
thread_manager = ThreadManager()