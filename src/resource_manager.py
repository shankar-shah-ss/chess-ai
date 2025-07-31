# resource_manager.py - Comprehensive resource management system
import pygame
import threading
import weakref
import os
from functools import lru_cache
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ResourceManager:
    """Singleton resource manager for images, fonts, and sounds"""
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
            
        self.image_cache = {}
        self.font_cache = {}
        self.sound_cache = {}
        self.surface_cache = {}
        self._cleanup_registered = False
        self._initialized = True
        
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Register cleanup
        import atexit
        atexit.register(self.cleanup_all)
    
    @lru_cache(maxsize=64)
    def get_piece_image(self, piece_name: str, color: str, size: int) -> Optional[pygame.Surface]:
        """Get cached piece image"""
        cache_key = f"{piece_name}_{color}_{size}"
        
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        # Try to load image
        image_paths = [
            f"../assets/images/imgs-{size}px/{color}_{piece_name}.png",
            f"assets/images/imgs-{size}px/{color}_{piece_name}.png",
            f"../assets/images/imgs-80px/{color}_{piece_name}.png",
            f"assets/images/imgs-80px/{color}_{piece_name}.png"
        ]
        
        for path in image_paths:
            if os.path.exists(path):
                try:
                    image = pygame.image.load(path).convert_alpha()
                    if size != 80:  # Scale if needed
                        image = pygame.transform.smoothscale(image, (size, size))
                    self.image_cache[cache_key] = image
                    return image
                except Exception as e:
                    logger.warning(f"Failed to load image {path}: {e}")
        
        # Return None if no image found
        logger.warning(f"No image found for {cache_key}")
        return None
    
    @lru_cache(maxsize=32)
    def get_font(self, name: str, size: int, bold: bool = False) -> pygame.font.Font:
        """Get cached font"""
        cache_key = f"{name}_{size}_{bold}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        try:
            if name.lower() in ['segoe ui', 'arial', 'helvetica']:
                font = pygame.font.SysFont(name, size, bold=bold)
            else:
                font = pygame.font.Font(name, size)
            
            self.font_cache[cache_key] = font
            return font
        except Exception as e:
            logger.warning(f"Failed to load font {name}: {e}")
            # Fallback to default font
            font = pygame.font.Font(None, size)
            self.font_cache[cache_key] = font
            return font
    
    def get_sound(self, filename: str) -> Optional[pygame.mixer.Sound]:
        """Get cached sound"""
        if filename in self.sound_cache:
            return self.sound_cache[filename]
        
        sound_paths = [
            f"../assets/sounds/{filename}",
            f"assets/sounds/{filename}"
        ]
        
        for path in sound_paths:
            if os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    self.sound_cache[filename] = sound
                    return sound
                except Exception as e:
                    logger.warning(f"Failed to load sound {path}: {e}")
        
        logger.warning(f"Sound file not found: {filename}")
        return None
    
    def create_surface(self, width: int, height: int, alpha: bool = False) -> pygame.Surface:
        """Create optimized surface"""
        if alpha:
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
        else:
            surface = pygame.Surface((width, height))
            surface = surface.convert()
        return surface
    
    def cleanup_cache(self, cache_type: str = "all"):
        """Clean up specific cache or all caches"""
        try:
            if cache_type in ["all", "images"]:
                for surface in self.image_cache.values():
                    if surface:
                        del surface
                self.image_cache.clear()
                logger.info("Image cache cleared")
            
            if cache_type in ["all", "fonts"]:
                self.font_cache.clear()
                logger.info("Font cache cleared")
            
            if cache_type in ["all", "sounds"]:
                self.sound_cache.clear()
                logger.info("Sound cache cleared")
            
            if cache_type in ["all", "surfaces"]:
                for surface in self.surface_cache.values():
                    if surface:
                        del surface
                self.surface_cache.clear()
                logger.info("Surface cache cleared")
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def cleanup_all(self):
        """Cleanup all resources"""
        self.cleanup_cache("all")
        logger.info("All resources cleaned up")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'images': len(self.image_cache),
            'fonts': len(self.font_cache),
            'sounds': len(self.sound_cache),
            'surfaces': len(self.surface_cache)
        }

# Global resource manager instance
resource_manager = ResourceManager()