import sqlite3
from typing import List, Tuple, Any, Optional
from contextlib import contextmanager

class DeckRommSyncDatabase:
    def __init__(self, db_name: str):
        """
        Initializes the database configuration.
        Each operation will create its own connection for thread safety.
        """
        self.db_name = db_name
        # Create initial connection to verify database exists and enable WAL mode
        self._init_database()
    
    def _init_database(self):
        """
        Initialize database with Write-Ahead Logging (WAL) for better concurrency.
        Creates all required tables if they don't exist.
        """
        with self._get_connection() as conn:
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()
            
            # Create config table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT
                )
            """)
            
            # Create collections table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    collections_id INTEGER PRIMARY KEY,
                    name TEXT,
                    rom_count INTEGER,
                    cover TEXT,
                    collection_sync INTEGER DEFAULT 0
                )
            """)
            
            # Create roms table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS roms (
                    roms_id INTEGER PRIMARY KEY,
                    collections_id INTEGER,
                    name TEXT,
                    url_cover TEXT,
                    filename TEXT,
                    platform_fs_slug TEXT,
                    platform_id INTEGER,
                    sync_status INTEGER DEFAULT 0,
                    FOREIGN KEY (collections_id) REFERENCES collections(collections_id)
                )
            """)
            
            # Create platforms_matching table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platforms_matching (
                    romm_platform_id INTEGER PRIMARY KEY,
                    romm_platform_name TEXT,
                    steamdeck_platform_name TEXT
                )
            """)
            
            # Create rom_saves table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rom_saves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rom_id INTEGER NOT NULL,
                    romm_save_id INTEGER,
                    emulator TEXT,
                    file_name TEXT NOT NULL,
                    file_size_bytes INTEGER,
                    local_path TEXT,
                    remote_updated_at TEXT,
                    local_updated_at TEXT,
                    sync_status INTEGER DEFAULT 0,
                    sync_direction TEXT,
                    last_sync_at TEXT,
                    error_message TEXT,
                    FOREIGN KEY (rom_id) REFERENCES roms(roms_id)
                )
            """)
            
            # Create rom_states table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rom_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rom_id INTEGER NOT NULL,
                    romm_state_id INTEGER,
                    emulator TEXT,
                    file_name TEXT NOT NULL,
                    file_size_bytes INTEGER,
                    local_path TEXT,
                    screenshot_path TEXT,
                    remote_updated_at TEXT,
                    local_updated_at TEXT,
                    sync_status INTEGER DEFAULT 0,
                    sync_direction TEXT,
                    last_sync_at TEXT,
                    error_message TEXT,
                    FOREIGN KEY (rom_id) REFERENCES roms(roms_id)
                )
            """)
            
            # Create sync_history table for saves if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS save_sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_saves INTEGER DEFAULT 0,
                    downloaded INTEGER DEFAULT 0,
                    uploaded INTEGER DEFAULT 0,
                    conflicts INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running'
                )
            """)
            
            # Create oauth_tokens table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_type TEXT DEFAULT 'bearer',
                    expires_at TEXT NOT NULL,
                    scopes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager that provides a thread-safe database connection.
        Each call creates a new connection that is automatically closed.
        """
        connection = sqlite3.connect(self.db_name, timeout=10.0)
        try:
            yield connection
        except Exception as e:
            connection.rollback()
            raise
        finally:
            connection.close()
    
    @property
    def connection(self):
        """
        Legacy property for backward compatibility.
        Creates a new connection each time it's accessed.
        Note: Caller is responsible for closing this connection.
        """
        return sqlite3.connect(self.db_name, timeout=10.0)
    
    @property
    def cursor(self):
        """
        Legacy property for backward compatibility.
        Creates a new cursor from a new connection.
        Note: This will leak connections - use _get_connection() instead.
        """
        return self.connection.cursor()

    def execute_query(self, query: str, params: Tuple = ()) -> None:
        """
        Executes an SQL query without return value (INSERT, UPDATE, DELETE).
        Thread-safe - creates its own connection.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
        except sqlite3.Error as e:
            print(f"SQLite Error: (0) {e}")
            raise
    
    def insert(self, table: str, columns: List[str], values: Tuple) -> None:
        """
        Executes an INSERT into the database.
        """
        cols = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        # print(query)
        self.execute_query(query, values)
    
    def insert_or_replace(self, table: str, columns: List[str], values: Tuple) -> None:
        """
        Executes an INSERT OR REPLACE into the database.
        This will update the row if a primary key conflict occurs.
        """
        cols = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
        self.execute_query(query, values)
    
    def update(self, table: str, updates: dict, condition: str, condition_values: Tuple) -> None:
        """
        Executes an UPDATE in the database.
        """
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        values = tuple(updates.values()) + condition_values
        self.execute_query(query, values)
    
    def delete(self, table: str, condition: str = '1=1', condition_values: Tuple = ()) -> None:
        """
        Executes a DELETE in the database.
        
        Args:
            table: Table name
            condition: WHERE clause condition (default: '1=1' to delete all)
            condition_values: Values for the WHERE clause
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        self.execute_query(query, condition_values)
    
    def fetch_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        """
        Executes a SELECT query and returns the results.
        Thread-safe - creates its own connection.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"SQLite Error: (1) {e}")
            return []
        
    def select(self, table: str, columns: List[str] = ['*'], condition: str = '', condition_values: Tuple = ()) -> List[Tuple]:
        """
        Executes a SELECT in the database and returns the results.
        """
        cols = ', '.join(columns)
        query = f"SELECT {cols} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        return self.fetch_query(query, condition_values)
    
    def select_as_dict(self, table: str, columns: List[str] = ['*'], condition: str = '', condition_values: Tuple = (), order_by: str = '', limit: int = None) -> List[dict]:
        """
        Executes a SELECT in the database and returns the results as a list of dictionaries.
        Thread-safe - creates its own connection.
        
        Args:
            table: Table name
            columns: List of column names to select
            condition: WHERE clause condition
            condition_values: Values for the WHERE clause
            order_by: ORDER BY clause (e.g., "id DESC")
            limit: Maximum number of rows to return
        """
        cols = ', '.join(columns)
        query = f"SELECT {cols} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, condition_values)
                rows = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]  # Gets the column names
                return [dict(zip(column_names, row)) for row in rows]  # Creates dicts
        except sqlite3.Error as e:
            print(f"SQLite Error: (2) {e}")
            return []
    
    def close(self):
        """
        Close method for compatibility.
        Since we use connection-per-operation, this is a no-op.
        """
        pass
    
    def __enter__(self):
        """Support for context manager usage."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager usage."""
        self.close()
        return False