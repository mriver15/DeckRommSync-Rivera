"""
Unit tests for Flask application routes and functionality
"""
import pytest
import json
from unittest.mock import patch, MagicMock


class TestAppImports:
    """Test that all imports work correctly."""
    
    def test_no_django_import(self):
        """Verify Django is not imported (Issue #1 fix)."""
        import app
        import sys
        
        # Check that django is not in the loaded modules from our app
        assert 'django' not in app.__dict__
        
    def test_required_imports_exist(self):
        """Verify all required imports are present."""
        import app
        
        # Check Flask is imported
        assert hasattr(app, 'Flask')
        assert hasattr(app, 'render_template')
        assert hasattr(app, 'request')
        assert hasattr(app, 'jsonify')
        
        # Check scheduler is imported
        assert hasattr(app, 'BackgroundScheduler')


class TestRoutes:
    """Test Flask routes."""
    
    def test_status_route_exists(self, client):
        """Test that the status route is accessible."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            # Mock database response
            mock_instance = MagicMock()
            mock_instance.select_as_dict.return_value = []
            mock_db.return_value = mock_instance
            
            response = client.get('/')
            assert response.status_code == 200
    
    def test_config_route_get(self, client):
        """Test GET request to config route."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_instance.select.return_value = []
            mock_instance.select_as_dict.return_value = []
            mock_db.return_value = mock_instance
            
            response = client.get('/config')
            assert response.status_code == 200
    
    def test_log_route_exists(self, client):
        """Test that the log route is accessible."""
        import os
        import logging
        
        # Create a temporary log file
        with open('background_worker.log', 'w') as f:
            f.write('Background Task started...\n')
            f.write('Test log entry\n')
        
        try:
            response = client.get('/log')
            assert response.status_code == 200
        finally:
            # Close all handlers first on Windows
            logger = logging.getLogger("background_worker")
            handlers = logger.handlers[:]
            for handler in handlers:
                handler.close()
                logger.removeHandler(handler)
            
            # Cleanup
            if os.path.exists('background_worker.log'):
                try:
                    os.remove('background_worker.log')
                except PermissionError:
                    pass  # File still in use, skip cleanup
    
    def test_log_route_missing_file(self, client):
        """Test log route when log file doesn't exist."""
        import os
        import logging
        
        # Close all handlers first
        logger = logging.getLogger("background_worker")
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)
        
        # Make sure log file doesn't exist
        if os.path.exists('background_worker.log'):
            try:
                os.remove('background_worker.log')
            except PermissionError:
                pass  # Skip if file is locked
        
        response = client.get('/log')
        assert response.status_code == 200  # Should still work, just show error message


class TestConfigEndpoints:
    """Test configuration update endpoints."""
    
    def test_romm_api_settings_update(self, client):
        """Test updating RomM API settings."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_db.return_value = mock_instance
            
            response = client.post('/config/config_romm_api_settings', data={
                'romm_api_base_url': 'http://test.com/api',
                'romm_username': 'testuser',
                'romm_password': 'testpass'
            })
            
            # Should redirect to config page
            assert response.status_code == 302
            assert response.location == '/config'
            
            # Verify update was called 3 times (once for each setting)
            assert mock_instance.update.call_count == 3
    
    def test_collection_sync_settings_update(self, client):
        """Test updating collection sync settings."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_db.return_value = mock_instance
            
            response = client.post('/config/config_collection_sync_settings', data={
                'collections_id': ['1', '2'],
                'collection_sync_1': 'on'
            })
            
            assert response.status_code == 302
            assert mock_instance.update.called
    
    def test_platform_matching_update(self, client):
        """Test updating platform matching."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_db.return_value = mock_instance
            
            response = client.post('/config/config_platform_matching', data={
                'romm_platform_id': '1',
                'steamdeck_platform_name': 'psx'
            })
            
            assert response.status_code == 302
            mock_instance.update.assert_called_once()
    
    def test_steamdeck_platform_path_update(self, client):
        """Test updating Steam Deck platform path."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_db.return_value = mock_instance
            
            response = client.post('/config/config_steamdeck_platform_path', data={
                'steamdeck_path': '/home/deck/retrodeck/roms/'
            })
            
            assert response.status_code == 302
            mock_instance.update.assert_called_once()


class TestDropdownEndpoints:
    """Test dropdown/API endpoints."""
    
    def test_reset_status_endpoint(self, client):
        """Test reset status API endpoint."""
        with patch('app.DeckRommSyncDatabase') as mock_db:
            mock_instance = MagicMock()
            mock_db.return_value = mock_instance
            
            response = client.post(
                '/dropdown/reset_status',
                data=json.dumps({'roms_id': 1}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert data['message'] == 'Status reset successfully'
            assert 'rom_id' in data
            assert data['rom_id'] == 1
            
            # Verify database update was called
            mock_instance.update.assert_called_once()


class TestLoadJsonConfig:
    """Test configuration loading."""
    
    def test_load_existing_config(self):
        """Test loading existing config.json."""
        import app
        import os
        
        # Create a temporary config file
        test_config = {
            "server": {"host": "127.0.0.1", "port": 5000},
            "database": {"name": "test.db", "type": "sqlite"}
        }
        
        with open('test_config.json', 'w') as f:
            json.dump(test_config, f)
        
        try:
            config = app.load_json_config('test_config.json')
            assert config == test_config
            assert config['server']['host'] == '127.0.0.1'
        finally:
            if os.path.exists('test_config.json'):
                os.remove('test_config.json')
    
    def test_load_missing_config(self):
        """Test loading non-existent config file."""
        import app
        
        config = app.load_json_config('nonexistent_config.json')
        assert config == {}


class TestBackgroundTask:
    """Test background task function."""
    
    def test_run_background_task(self):
        """Test that background task runs without errors."""
        from app import run_background_task
        
        with patch('app.BackgroundWorker') as mock_worker:
            mock_instance = MagicMock()
            mock_worker.return_value = mock_instance
            
            # Run the background task
            run_background_task()
            
            # Verify BackgroundWorker methods were called
            mock_instance.sync_rommCollections.assert_called_once()
            mock_instance.sync_copyRoms.assert_called_once()
