# DeckRommSync-Rivera

**Automated ROM synchronization from [RomM](https://github.com/rommapp/romm) to Steam Deck**

![DeckRomMSync](/docs/deckrommsync.png)

Sync your ROM collection from RomM server to Steam Deck with intelligent platform matching, OAuth2 authentication, save file sync, and real-time monitoring.

**Author:** Michael Rivera | **License:** MIT (No Selling)

---

## ⚡ Quick Start

### 1. Install
```bash
git clone https://github.com/mriver15/DeckRommSync-Rivera.git
cd DeckRommSync-Rivera
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
python app.py
# Open http://localhost:5000 in browser
```

**Config Page:**
- RomM API URL: `http://your-romm-server:8080/api`
- Authentication: Choose OAuth2 (RomM v4.4.0+) or Basic Auth
- Platform Matching: Map RomM platforms to RetroDECK folders
- Collections: Enable collections to sync

### 3. Sync
Click **Sync Now** on Status page or wait for automatic sync (runs every minute)

---

## ✨ Features

### Core
- ✅ **OAuth2 Authentication** - Secure token-based auth for RomM v4.4.0+
- ✅ **Bidirectional Save Sync** - Sync save files & save states between RomM and Steam Deck
- ✅ **Smart Platform Matching** - 70+ preset platform folder mappings
- ✅ **Collection-Based Sync** - Choose which collections to sync
- ✅ **Concurrent Downloads** - Parallel ROM downloads (configurable threads)
- ✅ **Real-Time Status** - Live sync progress with interactive UI

### UI
- ✅ **Modern Web Interface** - Responsive design with dark theme
- ✅ **Three View Modes** - Grid, List, Compact views for ROM library
- ✅ **Interactive ROM Cards** - Click for details, save counts, status badges
- ✅ **Statistics Dashboard** - Track sync history, disk space, success rates
- ✅ **Debug Mode** - Test configurations without downloading files

---

## 📖 Documentation

### User Guides
- **[OAuth Setup](docs/implementation/OAUTH_IMPLEMENTATION.md)** - RomM v4.4.0+ authentication
- **[Save Sync](docs/implementation/SAVE_SYNC_IMPLEMENTATION.md)** - Bidirectional save file synchronization
- **[Debug Mode](docs/implementation/DEBUG_MODE.md)** - Testing without downloads

### Advanced
- **[Feature Analysis](docs/implementation/FEATURES_AND_ANALYSIS.md)** - Complete feature documentation
- **[Recommended Improvements](docs/implementation/IMPROVEMENTS.md)** - Enhancement roadmap

---

## 🎮 Use Cases

**Portable Gaming:** Play on RomM server (EmulatorJS), continue on Steam Deck with synced saves

**Multi-Device:** Keep ROMs and saves synchronized across multiple devices

**Backup:** Automatic cloud backup of save files to RomM server

**Library Management:** Centralized ROM collection with selective sync

---

## 🛠️ Configuration

### config.json
```json
{
  "server": { "port": 5000 },
  "sync": { "max_workers": 8 },
  "oauth": {
    "enabled": true,
    "scopes": ["platforms.read", "roms.read", "collections.read", "assets.write"]
  },
  "debug": { "enabled": false }
}
```

### Environment Variables
```bash
ROMMSYNC_PORT=5000
ROMMSYNC_DEBUG=false
```

---

## 📊 Status Page

**Compact Sync Bar** - Real-time stats: success/pending/error/total ROMs

**Three View Modes:**
- **Grid:** Card view with cover art and status badges
- **List:** Detailed rows with platform info and save counts
- **Compact:** Dense table view for large libraries

**Interactive Features:**
- Click ROM to view details and save files
- Search and filter by status
- Real-time updates (2-second polling)
- Reset sync status per ROM

---

## 🔐 OAuth2 Authentication

**RomM v4.4.0+ (Recommended):**
- Secure token-based authentication
- Automatic token refresh (30-min access, 7-day refresh)
- Scope-based permissions
- No password in every request

**Backward Compatible:**
- Basic Auth still supported for older RomM versions
- Toggle in Config UI

**Required Scopes:**
- `platforms.read` - Platform data
- `roms.read` - ROM downloads
- `collections.read` - Collection info
- `assets.write` - Save file uploads

---

## 💾 Save File Sync

**Bidirectional Sync:**
- Download saves from RomM to Steam Deck
- Upload Steam Deck saves to RomM
- Automatic conflict resolution (newest wins)

**Supported:**
- Save files (.srm, .sav)
- Save states (quick saves)
- Multiple emulators (RetroArch, standalone)

**Database Tracking:**
- Sync history with timestamps
- Per-ROM save counts
- Error tracking and logging

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test coverage
pytest tests/ --cov=classes --cov-report=html

# Debug mode (no downloads)
# Set debug.enabled=true in config.json
```

**139 Tests Cover:**
- Database operations
- OAuth token management
- Save file sync logic
- Platform matching
- Error handling

---

## 📈 Performance

**Optimized Downloads:**
- Concurrent downloads (8 workers default)
- Chunked file transfers
- Resume support

**Recommended Settings:**
- Max workers: 4-8 (balance speed vs resources)
- Sync interval: 1-5 minutes
- Debug mode: Enable for testing configs

**Benchmarks:**
- 100 ROMs: ~10-20 minutes (network dependent)
- Save sync: ~100ms per save file
- OAuth token refresh: ~200ms every 25 minutes

---

## 🚀 Deployment

### Steam Deck (Native)
```bash
source venv/bin/activate
python app.py
# Access at http://steamdeck.local:5000
```

### Docker (Planned)
```bash
docker-compose up -d
```

### Systemd Service (Optional)
```bash
sudo cp deckrommsync.service /etc/systemd/system/
sudo systemctl enable deckrommsync
sudo systemctl start deckrommsync
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

**Development:**
```bash
pip install -r requirements-dev.txt
pre-commit install
pytest tests/
```

---

## 📝 License

MIT License (No Selling) - See [LICENSE.md](LICENSE.md)

---

## 🙏 Acknowledgments

Inspired by [PeriBluGaming's DeckRommSync-Standalone](https://github.com/PeriBluGaming/DeckRommSync-Standalone)

Built for the Steam Deck and RetroDECK community

---

## 📞 Support

**Issues:** [GitHub Issues](https://github.com/mriver15/DeckRommSync-Rivera/issues)

**Logs:** Check `background_worker.log` and `system.log`

**Community:** Steam Deck Discord, RetroDECK Discord

---

**Developed by Michael Rivera** | **Version 2.0.0** | **Updated: November 2025**
