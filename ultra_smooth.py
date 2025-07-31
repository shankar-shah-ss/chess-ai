#!/usr/bin/env python3
"""
Ultra-smooth chess game launcher with maximum performance optimizations
"""
import os
import sys

def optimize_system():
    """Apply system-level optimizations"""
    print("🚀 Applying ultra-smooth optimizations...")
    
    # Set environment variables for maximum performance
    os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '0'
    os.environ['SDL_VIDEODRIVER'] = 'metal'  # Use Metal on macOS for best performance
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    
    print("✓ System optimizations applied")

def main():
    print("⚡ ULTRA-SMOOTH CHESS AI")
    print("=" * 30)
    print("🎯 Target: Buttery smooth 120 FPS")
    print("🚫 Zero lag, zero unresponsiveness")
    print()
    
    optimize_system()
    
    # Change to src directory and run with optimizations
    os.chdir('src')
    
    print("🎮 Launching ultra-smooth chess...")
    print("=" * 30)
    
    # Import and run with all optimizations
    import pygame
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
    pygame.init()
    
    from main import Main
    main = Main()
    main.mainloop()

if __name__ == '__main__':
    main()