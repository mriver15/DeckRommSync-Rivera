# Documentation Index

**DeckRommSync-Rivera Implementation Documentation**

All implementation details, guides, and technical documentation organized in one place.

---

## Quick Links

### User Documentation
- [Main README](../../README.md) - Quick start and overview
- [OAuth Setup Guide](OAUTH_IMPLEMENTATION.md) - RomM v4.4.0+ authentication
- [Save Sync Guide](SAVE_SYNC_IMPLEMENTATION.md) - Bidirectional save synchronization
- [Debug Mode Guide](DEBUG_MODE.md) - Testing without downloads

### Technical Documentation
- [Feature Analysis](FEATURES_AND_ANALYSIS.md) - Complete feature breakdown
- [Recommended Improvements](IMPROVEMENTS.md) - Prioritized enhancement roadmap
- [Debug Mode Example](DEBUG_MODE_EXAMPLE.md) - Debug output examples

---

## Documentation Structure

```
docs/
├── implementation/
│   ├── INDEX.md (this file)
│   ├── OAUTH_IMPLEMENTATION.md
│   ├── SAVE_SYNC_IMPLEMENTATION.md
│   ├── DEBUG_MODE.md
│   ├── FEATURE_DEBUG_MODE.md
│   ├── FEATURES_AND_ANALYSIS.md
│   ├── IMPROVEMENTS.md
│   └── DEBUG_MODE_EXAMPLE.md
├── deckrommsync.png
└── platform_matching.png
```

---

## Phase Tracking

### ✅ Completed
- **Phase 1:** OAuth2 Authentication (6/8 tasks)
  - Token-based auth with auto-refresh
  - Database token storage
  - Configuration UI
  - Backward compatibility
  
- **Save Sync:** Bidirectional save/state synchronization
  - Download from RomM
  - Upload from Steam Deck
  - Conflict resolution

- **UI Redesign:** Modern status page
  - Grid/List/Compact views
  - Interactive ROM cards
  - Real-time updates

### ⏳ In Progress
- End-to-end OAuth testing with RomM v4.4.0
- Production deployment testing

### 📋 Planned
See [IMPROVEMENTS.md](IMPROVEMENTS.md) for full roadmap:
- Token encryption
- Download progress tracking
- Webhook notifications
- Docker support
- Health dashboard

---

## Key Features

### Authentication
- OAuth2 password grant flow
- Access tokens (30-min expiry)
- Refresh tokens (7-day expiry)
- Scope-based permissions
- Basic Auth fallback

### Save Synchronization
- Bidirectional sync
- Automatic conflict resolution (newest wins)
- Multiple emulator support
- Sync history tracking
- Per-ROM save counts

### Platform Matching
- 70+ preset platform mappings
- Custom folder names
- Auto-populated defaults
- RetroDECK structure support

### User Interface
- Three view modes (Grid, List, Compact)
- Portrait cover art (2:3 ratio)
- Interactive ROM details modal
- Real-time sync status
- Search and filter
- Save file badges

---

## Database Schema

### Core Tables
- `config` - Application settings
- `collections` - RomM collections
- `roms` - ROM metadata and sync status
- `platforms_matching` - Platform folder mappings

### OAuth Tables
- `oauth_tokens` - Access/refresh tokens with expiry

### Save Sync Tables
- `rom_saves` - Save file tracking
- `rom_states` - Save state tracking
- `save_sync_history` - Sync audit trail

---

## Configuration

### config.json Structure
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
  "sync": {
    "max_workers": 8,
    "enable_save_sync": true,
    "enable_state_sync": false
  },
  "oauth": {
    "enabled": true,
    "scopes": [
      "platforms.read",
      "roms.read",
      "collections.read",
      "assets.read",
      "assets.write"
    ]
  },
  "debug": {
    "enabled": false,
    "output_folder": "./debug_output"
  }
}
```

---

## Testing

### Test Coverage
- 139 total tests
- Database operations
- OAuth token management
- Save sync logic
- Platform matching
- Error handling
- Debug mode functionality

### Running Tests
```bash
pytest tests/ -v
pytest tests/ --cov=classes
```

---

## Migration Scripts

### Available Migrations
- `migrate_oauth.py` - Add OAuth2 support to existing installations
- `migrate_save_sync.py` - Add save sync tables and config

### Running Migrations
```bash
python migrate_oauth.py
python migrate_save_sync.py
```

---

## Performance Benchmarks

### OAuth Operations
- Token acquisition: ~200-500ms (one-time)
- Token refresh: ~100-300ms (every 25 minutes)
- API call overhead: +5ms

### Sync Operations
- ROM download: Network dependent
- Save file sync: ~100ms per file
- Collection sync: ~1-2 seconds for metadata
- 100 ROMs: ~10-20 minutes (8 workers)

### Database Operations
- Token load/save: +2ms
- ROM status update: <1ms
- Platform matching lookup: <1ms

---

## API Endpoints

### RomM API (Used)
- `POST /api/token` - OAuth2 authentication
- `GET /api/platforms/` - Platform list
- `GET /api/collections/` - Collection list
- `GET /api/collections/{id}` - Collection details
- `GET /api/roms/{id}` - ROM metadata
- `GET /api/roms/{id}/content/{filename}` - ROM download
- `GET /api/saves?rom_id={id}` - Save files list
- `POST /api/saves` - Upload save file
- `GET /api/states?rom_id={id}` - Save states list
- `POST /api/states` - Upload save state

### DeckRommSync API
- `GET /` - Status dashboard
- `GET /config` - Configuration page
- `GET /stats` - Statistics page
- `GET /log` - Log viewer
- `POST /api/trigger_sync` - Manual sync trigger
- `GET /api/sync_status` - Real-time sync status
- `POST /config/test_romm_connection` - Test RomM connectivity

---

## Security Considerations

### Current
- OAuth2 standard protocol
- Tokens stored in database
- Parameterized SQL queries
- HTTPS recommended

### Planned Improvements
- Token encryption (Fernet)
- HTTPS enforcement
- Token revocation support
- Audit logging
- Rate limiting

---

## Support & Troubleshooting

### Log Files
- `background_worker.log` - Sync operations
- `system.log` - Flask application logs

### Common Issues
1. **OAuth authentication failed**
   - Verify RomM v4.4.0+
   - Check credentials
   - Confirm scopes

2. **Save sync not working**
   - Check `enable_save_sync` in config
   - Verify file permissions
   - Check emulator paths

3. **ROMs not syncing**
   - Verify collection enabled
   - Check platform matching
   - Review background_worker.log

---

## Version History

### v2.0.0 (November 2025)
- OAuth2 authentication
- Bidirectional save sync
- Status page redesign
- Portrait cover art support

### v1.0.0
- Basic ROM synchronization
- Platform matching
- Collection-based sync
- Debug mode

---

## Contributing

See main [README.md](../../README.md) for contribution guidelines.

**Development workflow:**
1. Fork repository
2. Create feature branch
3. Add tests
4. Update documentation
5. Submit pull request

---

**Index Last Updated:** November 15, 2025  
**Documentation Version:** 2.0.0
