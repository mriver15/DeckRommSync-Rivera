from classes.RommAPIHelper import RommAPIHelper, RommAPIError
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase
import json
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class BackgroundWorker:
    def __init__(self, dbName: str, logger: logging.Logger, debug_mode: bool = False, debug_output_folder: str = "./debug_output", max_workers: int = 4):
        self.background_logger = logger
        self.dbName = dbName
        self.debug_mode = debug_mode
        self.debug_output_folder = debug_output_folder
        self.max_workers = max_workers
        self.stats_lock = Lock()  # Thread-safe stats updates
        
        # Create debug output folder if in debug mode
        if self.debug_mode:
            os.makedirs(self.debug_output_folder, exist_ok=True)
            self.background_logger.info(f"Debug mode enabled. Output folder: {self.debug_output_folder}")
        
        # Load RomM API configuration from database
        try:
            db = DeckRommSyncDatabase(dbName)
            configObj = db.select_as_dict("config")
            
            # Initialize with None
            self.romMAPIBaseUrl = None
            self.romMUsername = None
            self.romMPassword = None
            self.use_oauth = False
            self.oauth_scopes = []
            
            for config in configObj:            
                if config['config_key'] == 'romm_api_base_url':
                    self.romMAPIBaseUrl = config['config_value']
                elif config['config_key'] == 'romm_username':
                    self.romMUsername = config['config_value']
                elif config['config_key'] == 'romm_password':
                    self.romMPassword = config['config_value']
                elif config['config_key'] == 'use_oauth':
                    self.use_oauth = config['config_value'] == '1' or config['config_value'] == 'true'
                elif config['config_key'] == 'oauth_scopes':
                    self.oauth_scopes = config['config_value'].split(',') if config['config_value'] else []
            
            # Validate configuration
            if not all([self.romMAPIBaseUrl, self.romMUsername, self.romMPassword]):
                self.background_logger.error("Incomplete RomM configuration. Please configure API settings.")
                raise ValueError("Missing RomM API configuration")
                
        except Exception as e:
            self.background_logger.error(f"Failed to initialize BackgroundWorker: {e}")
            raise
        
        self.background_logger.info(f"BackgroundWorker initialized with {max_workers} concurrent workers")
    
    def _get_default_platform_folder(self, platform_name: str, platform_slug: str = "") -> str:
        """Get default platform folder name based on platform name or slug.
        
        Args:
            platform_name: Platform name from RomM
            platform_slug: Platform slug/fs_slug from RomM
            
        Returns:
            Default folder name for the platform
        """
        # Common platform mappings (lowercase for matching)
        platform_mappings = {
            # Sony
            'playstation': 'psx',
            'playstation 1': 'psx',
            'playstation 2': 'ps2',
            'playstation 3': 'ps3',
            'playstation portable': 'psp',
            'playstation vita': 'psvita',
            
            # Nintendo
            'nintendo entertainment system': 'nes',
            'super nintendo': 'snes',
            'super nintendo entertainment system': 'snes',
            'nintendo 64': 'n64',
            'nintendo gamecube': 'ngc',
            'gamecube': 'ngc',
            'nintendo wii': 'wii',
            'nintendo wii u': 'wiiu',
            'nintendo switch': 'switch',
            
            # Nintendo Handhelds
            'game boy': 'gb',
            'game boy color': 'gbc',
            'game boy advance': 'gba',
            'nintendo ds': 'nds',
            'nintendo 3ds': '3ds',
            
            # Sega
            'sega master system': 'mastersystem',
            'sega genesis': 'genesis',
            'sega mega drive': 'megadrive',
            'sega cd': 'segacd',
            'sega 32x': '32x',
            'sega saturn': 'saturn',
            'sega dreamcast': 'dreamcast',
            'dreamcast': 'dreamcast',
            'sega game gear': 'gamegear',
            
            # Microsoft
            'xbox': 'xbox',
            'xbox 360': 'xbox360',
            
            # Arcade
            'arcade': 'arcade',
            'mame': 'arcade',
            'neo geo': 'neogeo',
            'neo geo pocket': 'ngp',
            'neo geo pocket color': 'ngpc',
            
            # Other
            'atari 2600': 'atari2600',
            'atari 7800': 'atari7800',
            'atari lynx': 'lynx',
            'turbografx-16': 'tg16',
            'turbografx-cd': 'tgcd',
            'pc engine': 'pcengine',
            'pc engine cd': 'pcenginecd',
            'wonderswan': 'wonderswan',
            'wonderswan color': 'wonderswancolor',
            'virtual boy': 'virtualboy',
            'nec pc-98': 'pc98',
            'dos': 'dos',
            'amiga': 'amiga',
            'commodore 64': 'c64',
            'zx spectrum': 'zxspectrum',
            'msx': 'msx',
        }
        
        # Try to match by name first (case-insensitive)
        name_lower = platform_name.lower().strip()
        if name_lower in platform_mappings:
            return platform_mappings[name_lower]
        
        # If slug is provided and looks reasonable, use it
        if platform_slug and len(platform_slug) > 1:
            # Clean up slug (remove special chars, make lowercase)
            clean_slug = ''.join(c for c in platform_slug.lower() if c.isalnum())
            if clean_slug:
                return clean_slug
        
        # Fallback: create safe folder name from platform name
        safe_name = ''.join(c for c in platform_name.lower() if c.isalnum() or c == ' ')
        safe_name = safe_name.replace(' ', '_')
        return safe_name if safe_name else 'unknown'

    def sync_rommCollections(self):
        """Sync collections and platforms from RomM with error handling."""
        self.background_logger.info("Syncing RomM Collections - Starting")
        
        try:
            db = DeckRommSyncDatabase(self.dbName)
            
            # Create API helper with database for token management
            romm = RommAPIHelper(
                api_base_url=self.romMAPIBaseUrl,
                logger=self.background_logger,
                db=db
            )
            
            # Login using OAuth or Basic Auth
            if self.use_oauth:
                romm.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=True,
                    scopes=self.oauth_scopes or ['platforms.read', 'roms.read', 'collections.read']
                )
            else:
                romm.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=False
                )

            # Read Platforms from RomM
            platform_result = romm.getPlatforms()
            if platform_result is None:
                self.background_logger.error("Failed to fetch platforms from RomM")
                return
            
            platforms_synced = 0    
            for platform in platform_result:
                try:
                    platform_id = platform['id']
                    platform_name = platform['name']
                    platform_slug = platform.get('slug', '')
                    
                    # Check if platform already exists
                    existing = db.select_as_dict("platforms_matching", ['steamdeck_platform_name'], 
                                                'romm_platform_id = ?', (platform_id,))
                    
                    if not existing:
                        # New platform - set default folder name
                        default_folder = self._get_default_platform_folder(platform_name, platform_slug)
                        db.insert_or_replace("platforms_matching", 
                                           ["romm_platform_id", "romm_platform_name", "steamdeck_platform_name"], 
                                           (platform_id, platform_name, default_folder))
                        self.background_logger.info(f"New platform '{platform_name}' added with folder '{default_folder}'")
                    elif not existing[0].get('steamdeck_platform_name'):
                        # Existing platform without folder name - set default
                        default_folder = self._get_default_platform_folder(platform_name, platform_slug)
                        db.update("platforms_matching",
                                {"romm_platform_name": platform_name, "steamdeck_platform_name": default_folder},
                                "romm_platform_id = ?",
                                (platform_id,))
                        self.background_logger.info(f"Set default folder '{default_folder}' for platform '{platform_name}'")
                    else:
                        # Existing platform with folder name - only update the platform name, preserve folder
                        db.update("platforms_matching", 
                                {"romm_platform_name": platform_name},
                                "romm_platform_id = ?",
                                (platform_id,))
                    
                    platforms_synced += 1
                except Exception as e:
                    self.background_logger.warning(f"Failed to insert platform {platform.get('name', 'unknown')}: {e}")
            
            self.background_logger.info(f"Synced {platforms_synced} platforms")

            # Read Collections from RomM
            collection_result = romm.getCollections()
            if collection_result is None:
                self.background_logger.error("Failed to fetch collections from RomM")
                return
            
            collections_synced = 0
            roms_synced = 0

            # Go Through Collections and Insert them into the Database
            for collection in collection_result:
                try:
                    if isinstance(collection['path_covers_large'], list) and collection['path_covers_large']:
                        first_cover = collection['path_covers_large'][0]  # Safely get the first element
                    else:
                        first_cover = collection['path_covers_large']  # If it's not an array, just take the value        
                    
                    # Check if collection exists to preserve sync setting
                    existing = db.select_as_dict("collections", ['collection_sync'], 
                                                'collections_id = ?', (collection['id'],))
                    
                    if existing:
                        # Preserve existing collection_sync setting
                        sync_setting = existing[0]['collection_sync']
                        db.update("collections",
                                {"name": collection['name'], "rom_count": collection['rom_count'], "cover": first_cover},
                                "collections_id = ?",
                                (collection['id'],))
                    else:
                        # New collection - default to not synced
                        db.insert_or_replace("collections", ["collections_id", "name", "rom_count", "cover", "collection_sync"], 
                                            (collection['id'],
                                            collection['name'],
                                            collection['rom_count'],
                                            first_cover,
                                            0))
                    collections_synced += 1
                    
                    # Read ROMs from Collection
                    roms = collection.get('rom_ids', [])
                    for rom_id in roms:
                        try:
                            romObj = romm.getRomByID(rom_id)
                            if romObj is None:
                                self.background_logger.warning(f"Failed to fetch ROM {rom_id}")
                                continue
                                
                            filename = romObj.get('fs_name', '')
                            if not filename:
                                self.background_logger.warning(f"ROM {rom_id} has no filename, skipping")
                                continue
                            
                            # Get cover image URL - RomM v3+ uses different field names than older versions
                            # Try multiple sources in order of preference
                            cover_url = ''
                            base_url = self.romMAPIBaseUrl.replace('/api', '')
                            
                            # Try different cover image fields (RomM API variations)
                            if romObj.get('path_cover_l'):
                                cover_url = f"{base_url}{romObj['path_cover_l']}"
                            elif romObj.get('path_cover_s'):
                                cover_url = f"{base_url}{romObj['path_cover_s']}"
                            elif romObj.get('url_cover'):
                                cover_url = romObj['url_cover']
                            elif romObj.get('cover_path'):
                                cover_url = f"{base_url}{romObj['cover_path']}"
                            elif romObj.get('cover'):
                                # Some RomM versions return just 'cover' field
                                cover_path = romObj['cover']
                                if cover_path and not cover_path.startswith('http'):
                                    cover_url = f"{base_url}{cover_path}"
                                else:
                                    cover_url = cover_path or ''
                            
                            # Log if no cover found for debugging
                            if not cover_url:
                                self.background_logger.debug(f"No cover image found for ROM {rom_id} ({romObj.get('name', 'unknown')})")
                                         
                            # Insert ROM (using insert_or_replace to handle duplicates)
                            db.insert_or_replace("roms", ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                                               (romObj['id'],
                                               collection['id'],
                                               romObj['name'],
                                               cover_url,
                                               filename,
                                               romObj.get('platform_fs_slug', ''),
                                               romObj.get('platform_id', 0)))
                            roms_synced += 1
                        except Exception as e:
                            self.background_logger.error(f"Failed to process ROM {rom_id}: {e}")
                            continue
                            
                except Exception as e:
                    self.background_logger.error(f"Failed to process collection {collection.get('name', 'unknown')}: {e}")
                    continue
            
            self.background_logger.info(f"Syncing RomM Collections - Finished ({collections_synced} collections, {roms_synced} ROMs)")
            
        except RommAPIError as e:
            self.background_logger.error(f"RomM API error during collection sync: {e}")
        except Exception as e:
            self.background_logger.error(f"Unexpected error during collection sync: {e}", exc_info=True)


    def sync_copyRoms(self):
        """Sync (download) ROMs with comprehensive error handling."""
        self.background_logger.info("Syncing ROMS - Starting")
        
        start_time = datetime.now()
        
        try:
            db = DeckRommSyncDatabase(self.dbName)
            
            # Create sync_history table if it doesn't exist
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

            # Get Collections to sync
            collections = db.select_as_dict("collections", ['*'], 'collection_sync = ?', (1,))
            if not collections:
                self.background_logger.info("No collections enabled for sync")
                return
            
            # Get Steamdeck Path
            steamdeck_path_result = db.select_as_dict("config", ['config_value'], 
                                                      'config_key = ?', ('steamdeck_retrodeck_path',))
            if not steamdeck_path_result:
                self.background_logger.error("Steam Deck path not configured")
                return
                
            steamdeck_path = steamdeck_path_result[0].get("config_value")
            if not steamdeck_path:
                self.background_logger.error("Steam Deck path is empty")
                return
            
            # Create API helper with database
            romm = RommAPIHelper(
                api_base_url=self.romMAPIBaseUrl,
                timeout=60,
                logger=self.background_logger,
                db=db
            )
            
            # Login using OAuth or Basic Auth
            if self.use_oauth:
                romm.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=True,
                    scopes=self.oauth_scopes or ['platforms.read', 'roms.read', 'collections.read']
                )
            else:
                romm.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=False
                )
            
            # DEBUG: Set Steamdeck Path manually
            # steamdeck_path = "./output/"
            
            success_count = 0
            error_count = 0
            skipped_count = 0

            # Process collections with concurrent downloads
            for collection in collections:
                collection_name = collection.get('name', 'unknown')
                self.background_logger.info(f"Check Collection: {collection_name}")

                try:
                    # Get Roms from Collection
                    roms = db.select_as_dict("roms", ['*'], 
                                            'collections_id = ? and sync_status = ?', 
                                            (collection.get("collections_id"), 0))
                    
                    if not roms:
                        self.background_logger.info(f"No pending ROMs in collection '{collection_name}'")
                        continue
                    
                    self.background_logger.info(f"Processing {len(roms)} ROMs from '{collection_name}' with {self.max_workers} workers")
                    
                    # Use ThreadPoolExecutor for concurrent downloads
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        # Submit all ROM processing tasks
                        future_to_rom = {
                            executor.submit(self._process_single_rom, rom, steamdeck_path, collection_name): rom
                            for rom in roms
                        }
                        
                        # Process completed tasks
                        for future in as_completed(future_to_rom):
                            rom = future_to_rom[future]
                            try:
                                result = future.result()
                                # Thread-safe stats update
                                with self.stats_lock:
                                    success_count += result.get('success', 0)
                                    error_count += result.get('error', 0)
                                    skipped_count += result.get('skipped', 0)
                            except Exception as e:
                                self.background_logger.error(f"ROM {rom.get('roms_id')} task failed: {e}")
                                with self.stats_lock:
                                    error_count += 1
                    
                    self.background_logger.info(f"Collection '{collection_name}' processing complete")
                            
                except Exception as e:
                    self.background_logger.error(f"Error processing collection '{collection_name}': {e}")
                    continue
                    
            self.background_logger.info(f"Syncing ROMS - Finished (Success: {success_count}, Errors: {error_count}, Skipped: {skipped_count})")
            
            # Record sync history
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            total_roms = success_count + error_count + skipped_count
            
            db.insert("sync_history", 
                     ["start_time", "end_time", "duration_seconds", "total_roms", 
                      "success_count", "error_count", "skipped_count", "debug_mode"],
                     (start_time.isoformat(), end_time.isoformat(), duration, total_roms,
                      success_count, error_count, skipped_count, 1 if self.debug_mode else 0))
            
        except Exception as e:
            self.background_logger.error(f"Critical error during ROM sync: {e}", exc_info=True)
    
    def _process_single_rom(self, rom: Dict[str, Any], steamdeck_path: str, collection_name: str) -> Dict[str, Any]:
        """Process a single ROM (download or save metadata).
        
        Args:
            rom: ROM dictionary with metadata
            steamdeck_path: Base path for Steam Deck ROMs
            collection_name: Name of the collection being processed
            
        Returns:
            Dict with result status and counts
        """
        result = {'success': 0, 'error': 0, 'skipped': 0}
        
        roms_id = rom.get("roms_id")
        filename = rom.get("filename")
        platform_id = rom.get("platform_id")
        rom_name = rom.get("name", "unknown")
        
        try:
            db = DeckRommSyncDatabase(self.dbName)
            
            # Get Rom-Matching
            platform_matching = db.select_as_dict("platforms_matching", ['*'], 
                                                 'romm_platform_id = ?', (platform_id,))
            
            if not platform_matching:
                self.background_logger.error(f"No platform matching for ROM {roms_id} (platform_id: {platform_id})")
                db.update("roms", {"sync_status": 2}, "roms_id = ?", (roms_id,))
                result['error'] = 1
                return result
                
            steamdeck_platform_path = platform_matching[0].get("steamdeck_platform_name")
            if not steamdeck_platform_path:
                self.background_logger.error(f"Platform path not configured for platform_id {platform_id}")
                db.update("roms", {"sync_status": 2}, "roms_id = ?", (roms_id,))
                result['error'] = 1
                return result
            
            download_path = f"{steamdeck_path}{steamdeck_platform_path}/"
            
            # Debug mode: Output ROM metadata instead of downloading
            if self.debug_mode:
                self.background_logger.info(f"ROM-ID: {roms_id} | Debug mode: Saving metadata for '{rom_name}'")
                success = self._save_rom_metadata(rom, platform_matching[0], download_path)
            else:
                self.background_logger.info(f"ROM-ID: {roms_id} | Downloading '{rom_name}' to {download_path}")
                # Create RomM API Helper (thread-local)
                romm = RommAPIHelper(self.romMAPIBaseUrl, logger=self.background_logger)
                romm.login(self.romMUsername, self.romMPassword)
                # Download Rom
                success = romm.downloadRom(roms_id, filename, download_path)

            if success:
                self.background_logger.info(f"ROM-ID: {roms_id} | {'Metadata saved' if self.debug_mode else 'Download completed'} successfully")
                # Update Sync Status to success
                db.update("roms", {"sync_status": 1}, "roms_id = ?", (roms_id,))
                result['success'] = 1
            else:
                self.background_logger.error(f"ROM-ID: {roms_id} | {'Metadata save' if self.debug_mode else 'Download'} failed")
                # Update Sync Status to error
                db.update("roms", {"sync_status": 2}, "roms_id = ?", (roms_id,))
                result['error'] = 1
                
        except Exception as e:
            self.background_logger.error(f"Error processing ROM {roms_id} ('{rom_name}'): {e}")
            # Set error status
            try:
                db = DeckRommSyncDatabase(self.dbName)
                db.update("roms", {"sync_status": 2}, "roms_id = ?", (roms_id,))
            except Exception as db_error:
                self.background_logger.error(f"Failed to update ROM status: {db_error}")
            result['error'] = 1
        
        return result
    
    def _save_rom_metadata(self, rom: dict, platform_info: dict, download_path: str) -> bool:
        """Save ROM metadata to JSON file in debug output folder.
        
        Args:
            rom: Dictionary containing ROM information
            platform_info: Dictionary containing platform matching information
            download_path: Path where the ROM would have been downloaded
            
        Returns:
            bool: True if metadata was saved successfully, False otherwise
        """
        try:
            # Create platform subfolder in debug output
            platform_folder = os.path.join(self.debug_output_folder, platform_info.get('steamdeck_platform_name', 'unknown'))
            os.makedirs(platform_folder, exist_ok=True)
            
            # Create metadata dictionary
            metadata = {
                "rom_id": rom.get("roms_id"),
                "name": rom.get("name"),
                "filename": rom.get("filename"),
                "collection_id": rom.get("collections_id"),
                "platform": {
                    "romm_platform_id": rom.get("platform_id"),
                    "romm_platform_slug": rom.get("platform_fs_slug"),
                    "steamdeck_platform_name": platform_info.get("steamdeck_platform_name"),
                    "romm_platform_name": platform_info.get("romm_platform_name")
                },
                "url_cover": rom.get("url_cover"),
                "sync_status": rom.get("sync_status"),
                "download_path": download_path,
                "timestamp": datetime.now().isoformat(),
                "debug_mode": True
            }
            
            # Create safe filename from ROM name
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in rom.get("name", "unknown"))
            filename = f"{safe_name}_{rom.get('roms_id')}.json"
            filepath = os.path.join(platform_folder, filename)
            
            # Write metadata to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.background_logger.info(f"Saved ROM metadata to: {filepath}")
            return True
            
        except Exception as e:
            self.background_logger.error(f"Failed to save ROM metadata: {e}")
            return False
    
    def sync_save_files(self):
        """
        Synchronize save files between RomM and Steam Deck.
        Implements bidirectional sync with conflict resolution (newest wins).
        """
        self.background_logger.info("========== Save File Sync Started ==========")
        
        try:
            db = DeckRommSyncDatabase(self.dbName)
            
            # Check if save sync is enabled
            save_sync_config = db.select_as_dict("config", where="config_key = 'enable_save_sync'")
            if not save_sync_config or save_sync_config[0].get('config_value') != '1':
                self.background_logger.info("Save sync is disabled in configuration")
                return
            
            # Create sync history record
            sync_start = datetime.now().isoformat()
            db.insert("save_sync_history", 
                     ["sync_type", "started_at", "status"],
                     ("saves", sync_start, "running"))
            
            # Get the sync history ID
            history = db.select_as_dict("save_sync_history", order_by="id DESC", limit=1)
            history_id = history[0]['id'] if history else None
            
            # Get Steam Deck RetroDeck path
            steamdeck_path_config = db.select_as_dict("config", where="config_key = 'steamdeck_retrodeck_path'")
            if not steamdeck_path_config:
                self.background_logger.error("Steam Deck RetroDeck path not configured")
                return
            
            steamdeck_base_path = steamdeck_path_config[0]['config_value']
            
            # Create API helper with database
            api = RommAPIHelper(
                api_base_url=self.romMAPIBaseUrl,
                timeout=60,
                logger=self.background_logger,
                db=db
            )
            
            # Login using OAuth or Basic Auth
            if self.use_oauth:
                api.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=True,
                    scopes=self.oauth_scopes or [
                        'platforms.read',
                        'roms.read',
                        'collections.read',
                        'assets.read',
                        'assets.write'
                    ]
                )
            else:
                api.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=False
                )
            
            # Create API helper with database
            api = RommAPIHelper(
                api_base_url=self.romMAPIBaseUrl,
                timeout=60,
                logger=self.background_logger,
                db=db
            )
            
            # Login using OAuth or Basic Auth
            if self.use_oauth:
                api.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=True,
                    scopes=self.oauth_scopes or [
                        'platforms.read',
                        'roms.read',
                        'collections.read',
                        'assets.read',
                        'assets.write'
                    ]
                )
            else:
                api.login(
                    username=self.romMUsername,
                    password=self.romMPassword,
                    use_oauth=False
                )
            
            # Get all synced ROMs
            synced_roms = db.select_as_dict("roms", where="sync_status = 1")
            self.background_logger.info(f"Found {len(synced_roms)} synced ROMs to check for saves")
            
            total_saves = 0
            downloaded = 0
            uploaded = 0
            conflicts = 0
            errors = 0
            
            # Create RomM API Helper
            romm = RommAPIHelper(self.romMAPIBaseUrl, logger=self.background_logger)
            romm.login(self.romMUsername, self.romMPassword)
            
            for rom in synced_roms:
                rom_id = rom['roms_id']
                rom_name = rom['name']
                
                try:
                    # Get saves from RomM for this ROM
                    remote_saves = romm.getSavesByRomID(rom_id)
                    
                    if remote_saves is None:
                        continue
                    
                    if not remote_saves:
                        self.background_logger.debug(f"No saves found for ROM: {rom_name}")
                        continue
                    
                    total_saves += len(remote_saves)
                    
                    for save in remote_saves:
                        try:
                            save_result = self._sync_single_save(
                                db, romm, rom, save, steamdeck_base_path
                            )
                            
                            if save_result == 'downloaded':
                                downloaded += 1
                            elif save_result == 'uploaded':
                                uploaded += 1
                            elif save_result == 'conflict':
                                conflicts += 1
                            elif save_result == 'error':
                                errors += 1
                                
                        except Exception as e:
                            self.background_logger.error(f"Error syncing save {save.get('id')}: {e}")
                            errors += 1
                            
                except Exception as e:
                    self.background_logger.error(f"Error processing saves for ROM {rom_id}: {e}")
                    errors += 1
            
            # Update sync history
            sync_end = datetime.now().isoformat()
            if history_id:
                db.update("save_sync_history",
                         {
                             "completed_at": sync_end,
                             "total_saves": total_saves,
                             "downloaded": downloaded,
                             "uploaded": uploaded,
                             "conflicts": conflicts,
                             "errors": errors,
                             "status": "completed"
                         },
                         "id = ?",
                         (history_id,))
            
            self.background_logger.info(f"========== Save File Sync Completed ==========")
            self.background_logger.info(f"Total: {total_saves} | Downloaded: {downloaded} | Uploaded: {uploaded} | Conflicts: {conflicts} | Errors: {errors}")
            
        except Exception as e:
            self.background_logger.error(f"Save file sync failed: {e}")
    
    def _sync_single_save(self, db: DeckRommSyncDatabase, romm: RommAPIHelper, 
                          rom: dict, save: dict, steamdeck_base_path: str) -> str:
        """
        Sync a single save file with conflict resolution.
        
        Returns:
            'downloaded', 'uploaded', 'conflict', 'skipped', or 'error'
        """
        rom_id = rom['roms_id']
        save_id = save.get('id')
        emulator = save.get('emulator', 'unknown')
        file_name = save.get('file_name')
        remote_updated_at = save.get('updated_at')
        
        # Get save path
        local_path = self._get_save_path(rom, save, steamdeck_base_path)
        
        if not local_path:
            self.background_logger.error(f"Could not determine save path for ROM {rom_id}")
            return 'error'
        
        # Check if we have a database record for this save
        existing_save = db.select_as_dict(
            "rom_saves",
            where="rom_id = ? AND file_name = ?",
            condition_values=(rom_id, file_name)
        )
        
        # Check if local file exists
        local_exists = os.path.exists(local_path)
        
        if local_exists and existing_save:
            # Compare timestamps to determine conflict
            local_mtime = datetime.fromtimestamp(os.path.getmtime(local_path))
            remote_mtime = datetime.fromisoformat(remote_updated_at.replace('Z', '+00:00'))
            
            # Get last sync time
            last_sync = existing_save[0].get('last_sync_at')
            if last_sync:
                last_sync_dt = datetime.fromisoformat(last_sync)
                
                # Check if local file was modified after last sync
                local_modified_after_sync = local_mtime > last_sync_dt
                remote_modified_after_sync = remote_mtime > last_sync_dt
                
                if local_modified_after_sync and remote_modified_after_sync:
                    # Conflict: both modified since last sync - newest wins
                    self.background_logger.warning(
                        f"Conflict detected for save {file_name} - using newest version"
                    )
                    
                    if local_mtime > remote_mtime:
                        # Upload local version
                        result = romm.uploadSave(rom_id, local_path, emulator)
                        if result:
                            self._update_save_record(db, rom_id, save_id, save, local_path, 'upload')
                            return 'uploaded'
                        return 'error'
                    else:
                        # Download remote version
                        if romm.downloadSave(save_id, local_path):
                            self._update_save_record(db, rom_id, save_id, save, local_path, 'download')
                            return 'downloaded'
                        return 'error'
                
                elif local_modified_after_sync:
                    # Only local modified - upload
                    result = romm.uploadSave(rom_id, local_path, emulator)
                    if result:
                        self._update_save_record(db, rom_id, save_id, save, local_path, 'upload')
                        return 'uploaded'
                    return 'error'
                    
                elif remote_modified_after_sync:
                    # Only remote modified - download
                    if romm.downloadSave(save_id, local_path):
                        self._update_save_record(db, rom_id, save_id, save, local_path, 'download')
                        return 'downloaded'
                    return 'error'
                else:
                    # Neither modified - skip
                    return 'skipped'
            else:
                # No last sync record - compare timestamps directly
                if local_mtime > remote_mtime:
                    result = romm.uploadSave(rom_id, local_path, emulator)
                    if result:
                        self._update_save_record(db, rom_id, save_id, save, local_path, 'upload')
                        return 'uploaded'
                    return 'error'
                else:
                    if romm.downloadSave(save_id, local_path):
                        self._update_save_record(db, rom_id, save_id, save, local_path, 'download')
                        return 'downloaded'
                    return 'error'
        
        elif local_exists:
            # Local exists but not in database - upload to RomM
            result = romm.uploadSave(rom_id, local_path, emulator)
            if result:
                self._update_save_record(db, rom_id, save_id, save, local_path, 'upload')
                return 'uploaded'
            return 'error'
        
        else:
            # Local doesn't exist - download from RomM
            if romm.downloadSave(save_id, local_path):
                self._update_save_record(db, rom_id, save_id, save, local_path, 'download')
                return 'downloaded'
            return 'error'
    
    def _get_save_path(self, rom: dict, save: dict, steamdeck_base_path: str) -> Optional[str]:
        """
        Determine the local save file path based on emulator and platform.
        
        RetroDeck structure: /home/deck/retrodeck/saves/{emulator}/{platform}/{filename}
        """
        try:
            db = DeckRommSyncDatabase(self.dbName)
            
            emulator = save.get('emulator', 'retroarch').lower()
            file_name = save.get('file_name')
            platform_id = rom.get('platform_id')
            
            # Get platform matching
            platform_matching = db.select_as_dict(
                "platforms_matching",
                where="romm_platform_id = ?",
                condition_values=(platform_id,)
            )
            
            if not platform_matching:
                self.background_logger.error(f"No platform matching for platform_id {platform_id}")
                return None
            
            platform_folder = platform_matching[0].get('steamdeck_platform_name')
            
            # RetroDeck saves structure
            save_path = os.path.join(
                steamdeck_base_path,
                "saves",
                emulator,
                platform_folder,
                file_name
            )
            
            return save_path
            
        except Exception as e:
            self.background_logger.error(f"Error determining save path: {e}")
            return None
    
    def _update_save_record(self, db: DeckRommSyncDatabase, rom_id: int, save_id: int,
                           save: dict, local_path: str, direction: str):
        """Update or create save record in database."""
        try:
            now = datetime.now().isoformat()
            
            # Check if record exists
            existing = db.select_as_dict(
                "rom_saves",
                where="rom_id = ? AND file_name = ?",
                condition_values=(rom_id, save.get('file_name'))
            )
            
            file_size = save.get('file_size_bytes', 0)
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
            
            save_data = {
                'romm_save_id': save_id,
                'emulator': save.get('emulator'),
                'remote_updated_at': save.get('updated_at'),
                'local_updated_at': now,
                'sync_status': 1,
                'sync_direction': direction,
                'last_sync_at': now,
                'file_size_bytes': file_size
            }
            
            if existing:
                # Update existing record
                db.update("rom_saves", save_data, "id = ?", (existing[0]['id'],))
            else:
                # Insert new record
                save_data.update({
                    'rom_id': rom_id,
                    'file_name': save.get('file_name'),
                    'local_path': local_path
                })
                
                columns = list(save_data.keys())
                values = tuple(save_data.values())
                db.insert("rom_saves", columns, values)
                
        except Exception as e:
            self.background_logger.error(f"Failed to update save record: {e}") 