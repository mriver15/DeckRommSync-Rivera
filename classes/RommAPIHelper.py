import requests
from base64 import b64encode
import os
import urllib.parse
import logging
from typing import Optional, Dict, List, Any
from requests.exceptions import RequestException, Timeout, ConnectionError

class RommAPIError(Exception):
    """Base exception for RomM API errors."""
    pass

class RommAPIHelper:
    def __init__(self, api_base_url: str, timeout: int = 30, logger: Optional[logging.Logger] = None):
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.auth_encoded = None        
    
    def login(self, username: str, password: str) -> None:
        """
        Authenticate with RomM API using Basic Auth.
        
        Args:
            username: RomM username
            password: RomM password
        """
        try:
            auth_string = f"{username}:{password}"
            self.auth_encoded = b64encode(auth_string.encode()).decode()
            self.logger.info("Successfully authenticated with RomM API")
        except Exception as e:
            self.logger.error(f"Failed to encode credentials: {e}")
            raise RommAPIError(f"Authentication failed: {e}") from e
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            RommAPIError: If request fails
        """
        if not self.auth_encoded:
            raise RommAPIError("Not authenticated. Call login() first.")
        
        url = self.api_base_url + endpoint
        headers = kwargs.pop('headers', {})
        headers.update({
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self.auth_encoded}"
        })
        
        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
            return response
            
        except Timeout as e:
            self.logger.error(f"Request timeout for {endpoint}: {e}")
            raise RommAPIError(f"Request timeout: {endpoint}") from e
        except ConnectionError as e:
            self.logger.error(f"Connection error for {endpoint}: {e}")
            raise RommAPIError(f"Connection error: {endpoint}") from e
        except RequestException as e:
            self.logger.error(f"Request failed for {endpoint}: {e}")
            raise RommAPIError(f"Request failed: {endpoint} - {str(e)}") from e              

    # Heartbeat
    def getRommHeartbeat(self) -> Optional[Dict[str, Any]]:
        """
        Check RomM server health.
        
        Returns:
            Health status dict or None if failed
        """
        try:
            response = self._make_request('GET', '/heartbeat')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Heartbeat failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in heartbeat: {e}")
            return None
    
    
    def getCollections(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all collections from RomM.
        
        Returns:
            List of collections or None if failed
        """
        try:
            response = self._make_request('GET', '/collections/')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get collections: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting collections: {e}")
            return None

    def getCollectionByID(self, collectionID: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific collection by ID.
        
        Args:
            collectionID: Collection ID
            
        Returns:
            Collection dict or None if failed
        """
        try:
            response = self._make_request('GET', f'/collections/{collectionID}')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get collection {collectionID}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting collection {collectionID}: {e}")
            return None  

    
    def getPlatforms(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all gaming platforms from RomM.
        
        Returns:
            List of platforms or None if failed
        """
        try:
            response = self._make_request('GET', '/platforms/')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get platforms: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting platforms: {e}")
            return None
    
    def getRomByID(self, romID: int) -> Optional[Dict[str, Any]]:
        """
        Get ROM details by ID.
        
        Args:
            romID: ROM ID
            
        Returns:
            ROM dict or None if failed
        """
        try:
            response = self._make_request('GET', f'/roms/{romID}')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get ROM {romID}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting ROM {romID}: {e}")
            return None         

    def downloadRom(self, romID: int, romFilename: str, download_path: str) -> bool:
        """
        Download a ROM file.
        
        Args:
            romID: ROM ID
            romFilename: ROM filename
            download_path: Destination directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare URL
            endpoint = f'/roms/{romID}/content/{romFilename}'
            
            # Do HTTP GET Request with streaming
            response = self._make_request('GET', endpoint, stream=True)
            
            # Get Filename from HTTP-Request Response
            content_disposition = response.headers.get("content-disposition")
            if content_disposition and "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
                filename = urllib.parse.unquote(filename)  # Decodes %20 to space
            else:
                filename = romFilename

            # Make sure the Download Folder exists | If not, create it
            try:
                os.makedirs(download_path, exist_ok=True)
            except OSError as e:
                self.logger.error(f"Failed to create directory {download_path}: {e}")
                raise RommAPIError(f"Cannot create download directory: {e}") from e

            # Build file-path
            file_path = os.path.join(download_path, filename)

            # Check if File exists
            if os.path.exists(file_path):
                self.logger.info(f"File already exists: {file_path} – Download skipped.")
                return True
            
            # Download File in Chunks and save it
            try:
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            file.write(chunk)
                
                self.logger.info(f"Successfully downloaded: {file_path}")
                return True
                
            except IOError as e:
                self.logger.error(f"Failed to write file {file_path}: {e}")
                # Clean up partial file
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                raise RommAPIError(f"Failed to write file: {e}") from e
            
        except RommAPIError as e:
            self.logger.error(f"Failed to download ROM {romID}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading ROM {romID}: {e}")
            return False
 
