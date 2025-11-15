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
            
            for config in configObj:            
                if config['config_key'] == 'romm_api_base_url':
                    self.romMAPIBaseUrl = config['config_value']
                elif config['config_key'] == 'romm_username':
                    self.romMUsername = config['config_value']
                elif config['config_key'] == 'romm_password':
                    self.romMPassword = config['config_value']
            
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
            # Create API helper with logger
            romm = RommAPIHelper(self.romMAPIBaseUrl, logger=self.background_logger)
            romm.login(self.romMUsername, self.romMPassword)
            db = DeckRommSyncDatabase(self.dbName)

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
                                         
                            # Insert ROM (using insert_or_replace to handle duplicates)
                            db.insert_or_replace("roms", ["roms_id", "collections_id", "name", "url_cover", "filename", "platform_fs_slug", "platform_id"],
                                               (romObj['id'],
                                               collection['id'],
                                               romObj['name'],
                                               romObj.get('url_cover', ''),
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