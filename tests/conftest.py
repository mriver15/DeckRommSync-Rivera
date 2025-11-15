"""
Pytest configuration and fixtures for DeckRommSync tests
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_deckrommsync.db")
    
    # Create database instance
    db = DeckRommSyncDatabase(db_path)
    
    # Initialize schema
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT
        )
    """)
    
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS collections (
            collections_id INTEGER PRIMARY KEY,
            name TEXT,
            rom_count INTEGER,
            cover TEXT,
            collection_sync INTEGER DEFAULT 0
        )
    """)
    
    db.execute_query("""
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
    
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS platforms_matching (
            romm_platform_id INTEGER PRIMARY KEY,
            romm_platform_name TEXT,
            steamdeck_platform_name TEXT
        )
    """)
    
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            duration_seconds REAL,
            total_roms INTEGER,
            success_count INTEGER,
            error_count INTEGER,
            skipped_count INTEGER,
            debug_mode INTEGER DEFAULT 0
        )
    """)
    
    yield db
    
    # Cleanup
    db.connection.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_romm_api(mocker):
    """Mock RomM API responses."""
    mock_responses = {
        'heartbeat': {'status': 'ok'},
        'platforms': [
            {'id': 1, 'name': 'PlayStation', 'fs_slug': 'psx'},
            {'id': 2, 'name': 'Nintendo 64', 'fs_slug': 'n64'},
        ],
        'collections': [
            {
                'id': 1,
                'name': 'My Collection',
                'rom_count': 2,
                'path_covers_large': ['http://example.com/cover.jpg'],
                'rom_ids': [1, 2]
            }
        ],
        'rom_detail': {
            'id': 1,
            'name': 'Test Game',
            'fs_name': 'test_game.iso',
            'platform_id': 1,
            'platform_fs_slug': 'psx',
            'url_cover': 'http://example.com/cover.jpg'
        }
    }
    return mock_responses


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        'romm_api_base_url': 'http://localhost:8080/api',
        'romm_username': 'test_user',
        'romm_password': 'test_password',
        'steamdeck_retrodeck_path': '/test/path/'
    }
