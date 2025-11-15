import requests
from base64 import b64encode
import os
import urllib.parse
import logging
from typing import Optional, Dict, List, Any
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime, timedelta

class RommAPIError(Exception):
    """Base exception for RomM API errors."""
    pass

class RommAPIHelper:
    def __init__(self, api_base_url: str, timeout: int = 30, logger: Optional[logging.Logger] = None, db=None):
        self.api_base_url = api_base_url
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.db = db
        
        # Authentication state
        self.auth_encoded = None
        self.use_oauth = False
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.scopes = None
        
        # Try to load existing OAuth token from database
        if self.db:
            self._load_token_from_db()        
    
    def login(self, username: str, password: str, use_oauth: bool = False, scopes: Optional[List[str]] = None) -> None:
        """
        Authenticate with RomM API using OAuth2 or Basic Auth.
        
        Args:
            username: RomM username
            password: RomM password
            use_oauth: Use OAuth2 instead of Basic Auth (default: False)
            scopes: OAuth2 scopes (e.g., ['platforms.read', 'roms.read'])
        """
        if use_oauth:
            self._login_oauth(username, password, scopes or [])
        else:
            self._login_basic(username, password)
    
    def _login_basic(self, username: str, password: str) -> None:
        """
        Authenticate with RomM API using Basic Auth.
        
        Args:
            username: RomM username
            password: RomM password
        """
        try:
            auth_string = f"{username}:{password}"
            self.auth_encoded = b64encode(auth_string.encode()).decode()
            self.use_oauth = False
            self.logger.info("Successfully authenticated with RomM API (Basic Auth)")
        except Exception as e:
            self.logger.error(f"Failed to encode credentials: {e}")
            raise RommAPIError(f"Authentication failed: {e}") from e
    
    def _login_oauth(self, username: str, password: str, scopes: List[str]) -> None:
        """
        Authenticate with RomM API using OAuth2 password grant.
        
        Args:
            username: RomM username
            password: RomM password
            scopes: List of OAuth2 scopes
        """
        try:
            url = self.api_base_url + '/token'
            data = {
                'grant_type': 'password',
                'username': username,
                'password': password,
                'scope': ' '.join(scopes)
            }
            
            response = requests.post(
                url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
            self.scopes = scopes
            self.use_oauth = True
            
            # Save token to database if available
            if self.db:
                self._save_token_to_db()
            
            self.logger.info(f"Successfully authenticated with RomM API (OAuth2) - Scopes: {', '.join(scopes)}")
            
        except RequestException as e:
            self.logger.error(f"OAuth2 authentication failed: {e}")
            raise RommAPIError(f"OAuth2 authentication failed: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during OAuth2 authentication: {e}")
            raise RommAPIError(f"OAuth2 authentication failed: {e}") from e
    
    def _refresh_access_token(self) -> None:
        """
        Refresh the OAuth2 access token using the refresh token.
        """
        if not self.refresh_token:
            raise RommAPIError("No refresh token available. Re-authentication required.")
        
        try:
            url = self.api_base_url + '/token'
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(
                url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Some OAuth2 implementations issue new refresh tokens
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
            
            # Save updated token to database
            if self.db:
                self._save_token_to_db()
            
            self.logger.info("Successfully refreshed OAuth2 access token")
            
        except RequestException as e:
            self.logger.error(f"Token refresh failed: {e}")
            raise RommAPIError(f"Token refresh failed: {e}") from e
    
    def _ensure_valid_token(self) -> None:
        """
        Ensure the OAuth2 token is valid, refreshing if necessary.
        """
        if not self.use_oauth:
            return
        
        if not self.access_token:
            raise RommAPIError("Not authenticated. Call login() first.")
        
        # Refresh token if it expires in less than 5 minutes
        if self.token_expiry and datetime.now() >= self.token_expiry - timedelta(minutes=5):
            self.logger.info("Access token expiring soon, refreshing...")
            self._refresh_access_token()
    
    def _save_token_to_db(self) -> None:
        """
        Save OAuth2 tokens to database.
        """
        if not self.db:
            return
        
        try:
            now = datetime.now().isoformat()
            
            # Delete old tokens first
            self.db.delete('oauth_tokens', condition='1=1')
            
            # Insert new token
            self.db.insert('oauth_tokens', {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': 'bearer',
                'expires_at': self.token_expiry.isoformat() if self.token_expiry else None,
                'scopes': ','.join(self.scopes) if self.scopes else '',
                'created_at': now,
                'updated_at': now
            })
            
        except Exception as e:
            self.logger.error(f"Failed to save token to database: {e}")
    
    def _load_token_from_db(self) -> None:
        """
        Load OAuth2 tokens from database.
        """
        if not self.db:
            return
        
        try:
            tokens = self.db.select('oauth_tokens', order_by='id DESC', limit=1)
            if tokens:
                token = tokens[0]
                self.access_token = token.get('access_token')
                self.refresh_token = token.get('refresh_token')
                expires_at = token.get('expires_at')
                if expires_at:
                    self.token_expiry = datetime.fromisoformat(expires_at)
                scopes_str = token.get('scopes', '')
                self.scopes = scopes_str.split(',') if scopes_str else []
                self.use_oauth = True if self.access_token else False
                
                # Check if token is expired
                if self.token_expiry and datetime.now() >= self.token_expiry:
                    self.logger.info("Loaded token is expired, will need refresh")
                else:
                    self.logger.info("Successfully loaded OAuth2 token from database")
                    
        except Exception as e:
            self.logger.error(f"Failed to load token from database: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with error handling and automatic token refresh.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            RommAPIError: If request fails
        """
        # Ensure authentication
        if self.use_oauth:
            self._ensure_valid_token()
            if not self.access_token:
                raise RommAPIError("Not authenticated. Call login() first.")
        else:
            if not self.auth_encoded:
                raise RommAPIError("Not authenticated. Call login() first.")
        
        url = self.api_base_url + endpoint
        headers = kwargs.pop('headers', {})
        
        # Set authentication header based on auth method
        if self.use_oauth:
            headers.update({
                "accept": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            })
        else:
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
    
    # Save Files API Methods
    
    def getSavesByRomID(self, romID: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all save files for a specific ROM.
        
        Args:
            romID: ROM ID
            
        Returns:
            List of save file dicts or None if failed
        """
        try:
            response = self._make_request('GET', f'/saves?rom_id={romID}')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get saves for ROM {romID}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting saves for ROM {romID}: {e}")
            return None
    
    def downloadSave(self, saveID: int, download_path: str) -> bool:
        """
        Download a save file.
        
        Args:
            saveID: Save file ID
            download_path: Full path where save file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f'/saves/{saveID}/content'
            response = self._make_request('GET', endpoint, stream=True)
            
            # Get filename from response headers
            content_disposition = response.headers.get("content-disposition")
            if content_disposition and "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
                filename = urllib.parse.unquote(filename)
            else:
                filename = os.path.basename(download_path)
            
            # Ensure directory exists
            directory = os.path.dirname(download_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            # Download file
            with open(download_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            self.logger.info(f"Successfully downloaded save: {download_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download save {saveID}: {e}")
            # Clean up partial file
            if os.path.exists(download_path):
                try:
                    os.remove(download_path)
                except:
                    pass
            return False
    
    def uploadSave(self, romID: int, save_file_path: str, emulator: str = None) -> Optional[Dict[str, Any]]:
        """
        Upload a save file to RomM.
        
        Args:
            romID: ROM ID
            save_file_path: Path to the save file
            emulator: Emulator name (optional)
            
        Returns:
            Created save metadata dict or None if failed
        """
        try:
            if not os.path.exists(save_file_path):
                self.logger.error(f"Save file not found: {save_file_path}")
                return None
            
            endpoint = f'/saves'
            
            # Prepare multipart form data
            files = {
                'file': (os.path.basename(save_file_path), open(save_file_path, 'rb'), 'application/octet-stream')
            }
            
            data = {
                'rom_id': romID
            }
            
            if emulator:
                data['emulator'] = emulator
            
            # Override headers for multipart upload
            headers = {
                "accept": "application/json",
                "Authorization": f"Basic {self.auth_encoded}"
            }
            
            response = requests.post(
                self.api_base_url + endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            self.logger.info(f"Successfully uploaded save for ROM {romID}")
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to upload save for ROM {romID}: {e}")
            return None
        finally:
            # Close file if it was opened
            if 'files' in locals() and files.get('file'):
                try:
                    files['file'][1].close()
                except:
                    pass
    
    # Save States API Methods
    
    def getStatesByRomID(self, romID: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get all save states for a specific ROM.
        
        Args:
            romID: ROM ID
            
        Returns:
            List of save state dicts or None if failed
        """
        try:
            response = self._make_request('GET', f'/states?rom_id={romID}')
            return response.json()
        except RommAPIError as e:
            self.logger.error(f"Failed to get states for ROM {romID}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting states for ROM {romID}: {e}")
            return None
    
    def downloadState(self, stateID: int, download_path: str) -> bool:
        """
        Download a save state file.
        
        Args:
            stateID: Save state ID
            download_path: Full path where state file should be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f'/states/{stateID}/content'
            response = self._make_request('GET', endpoint, stream=True)
            
            # Ensure directory exists
            directory = os.path.dirname(download_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            # Download file
            with open(download_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
            
            self.logger.info(f"Successfully downloaded state: {download_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download state {stateID}: {e}")
            # Clean up partial file
            if os.path.exists(download_path):
                try:
                    os.remove(download_path)
                except:
                    pass
            return False
    
    def uploadState(self, romID: int, state_file_path: str, emulator: str = None) -> Optional[Dict[str, Any]]:
        """
        Upload a save state to RomM.
        
        Args:
            romID: ROM ID
            state_file_path: Path to the state file
            emulator: Emulator name (optional)
            
        Returns:
            Created state metadata dict or None if failed
        """
        try:
            if not os.path.exists(state_file_path):
                self.logger.error(f"State file not found: {state_file_path}")
                return None
            
            endpoint = f'/states'
            
            # Prepare multipart form data
            files = {
                'file': (os.path.basename(state_file_path), open(state_file_path, 'rb'), 'application/octet-stream')
            }
            
            data = {
                'rom_id': romID
            }
            
            if emulator:
                data['emulator'] = emulator
            
            # Ensure valid authentication
            if self.use_oauth:
                self._ensure_valid_token()
                auth_header = f"Bearer {self.access_token}"
            else:
                auth_header = f"Basic {self.auth_encoded}"
            
            # Override headers for multipart upload
            headers = {
                "accept": "application/json",
                "Authorization": auth_header
            }
            
            response = requests.post(
                self.api_base_url + endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            self.logger.info(f"Successfully uploaded state for ROM {romID}")
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to upload state for ROM {romID}: {e}")
            return None
        finally:
            # Close file if it was opened
            if 'files' in locals() and files.get('file'):
                try:
                    files['file'][1].close()
                except:
                    pass
 
