# Debug Mode Example

This example demonstrates how to use debug mode to inspect ROM metadata without downloading files.

## Step 1: Enable Debug Mode

Edit `config.json`:

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 5000
    },
    "database": {
        "name": "deckrommsync.db",
        "type": "sqlite"
    },
    "debug": {
        "enabled": true,
        "output_folder": "./debug_output"
    }
}
```

## Step 2: Run the Application

```bash
python app.py
```

## Step 3: Check the Logs

The background worker log will show:

```
2025-11-15 10:30:45 - INFO - Background Task started...
2025-11-15 10:30:45 - INFO - Running in DEBUG MODE - ROM metadata will be saved to ./debug_output
2025-11-15 10:30:45 - INFO - Debug mode enabled. Output folder: ./debug_output
```

## Step 4: Wait for Sync or Trigger Manually

The background task runs every 1 minute by default. After it runs, check the `debug_output` folder.

## Step 5: Inspect the Output

```
debug_output/
├── psx/
│   ├── Final_Fantasy_VII_123.json
│   ├── Metal_Gear_Solid_456.json
│   └── Crash_Bandicoot_789.json
├── n64/
│   ├── Super_Mario_64_101.json
│   └── The_Legend_of_Zelda_Ocarina_of_Time_102.json
└── gba/
    ├── Pokemon_FireRed_201.json
    └── Metroid_Fusion_202.json
```

## Step 6: View ROM Metadata

Open any JSON file to see the ROM details:

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
  "download_path": "/home/deck/retrodeck/roms/psx/",
  "timestamp": "2025-11-15T10:31:15.456789",
  "debug_mode": true
}
```

## Use Cases

### 1. Verify Platform Matching

Check if your platform folders are correctly configured:

```bash
# List all platform folders created
ls debug_output/
```

If you see unexpected folder names, update your platform matching in the config page.

### 2. Check File Paths

Verify the `download_path` in each JSON file matches your expected structure:

```bash
# Search for download paths
grep -r "download_path" debug_output/ | head -5
```

### 3. Find ROMs by Name

```bash
# Find all Pokemon ROMs
find debug_output/ -name "*Pokemon*"
```

### 4. Count ROMs per Platform

```bash
# Count JSON files in each platform folder
for dir in debug_output/*/; do
    echo "$(basename $dir): $(find $dir -name '*.json' | wc -l) ROMs"
done
```

### 5. Export ROM List

```bash
# Create a simple CSV of all ROMs
echo "Platform,ROM Name,Filename" > roms.csv
for json in debug_output/*/*.json; do
    platform=$(basename $(dirname $json))
    name=$(jq -r '.name' $json)
    filename=$(jq -r '.filename' $json)
    echo "$platform,$name,$filename" >> roms.csv
done
```

## Disable Debug Mode When Ready

Once you've verified everything works, disable debug mode to start actual downloads:

1. Edit `config.json` and set `"enabled": false`
2. Restart the application
3. The next sync will download actual ROM files

## Notes

- ROMs processed in debug mode are marked as "synced" (status = 1) in the database
- To re-process them, use the "Reset Sync Status" button in the web UI
- Debug mode creates minimal disk usage (only small JSON files)
- Perfect for testing on limited bandwidth or storage
