#!/usr/bin/env python3
"""
Interactive timeout configurator for chess engine
"""

import sys
import os
import json
from typing import Dict, List, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def load_current_config() -> Dict:
    """Load current configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'chess_ai_config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_default_config()

def create_default_config() -> Dict:
    """Create default configuration"""
    return {
        "engine": {
            "stockfish_path": "stockfish",
            "default_depth": 15,
            "default_skill_level": 10,
            "max_depth": 20,
            "max_skill_level": 20,
            "timeout_seconds": 30,
            "custom_timeouts": {
                "beginner": {"skill_range": [1, 5], "depth_range": [5, 10], "timeout_ms": 1500},
                "intermediate": {"skill_range": [6, 12], "depth_range": [8, 15], "timeout_ms": 2500},
                "advanced": {"skill_range": [13, 17], "depth_range": [12, 18], "timeout_ms": 3500},
                "expert": {"skill_range": [18, 19], "depth_range": [15, 20], "timeout_ms": 4500},
                "maximum": {"skill_range": [20, 20], "depth_range": [18, 20], "timeout_ms": 6000}
            }
        }
    }

def save_config(config: Dict):
    """Save configuration to file"""
    config_path = os.path.join(os.path.dirname(__file__), 'src', 'chess_ai_config.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return False

def display_current_timeouts():
    """Display current timeout configuration"""
    print("🕐 Current Engine Timeout Configuration")
    print("=" * 50)
    
    # Show hardcoded timeouts from engine.py
    print("📋 Hardcoded Timeouts (from engine.py):")
    timeouts = [
        ("Skill ≥20 & Depth ≥20", "5000ms (5.0s)", "Maximum strength"),
        ("Skill ≥18 OR Depth ≥18", "4000ms (4.0s)", "Very high strength"),
        ("Skill ≥15 OR Depth ≥15", "3000ms (3.0s)", "High strength"),
        ("Others", "2000ms (2.0s)", "Normal play")
    ]
    
    for condition, timeout, description in timeouts:
        print(f"   • {condition:<25} → {timeout:<12} ({description})")
    
    print()
    
    # Show fallback timeouts
    print("🔄 Fallback Timeouts (when primary fails):")
    fallbacks = [
        ("Depth 8", "3000ms (3.0s)"),
        ("Depth 6", "2000ms (2.0s)"),
        ("Depth 4", "1000ms (1.0s)"),
        ("Depth 2", "500ms (0.5s)")
    ]
    
    for depth, timeout in fallbacks:
        print(f"   • {depth:<10} → {timeout}")
    
    print()

def show_timeout_matrix():
    """Show detailed timeout matrix"""
    print("📊 Detailed Timeout Matrix")
    print("=" * 35)
    
    skill_levels = list(range(1, 21))
    depths = [5, 8, 10, 12, 15, 18, 20]
    
    def get_timeout(skill: int, depth: int) -> int:
        if skill >= 20 and depth >= 20:
            return 5000
        elif skill >= 18 or depth >= 18:
            return 4000
        elif skill >= 15 or depth >= 15:
            return 3000
        else:
            return 2000
    
    # Show matrix for key skill levels
    key_skills = [1, 5, 10, 15, 18, 20]
    
    print(f"{'Skill':<6}", end="")
    for depth in depths:
        print(f"D{depth:>2}", end="  ")
    print()
    print("-" * 45)
    
    for skill in key_skills:
        print(f"{skill:<6}", end="")
        for depth in depths:
            timeout = get_timeout(skill, depth)
            color = ""
            if timeout == 2000:
                color = "🟢"  # Fast
            elif timeout == 3000:
                color = "🟡"  # Medium
            elif timeout == 4000:
                color = "🟠"  # Slow
            elif timeout >= 5000:
                color = "🔴"  # Maximum
            
            print(f"{color}{timeout//1000}", end="   ")
        print()
    
    print()
    print("Legend: 🟢=2s 🟡=3s 🟠=4s 🔴=5s")
    print()

def analyze_performance_impact():
    """Analyze performance impact of different timeouts"""
    print("⚡ Performance Impact Analysis")
    print("=" * 35)
    
    scenarios = [
        ("Blitz Game (1+0)", "Need <1s per move", "Use Depth 6-8, any skill"),
        ("Rapid Game (10+0)", "Need 1-2s per move", "Use Depth 10-12, Skill 10-15"),
        ("Classical Game (90+30)", "Can use 3-5s per move", "Use Depth 15-20, Skill 18-20"),
        ("Analysis Mode", "No time pressure", "Use maximum settings"),
        ("Mobile/Weak CPU", "Need fast response", "Use Depth 5-8, lower timeouts"),
        ("Server/Strong CPU", "Can handle longer", "Use maximum settings")
    ]
    
    for scenario, requirement, recommendation in scenarios:
        print(f"🎯 {scenario}")
        print(f"   Requirement: {requirement}")
        print(f"   Recommendation: {recommendation}")
        print()

def create_custom_timeout_profiles():
    """Create custom timeout profiles"""
    print("🎨 Custom Timeout Profiles")
    print("=" * 30)
    
    profiles = {
        "lightning": {
            "name": "Lightning Fast",
            "description": "For blitz games and quick play",
            "timeouts": {
                "all_levels": 800  # 0.8 seconds
            },
            "fallbacks": [(4, 500), (2, 300)]
        },
        "balanced": {
            "name": "Balanced Play",
            "description": "Good balance of speed and strength",
            "timeouts": {
                "beginner": 1500,    # 1.5s
                "intermediate": 2000, # 2.0s
                "advanced": 2500,    # 2.5s
                "expert": 3000       # 3.0s
            },
            "fallbacks": [(6, 1500), (4, 800), (2, 400)]
        },
        "tournament": {
            "name": "Tournament Strength",
            "description": "Maximum strength for serious games",
            "timeouts": {
                "beginner": 3000,    # 3.0s
                "intermediate": 4000, # 4.0s
                "advanced": 5000,    # 5.0s
                "expert": 7000       # 7.0s
            },
            "fallbacks": [(10, 3000), (8, 2000), (6, 1000), (4, 500)]
        },
        "analysis": {
            "name": "Deep Analysis",
            "description": "For position analysis and study",
            "timeouts": {
                "all_levels": 10000  # 10 seconds
            },
            "fallbacks": [(15, 8000), (12, 5000), (10, 3000), (8, 2000)]
        }
    }
    
    for profile_id, profile in profiles.items():
        print(f"🔧 {profile['name']}")
        print(f"   Purpose: {profile['description']}")
        
        if 'all_levels' in profile['timeouts']:
            timeout = profile['timeouts']['all_levels']
            print(f"   Timeout: {timeout}ms ({timeout/1000:.1f}s) for all levels")
        else:
            print(f"   Timeouts:")
            for level, timeout in profile['timeouts'].items():
                print(f"     • {level.capitalize()}: {timeout}ms ({timeout/1000:.1f}s)")
        
        print(f"   Fallbacks: {profile['fallbacks']}")
        print()

def generate_timeout_modification_code():
    """Generate code to modify timeouts"""
    print("💻 How to Modify Engine Timeouts")
    print("=" * 35)
    
    print("📝 Method 1: Modify engine.py directly")
    print("-" * 25)
    print("""
In src/engine.py, find the get_best_move() method around line 362:

# Current code:
if time_limit is None:
    if self.skill_level >= 20 and self.depth >= 20:
        time_limit = 5000   # 5 seconds
    elif self.skill_level >= 18 or self.depth >= 18:
        time_limit = 4000   # 4 seconds
    elif self.skill_level >= 15 or self.depth >= 15:
        time_limit = 3000   # 3 seconds
    else:
        time_limit = 2000   # 2 seconds

# Modify these values to your preference:
# - Increase for stronger play (slower)
# - Decrease for faster play (weaker)
""")
    
    print("📝 Method 2: Add custom timeout method")
    print("-" * 25)
    print("""
Add this method to ChessEngine class:

def get_custom_timeout(self, profile='balanced'):
    profiles = {
        'fast': {
            'max': 1500, 'high': 1200, 'medium': 1000, 'low': 800
        },
        'balanced': {
            'max': 3000, 'high': 2500, 'medium': 2000, 'low': 1500
        },
        'strong': {
            'max': 6000, 'high': 5000, 'medium': 4000, 'low': 3000
        }
    }
    
    config = profiles.get(profile, profiles['balanced'])
    
    if self.skill_level >= 20 and self.depth >= 20:
        return config['max']
    elif self.skill_level >= 18 or self.depth >= 18:
        return config['high']
    elif self.skill_level >= 15 or self.depth >= 15:
        return config['medium']
    else:
        return config['low']

# Then use: time_limit = self.get_custom_timeout('fast')
""")
    
    print("📝 Method 3: Configuration file approach")
    print("-" * 25)
    print("""
Add to chess_ai_config.json:

{
  "engine": {
    "timeout_profiles": {
      "blitz": {"base": 1000, "multiplier": 1.0},
      "rapid": {"base": 2000, "multiplier": 1.2},
      "classical": {"base": 4000, "multiplier": 1.5}
    },
    "active_profile": "rapid"
  }
}

Then load and use in engine.py
""")

def interactive_timeout_calculator():
    """Interactive timeout calculator"""
    print("🧮 Interactive Timeout Calculator")
    print("=" * 35)
    
    try:
        print("Enter your preferences:")
        
        game_type = input("Game type (blitz/rapid/classical/analysis): ").lower()
        cpu_strength = input("CPU strength (weak/medium/strong): ").lower()
        priority = input("Priority (speed/balance/strength): ").lower()
        
        # Calculate recommended timeouts
        base_timeouts = {
            'blitz': 1000,
            'rapid': 2500,
            'classical': 4000,
            'analysis': 8000
        }
        
        cpu_multipliers = {
            'weak': 0.7,
            'medium': 1.0,
            'strong': 1.4
        }
        
        priority_multipliers = {
            'speed': 0.6,
            'balance': 1.0,
            'strength': 1.6
        }
        
        base = base_timeouts.get(game_type, 2500)
        cpu_mult = cpu_multipliers.get(cpu_strength, 1.0)
        priority_mult = priority_multipliers.get(priority, 1.0)
        
        recommended_timeout = int(base * cpu_mult * priority_mult)
        
        print(f"\n🎯 Recommended Configuration:")
        print(f"   Base timeout: {base}ms")
        print(f"   CPU adjustment: ×{cpu_mult}")
        print(f"   Priority adjustment: ×{priority_mult}")
        print(f"   Final timeout: {recommended_timeout}ms ({recommended_timeout/1000:.1f}s)")
        
        # Show skill/depth recommendations
        if recommended_timeout <= 1500:
            print(f"   Recommended: Skill 5-12, Depth 6-10")
        elif recommended_timeout <= 3000:
            print(f"   Recommended: Skill 10-15, Depth 10-15")
        elif recommended_timeout <= 5000:
            print(f"   Recommended: Skill 15-18, Depth 15-18")
        else:
            print(f"   Recommended: Skill 18-20, Depth 18-20")
        
    except KeyboardInterrupt:
        print("\n⚠️ Calculator interrupted")
    except Exception as e:
        print(f"❌ Error in calculator: {e}")

def main():
    """Main function"""
    print("🕐 Chess Engine Timeout Analysis & Configuration Tool")
    print("=" * 60)
    print()
    
    try:
        display_current_timeouts()
        show_timeout_matrix()
        analyze_performance_impact()
        create_custom_timeout_profiles()
        generate_timeout_modification_code()
        
        print("\n" + "="*60)
        interactive_timeout_calculator()
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()