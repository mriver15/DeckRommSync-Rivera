"""
Input validation utilities for form data and API inputs.
"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates user inputs to prevent injection attacks and ensure data integrity."""
    
    # Regex patterns
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    # Username: alphanumeric, underscore, dash, 3-50 chars
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    
    # Platform name: alphanumeric, spaces, dash, slash, 1-100 chars
    PLATFORM_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9 _\-/]{1,100}$')
    
    # File path: allow most chars but prevent null bytes and control chars
    PATH_PATTERN = re.compile(r'^[^\x00-\x1f\x7f]+$')
    
    @staticmethod
    def validate_url(url: Optional[str], field_name: str = "URL") -> str:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            field_name: Name of the field for error messages
            
        Returns:
            Cleaned URL string
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError(f"{field_name} cannot be empty")
        
        url = url.strip()
        
        if not InputValidator.URL_PATTERN.match(url):
            raise ValidationError(f"{field_name} is not a valid URL. Must start with http:// or https://")
        
        # Additional check using urlparse
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValidationError(f"{field_name} is missing scheme or network location")
        except Exception:
            raise ValidationError(f"{field_name} format is invalid")
        
        # Remove trailing slash for consistency
        if url.endswith('/'):
            url = url.rstrip('/')
        
        return url
    
    @staticmethod
    def validate_username(username: Optional[str], field_name: str = "Username") -> str:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            field_name: Name of the field for error messages
            
        Returns:
            Cleaned username string
            
        Raises:
            ValidationError: If username is invalid
        """
        if not username:
            raise ValidationError(f"{field_name} cannot be empty")
        
        username = username.strip()
        
        if not InputValidator.USERNAME_PATTERN.match(username):
            raise ValidationError(
                f"{field_name} must be 3-50 characters and contain only letters, "
                "numbers, underscores, or dashes"
            )
        
        return username
    
    @staticmethod
    def validate_password(password: Optional[str], field_name: str = "Password", min_length: int = 1) -> str:
        """
        Validate password.
        
        Args:
            password: Password to validate
            field_name: Name of the field for error messages
            min_length: Minimum password length (default 1 for backward compatibility)
            
        Returns:
            Password string (not stripped to preserve spaces)
            
        Raises:
            ValidationError: If password is invalid
        """
        if password is None:
            raise ValidationError(f"{field_name} cannot be empty")
        
        if len(password) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")
        
        if len(password) > 255:
            raise ValidationError(f"{field_name} is too long (max 255 characters)")
        
        # Check for null bytes
        if '\x00' in password:
            raise ValidationError(f"{field_name} contains invalid characters")
        
        return password
    
    @staticmethod
    def validate_platform_name(platform_name: Optional[str], field_name: str = "Platform name") -> str:
        """
        Validate platform name.
        
        Args:
            platform_name: Platform name to validate
            field_name: Name of the field for error messages
            
        Returns:
            Cleaned platform name string
            
        Raises:
            ValidationError: If platform name is invalid
        """
        if not platform_name:
            raise ValidationError(f"{field_name} cannot be empty")
        
        platform_name = platform_name.strip()
        
        if not InputValidator.PLATFORM_NAME_PATTERN.match(platform_name):
            raise ValidationError(
                f"{field_name} must be 1-100 characters and contain only letters, "
                "numbers, spaces, underscores, dashes, or slashes"
            )
        
        return platform_name
    
    @staticmethod
    def validate_path(path: Optional[str], field_name: str = "Path") -> str:
        """
        Validate file system path.
        
        Args:
            path: Path to validate
            field_name: Name of the field for error messages
            
        Returns:
            Cleaned path string
            
        Raises:
            ValidationError: If path is invalid
        """
        if not path:
            raise ValidationError(f"{field_name} cannot be empty")
        
        path = path.strip()
        
        if not InputValidator.PATH_PATTERN.match(path):
            raise ValidationError(f"{field_name} contains invalid control characters")
        
        if len(path) > 1024:
            raise ValidationError(f"{field_name} is too long (max 1024 characters)")
        
        # Check for null bytes
        if '\x00' in path:
            raise ValidationError(f"{field_name} contains null bytes")
        
        return path
    
    @staticmethod
    def validate_integer(value: Optional[str], field_name: str = "Value", 
                        min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """
        Validate and convert string to integer.
        
        Args:
            value: String value to convert
            field_name: Name of the field for error messages
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Integer value
            
        Raises:
            ValidationError: If value is invalid
        """
        if value is None or value == '':
            raise ValidationError(f"{field_name} cannot be empty")
        
        try:
            int_val = int(value)
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid integer")
        
        if min_val is not None and int_val < min_val:
            raise ValidationError(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and int_val > max_val:
            raise ValidationError(f"{field_name} must be at most {max_val}")
        
        return int_val
    
    @staticmethod
    def sanitize_string(value: Optional[str], max_length: int = 1000) -> str:
        """
        Sanitize a general string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If string is invalid
        """
        if value is None:
            return ""
        
        # Strip whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(f"Input is too long (max {max_length} characters)")
        
        # Remove null bytes and control characters (except newlines and tabs)
        value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', value)
        
        return value
    
    @staticmethod
    def validate_collection_id(collection_id: Optional[str]) -> int:
        """Validate collection ID."""
        return InputValidator.validate_integer(collection_id, "Collection ID", min_val=1)
    
    @staticmethod
    def validate_rom_id(rom_id: Optional[str]) -> int:
        """Validate ROM ID."""
        return InputValidator.validate_integer(rom_id, "ROM ID", min_val=1)
    
    @staticmethod
    def validate_platform_id(platform_id: Optional[str]) -> int:
        """Validate platform ID."""
        return InputValidator.validate_integer(platform_id, "Platform ID", min_val=1)
