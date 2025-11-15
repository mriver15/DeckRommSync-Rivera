"""
Unit tests for RommAPIHelper class
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from classes.RommAPIHelper import RommAPIHelper


class TestRommAPIInitialization:
    """Test RommAPIHelper initialization."""
    
    def test_init_sets_base_url(self):
        """Test that initialization sets base URL."""
        api = RommAPIHelper('http://localhost:8080/api')
        assert api.api_base_url == 'http://localhost:8080/api'


class TestLogin:
    """Test login functionality."""
    
    def test_login_encodes_credentials(self):
        """Test that login properly encodes credentials."""
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('testuser', 'testpass')
        
        # Verify auth_encoded is set
        assert hasattr(api, 'auth_encoded')
        assert api.auth_encoded is not None
        
        # Decode and verify
        from base64 import b64decode
        decoded = b64decode(api.auth_encoded).decode()
        assert decoded == 'testuser:testpass'


class TestGetHeartbeat:
    """Test heartbeat endpoint."""
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_heartbeat_success(self, mock_make_request):
        """Test successful heartbeat response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_make_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.getRommHeartbeat()
        
        assert result == {'status': 'ok'}
        mock_make_request.assert_called_once()
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_heartbeat_failure(self, mock_make_request):
        """Test failed heartbeat response."""
        from classes.RommAPIHelper import RommAPIError
        mock_make_request.side_effect = RommAPIError("Connection error")
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.getRommHeartbeat()
        
        assert result is None


class TestGetCollections:
    """Test collections endpoint."""
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_get_collections_success(self, mock_make_request):
        """Test successful collections retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Collection 1'},
            {'id': 2, 'name': 'Collection 2'}
        ]
        mock_make_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.getCollections()
        
        assert len(result) == 2
        assert result[0]['name'] == 'Collection 1'


class TestGetPlatforms:
    """Test platforms endpoint."""
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_get_platforms_success(self, mock_make_request):
        """Test successful platforms retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'name': 'PlayStation'},
            {'id': 2, 'name': 'Nintendo 64'}
        ]
        mock_make_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.getPlatforms()
        
        assert len(result) == 2
        assert result[0]['name'] == 'PlayStation'


class TestGetRomByID:
    """Test ROM detail endpoint."""
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_get_rom_by_id_success(self, mock_make_request):
        """Test successful ROM retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Test Game',
            'fs_name': 'test_game.iso'
        }
        mock_make_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.getRomByID(1)
        
        assert result['id'] == 1
        assert result['name'] == 'Test Game'


class TestDownloadRom:
    """Test ROM download functionality."""
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    @patch('classes.RommAPIHelper.os.makedirs')
    @patch('classes.RommAPIHelper.os.path.exists')
    def test_download_rom_new_file(self, mock_exists, mock_makedirs, mock_make_request):
        """Test downloading a new ROM file."""
        # Setup mocks
        mock_exists.return_value = False  # File doesn't exist
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-disposition': 'attachment; filename="game.iso"'}
        mock_response.iter_content = lambda chunk_size: [b'test data']
        mock_make_request.return_value = mock_response
        
        # Mock file writing
        mock_open = MagicMock()
        with patch('builtins.open', mock_open):
            api = RommAPIHelper('http://localhost:8080/api')
            api.login('user', 'pass')
            result = api.downloadRom(1, 'game.iso', '/tmp/')
        
        # Verify directory creation was called
        mock_makedirs.assert_called_once_with('/tmp/', exist_ok=True)
        # Verify file was opened for writing
        mock_open.assert_called_once()
        assert result is True
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    @patch('classes.RommAPIHelper.os.path.exists')
    def test_download_rom_file_exists(self, mock_exists, mock_make_request):
        """Test skipping download when file exists."""
        mock_exists.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-disposition': 'attachment; filename="game.iso"'}
        mock_make_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.downloadRom(1, 'game.iso', '/tmp/')
        
        assert result is True
    
    @patch('classes.RommAPIHelper.RommAPIHelper._make_request')
    def test_download_rom_error(self, mock_make_request):
        """Test ROM download error handling."""
        from classes.RommAPIHelper import RommAPIError
        mock_make_request.side_effect = RommAPIError("Not found")
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        result = api.downloadRom(1, 'game.iso', '/tmp/')
        
        assert result is False
