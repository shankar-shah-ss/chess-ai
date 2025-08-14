# 🏆 Chess AI with Intelligent Opening Variety System

A sophisticated chess AI application featuring an intelligent opening system that prevents repetitive play and ensures variety across games.

## ✨ Key Features

### 🎯 **Intelligent Opening Variety System**
- **10+ Game Repetition Prevention**: Same openings are blocked for at least 10 games
- **Random Selection from Book Moves**: When multiple quality moves are available, engine randomly selects one
- **Quality-Weighted Randomization**: Maintains strong play while ensuring variety
- **ELO-Specific Tracking**: Different skill levels have separate opening histories
- **Persistent Storage**: Opening history saved across sessions

### 🎮 **Game Modes**
- Human vs Engine
- Engine vs Engine  
- Human vs Human
- Multiple difficulty levels (800-3200+ ELO)

### 📚 **Advanced Opening System**
- **Lichess Masters Database**: High-quality opening moves from master games
- **Intelligent Move Selection**: `intelligent_random` strategy balances quality and variety
- **Deep Opening Knowledge**: Up to 20 moves deep
- **Real-time API Integration**: Always up-to-date opening data

### 🎨 **User Interface**
- Clean, intuitive GUI built with Pygame
- Multiple themes and piece sets
- Sound effects and visual feedback
- Game saving and loading (PGN format)

## 🚀 Quick Start

### Prerequisites
```bash
pip install pygame stockfish chess requests
```

### Installation
1. Clone or download the repository
2. Ensure Stockfish engine is installed and accessible
3. Run the application:
```bash
cd src
python main.py
```

## 🔧 Configuration

### Opening System Configuration (`src/lichess_config.json`)
```json
{
  "lichess_opening_system": {
    "move_selection": "intelligent_random",
    "variety_enabled": true,
    "min_games_gap": 10,
    "max_depth": 20,
    "min_games": 10
  }
}
```

### Move Selection Strategies
- **`intelligent_random`**: Smart random selection with variety management (recommended)
- **`best`**: Always select highest-rated move
- **`popular`**: Select most frequently played move
- **`random`**: Weighted random based on game frequency

## 📊 System Architecture

### Core Components
- **`engine.py`**: Chess engine integration with Stockfish
- **`opening_variety_manager.py`**: Intelligent variety management system
- **`lichess_opening_book.py`**: Lichess masters database integration
- **`game.py`**: Main game logic and UI
- **`main.py`**: Application entry point

### Data Storage
- **`data/opening_history.json`**: Opening variety tracking data
- **`games/`**: Saved games in PGN format
- **`logs/`**: Application and error logs

## 🧪 Testing

### Verification Script
```bash
python verify_intelligent_opening_system.py
```

This script verifies:
- ✅ Critical fixes applied
- ✅ Configuration correct
- ✅ Opening variety manager working
- ✅ Random selection from multiple moves
- ✅ Engine integration complete

### Test Results
All 5 verification tests pass, confirming the system is fully operational.

## 📈 Opening Variety Statistics

The system tracks:
- Games recorded per ELO level
- Blocked openings count
- Recent opening signatures
- Diversity scores
- Most played openings analysis

Access stats via:
```python
from engine import ChessEngine
engine = ChessEngine(target_elo=1600)
stats = engine.get_opening_variety_stats()
```

## 🎯 How It Works

### Opening Selection Process
1. **Check Available Moves**: Query Lichess masters database for position
2. **Filter by Variety**: Remove recently played openings (last 10 games)
3. **Quality Weighting**: Calculate weights based on win rate, popularity, and reliability
4. **Random Selection**: Choose move using weighted randomization
5. **Record Move**: Track for future variety management

### Variety Enforcement
- **Opening Signatures**: Generated from first 4 moves of each game
- **ELO-Specific Blocking**: 1500 ELO and 1600 ELO have separate histories
- **Time-Based Bonuses**: Older openings get higher selection probability
- **Fallback Protection**: System never gets completely stuck

## 🏆 Benefits

### For Players
- **Never Boring**: Each game features different opening patterns
- **Educational**: Exposure to wide variety of opening systems
- **Challenging**: Unpredictable but high-quality opening play

### For Developers
- **Modular Design**: Easy to extend and modify
- **Well-Documented**: Comprehensive code documentation
- **Tested**: Verified functionality with test suite
- **Configurable**: Adjustable parameters for different needs

## 📁 Project Structure

```
chess-ai/
├── src/                          # Source code
│   ├── main.py                   # Application entry point
│   ├── engine.py                 # Chess engine integration
│   ├── opening_variety_manager.py # Variety management system
│   ├── lichess_opening_book.py   # Opening book integration
│   ├── game.py                   # Game logic and UI
│   └── ...                       # Other game components
├── data/                         # Application data
├── games/                        # Saved games
├── assets/                       # Images and sounds
├── books/                        # Opening book database
└── README.md                     # This file
```

## 🔍 Verification

The system has been thoroughly tested and verified:
- **All critical fixes applied** ✅
- **Intelligent opening variety system operational** ✅
- **Random selection from multiple book moves working** ✅
- **Opening repetition prevention (10+ games) working** ✅
- **Engine integration complete** ✅

## 🎉 Status

**PRODUCTION READY** - The chess AI now features a world-class opening system that combines master-level opening quality with intelligent variety management!

---

*For detailed technical documentation, see `INTELLIGENT_OPENING_SYSTEM_COMPLETE.md`*