# Debug Mode Feature Summary

## Overview

Added a debug mode feature that allows testing ROM synchronization without downloading actual files. Instead, the system saves ROM metadata as JSON files organized by platform.

## Changes Made

### 1. Configuration (`config.json`)
- Added `debug` section with two settings:
  - `enabled`: Boolean to enable/disable debug mode
  - `output_folder`: Path where ROM metadata will be saved

### 2. BackgroundWorker Class (`classes/BackgroundWorker.py`)
- Added `debug_mode` and `debug_output_folder` parameters to `__init__`
- Creates debug output folder on initialization when debug mode is enabled
- Modified `sync_copyRoms()` to check debug mode and save metadata instead of downloading
- Added `_save_rom_metadata()` method to create JSON files with ROM information
- Automatically creates platform subfolders (psx, n64, gba, etc.)
- Handles special characters in ROM names for safe filenames

### 3. Application (`app.py`)
- Updated `run_background_task()` to read debug settings from config
- Passes debug configuration to BackgroundWorker initialization
- Logs when debug mode is active

### 4. Tests (`tests/test_debug_mode.py`)
- 7 comprehensive tests covering:
  - Debug mode initialization
  - Metadata file creation
  - Platform folder organization
  - Special character handling
  - Error handling
  - Output folder creation

### 5. Documentation
- **DEBUG_MODE.md**: Complete feature documentation
- **docs/DEBUG_MODE_EXAMPLE.md**: Practical usage examples
- **README.md**: Added debug mode section with overview
- **TODO_TESTS.md**: Updated test coverage summary

### 6. Sample Output (`debug_output_sample/`)
- Created sample ROM metadata files to demonstrate output format
- Organized by platform (psx, n64, gba)
- Shows realistic ROM metadata structure

## JSON Metadata Format

Each ROM generates a JSON file with:
```json
{
  "rom_id": 123,
  "name": "Final Fantasy VII",
  "filename": "Final Fantasy VII (USA).cue",
  "collection_id": 5,
  "platform": {
    "romm_platform_id": 2,
    "romm_platform_slug": "psx",
    "steamdeck_platform_name": "psx",
    "romm_platform_name": "Sony PlayStation"
  },
  "url_cover": "https://images.romm.app/covers/ff7.jpg",
  "sync_status": 0,
  "download_path": "/home/deck/retrodeck/roms/psx/",
  "timestamp": "2025-11-15T10:31:15.456789",
  "debug_mode": true
}
```

## Use Cases

1. **Testing Platform Matching**: Verify folder names are correct before downloading
2. **Bandwidth Conservation**: Test sync logic without consuming bandwidth
3. **Storage Testing**: Check disk space requirements before actual sync
4. **Configuration Validation**: Ensure paths and settings are correct
5. **ROM Cataloging**: Generate inventory of available ROMs

## Test Results

All 139 tests passing:
- 7 new debug mode tests
- All existing tests still pass (no breaking changes)

## How to Use

1. Edit `config.json`:
   ```json
   "debug": {
       "enabled": true,
       "output_folder": "./debug_output"
   }
   ```

2. Restart the application

3. Check `debug_output/` folder after sync runs

4. Inspect JSON files to verify configuration

5. Set `"enabled": false` when ready for actual downloads

## Technical Details

- Debug mode respects all existing sync logic (collections, platforms, status)
- ROMs processed in debug mode are marked as "synced" (status = 1)
- Reset sync status in UI to re-process ROMs
- No changes to database schema required
- Backward compatible (debug mode disabled by default)
- Minimal disk usage (only small JSON files)

## Files Modified

- `config.json`
- `classes/BackgroundWorker.py`
- `app.py`
- `README.md`
- `TODO_TESTS.md`

## Files Created

- `tests/test_debug_mode.py`
- `DEBUG_MODE.md`
- `docs/DEBUG_MODE_EXAMPLE.md`
- `debug_output_sample/psx/Final_Fantasy_VII_123.json`
- `debug_output_sample/psx/Metal_Gear_Solid_456.json`
- `debug_output_sample/n64/Super_Mario_64_789.json`
- `debug_output_sample/gba/Pokemon_FireRed_101.json`

## Benefits

✅ **Testing Made Easy**: Test sync configuration without downloads  
✅ **No Bandwidth**: Zero network usage during debug sync  
✅ **Minimal Storage**: JSON files are tiny compared to ROM files  
✅ **Full Metadata**: All ROM information preserved for inspection  
✅ **Platform Verification**: Quickly see if folder mapping is correct  
✅ **Safe to Enable**: No risk to existing ROM files  
✅ **Easy to Disable**: Simple config change to switch to production
