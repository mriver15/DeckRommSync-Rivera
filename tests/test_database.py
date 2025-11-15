"""
Unit tests for DeckRommSyncDatabase class
"""
import pytest
import sqlite3
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase


class TestDatabaseInitialization:
    """Test database initialization."""
    
    def test_database_connection(self, temp_db):
        """Test that database connection is established."""
        assert temp_db.connection is not None
        assert temp_db.cursor is not None
    
    def test_database_file_creation(self, temp_db):
        """Test that database file is created."""
        import os
        assert os.path.exists(temp_db.db_name)


class TestInsertOperations:
    """Test database insert operations."""
    
    def test_insert_single_row(self, temp_db):
        """Test inserting a single row."""
        temp_db.insert(
            'config',
            ['config_key', 'config_value'],
            ('test_key', 'test_value')
        )
        
        result = temp_db.select('config', ['*'], 'config_key = ?', ('test_key',))
        assert len(result) == 1
        assert result[0][1] == 'test_key'
        assert result[0][2] == 'test_value'
    
    def test_insert_collection(self, temp_db):
        """Test inserting a collection."""
        temp_db.insert(
            'collections',
            ['collections_id', 'name', 'rom_count', 'cover', 'collection_sync'],
            (1, 'Test Collection', 5, 'http://example.com/cover.jpg', 1)
        )
        
        result = temp_db.select('collections', ['*'], 'collections_id = ?', (1,))
        assert len(result) == 1
        assert result[0][1] == 'Test Collection'
        assert result[0][2] == 5
    
    def test_insert_rom(self, temp_db):
        """Test inserting a ROM."""
        # First insert a collection
        temp_db.insert(
            'collections',
            ['collections_id', 'name', 'rom_count', 'cover', 'collection_sync'],
            (1, 'Test Collection', 1, 'http://example.com/cover.jpg', 0)
        )
        
        # Then insert a ROM
        temp_db.insert(
            'roms',
            ['roms_id', 'collections_id', 'name', 'filename', 'platform_id', 'sync_status'],
            (1, 1, 'Test Game', 'test_game.iso', 1, 0)
        )
        
        result = temp_db.select('roms', ['*'], 'roms_id = ?', (1,))
        assert len(result) == 1
        assert result[0][2] == 'Test Game'


class TestUpdateOperations:
    """Test database update operations."""
    
    def test_update_config_value(self, temp_db):
        """Test updating a config value."""
        # Insert initial value
        temp_db.insert('config', ['config_key', 'config_value'], ('test_key', 'old_value'))
        
        # Update the value
        temp_db.update(
            'config',
            {'config_value': 'new_value'},
            'config_key = ?',
            ('test_key',)
        )
        
        # Verify update
        result = temp_db.select('config', ['config_value'], 'config_key = ?', ('test_key',))
        assert result[0][0] == 'new_value'
    
    def test_update_rom_sync_status(self, temp_db):
        """Test updating ROM sync status."""
        # Insert collection and ROM
        temp_db.insert(
            'collections',
            ['collections_id', 'name', 'rom_count', 'cover', 'collection_sync'],
            (1, 'Test Collection', 1, 'cover.jpg', 0)
        )
        temp_db.insert(
            'roms',
            ['roms_id', 'collections_id', 'name', 'filename', 'platform_id', 'sync_status'],
            (1, 1, 'Test Game', 'game.iso', 1, 0)
        )
        
        # Update sync status (storing as integer)
        temp_db.update('roms', {'sync_status': 1}, 'roms_id = ?', (1,))
        
        # Verify
        result = temp_db.select('roms', ['sync_status'], 'roms_id = ?', (1,))
        assert result[0][0] == 1  # SQLite returns integer
    
    def test_update_collection_sync_flag(self, temp_db):
        """Test updating collection sync flag."""
        temp_db.insert(
            'collections',
            ['collections_id', 'name', 'rom_count', 'cover', 'collection_sync'],
            (1, 'Test Collection', 0, 'cover.jpg', 0)
        )
        
        temp_db.update('collections', {'collection_sync': 1}, 'collections_id = ?', (1,))
        
        result = temp_db.select('collections', ['collection_sync'], 'collections_id = ?', (1,))
        assert result[0][0] == 1


class TestSelectOperations:
    """Test database select operations."""
    
    def test_select_all(self, temp_db):
        """Test selecting all rows."""
        # Insert multiple config entries
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        temp_db.insert('config', ['config_key', 'config_value'], ('key2', 'value2'))
        
        result = temp_db.select('config')
        assert len(result) >= 2
    
    def test_select_with_condition(self, temp_db):
        """Test selecting with WHERE condition."""
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        temp_db.insert('config', ['config_key', 'config_value'], ('key2', 'value2'))
        
        result = temp_db.select('config', ['*'], 'config_key = ?', ('key1',))
        assert len(result) == 1
        assert result[0][1] == 'key1'
    
    def test_select_specific_columns(self, temp_db):
        """Test selecting specific columns."""
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        
        result = temp_db.select('config', ['config_value'], 'config_key = ?', ('key1',))
        assert len(result) == 1
        assert result[0][0] == 'value1'


class TestSelectAsDict:
    """Test select_as_dict operations."""
    
    def test_select_as_dict_returns_dict(self, temp_db):
        """Test that select_as_dict returns dictionaries."""
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        
        result = temp_db.select_as_dict('config', ['*'], 'config_key = ?', ('key1',))
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]['config_key'] == 'key1'
        assert result[0]['config_value'] == 'value1'
    
    def test_select_as_dict_multiple_rows(self, temp_db):
        """Test select_as_dict with multiple rows."""
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        temp_db.insert('config', ['config_key', 'config_value'], ('key2', 'value2'))
        
        result = temp_db.select_as_dict('config')
        assert len(result) >= 2
        assert all(isinstance(row, dict) for row in result)
    
    def test_select_as_dict_collections(self, temp_db):
        """Test select_as_dict with collections table."""
        temp_db.insert(
            'collections',
            ['collections_id', 'name', 'rom_count', 'cover', 'collection_sync'],
            (1, 'Test Collection', 10, 'cover.jpg', 1)
        )
        
        result = temp_db.select_as_dict('collections', ['*'], 'collection_sync = ?', (1,))
        assert len(result) == 1
        assert result[0]['collections_id'] == 1
        assert result[0]['name'] == 'Test Collection'
        assert result[0]['rom_count'] == 10


class TestErrorHandling:
    """Test error handling in database operations."""
    
    def test_select_nonexistent_table(self, temp_db):
        """Test selecting from non-existent table."""
        result = temp_db.select('nonexistent_table')
        assert result == []
    
    def test_select_as_dict_nonexistent_table(self, temp_db):
        """Test select_as_dict from non-existent table."""
        result = temp_db.select_as_dict('nonexistent_table')
        assert result == []
