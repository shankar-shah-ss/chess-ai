#!/usr/bin/env python3
"""
Chess AI Launcher - Shows all available features
"""
import os
import sys

def main():
    print("🏁 Starting Chess AI with Advanced Features")
    print("=" * 50)
    print()
    print("🎮 GAME MODES:")
    print("  1 - Human vs Human")
    print("  2 - Human vs Engine") 
    print("  3 - Engine vs Engine")
    print()
    print("🤖 ENGINE CONTROLS:")
    print("  +/- - Increase/Decrease engine level (0-20)")
    print("  Ctrl+↑/↓ - Increase/Decrease engine depth (1-20)")
    print("  W - Toggle white engine")
    print("  B - Toggle black engine")
    print()
    print("🎨 GAME CONTROLS:")
    print("  T - Change theme")
    print("  R - Reset game")
    print("  I - Toggle info panel")
    print("  H - Show/hide help")
    print("  F11 - Toggle fullscreen")
    print()
    print("📊 ANALYSIS FEATURES:")
    print("  A - Enter analysis mode (after game)")
    print("  S - Show game summary")
    print("  ←/→ - Navigate moves")
    print("  Space - Auto-play moves")
    print()
    print("🚀 Starting game...")
    print("=" * 50)
    
    # Change to src directory and run
    os.chdir('src')
    os.system('python3 main.py')

if __name__ == '__main__':
    main()