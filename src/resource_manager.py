# resource_manager.py - Comprehensive resource management system
from pygame import Surface, image, font, mixer, transform, SRCALPHA, get_init, init
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
        # Fast path: avoid lock if instance exists
        if cls._instance is not None:
            return cls._instance
            
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Fast path: avoid repeated initialization
        if getattr(self, '_initialized', False):
            return
            
        self.image_cache = {}
        self.font_cache = {}
        self.sound_cache = {}
        self.surface_cache = {}
        self._cleanup_registered = False
        
        # Initialize pygame if not already done
        if not get_init():
            init()
        if not font.get_init():
            font.init()
        
        # Register cleanup
        import atexit
        atexit.register(self.cleanup_all)
        
        self._initialized = True
    
    @lru_cache(maxsize=64)
    def get_piece_image(self, piece_name: str, color: str, size: int) -> Optional[Surface]:
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
                    img = image.load(path).convert_alpha()
                    if size != 80:  # Scale if needed
                        img = transform.smoothscale(img, (size, size))
                    self.image_cache[cache_key] = img
                    return img
                except Exception as e:
                    logger.warning("Failed to load image %s: %s", path.replace('\n', '').replace('\r', ''), str(e).replace('\n', '').replace('\r', ''))
        
        # Return None if no image found
        logger.warning("No image found for %s", cache_key.replace('\n', '').replace('\r', ''))
        return None
    
    @lru_cache(maxsize=32)
    def get_font(self, name: str, size: int, bold: bool = False) -> font.Font:
        """Get cached font"""
        cache_key = f"{name}_{size}_{bold}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        try:
            if name.lower() in ['segoe ui', 'arial', 'helvetica']:
                fnt = font.SysFont(name, size, bold=bold)
            else:
                fnt = font.Font(name, size)
            
            self.font_cache[cache_key] = fnt
            return fnt
        except Exception as e:
            logger.warning("Failed to load font %s: %s", name.replace('\n', '').replace('\r', ''), str(e).replace('\n', '').replace('\r', ''))
            # Fallback to default font
            fnt = font.Font(None, size)
            self.font_cache[cache_key] = fnt
            return fnt
    
    def get_sound(self, filename: str) -> Optional[mixer.Sound]:
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
                    sound = mixer.Sound(path)
                    self.sound_cache[filename] = sound
                    return sound
                except Exception as e:
                    logger.warning("Failed to load sound %s: %s", path.replace('\n', '').replace('\r', ''), str(e).replace('\n', '').replace('\r', ''))
        
        logger.warning("Sound file not found: %s", filename.replace('\n', '').replace('\r', ''))
        return None
    
    def create_surface(self, width: int, height: int, alpha: bool = False) -> Surface:
        """Create optimized surface"""
        if alpha:
            surface = Surface((width, height), SRCALPHA)
        else:
            surface = Surface((width, height))
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
            logger.error("Error cleaning up cache: %s", str(e).replace('\n', '').replace('\r', ''))
    
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