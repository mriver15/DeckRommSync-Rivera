"""
Tests for debug mode functionality in BackgroundWorker.
"""

import pytest
import os
import json
import logging
from classes.BackgroundWorker import BackgroundWorker
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def debug_logger():
    """Create a test logger."""
    logger = logging.getLogger("test_debug")
    logger.setLevel(logging.INFO)
    return logger


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database with sample data."""
    db_path = tmp_path / "test_debug.db"
    db = DeckRommSyncDatabase(str(db_path))
    
    # Insert test configuration
    db.insert("config", ["config_key", "config_value"], ("romm_api_base_url", "http://test.com"))
    db.insert("config", ["config_key", "config_value"], ("romm_username", "testuser"))
    db.insert("config", ["config_key", "config_value"], ("romm_password", "testpass"))
    db.insert("config", ["config_key", "config_value"], ("steamdeck_retrodeck_path", "/test/path/"))
    
    # Insert test collection
    db.insert("collections", ["collections_id", "name", "rom_count", "cover", "collection_sync"],
             (1, "Test Collection", 1, "cover.jpg", 1))
    
    # Insert test platform
    db.insert("platforms_matching", ["romm_platform_id", "romm_platform_name", "steamdeck_platform_name"],
             (1, "Test Platform", "test_platform"))
    
    # Insert test ROM
    db.insert("roms", ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id", "sync_status"],
             (1, 1, "Test ROM", "http://cover.jpg", "test.rom", "test", 1, 0))
    
    yield str(db_path)


def test_debug_mode_initialization(debug_logger, tmp_path):
    """Test that BackgroundWorker initializes correctly with debug mode."""
    debug_folder = tmp_path / "debug_output"
    
    # Create worker with debug mode
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        assert worker.debug_mode is True
        assert worker.debug_output_folder == str(debug_folder)
        assert os.path.exists(debug_folder)


def test_debug_mode_disabled_by_default(debug_logger):
    """Test that debug mode is disabled by default."""
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger)
        
        assert worker.debug_mode is False


def test_save_rom_metadata(debug_logger, tmp_path):
    """Test that ROM metadata is saved correctly."""
    debug_folder = tmp_path / "debug_output"
    
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        # Test ROM data
        rom = {
            "roms_id": 123,
            "name": "Test ROM",
            "filename": "test.rom",
            "collections_id": 1,
            "platform_id": 2,
            "platform_fs_slug": "psx",
            "url_cover": "http://example.com/cover.jpg",
            "sync_status": 0
        }
        
        platform_info = {
            "romm_platform_id": 2,
            "romm_platform_name": "PlayStation",
            "steamdeck_platform_name": "psx"
        }
        
        download_path = "/path/to/roms/psx/"
        
        # Save metadata
        result = worker._save_rom_metadata(rom, platform_info, download_path)
        
        assert result is True
        
        # Check that file was created
        platform_folder = debug_folder / "psx"
        assert os.path.exists(platform_folder)
        
        # Find the JSON file
        json_files = list(platform_folder.glob("*.json"))
        assert len(json_files) == 1
        
        # Read and verify metadata
        with open(json_files[0], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        assert metadata["rom_id"] == 123
        assert metadata["name"] == "Test ROM"
        assert metadata["filename"] == "test.rom"
        assert metadata["platform"]["steamdeck_platform_name"] == "psx"
        assert metadata["download_path"] == download_path
        assert metadata["debug_mode"] is True
        assert "timestamp" in metadata


def test_save_rom_metadata_with_special_characters(debug_logger, tmp_path):
    """Test that ROM names with special characters are handled correctly."""
    debug_folder = tmp_path / "debug_output"
    
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        # ROM with special characters
        rom = {
            "roms_id": 456,
            "name": "Test: ROM/Game (USA) [!]",
            "filename": "test.rom",
            "collections_id": 1,
            "platform_id": 1,
            "platform_fs_slug": "nes",
            "url_cover": "",
            "sync_status": 0
        }
        
        platform_info = {
            "romm_platform_id": 1,
            "romm_platform_name": "NES",
            "steamdeck_platform_name": "nes"
        }
        
        result = worker._save_rom_metadata(rom, platform_info, "/path/")
        
        assert result is True
        
        # Check that file was created with sanitized name
        platform_folder = debug_folder / "nes"
        json_files = list(platform_folder.glob("*.json"))
        assert len(json_files) == 1
        
        # Filename should not contain special characters
        filename = json_files[0].name
        assert "/" not in filename
        assert ":" not in filename
        assert "[" not in filename
        assert "]" not in filename


def test_save_rom_metadata_creates_platform_folders(debug_logger, tmp_path):
    """Test that platform folders are created automatically."""
    debug_folder = tmp_path / "debug_output"
    
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        platforms = ["psx", "n64", "gba", "snes"]
        
        for idx, platform in enumerate(platforms):
            rom = {
                "roms_id": idx,
                "name": f"Test ROM {idx}",
                "filename": "test.rom",
                "collections_id": 1,
                "platform_id": idx,
                "platform_fs_slug": platform,
                "url_cover": "",
                "sync_status": 0
            }
            
            platform_info = {
                "romm_platform_id": idx,
                "romm_platform_name": platform.upper(),
                "steamdeck_platform_name": platform
            }
            
            worker._save_rom_metadata(rom, platform_info, "/path/")
        
        # Check that all platform folders were created
        for platform in platforms:
            platform_folder = debug_folder / platform
            assert os.path.exists(platform_folder)
            assert len(list(platform_folder.glob("*.json"))) == 1


def test_save_rom_metadata_error_handling(debug_logger, tmp_path):
    """Test that metadata save handles missing data gracefully."""
    debug_folder = tmp_path / "debug_output"
    
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        # ROM data with missing keys - should still create file with defaults
        rom = {}
        platform_info = {}
        
        result = worker._save_rom_metadata(rom, platform_info, "/path/")
        
        # Should succeed even with missing data (uses .get() defaults)
        assert result is True
        
        # Verify file was created with unknown platform
        unknown_folder = debug_folder / "unknown"
        assert os.path.exists(unknown_folder)
        json_files = list(unknown_folder.glob("*.json"))
        assert len(json_files) == 1


def test_debug_output_folder_creation(debug_logger, tmp_path):
    """Test that debug output folder is created on initialization."""
    debug_folder = tmp_path / "new_debug_folder" / "nested"
    
    assert not os.path.exists(debug_folder)
    
    with patch('classes.BackgroundWorker.DeckRommSyncDatabase') as mock_db:
        mock_db.return_value.select_as_dict.return_value = [
            {"config_key": "romm_api_base_url", "config_value": "http://test.com"},
            {"config_key": "romm_username", "config_value": "testuser"},
            {"config_key": "romm_password", "config_value": "testpass"}
        ]
        
        worker = BackgroundWorker("test.db", debug_logger, debug_mode=True, debug_output_folder=str(debug_folder))
        
        assert os.path.exists(debug_folder)
