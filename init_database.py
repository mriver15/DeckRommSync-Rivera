#!/usr/bin/env python3
"""
Database Initialization Script for DeckRommSync-Rivera

This script initializes the database with all required tables.
Run this when setting up DeckRommSync on a new device.

Usage:
    python init_database.py
"""

import sys
import os
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase

def init_database(db_name: str = "deckrommsync.db"):
    """
    Initialize the database with all required tables.
    
    Args:
        db_name: Name of the SQLite database file
    """
    print("=" * 60)
    print("DeckRommSync Database Initialization")
    print("=" * 60)
    print()
    
    # Check if database already exists
    db_exists = os.path.exists(db_name)
    if db_exists:
        print(f"⚠️  Database '{db_name}' already exists.")
        response = input("Do you want to continue? This will create missing tables. (y/n): ")
        if response.lower() != 'y':
            print("Initialization cancelled.")
            return
        print()
    
    try:
        print("Initializing database...")
        db = DeckRommSyncDatabase(db_name)
        
        # The __init__ method automatically calls _init_database()
        # which creates all tables
        
        print("✓ Core tables created:")
        print("  - config")
        print("  - collections")
        print("  - roms")
        print("  - platforms_matching")
        print()
        print("✓ Save sync tables created:")
        print("  - rom_saves")
        print("  - rom_states")
        print("  - save_sync_history")
        print()
        print("✓ OAuth tables created:")
        print("  - oauth_tokens")
        print()
        
        # Add default configuration if config table is empty
        config_count = len(db.select('config'))
        if config_count == 0:
            print("Adding default configuration...")
            
            default_configs = [
                ('romm_api_base_url', ''),
                ('romm_username', ''),
                ('romm_password', ''),
                ('steamdeck_retrodeck_path', '/home/deck/retrodeck/roms'),
                ('use_oauth', '0'),
                ('oauth_scopes', 'platforms.read,roms.read,collections.read,assets.read,assets.write'),
                ('enable_save_sync', '1'),
                ('enable_state_sync', '0'),
            ]
            
            for key, value in default_configs:
                db.insert('config', ['config_key', 'config_value'], (key, value))
            
            print(f"✓ Added {len(default_configs)} default configuration entries")
            print()
            print("⚠️  IMPORTANT: Configure your RomM API settings in the web UI:")
            print("   1. Start the application: python app.py")
            print("   2. Open http://localhost:5000/config")
            print("   3. Enter your RomM API URL, username, and password")
            print()
        else:
            print(f"✓ Configuration table already has {config_count} entries")
            print()
        
        print("=" * 60)
        print("✅ Database initialization completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run: python app.py")
        print("  2. Configure RomM API settings at http://localhost:5000/config")
        print("  3. Enable collections to sync")
        print("  4. Click 'Sync Now' on the status page")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Error during initialization:")
        print("=" * 60)
        print(f"  {str(e)}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    # Allow custom database name from command line
    db_name = sys.argv[1] if len(sys.argv) > 1 else "deckrommsync.db"
    init_database(db_name)
