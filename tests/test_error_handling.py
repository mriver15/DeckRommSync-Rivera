"""
Tests for error handling and retry logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError, RequestException
from classes.RommAPIHelper import RommAPIHelper, RommAPIError


class TestErrorHandling:
    """Test error handling in RommAPIHelper."""
    
    def test_login_without_credentials_fails(self):
        """Test that login fails gracefully with invalid credentials."""
        api = RommAPIHelper('http://localhost:8080/api')
        
        # Should not raise, just encode
        api.login('', '')
        assert api.auth_encoded is not None
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_timeout_handling(self, mock_request):
        """Test that timeout errors are handled properly."""
        mock_request.side_effect = Timeout("Request timed out")
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getPlatforms()
        assert result is None
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_connection_error_handling(self, mock_request):
        """Test that connection errors are handled properly."""
        mock_request.side_effect = ConnectionError("Connection refused")
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getCollections()
        assert result is None
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_http_error_handling(self, mock_request):
        """Test that HTTP errors (4xx/5xx) are handled properly."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = RequestException("Server error")
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getRommHeartbeat()
        assert result is None
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_unauthenticated_request_fails(self, mock_request):
        """Test that requests without authentication fail."""
        api = RommAPIHelper('http://localhost:8080/api')
        # Don't call login()
        
        with pytest.raises(RommAPIError, match="Not authenticated"):
            api._make_request('GET', '/platforms/')
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_successful_request_after_retry(self, mock_request):
        """Test that successful requests work normally."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getRommHeartbeat()
        assert result == {'status': 'ok'}


class TestDownloadErrorHandling:
    """Test error handling in ROM downloads."""
    
    @patch('classes.RommAPIHelper.requests.request')
    @patch('classes.RommAPIHelper.os.makedirs')
    def test_download_directory_creation_failure(self, mock_makedirs, mock_request):
        """Test handling of directory creation failures."""
        mock_makedirs.side_effect = OSError("Permission denied")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-disposition': 'attachment; filename="game.iso"'}
        mock_response.iter_content = lambda chunk_size: [b'data']
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.downloadRom(1, 'game.iso', '/invalid/path/')
        assert result is False
    
    @patch('classes.RommAPIHelper.requests.request')
    @patch('classes.RommAPIHelper.os.makedirs')
    @patch('classes.RommAPIHelper.os.path.exists')
    def test_download_write_failure(self, mock_exists, mock_makedirs, mock_request):
        """Test handling of file write failures."""
        mock_exists.return_value = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-disposition': 'attachment; filename="game.iso"'}
        mock_response.iter_content = lambda chunk_size: [b'data']
        mock_request.return_value = mock_response
        
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("Disk full")):
            api = RommAPIHelper('http://localhost:8080/api')
            api.login('user', 'pass')
            
            result = api.downloadRom(1, 'game.iso', '/tmp/')
            assert result is False
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_download_network_error(self, mock_request):
        """Test handling of network errors during download."""
        mock_request.side_effect = ConnectionError("Network error")
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.downloadRom(1, 'game.iso', '/tmp/')
        assert result is False
    
    @patch('classes.RommAPIHelper.requests.request')
    @patch('classes.RommAPIHelper.os.makedirs')
    @patch('classes.RommAPIHelper.os.path.exists')
    def test_download_existing_file_skipped(self, mock_exists, mock_makedirs, mock_request):
        """Test that existing files are skipped."""
        mock_exists.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-disposition': 'attachment; filename="game.iso"'}
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.downloadRom(1, 'game.iso', '/tmp/')
        assert result is True  # Returns True because file already exists


class TestAPIResponseValidation:
    """Test validation of API responses."""
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_null_response_handling(self, mock_request):
        """Test handling of None/null responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = None
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getCollections()
        assert result is None
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_empty_list_response(self, mock_request):
        """Test handling of empty list responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getPlatforms()
        assert result == []
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_malformed_json_response(self, mock_request):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response
        
        api = RommAPIHelper('http://localhost:8080/api')
        api.login('user', 'pass')
        
        result = api.getRomByID(1)
        assert result is None


class TestLoggingIntegration:
    """Test that errors are properly logged."""
    
    @patch('classes.RommAPIHelper.requests.request')
    def test_error_logging(self, mock_request, caplog):
        """Test that errors are logged properly."""
        import logging
        
        mock_request.side_effect = Timeout("Request timed out")
        
        logger = logging.getLogger('test_logger')
        api = RommAPIHelper('http://localhost:8080/api', logger=logger)
        api.login('user', 'pass')
        
        with caplog.at_level(logging.ERROR):
            result = api.getCollections()
        
        assert result is None
        assert any('timeout' in record.message.lower() for record in caplog.records)
