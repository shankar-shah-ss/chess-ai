#!/usr/bin/env python3
"""
Chess Analysis System - Live Demo
Shows the analysis system working in the actual game
"""

import sys
sys.path.append('src')
import pygame
import time
from main import Main

def demo_analysis_system():
    """Demonstrate the analysis system in action"""
    print("🎯 Chess Analysis System - Live Demo")
    print("=" * 60)
    print()
    print("🎮 CONTROLS:")
    print("   F5 - Toggle Analysis Panel")
    print("   F1 - Review Mode (load and navigate games)")
    print("   F2 - Engine Analysis Mode (real-time evaluation)")
    print("   F3 - Move Classification Mode (move quality)")
    print("   F4 - Interactive Exploration Mode (custom positions)")
    print("   Arrow Keys - Navigate moves in review mode")
    print("   ESC - Exit demo")
    print()
    print("📁 SAMPLE GAMES CREATED:")
    print("   • Immortal Game (Anderssen vs Kieseritzky, 1851)")
    print("   • Evergreen Game (Anderssen vs Dufresne, 1852)")
    print("   • Opera Game (Morphy vs Duke/Count, 1858)")
    print()
    print("🚀 Starting Chess Game with Analysis System...")
    print("   Press F5 to open the analysis panel!")
    print()
    
    # Start the main game
    try:
        main = Main()
        main.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Demo ended by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_analysis_system()