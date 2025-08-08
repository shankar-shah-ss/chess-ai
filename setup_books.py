#!/usr/bin/env python3
# setup_books.py - Setup opening books for the chess AI
import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Setup opening books"""
    print("📚 Chess AI Opening Book Setup")
    print("=" * 40)
    
    try:
        from book_downloader import setup_opening_books
        
        books_dir = os.path.join(os.path.dirname(__file__), 'books')
        print(f"Setting up books in: {books_dir}")
        
        success = setup_opening_books(books_dir)
        
        if success:
            print("\n✅ Opening books setup completed!")
            print("\nYour chess AI now has access to:")
            print("• Essential opening moves (built-in)")
            print("• Sample master games")
            print("• Polyglot opening books (if downloaded)")
            print("\nThe engine will now:")
            print("1. 📖 Use book moves in the opening (up to 25 moves deep)")
            print("2. 🔄 Rotate between top moves for variety")
            print("3. 🤖 Fall back to engine calculation when out of book")
            
        else:
            print("\n⚠️ Setup completed with some issues")
            print("The basic opening book will still work with built-in moves")
        
        return success
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()