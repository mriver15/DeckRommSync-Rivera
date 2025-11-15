# Debug Mode Documentation

## Overview

Debug mode allows you to test the ROM synchronization process without actually downloading ROM files. Instead of downloading, the application will save ROM metadata as JSON files in a specified output folder.

## Configuration

Edit `config.json` to enable debug mode:

```json
{
    "debug": {
        "enabled": true,
        "output_folder": "./debug_output"
    }
}
```

### Configuration Options

- **`enabled`** (boolean): Set to `true` to enable debug mode, `false` to disable
- **`output_folder`** (string): Path to the folder where ROM metadata will be saved

## How It Works

When debug mode is enabled:

1. The background worker will **NOT** download actual ROM files
2. Instead, it creates JSON files containing ROM metadata
3. Files are organized in subfolders by platform (e.g., `psx`, `n64`, `gba`)
4. Each ROM gets a separate JSON file with comprehensive metadata
5. Sync status is still updated in the database (success/error)
6. All logging continues as normal

## Output Structure

```
debug_output/
├── psx/
│   ├── Final_Fantasy_VII_123.json
│   ├── Metal_Gear_Solid_456.json
│   └── ...
├── n64/
│   ├── Super_Mario_64_789.json
│   └── ...
└── gba/
    └── ...
```

## Metadata Format

Each JSON file contains:

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
  "url_cover": "https://example.com/covers/ff7.jpg",
  "sync_status": 0,
  "download_path": "/path/to/retrodeck/roms/psx/",
  "timestamp": "2025-11-15T10:30:45.123456",
  "debug_mode": true
}
```

## Use Cases

Debug mode is useful for:

- **Testing** - Verify sync logic without downloading large files
- **Development** - Check platform matching and path configuration
- **Troubleshooting** - Identify issues without consuming bandwidth/storage
- **Inspection** - Review ROM metadata before actual synchronization
- **Documentation** - Generate a catalog of available ROMs

## Logging

When debug mode is enabled, the background worker log will show:

```
2025-11-15 10:30:45 - INFO - Background Task started...
2025-11-15 10:30:45 - INFO - Running in DEBUG MODE - ROM metadata will be saved to ./debug_output
2025-11-15 10:30:45 - INFO - Debug mode enabled. Output folder: ./debug_output
...
2025-11-15 10:30:50 - INFO - ROM-ID: 123 | Debug mode: Saving metadata for 'Final Fantasy VII'
2025-11-15 10:30:50 - INFO - Saved ROM metadata to: ./debug_output/psx/Final_Fantasy_VII_123.json
2025-11-15 10:30:50 - INFO - ROM-ID: 123 | Metadata saved successfully
```

## Switching Between Modes

To switch from debug mode to production:

1. Edit `config.json` and set `"enabled": false`
2. Restart the Flask application
3. The next sync will download actual ROM files

To switch from production to debug mode:

1. Edit `config.json` and set `"enabled": true`
2. Optionally change `"output_folder"` to a different location
3. Restart the Flask application
4. The next sync will save metadata files instead of downloading

## Important Notes

- Debug mode still updates the database sync status (0=pending, 1=success, 2=error)
- ROMs marked as "synced" in debug mode will not be re-processed unless you reset their status
- The debug output folder is created automatically if it doesn't exist
- Existing metadata files will be overwritten if the same ROM is processed again
- Debug mode does NOT affect the collection/platform synchronization (only ROM downloads)

## Cleanup

To clean up debug output:

```bash
# On Windows
rmdir /s debug_output

# On Linux/Mac
rm -rf debug_output
```

Or simply delete the folder through your file explorer.
