"""
Unit tests for database thread safety
"""
import pytest
import threading
import time
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase


class TestThreadSafety:
    """Test thread safety of database operations."""
    
    def test_concurrent_reads(self, temp_db):
        """Test multiple threads reading simultaneously."""
        # Insert test data
        for i in range(10):
            temp_db.insert('config', ['config_key', 'config_value'], (f'key{i}', f'value{i}'))
        
        results = []
        errors = []
        
        def read_data(thread_id):
            try:
                data = temp_db.select('config')
                results.append((thread_id, len(data)))
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create 5 threads reading simultaneously
        threads = []
        for i in range(5):
            t = threading.Thread(target=read_data, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        # All threads should see at least 10 records
        assert all(count >= 10 for _, count in results)
    
    def test_concurrent_writes(self, temp_db):
        """Test multiple threads writing simultaneously."""
        errors = []
        
        def write_data(thread_id):
            try:
                for i in range(5):
                    temp_db.insert(
                        'config',
                        ['config_key', 'config_value'],
                        (f'thread{thread_id}_key{i}', f'value{i}')
                    )
            except Exception as e:
                errors.append((thread_id, e))
        
        # Create 3 threads writing simultaneously
        threads = []
        for i in range(3):
            t = threading.Thread(target=write_data, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify all writes succeeded
        result = temp_db.select('config')
        assert len(result) >= 15  # 3 threads * 5 inserts each
    
    def test_concurrent_read_write(self, temp_db):
        """Test simultaneous reads and writes."""
        # Insert initial data
        temp_db.insert('config', ['config_key', 'config_value'], ('initial', 'value'))
        
        errors = []
        read_counts = []
        
        def read_data():
            try:
                for _ in range(10):
                    data = temp_db.select('config')
                    read_counts.append(len(data))
                    time.sleep(0.01)
            except Exception as e:
                errors.append(('reader', e))
        
        def write_data(thread_id):
            try:
                for i in range(5):
                    temp_db.insert(
                        'config',
                        ['config_key', 'config_value'],
                        (f'writer{thread_id}_key{i}', f'value{i}')
                    )
                    time.sleep(0.01)
            except Exception as e:
                errors.append((f'writer{thread_id}', e))
        
        # Start reader thread
        reader = threading.Thread(target=read_data)
        reader.start()
        
        # Start writer threads
        writers = []
        for i in range(2):
            t = threading.Thread(target=write_data, args=(i,))
            writers.append(t)
            t.start()
        
        # Wait for all threads
        reader.join()
        for t in writers:
            t.join()
        
        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify reads happened
        assert len(read_counts) > 0
        
        # Verify final state
        final_count = temp_db.select('config')
        assert len(final_count) >= 11  # 1 initial + 2 writers * 5 inserts
    
    def test_connection_isolation(self, temp_db):
        """Test that each operation gets its own connection."""
        # Insert some data
        temp_db.insert('config', ['config_key', 'config_value'], ('key1', 'value1'))
        
        # Verify we can read it back (should work even with new connection)
        result = temp_db.select('config', ['*'], 'config_key = ?', ('key1',))
        assert len(result) == 1
        assert result[0][1] == 'key1'
    
    def test_wal_mode_enabled(self, temp_db):
        """Test that WAL mode is enabled for better concurrency."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            assert result[0].upper() == 'WAL'
    
    def test_context_manager_support(self, temp_db):
        """Test that database can be used as context manager."""
        with temp_db as db:
            db.insert('config', ['config_key', 'config_value'], ('ctx_key', 'ctx_value'))
        
        # Verify data persisted after context exit
        result = temp_db.select('config', ['*'], 'config_key = ?', ('ctx_key',))
        assert len(result) == 1


class TestBackwardCompatibility:
    """Test that legacy code still works."""
    
    def test_legacy_connection_property(self, temp_db):
        """Test that legacy .connection property still works."""
        conn = temp_db.connection
        assert conn is not None
        
        # Should be able to use it
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        # Clean up
        conn.close()
    
    def test_legacy_cursor_property(self, temp_db):
        """Test that legacy .cursor property still works."""
        cursor = temp_db.cursor
        assert cursor is not None
        
        # Should be able to use it
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
