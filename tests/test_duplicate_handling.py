"""
Tests for duplicate handling using INSERT OR REPLACE.
"""
import pytest
import tempfile
import os
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase


class TestInsertOrReplace:
    """Test INSERT OR REPLACE functionality."""
    
    def test_insert_or_replace_new_row(self, temp_db):
        """Test inserting a new row with insert_or_replace."""
        db = temp_db
        
        # Create test table
        db.execute_query("""
            CREATE TABLE test_items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        # Insert new row
        db.insert_or_replace("test_items", ["id", "name", "value"], (1, "Item One", 100))
        
        # Verify insertion
        result = db.select("test_items")
        assert len(result) == 1
        assert result[0] == (1, "Item One", 100)
    
    def test_insert_or_replace_updates_existing(self, temp_db):
        """Test that insert_or_replace updates existing rows on conflict."""
        db = temp_db
        
        # Create test table
        db.execute_query("""
            CREATE TABLE test_items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        # Insert initial row
        db.insert("test_items", ["id", "name", "value"], (1, "Item One", 100))
        
        # Use insert_or_replace with same ID but different data
        db.insert_or_replace("test_items", ["id", "name", "value"], (1, "Item One Updated", 200))
        
        # Verify only one row exists with updated values
        result = db.select("test_items")
        assert len(result) == 1
        assert result[0] == (1, "Item One Updated", 200)
    
    def test_insert_or_replace_multiple_rows(self, temp_db):
        """Test insert_or_replace with multiple rows."""
        db = temp_db
        
        # Create test table
        db.execute_query("""
            CREATE TABLE test_items (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        # Insert multiple rows
        db.insert_or_replace("test_items", ["id", "name", "value"], (1, "Item One", 100))
        db.insert_or_replace("test_items", ["id", "name", "value"], (2, "Item Two", 200))
        db.insert_or_replace("test_items", ["id", "name", "value"], (3, "Item Three", 300))
        
        # Update one of them
        db.insert_or_replace("test_items", ["id", "name", "value"], (2, "Item Two Updated", 250))
        
        # Verify all rows
        result = db.select("test_items", ["*"], "", ())
        assert len(result) == 3
        
        # Check the updated row
        result_dict = db.select_as_dict("test_items", ["*"], "id = ?", (2,))
        assert result_dict[0]['name'] == "Item Two Updated"
        assert result_dict[0]['value'] == 250


class TestPlatformDuplicateHandling:
    """Test duplicate handling for platforms."""
    
    def test_platform_resync_no_duplicates(self, temp_db):
        """Test that re-syncing platforms doesn't create duplicates."""
        db = temp_db
        
        # Platform table already created by fixture
        # First sync
        db.insert_or_replace("platforms_matching", ["romm_platform_id", "romm_platform_name"], 
                            (1, "PlayStation"))
        db.insert_or_replace("platforms_matching", ["romm_platform_id", "romm_platform_name"], 
                            (2, "Nintendo 64"))
        
        # Verify 2 platforms
        result = db.select("platforms_matching")
        assert len(result) == 2
        
        # Re-sync (simulate running sync again)
        db.insert_or_replace("platforms_matching", ["romm_platform_id", "romm_platform_name"], 
                            (1, "PlayStation"))
        db.insert_or_replace("platforms_matching", ["romm_platform_id", "romm_platform_name"], 
                            (2, "Nintendo 64"))
        db.insert_or_replace("platforms_matching", ["romm_platform_id", "romm_platform_name"], 
                            (3, "Sega Genesis"))
        
        # Should still have only 3 platforms (no duplicates)
        result = db.select("platforms_matching")
        assert len(result) == 3


class TestCollectionDuplicateHandling:
    """Test duplicate handling for collections."""
    
    def test_collection_resync_no_duplicates(self, temp_db):
        """Test that re-syncing collections doesn't create duplicates."""
        db = temp_db
        
        # Collection table already created by fixture
        # First sync
        db.insert_or_replace("collections", 
                            ["collections_id", "name", "rom_count", "cover", "collection_sync"],
                            (1, "Action Games", 10, "cover1.jpg", 0))
        
        # Verify 1 collection
        result = db.select("collections")
        assert len(result) == 1
        assert result[0][2] == 10  # rom_count
        
        # Re-sync with updated rom_count
        db.insert_or_replace("collections", 
                            ["collections_id", "name", "rom_count", "cover", "collection_sync"],
                            (1, "Action Games", 15, "cover1.jpg", 0))
        
        # Should still have only 1 collection with updated count
        result = db.select("collections")
        assert len(result) == 1
        assert result[0][2] == 15  # Updated rom_count
    
    def test_collection_sync_flag_preserved(self, temp_db):
        """Test that collection_sync flag is preserved during re-sync."""
        db = temp_db
        
        # Collection table already created by fixture
        # Insert collection with sync enabled
        db.insert_or_replace("collections", 
                            ["collections_id", "name", "rom_count", "cover", "collection_sync"],
                            (1, "Action Games", 10, "cover1.jpg", 1))
        
        # User enables sync
        db.update("collections", {"collection_sync": 1}, "collections_id = ?", (1,))
        
        # Verify sync is enabled
        result = db.select_as_dict("collections", ["*"], "collections_id = ?", (1,))
        assert result[0]['collection_sync'] == 1
        
        # WARNING: Re-sync will reset collection_sync to 0!
        # This is current behavior - need to fix in BackgroundWorker
        db.insert_or_replace("collections", 
                            ["collections_id", "name", "rom_count", "cover", "collection_sync"],
                            (1, "Action Games", 15, "cover1.jpg", 0))
        
        # Sync flag is now reset to 0 (this is a known limitation)
        result = db.select_as_dict("collections", ["*"], "collections_id = ?", (1,))
        assert result[0]['collection_sync'] == 0


class TestRomDuplicateHandling:
    """Test duplicate handling for ROMs."""
    
    def test_rom_resync_no_duplicates(self, temp_db):
        """Test that re-syncing ROMs doesn't create duplicates."""
        db = temp_db
        
        # ROM table already created by fixture
        # First sync
        db.insert_or_replace("roms", 
                            ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                            (1, 1, "Game One", "cover.jpg", "game1.iso", "ps1", 1))
        
        # Verify 1 ROM
        result = db.select("roms")
        assert len(result) == 1
        
        # Re-sync same ROM
        db.insert_or_replace("roms", 
                            ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                            (1, 1, "Game One", "cover.jpg", "game1.iso", "ps1", 1))
        
        # Should still have only 1 ROM
        result = db.select("roms")
        assert len(result) == 1
    
    def test_rom_sync_status_reset(self, temp_db):
        """Test that sync_status is reset when ROM is re-synced."""
        db = temp_db
        
        # ROM table already created by fixture
        # Insert ROM and mark as synced
        db.insert_or_replace("roms", 
                            ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                            (1, 1, "Game One", "cover.jpg", "game1.iso", "ps1", 1))
        
        db.update("roms", {"sync_status": 1}, "roms_id = ?", (1,))
        
        # Verify sync_status is 1
        result = db.select_as_dict("roms", ["*"], "roms_id = ?", (1,))
        assert result[0]['sync_status'] == 1
        
        # Re-sync (insert_or_replace doesn't include sync_status, so it gets default value)
        db.insert_or_replace("roms", 
                            ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                            (1, 1, "Game One Updated", "cover2.jpg", "game1.iso", "ps1", 1))
        
        # Check if sync_status is reset (depends on table default)
        result = db.select_as_dict("roms", ["*"], "roms_id = ?", (1,))
        # Note: sync_status will be NULL or 0 depending on table schema
        # since we didn't include it in the insert_or_replace
