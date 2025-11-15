# DeckRommSync-Rivera

DeckRommSync-Rivera is an enhanced ROM synchronization tool that automatically syncs your ROMs from [RomM](https://github.com/rommapp/romm) to your Steam Deck with intelligent platform matching, real-time status monitoring, and concurrent downloads.

![DeckRomMSync](/docs/deckrommsync.png)

**Author:** Michael Rivera  
**Inspired by:** [PeriBluGaming's DeckRommSync-Standalone](https://github.com/PeriBluGaming/DeckRommSync-Standalone)

## ✨ Features

### Core Functionality
- ✅ Automatic ROM synchronization from RomM to Steam Deck
- ✅ Smart platform matching with 70+ preset folder names
- ✅ Collection-based sync control
- ✅ Concurrent downloads (configurable worker threads)
- ✅ Background worker with scheduled syncing
- ✅ Manual sync trigger - sync on demand

### User Interface
- ✅ Modern web UI with dark/light themes
- ✅ Real-time sync status with animated spinner
- ✅ Live progress tracking (success/pending/errors)
- ✅ Statistics dashboard with sync history
- ✅ Toast notifications for user feedback
- ✅ Folder picker for easy path selection

### Developer Features
- ✅ Debug mode for testing without downloads
- ✅ Comprehensive test suite (139 tests)
- ✅ Thread-safe database operations
- ✅ Input validation and error handling
- ✅ Detailed logging system

## 🚀 Installation

1. Clone the Repository to your Steam Deck
   ```bash
   git clone https://github.com/mriver15/DeckRommSync-Rivera.git
   cd DeckRommSync-Rivera
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install Requirements
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Adjust settings in `config.json`:
   - Server port (default: 5000)
   - Max workers for concurrent downloads (default: 8)
   - Debug mode settings

## ⚙️ Configuration

### Starting the Application

Make sure the virtual environment is activated:
```bash
source venv/bin/activate
python3 app.py
```

Access the web interface at `http://{steamdeck-ip}:5000`

### Initial Setup

#### 1. RomM API Settings
Navigate to the **Config** page and configure:

- **RomM API URL:** `http://{romm-ip}:{romm-port}/api`
- **Username:** Your RomM username
- **Password:** Your RomM password

Click **Save Settings**. The background worker will sync platforms and collections within 1 minute (or click **Sync Now** on the Status page for immediate sync).

#### 2. Platform Matching

**Steam Deck System Path:** Click **Browse** or enter the path to your RetroDECK roms directory (e.g., `/home/deck/retrodeck/roms/`)

**Platform Folders:** Platform folder names are now **automatically populated** with common defaults:
- PlayStation → `psx`
- Nintendo 64 → `n64`
- Game Boy Advance → `gba`
- Nintendo DS → `nds`
- And 70+ more...

You can customize any folder name as needed and click **Save** for that platform.

![Platform-Matching](/docs/platform_matching.png)

#### 3. Activate Collection Sync

In the **Sync Collections** section:
1. Check the boxes next to collections you want to sync
2. Click **Save Collections**
3. Click **Sync Now** on the Status page or wait for automatic sync

Collections will maintain their enabled/disabled state across syncs.

## 📊 Statistics Dashboard

Access `/stats` to view:
- Total ROMs synced vs pending vs errors
- Success rate percentage
- Estimated disk space usage
- Per-platform breakdown
- Per-collection statistics
- Recent sync history with timestamps

## 🐛 Debug Mode

Debug mode allows testing without downloading ROM files - perfect for configuration validation.

### Enable Debug Mode

Edit `config.json`:
```json
{
    "debug": {
        "enabled": true,
        "output_folder": "./debug_output"
    },
    "sync": {
        "max_workers": 8
    }
}
```

### What Debug Mode Does

- Saves ROM metadata as JSON files instead of downloading
- Organizes files by platform folder structure
- Tests platform matching configuration
- Validates folder permissions
- Minimal disk usage and bandwidth

### Example Output

```text
debug_output/
├── psx/
│   ├── Final_Fantasy_VII_123.json
│   └── Metal_Gear_Solid_456.json
├── n64/
│   └── Super_Mario_64_789.json
└── gba/
    └── Pokemon_FireRed_101.json
```

See [DEBUG_MODE.md](DEBUG_MODE.md) for complete documentation.

## 🔄 Real-Time Sync Status

The Status page shows:
- **Sync spinner** - Animated during active sync
- **Current step** - What the sync process is doing
- **Progress metrics** - Live counts of synced/pending/error ROMs
- **Progress bar** - Visual percentage of completion
- **Sync Now button** - Trigger manual sync immediately
- **Last update timestamp** - When status was last refreshed

Status updates every 2 seconds automatically.

## 🛠️ Performance Tuning

### Concurrent Downloads

Adjust `max_workers` in `config.json` to control parallel downloads:

```json
{
    "sync": {
        "max_workers": 8  // 4-8 recommended, higher = faster but more resources
    }
}
```

### Scheduled Sync Interval

The background worker runs every 1 minute by default. To change this, modify `app.py`:

```python
scheduler.add_job(run_background_task, "interval", minutes=5)  # Change to 5 minutes
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
pytest tests/ -v
```

All 139 tests validate:
- Database operations
- API interactions
- Input validation
- Error handling
- Thread safety
- Debug mode functionality
- Duplicate handling

## 📝 License

See [LICENSE.md](LICENSE.md)

## 🙏 Acknowledgments

This project is inspired by and builds upon [PeriBluGaming's DeckRommSync-Standalone](https://github.com/PeriBluGaming/DeckRommSync-Standalone). Special thanks to the original author for the foundation that made this enhanced version possible.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Developed by Michael Rivera**  
**Built for the Steam Deck and RetroDECK community**
