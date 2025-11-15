#!/usr/bin/env python3
"""
Migration script to add OAuth2 configuration to existing DeckRommSync installations.

This script:
1. Adds use_oauth and oauth_scopes configuration to the database
2. Creates the oauth_tokens table (handled by DeckRommSyncDatabase)
3. Provides instructions for configuring OAuth2

Usage:
    python migrate_oauth.py
"""

import sqlite3
import json
from datetime import datetime

def migrate_database():
    """Add OAuth2 configuration to database."""
    
    print("Starting OAuth2 migration...")
    print("=" * 60)
    
    # Connect to database
    conn = sqlite3.connect('deckrommsync.db')
    cursor = conn.cursor()
    
    try:
        # Check if use_oauth config exists
        cursor.execute("SELECT config_value FROM config WHERE config_key = 'use_oauth'")
        result = cursor.fetchone()
        
        if result:
            print("✓ OAuth configuration already exists")
        else:
            # Add use_oauth config (disabled by default)
            print("Adding use_oauth configuration...")
            cursor.execute("""
                INSERT INTO config (config_key, config_value) 
                VALUES ('use_oauth', '0')
            """)
            print("✓ use_oauth configuration added (disabled by default)")
        
        # Check if oauth_scopes config exists
        cursor.execute("SELECT config_value FROM config WHERE config_key = 'oauth_scopes'")
        result = cursor.fetchone()
        
        if result:
            print("✓ OAuth scopes configuration already exists")
        else:
            # Add oauth_scopes config with default scopes
            print("Adding oauth_scopes configuration...")
            default_scopes = "platforms.read,roms.read,collections.read,assets.read,assets.write"
            cursor.execute("""
                INSERT INTO config (config_key, config_value) 
                VALUES ('oauth_scopes', ?)
            """, (default_scopes,))
            print("✓ oauth_scopes configuration added")
            print(f"  Default scopes: {default_scopes}")
        
        # Commit changes
        conn.commit()
        
        # Verify oauth_tokens table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='oauth_tokens'
        """)
        if cursor.fetchone():
            print("✓ oauth_tokens table exists")
        else:
            print("⚠ oauth_tokens table will be created on next application start")
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
        print("\nNext steps:")
        print("1. Update config.json to enable OAuth:")
        print('   "oauth": {')
        print('     "enabled": true,')
        print('     "scopes": [')
        print('       "platforms.read",')
        print('       "roms.read",')
        print('       "collections.read",')
        print('       "assets.read",')
        print('       "assets.write"')
        print('     ]')
        print('   }')
        print("\n2. Or use the web UI to enable OAuth in the configuration page")
        print("\n3. The application will automatically handle token management")
        print("\nNote: OAuth is disabled by default for backward compatibility.")
        print("      Existing Basic Auth configurations will continue to work.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
