#!/usr/bin/env python3
"""
Migration script to add save sync configuration to existing database.
Run this once to enable save sync features.
"""

from classes.DeckRommSyncDatabase import DeckRommSyncDatabase
import json

def migrate():
    """Add save sync configuration to database."""
    print("Starting save sync migration...")
    
    # Load config to get database name
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    db_name = config.get('database', {}).get('name', 'deckrommsync.db')
    db = DeckRommSyncDatabase(db_name)
    
    # Check if enable_save_sync config exists
    existing_config = db.select_as_dict("config", condition="config_key = 'enable_save_sync'")
    
    if not existing_config:
        print("Adding enable_save_sync configuration...")
        db.insert("config", ["config_key", "config_value"], ("enable_save_sync", "1"))
        print("✓ enable_save_sync configuration added (enabled by default)")
    else:
        print("✓ enable_save_sync configuration already exists")
    
    # Check if enable_state_sync config exists
    existing_state_config = db.select_as_dict("config", condition="config_key = 'enable_state_sync'")
    
    if not existing_state_config:
        print("Adding enable_state_sync configuration...")
        db.insert("config", ["config_key", "config_value"], ("enable_state_sync", "0"))
        print("✓ enable_state_sync configuration added (disabled by default)")
    else:
        print("✓ enable_state_sync configuration already exists")
    
    # Tables are auto-created by DeckRommSyncDatabase._init_database()
    print("\n✓ Database tables rom_saves, rom_states, and save_sync_history are created automatically")
    
    print("\n" + "="*50)
    print("Migration completed successfully!")
    print("="*50)
    print("\nSave sync is now enabled. You can configure it in:")
    print("1. config.json - Set sync.enable_save_sync to true/false")
    print("2. Database - Update config table enable_save_sync to 1/0")
    print("\nNext steps:")
    print("1. Run the application: python app.py")
    print("2. Sync will automatically include save files")
    print("3. Monitor background_worker.log for save sync activity")
    
if __name__ == "__main__":
    migrate()
