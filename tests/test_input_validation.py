"""
Tests for input validation functionality.
"""
import pytest
from classes.InputValidator import InputValidator, ValidationError


class TestURLValidation:
    """Test URL validation."""
    
    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        url = InputValidator.validate_url("http://example.com")
        assert url == "http://example.com"
    
    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        url = InputValidator.validate_url("https://example.com/api")
        assert url == "https://example.com/api"
    
    def test_valid_url_with_port(self):
        """Test URL with port number."""
        url = InputValidator.validate_url("http://localhost:8080/api")
        assert url == "http://localhost:8080/api"
    
    def test_valid_ip_address_url(self):
        """Test URL with IP address."""
        url = InputValidator.validate_url("http://192.168.1.100:5000")
        assert url == "http://192.168.1.100:5000"
    
    def test_url_trailing_slash_removed(self):
        """Test that trailing slash is removed."""
        url = InputValidator.validate_url("https://example.com/")
        assert url == "https://example.com"
    
    def test_empty_url_fails(self):
        """Test that empty URL fails validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_url("")
    
    def test_none_url_fails(self):
        """Test that None URL fails validation."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_url(None)
    
    def test_invalid_url_no_scheme(self):
        """Test that URL without scheme fails."""
        with pytest.raises(ValidationError, match="not a valid URL"):
            InputValidator.validate_url("example.com")
    
    def test_invalid_url_wrong_scheme(self):
        """Test that URL with wrong scheme fails."""
        with pytest.raises(ValidationError, match="not a valid URL"):
            InputValidator.validate_url("ftp://example.com")
    
    def test_url_with_whitespace_trimmed(self):
        """Test that whitespace is trimmed."""
        url = InputValidator.validate_url("  https://example.com  ")
        assert url == "https://example.com"


class TestUsernameValidation:
    """Test username validation."""
    
    def test_valid_username_letters(self):
        """Test valid username with letters."""
        username = InputValidator.validate_username("testuser")
        assert username == "testuser"
    
    def test_valid_username_with_numbers(self):
        """Test valid username with numbers."""
        username = InputValidator.validate_username("user123")
        assert username == "user123"
    
    def test_valid_username_with_underscore(self):
        """Test valid username with underscore."""
        username = InputValidator.validate_username("test_user")
        assert username == "test_user"
    
    def test_valid_username_with_dash(self):
        """Test valid username with dash."""
        username = InputValidator.validate_username("test-user")
        assert username == "test-user"
    
    def test_username_min_length(self):
        """Test minimum username length."""
        username = InputValidator.validate_username("abc")
        assert username == "abc"
    
    def test_username_too_short_fails(self):
        """Test that too short username fails."""
        with pytest.raises(ValidationError, match="3-50 characters"):
            InputValidator.validate_username("ab")
    
    def test_username_too_long_fails(self):
        """Test that too long username fails."""
        with pytest.raises(ValidationError, match="3-50 characters"):
            InputValidator.validate_username("a" * 51)
    
    def test_username_with_spaces_fails(self):
        """Test that username with spaces fails."""
        with pytest.raises(ValidationError, match="3-50 characters"):
            InputValidator.validate_username("test user")
    
    def test_username_with_special_chars_fails(self):
        """Test that username with special chars fails."""
        with pytest.raises(ValidationError, match="3-50 characters"):
            InputValidator.validate_username("test@user")
    
    def test_empty_username_fails(self):
        """Test that empty username fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_username("")


class TestPasswordValidation:
    """Test password validation."""
    
    def test_valid_password(self):
        """Test valid password."""
        password = InputValidator.validate_password("mypassword123")
        assert password == "mypassword123"
    
    def test_password_with_special_chars(self):
        """Test password with special characters."""
        password = InputValidator.validate_password("P@ssw0rd!")
        assert password == "P@ssw0rd!"
    
    def test_password_with_spaces(self):
        """Test password with spaces (should be preserved)."""
        password = InputValidator.validate_password("my password")
        assert password == "my password"
    
    def test_password_min_length_custom(self):
        """Test password with custom minimum length."""
        password = InputValidator.validate_password("12345678", min_length=8)
        assert password == "12345678"
    
    def test_password_too_short_fails(self):
        """Test that password shorter than min fails."""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            InputValidator.validate_password("1234", min_length=8)
    
    def test_password_too_long_fails(self):
        """Test that password longer than 255 chars fails."""
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_password("a" * 256)
    
    def test_password_with_null_byte_fails(self):
        """Test that password with null byte fails."""
        with pytest.raises(ValidationError, match="invalid characters"):
            InputValidator.validate_password("pass\x00word")
    
    def test_none_password_fails(self):
        """Test that None password fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_password(None)


class TestPlatformNameValidation:
    """Test platform name validation."""
    
    def test_valid_platform_name(self):
        """Test valid platform name."""
        name = InputValidator.validate_platform_name("PlayStation 2")
        assert name == "PlayStation 2"
    
    def test_platform_name_with_slash(self):
        """Test platform name with slash."""
        name = InputValidator.validate_platform_name("NES/SNES")
        assert name == "NES/SNES"
    
    def test_platform_name_with_dash(self):
        """Test platform name with dash."""
        name = InputValidator.validate_platform_name("Game-Boy")
        assert name == "Game-Boy"
    
    def test_platform_name_with_underscore(self):
        """Test platform name with underscore."""
        name = InputValidator.validate_platform_name("retro_games")
        assert name == "retro_games"
    
    def test_empty_platform_name_fails(self):
        """Test that empty platform name fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_platform_name("")
    
    def test_platform_name_too_long_fails(self):
        """Test that too long platform name fails."""
        with pytest.raises(ValidationError, match="1-100 characters"):
            InputValidator.validate_platform_name("a" * 101)
    
    def test_platform_name_with_special_chars_fails(self):
        """Test that platform name with special chars fails."""
        with pytest.raises(ValidationError, match="1-100 characters"):
            InputValidator.validate_platform_name("PlayStation@2")


class TestPathValidation:
    """Test file path validation."""
    
    def test_valid_unix_path(self):
        """Test valid Unix path."""
        path = InputValidator.validate_path("/home/user/roms")
        assert path == "/home/user/roms"
    
    def test_valid_windows_path(self):
        """Test valid Windows path."""
        path = InputValidator.validate_path("C:\\Users\\Test\\ROMs")
        assert path == "C:\\Users\\Test\\ROMs"
    
    def test_valid_relative_path(self):
        """Test valid relative path."""
        path = InputValidator.validate_path("./roms/ps2")
        assert path == "./roms/ps2"
    
    def test_empty_path_fails(self):
        """Test that empty path fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_path("")
    
    def test_path_with_null_byte_fails(self):
        """Test that path with null byte fails."""
        with pytest.raises(ValidationError, match="invalid control characters"):
            InputValidator.validate_path("/home/user\x00/roms")
    
    def test_path_too_long_fails(self):
        """Test that path longer than 1024 chars fails."""
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.validate_path("/" + "a" * 1024)
    
    def test_path_with_control_chars_fails(self):
        """Test that path with control characters fails."""
        with pytest.raises(ValidationError, match="invalid control characters"):
            InputValidator.validate_path("/home/user\x01/roms")


class TestIntegerValidation:
    """Test integer validation."""
    
    def test_valid_integer(self):
        """Test valid integer string."""
        value = InputValidator.validate_integer("42")
        assert value == 42
    
    def test_negative_integer(self):
        """Test negative integer."""
        value = InputValidator.validate_integer("-10")
        assert value == -10
    
    def test_integer_with_min_value(self):
        """Test integer with minimum value constraint."""
        value = InputValidator.validate_integer("10", min_val=5)
        assert value == 10
    
    def test_integer_with_max_value(self):
        """Test integer with maximum value constraint."""
        value = InputValidator.validate_integer("10", max_val=20)
        assert value == 10
    
    def test_integer_below_min_fails(self):
        """Test that integer below minimum fails."""
        with pytest.raises(ValidationError, match="at least 10"):
            InputValidator.validate_integer("5", min_val=10)
    
    def test_integer_above_max_fails(self):
        """Test that integer above maximum fails."""
        with pytest.raises(ValidationError, match="at most 10"):
            InputValidator.validate_integer("15", max_val=10)
    
    def test_non_integer_fails(self):
        """Test that non-integer string fails."""
        with pytest.raises(ValidationError, match="valid integer"):
            InputValidator.validate_integer("not a number")
    
    def test_float_fails(self):
        """Test that float string fails."""
        with pytest.raises(ValidationError, match="valid integer"):
            InputValidator.validate_integer("3.14")
    
    def test_empty_integer_fails(self):
        """Test that empty string fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            InputValidator.validate_integer("")


class TestSpecializedValidators:
    """Test specialized ID validators."""
    
    def test_valid_collection_id(self):
        """Test valid collection ID."""
        id_val = InputValidator.validate_collection_id("123")
        assert id_val == 123
    
    def test_collection_id_zero_fails(self):
        """Test that collection ID 0 fails."""
        with pytest.raises(ValidationError, match="at least 1"):
            InputValidator.validate_collection_id("0")
    
    def test_valid_rom_id(self):
        """Test valid ROM ID."""
        id_val = InputValidator.validate_rom_id("456")
        assert id_val == 456
    
    def test_rom_id_negative_fails(self):
        """Test that negative ROM ID fails."""
        with pytest.raises(ValidationError, match="at least 1"):
            InputValidator.validate_rom_id("-1")
    
    def test_valid_platform_id(self):
        """Test valid platform ID."""
        id_val = InputValidator.validate_platform_id("789")
        assert id_val == 789


class TestSanitizeString:
    """Test string sanitization."""
    
    def test_sanitize_normal_string(self):
        """Test sanitizing normal string."""
        result = InputValidator.sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_string_with_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        result = InputValidator.sanitize_string("  Hello  ")
        assert result == "Hello"
    
    def test_sanitize_string_removes_control_chars(self):
        """Test that control characters are removed."""
        result = InputValidator.sanitize_string("Hello\x00\x01World")
        assert result == "HelloWorld"
    
    def test_sanitize_string_preserves_newlines(self):
        """Test that newlines are preserved."""
        result = InputValidator.sanitize_string("Line1\nLine2")
        assert result == "Line1\nLine2"
    
    def test_sanitize_string_too_long_fails(self):
        """Test that too long string fails."""
        with pytest.raises(ValidationError, match="too long"):
            InputValidator.sanitize_string("a" * 1001, max_length=1000)
    
    def test_sanitize_none_returns_empty(self):
        """Test that None returns empty string."""
        result = InputValidator.sanitize_string(None)
        assert result == ""
