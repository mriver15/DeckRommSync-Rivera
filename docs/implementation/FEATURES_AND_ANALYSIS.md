# DeckRommSync - Feature Documentation & Analysis

**Version:** 1.0.0  
**Author:** PeriBluGaming  
**License:** MIT (Modified - No Selling)  
**Purpose:** Automated ROM synchronization from RomM to Steam Deck

---

## Executive Summary

DeckRommSync is a Flask-based web application that automates the synchronization of ROM files from a RomM server to a Steam Deck running RetroDeck. The application provides a web UI for configuration, monitoring, and management of ROM collections with automatic background synchronization.

---

## Core Features

### 1. **RomM API Integration**
- **Authentication:** HTTP Basic authentication with username/password
- **API Endpoints Used:**
  - `/heartbeat` - Server health check
  - `/platforms/` - Retrieve available gaming platforms
  - `/collections/` - List all ROM collections
  - `/collections/{id}` - Get specific collection details
  - `/roms/{id}` - Get ROM metadata
  - `/roms/{id}/content/{filename}` - Download ROM files

### 2. **Database Management (SQLite)**
Located in: `classes/DeckRommSyncDatabase.py`

**Tables (Inferred):**
- `config` - Application configuration (API URLs, credentials, paths)
  - Fields: `config_key`, `config_value`
- `collections` - RomM collections
  - Fields: `collections_id`, `name`, `rom_count`, `cover`, `collection_sync`
- `roms` - Individual ROM files
  - Fields: `roms_id`, `collections_id`, `name`, `url_cover`, `filename`, `platform_fs_slug`, `platform_id`, `sync_status`
- `platforms_matching` - Platform name mapping
  - Fields: `romm_platform_id`, `romm_platform_name`, `steamdeck_platform_name`

**Database Operations:**
- ✅ Insert with duplicate handling
- ✅ Update with conditions
- ✅ Select with filtering
- ✅ Dictionary-based result sets
- ❌ No delete operations implemented
- ❌ No transactions
- ❌ No connection pooling

### 3. **Background Worker (Automated Sync)**
Located in: `classes/BackgroundWorker.py`

**Scheduler Configuration:**
- **Interval:** Every 1 minute (configurable in code)
- **Engine:** APScheduler BackgroundScheduler
- **Logging:** Dedicated log file (`background_worker.log`)

**Sync Operations:**

#### a) Collection Synchronization (`sync_rommCollections`)
1. Fetches all platforms from RomM API
2. Stores platform data in `platforms_matching` table
3. Retrieves all collections from RomM
4. For each collection:
   - Extracts cover image (handles array or single value)
   - Inserts collection metadata
   - Fetches all ROM IDs in the collection
   - For each ROM:
     - Retrieves ROM metadata
     - Inserts ROM record with sync_status = 0 (pending)

#### b) ROM Download Synchronization (`sync_copyRoms`)
1. Queries collections marked for sync (`collection_sync = 1`)
2. Retrieves Steam Deck RetroDeck path from config
3. For each collection:
   - Fetches ROMs with `sync_status = 0` (not yet synced)
   - For each ROM:
     - Gets platform matching info
     - Constructs destination path: `{steamdeck_path}/{platform_name}/{filename}`
     - Downloads ROM file from RomM
     - Updates `sync_status = 1` (completed)
     - Logs progress

**File Download Logic:**
- Chunked download (8192 bytes)
- URL-decoding of filenames (handles spaces, special chars)
- Duplicate file detection (skips if exists)
- Creates directories as needed

### 4. **Web Interface (Flask)**

#### Routes & Pages:

**`/` - Status Dashboard**
- Displays all collections with `collection_sync = 1`
- Shows ROMs per collection with sync status icons:
  - 🟡 `sync_status = 0` - Pending/In Progress
  - 🟢 `sync_status = 1` - Completed
  - 🔴 `sync_status = 2` - Error
- Lists ROM details: name, cover image, platform
- Dropdown menu per ROM:
  - "Show Details" (not implemented)
  - "Reset Sync Status" (resets to 0)
- Collapsible collection views
- Real-time data from database

**`/config` - Configuration Page**

Three configuration sections:

1. **RomM API Settings**
   - RomM API Base URL
   - Username
   - Password
   - Updates `config` table

2. **Sync Collections**
   - Checkbox list of all collections
   - Enable/disable sync per collection
   - Updates `collection_sync` field

3. **Platform Matching**
   - Steam Deck system path configuration
   - Table mapping RomM platform names to RetroDeck folder names
   - Individual save per platform
   - Critical for correct ROM placement

**`/log` - Log Viewer**
- Reads `background_worker.log`
- Groups log entries by sync session
- Displays in reverse chronological order
- Shows sync start/finish timestamps
- Expandable log sections

#### API Endpoints:

**`POST /config/config_romm_api_settings`**
- Updates RomM API configuration
- Redirects to config page

**`POST /config/config_collection_sync_settings`**
- Updates collection sync flags
- Processes checkbox array
- Redirects to config page

**`POST /config/config_platform_matching`**
- Updates single platform mapping
- Redirects to config page

**`POST /config/config_steamdeck_platform_path`**
- Updates RetroDeck base path
- Redirects to config page

**`POST /dropdown/reset_status`**
- JSON endpoint
- Resets ROM sync_status to 0
- Returns JSON response
- Triggers page reload

### 5. **Logging System**

Two separate loggers:

**System Logger** (`system.log`)
- Flask application events
- Page access logs
- Configuration loads

**Background Worker Logger** (`background_worker.log`)
- Sync operations
- ROM download progress
- Collection processing
- Error tracking
- Format: `YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE`

### 6. **Frontend (Bulma CSS)**

**Technologies:**
- Bulma CSS Framework (v1.0.2)
- Font Awesome Icons (v6.7.2)
- Custom CSS for extensions
- Vanilla JavaScript (no framework)

**UI Components:**
- Responsive navbar
- Card-based layouts
- Form controls
- Tables with inline editing
- Dropdowns
- Collapsible sections
- Custom icon styling

**JavaScript Features:**
- Toggle collection visibility
- Dropdown menu activation
- AJAX status reset (Fetch API)
- Auto page reload after updates

---

## Configuration Files

### `config.json`
```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 5000
    },
    "database": {
        "name": "deckrommsync.db",
        "type": "sqlite"
    }
}
```

### `requirements.txt`
- APScheduler==3.11.0 - Background task scheduling
- Django==3.1 ⚠️ **ISSUE: Not used, bloat dependency**
- Flask==3.1.0 - Web framework
- Requests==2.32.3 - HTTP library

---

## Architecture Analysis

### Strengths ✅

1. **Clean Separation of Concerns**
   - Database layer abstracted
   - API helper isolated
   - Background worker separate from web app

2. **User-Friendly Web Interface**
   - Visual status indicators
   - Easy configuration
   - Log monitoring

3. **Robust File Handling**
   - Duplicate detection
   - Chunked downloads
   - Directory creation

4. **Flexible Platform Mapping**
   - Manual override capability
   - Per-platform configuration

### Issues & Bugs 🐛

#### Critical Issues:

1. **Django Import Error** (Line 2, `app.py`)
   ```python
   from django.shortcuts import render  # NEVER USED!
   ```
   - Django is imported but never used
   - Will cause import errors if Django not installed
   - Should be removed

2. **Thread Safety Issues**
   - SQLite connection created with `check_same_thread=False`
   - Shared across multiple threads (Flask + Background Worker)
   - Can cause database locks and corruption
   - **Solution:** Use connection pooling or separate connections per thread

3. **No Error Handling for API Failures**
   - If RomM API is down, sync will fail silently
   - No retry logic
   - No user notification of failures

4. **Duplicate Insert Logic**
   - `insert()` method doesn't handle duplicates
   - Will fail on primary key violations
   - Should use `INSERT OR REPLACE` or `INSERT OR IGNORE`

5. **Password Stored in Plain Text**
   - Config table stores password unencrypted
   - Visible in database
   - **Security Risk**

#### Medium Issues:

6. **No Sync Status = 2 (Error) Handling**
   - UI shows error icon for status 2
   - But nothing sets status to 2
   - No error recovery mechanism

7. **Inefficient API Calls**
   - `sync_rommCollections` fetches ROMs individually
   - Should batch if API supports it
   - Creates N+1 query problem

8. **Hard-coded Scheduler Interval**
   - Fixed at 1 minute in code
   - Should be configurable via config.json or UI

9. **No Progress Indicators**
   - User can't see active downloads
   - No percentage complete
   - No ETA

10. **Memory Issues with Large Files**
    - Entire file loaded in memory during download
    - Could fail with very large ROMs
    - Better to stream directly to disk

#### Minor Issues:

11. **Inconsistent Naming**
    - `romMAPIBaseUrl` (camelCase)
    - `background_logger` (snake_case)
    - Should standardize

12. **No Database Migrations**
    - Schema changes require manual updates
    - No version tracking

13. **No Input Validation**
    - Form inputs not sanitized
    - Could lead to SQL injection (using parameterized queries helps, but still risky)
    - No URL validation

14. **Comments in German (Now Fixed)**
    - Previously had mixed language comments

15. **No Tests**
    - No unit tests
    - No integration tests
    - Hard to maintain

16. **Logging Not Rotating**
    - Log files will grow indefinitely
    - Could fill disk space

17. **No Authentication on Web UI**
    - Anyone on network can access
    - Can change configuration
    - Security risk

---

## Improvement Recommendations

### High Priority 🔴

1. **Remove Django Dependency**
   ```python
   # Remove this line from app.py:
   from django.shortcuts import render
   ```
   Update requirements.txt to remove Django

2. **Fix Thread Safety**
   - Create separate database connections for Flask and Background Worker
   - Or use SQLite's WAL mode
   - Or implement proper connection pooling

3. **Add Error Handling & Retry Logic**
   ```python
   # Example:
   def sync_with_retry(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               time.sleep(2 ** attempt)
   ```

4. **Implement Proper Duplicate Handling**
   ```python
   query = f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})"
   ```

5. **Add Basic Authentication**
   - Use Flask-Login or Flask-HTTPAuth
   - Protect all routes
   - Store hashed passwords

6. **Encrypt Sensitive Data**
   - Use cryptography library
   - Encrypt passwords before storing
   - Environment variables for secrets

### Medium Priority 🟡

7. **Make Scheduler Configurable**
   - Add to config.json:
     ```json
     "sync_interval_minutes": 5
     ```

8. **Add Error Status Handling**
   - Wrap downloads in try/except
   - Set `sync_status = 2` on failure
   - Log error details
   - Add retry button in UI

9. **Implement Progress Tracking**
   - Add `download_progress` field to roms table
   - Update during download
   - Show in UI with progress bar

10. **Add Database Migrations**
    - Use Alembic or Flask-Migrate
    - Version control schema changes

11. **Input Validation**
    - Validate URLs (regex or validators library)
    - Sanitize all form inputs
    - Check file paths

12. **Log Rotation**
    ```python
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(
        'background_worker.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    ```

### Low Priority 🟢

13. **Add Unit Tests**
    - pytest for backend
    - Test database operations
    - Mock API calls

14. **API Rate Limiting**
    - Respect RomM server limits
    - Add delays between requests

15. **Better UI/UX**
    - Toast notifications
    - Real-time updates (WebSockets)
    - Dark/light theme toggle
    - Search/filter collections

16. **Export/Import Configuration**
    - Backup settings
    - Share configurations

17. **Multi-User Support**
    - User accounts
    - Per-user collections

18. **Statistics Dashboard**
    - Total ROMs synced
    - Disk space used
    - Sync history
    - Success/failure rates

---

## Expansion Ideas

### Feature Enhancements 🚀

1. **Selective ROM Sync**
   - Choose individual ROMs instead of entire collections
   - Filter by platform, genre, rating
   - Exclude certain ROMs

2. **Scheduled Syncs**
   - Set specific times for sync
   - Pause during gaming hours
   - Custom schedules per collection

3. **Bandwidth Management**
   - Download speed limits
   - Pause/resume downloads
   - Queue management

4. **ROM Metadata Sync**
   - Download cover art
   - Game descriptions
   - Save files sync

5. **Multi-Destination Support**
   - Sync to multiple Steam Decks
   - Cloud storage backup
   - NAS integration

6. **Webhook Notifications**
   - Discord notifications
   - Email alerts
   - Slack integration

7. **Advanced Filtering**
   - Only sync ROMs > X rating
   - Exclude certain regions
   - Language filtering

8. **Compression Support**
   - Auto-extract archives
   - Compress before transfer
   - CHD/ISO support

9. **Incremental Sync**
   - Only sync new/changed ROMs
   - Version tracking
   - Differential updates

10. **Mobile App**
    - iOS/Android companion
    - Remote management
    - Push notifications

### Technical Improvements 🛠️

1. **RESTful API**
   - JSON API for programmatic access
   - API documentation (OpenAPI/Swagger)
   - Rate limiting

2. **Docker Support**
   - Dockerfile
   - Docker Compose
   - Easy deployment

3. **Configuration Wizard**
   - First-run setup
   - Auto-detect RetroDeck path
   - Test RomM connection

4. **Health Checks**
   - Monitor RomM availability
   - Disk space warnings
   - Network connectivity checks

5. **Database Optimization**
   - Indexes on frequently queried fields
   - Query optimization
   - Vacuum/cleanup tasks

6. **Caching**
   - Cache API responses
   - Redis for session storage
   - Reduce API calls

---

## Data Flow Diagram

```
┌─────────────┐
│   RomM API  │
└──────┬──────┘
       │
       │ 1. Fetch Collections/ROMs
       │
       ▼
┌─────────────────────┐
│ BackgroundWorker    │
│  - sync_rommColl... │
│  - sync_copyRoms    │
└──────┬──────────────┘
       │
       │ 2. Store Metadata
       │
       ▼
┌─────────────────────┐
│  SQLite Database    │
│  - collections      │
│  - roms             │
│  - platforms_match  │
│  - config           │
└──────┬──────────────┘
       │
       │ 3. Read/Update
       │
       ▼
┌─────────────────────┐
│   Flask Web App     │
│  - Status Page      │
│  - Config Page      │
│  - Log Page         │
└──────┬──────────────┘
       │
       │ 4. User Interaction
       │
       ▼
┌─────────────────────┐
│   Web Browser       │
│  (Bulma UI)         │
└─────────────────────┘

Parallel Process:
┌─────────────┐
│   RomM API  │
└──────┬──────┘
       │
       │ 5. Download ROM Files
       │
       ▼
┌─────────────────────┐
│ BackgroundWorker    │
│  - downloadRom()    │
└──────┬──────────────┘
       │
       │ 6. Save to Disk
       │
       ▼
┌─────────────────────┐
│  Steam Deck         │
│  RetroDeck Folders  │
└─────────────────────┘
```

---

## File Structure

```
DeckRommSync-Rivera/
├── app.py                      # Main Flask application
├── config.json                 # Server configuration
├── requirements.txt            # Python dependencies
├── deckrommsync.db            # SQLite database
├── background_worker.log       # Background sync logs
├── system.log                  # System/Flask logs
├── README.md                   # Installation guide
├── LICENSE.md                  # MIT License (No Selling)
│
├── classes/
│   ├── BackgroundWorker.py     # Sync automation logic
│   ├── DeckRommSyncDatabase.py # Database abstraction layer
│   └── RommAPIHelper.py        # RomM API client
│
├── templates/
│   ├── base.html               # Base template (navbar, layout)
│   ├── status.html             # Status dashboard
│   ├── config.html             # Configuration page
│   └── log.html                # Log viewer
│
└── docs/
    ├── deckrommsync.png        # Screenshot
    └── platform_matching.png   # Platform config screenshot
```

---

## Database Schema (Inferred)

```sql
-- Config table
CREATE TABLE config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT
);

-- Example rows:
-- romm_api_base_url, http://romm:8080/api
-- romm_username, admin
-- romm_password, password123
-- steamdeck_retrodeck_path, /home/deck/retrodeck/roms

-- Collections table
CREATE TABLE collections (
    collections_id INTEGER PRIMARY KEY,
    name TEXT,
    rom_count INTEGER,
    cover TEXT,
    collection_sync INTEGER DEFAULT 0  -- 0=disabled, 1=enabled
);

-- ROMs table
CREATE TABLE roms (
    roms_id INTEGER PRIMARY KEY,
    collections_id INTEGER,
    name TEXT,
    url_cover TEXT,
    filename TEXT,
    platform_fs_slug TEXT,
    platform_id INTEGER,
    sync_status INTEGER DEFAULT 0,  -- 0=pending, 1=synced, 2=error
    FOREIGN KEY (collections_id) REFERENCES collections(collections_id)
);

-- Platform matching table
CREATE TABLE platforms_matching (
    romm_platform_id INTEGER PRIMARY KEY,
    romm_platform_name TEXT,
    steamdeck_platform_name TEXT
);
```

---

## Security Considerations ⚠️

### Current Security Issues:

1. **No Authentication:** Anyone on network can access
2. **Plain Text Passwords:** Stored unencrypted in database
3. **No HTTPS:** Traffic not encrypted
4. **No CSRF Protection:** Forms vulnerable to CSRF attacks
5. **No Input Validation:** SQL injection possible (mitigated by parameterized queries)
6. **Exposed Configuration:** Sensitive data in logs

### Recommended Security Measures:

1. Add Flask-Login for authentication
2. Use bcrypt/argon2 for password hashing
3. Implement HTTPS with SSL certificates
4. Add CSRF tokens (Flask-WTF)
5. Validate and sanitize all inputs
6. Move secrets to environment variables
7. Add rate limiting (Flask-Limiter)
8. Implement audit logging

---

## Performance Considerations

### Current Limitations:

1. **Synchronous Downloads:** One ROM at a time
2. **No Parallelization:** Sequential API calls
3. **Database Locks:** Single SQLite connection shared
4. **Memory Usage:** Large files loaded in memory
5. **No Caching:** Repeated API calls for same data

### Optimization Opportunities:

1. **Async Downloads:** Download multiple ROMs simultaneously
2. **Connection Pooling:** Reuse HTTP connections
3. **Database Indexing:** Speed up queries
4. **Stream Downloads:** Write directly to disk
5. **Cache API Responses:** Reduce RomM load
6. **Background Queue:** Use Celery or RQ for tasks

---

## Conclusion

DeckRommSync is a functional MVP for automating ROM synchronization from RomM to Steam Deck. The codebase is well-structured with clear separation of concerns, but has several critical issues that should be addressed before production use:

**Must Fix Before Production:**
- Remove Django dependency
- Fix thread safety issues
- Add authentication
- Implement error handling
- Encrypt passwords

**Recommended Next Steps:**
1. Fix critical bugs
2. Add comprehensive error handling
3. Implement security measures
4. Add progress tracking
5. Write tests
6. Create Docker deployment

The application has strong potential for expansion with features like selective sync, scheduling, notifications, and multi-device support. The clean architecture makes it relatively easy to extend and maintain once core issues are resolved.

---

## RomM v4.4.0 Update Analysis

**Analysis Date:** November 15, 2025  
**RomM Version:** 4.4.0 (Released November 10, 2025)  
**Current Implementation:** Basic Auth with RomM v3.x/v4.x API patterns

### Major Changes in RomM v4.4.0

RomM has undergone significant improvements since this project was originally built. The following sections detail new features and recommended integration strategies.

---

## New Features Available in RomM API

### 1. **OAuth2 Bearer Token Authentication** 🔐

**Current State:** Using HTTP Basic Auth (username/password on every request)

**RomM v4.4.0 Change:**
- Robust OAuth2 implementation with access and refresh tokens
- Access tokens: 30-minute expiry
- Refresh tokens: 7-day expiry
- Scope-based permissions (read/write/admin)

**API Endpoints:**
```
POST /api/token
  grant_type: "password"
  username: "admin"
  password: "password"
  scope: "roms.read platforms.read"
  
Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires": 1800
}
```

**Benefits:**
- ✅ More secure (no credential exposure in every request)
- ✅ Better for long-running background workers
- ✅ Token refresh without re-authentication
- ✅ Scoped permissions prevent over-privileged access
- ✅ Standard OAuth2 flow compatible with other tools

**Required Scopes for DeckRommSync:**
- `platforms.read` - Read platform data
- `roms.read` - Read ROM metadata and download files
- `collections.read` - Read collection information
- `assets.read` - Optional: Download cover art, screenshots

**Implementation Impact:** MEDIUM
- Requires refactoring `RommAPIHelper.py`
- Add token storage in database or memory
- Implement token refresh logic
- Backward compatibility concerns if supporting older RomM

---

### 2. **Save Files & Save States API** 💾

**Current State:** Not implemented (ROMs only)

**RomM v4.4.0 Endpoints:**
```
GET /api/saves?rom_id={id}
POST /api/saves (upload save file)
GET /api/states?rom_id={id}
POST /api/states (upload save state)
```

**Schema:**
```python
{
  "id": int,
  "rom_id": int,
  "user_id": int,
  "emulator": str,
  "file_name": str,
  "file_size_bytes": int,
  "created_at": datetime,
  "updated_at": datetime
}
```

**Use Case for Steam Deck:**
Critical feature for portable gaming! Users often:
1. Play games on RomM server (via EmulatorJS)
2. Want to continue on Steam Deck
3. Need save file synchronization

**Benefits:**
- ✅ Seamless game continuation across devices
- ✅ Cloud save backup
- ✅ Support for multiple save states per ROM
- ✅ Emulator-specific save formats

**Implementation Impact:** HIGH
- New database tables: `saves`, `save_states`
- New sync operations in BackgroundWorker
- UI for managing save files
- Bidirectional sync (upload Steam Deck saves back to RomM)
- Complex: Emulator format detection, file path mapping

**Database Schema Addition:**
```sql
CREATE TABLE saves (
    id INTEGER PRIMARY KEY,
    rom_id INTEGER,
    emulator TEXT,
    file_name TEXT,
    local_path TEXT,
    synced_at DATETIME,
    FOREIGN KEY (rom_id) REFERENCES roms(roms_id)
);

CREATE TABLE save_states (
    id INTEGER PRIMARY KEY,
    rom_id INTEGER,
    emulator TEXT,
    file_name TEXT,
    local_path TEXT,
    screenshot_path TEXT,  -- Optional preview
    synced_at DATETIME,
    FOREIGN KEY (rom_id) REFERENCES roms(roms_id)
);
```

---

### 3. **Alternative Media Assets** 🎨

**Current State:** Only cover images (`url_cover`)

**RomM v4.4.0 Media Types:**
```yaml
- box2d        # Normal cover (default)
- box3d        # 3D box art
- physical     # Disc/cartridge image
- miximage     # Combined media composition
- screenshot   # In-game screenshot
- title_screen # Title screen
- marquee      # Arcade marquee
- logo         # Transparent logo
- fanart       # Fan-created artwork
- bezel        # Emulator bezel
- manual       # PDF manual
- video        # Gameplay video
```

**Benefits:**
- ✅ Enhanced EmulationStation/ES-DE integration
- ✅ Better visual library on Steam Deck
- ✅ Support for modern frontend scrapers
- ✅ PDF manuals for authentic retro experience

**Implementation Impact:** LOW-MEDIUM
- Extend `roms` table with media URLs
- Optional: Download media to Steam Deck
- Use case: ES-DE gamelist.xml generation
- Storage consideration: Videos can be large (10-100MB each)

---

### 4. **Hash-based ROM Verification** 🔍

**Current State:** Filename-based matching only

**RomM v4.4.0 Feature:**
- Pre-calculated hashes for ROM files (MD5, SHA1, CRC32)
- Screenscraper database matching
- Improved metadata accuracy

**Benefits:**
- ✅ Verify ROM file integrity
- ✅ Detect corrupt downloads
- ✅ Match ROMs even with renamed files
- ✅ Better duplicate detection

**Implementation Impact:** LOW
- Store hash in database
- Optional: Verify downloaded files
- Use case: Resume interrupted downloads, verify existing files

---

### 5. **ES-DE Gamelist.xml Support** 📋

**Current State:** No metadata export

**RomM v4.4.0 Feature:**
- Parse ES-DE `gamelist.xml` for metadata import
- Export ROM data to ES-DE format

**Benefits:**
- ✅ ES-DE integration (popular Steam Deck frontend)
- ✅ Preserve existing metadata from Steam Deck
- ✅ Standardized metadata format
- ✅ Better emulator frontend integration

**Implementation Impact:** MEDIUM
- Export endpoint: Generate gamelist.xml per platform
- Place in correct RetroDeck directory structure

---

### 6. **Statistics Endpoint** 📊

**Current State:** Custom statistics dashboard with `sync_history` table

**RomM v4.4.0 Endpoint:**
```
GET /api/stats
Response:
{
  "PLATFORMS": 15,
  "ROMS": 2847,
  "SAVES": 142,
  "STATES": 89,
  "SCREENSHOTS": 523,
  "TOTAL_FILESIZE_BYTES": 52428800000
}
```

**Benefits:**
- ✅ Complement existing statistics dashboard
- ✅ Show RomM server stats vs. local sync stats
- ✅ Display: "X of Y ROMs synced"

**Implementation Impact:** LOW

---

### 7. **Task Management API** ⚙️

**Current State:** Custom sync tracking with `sync_status` field

**RomM v4.4.0 Endpoints:**
```
GET /api/tasks - List all tasks with status
POST /api/tasks/run - Trigger all tasks
POST /api/tasks/run/{task_name} - Trigger specific task
```

**Benefits:**
- ✅ Standardized task monitoring
- ✅ Built-in task queuing
- ✅ Better visibility in RomM admin panel

**Implementation Impact:** MEDIUM

---

## Implementation Recommendations

### Priority 1: Critical Updates (Security & Reliability) 🔴

#### 1.1 OAuth2 Token Authentication
**Effort:** 2-3 days | **Impact:** HIGH

**Changes Required:**
- `RommAPIHelper.py`: Add token management
- `DeckRommSyncDatabase.py`: Store tokens (encrypted)
- `BackgroundWorker.py`: Use tokens instead of Basic Auth

**Implementation Sketch:**
```python
class RommAPIHelper:
    def login_oauth(self, username: str, password: str, scopes: list):
        """Authenticate using OAuth2 password grant"""
        response = requests.post(
            f"{self.api_base_url}/token",
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": " ".join(scopes)
            }
        )
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires"])
    
    def refresh_access_token(self):
        """Refresh expired access token"""
        response = requests.post(
            f"{self.api_base_url}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
        )
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=token_data["expires"])
```

---

#### 1.2 Save Files & Save States Synchronization
**Effort:** 5-7 days | **Impact:** VERY HIGH

**Features:**
- Download save files from RomM
- Upload Steam Deck saves to RomM
- Bidirectional sync with conflict resolution

**Database Schema:**
```sql
CREATE TABLE rom_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rom_id INTEGER,
    romm_save_id INTEGER,
    emulator TEXT,
    file_name TEXT,
    local_path TEXT,
    remote_updated_at DATETIME,
    local_updated_at DATETIME,
    sync_status INTEGER DEFAULT 0,
    FOREIGN KEY (rom_id) REFERENCES roms(roms_id)
);
```

**BackgroundWorker Addition:**
```python
def sync_save_files(self):
    """Bidirectional save file synchronization"""
    synced_roms = self.db.select("roms", where="sync_status = 1")
    
    for rom in synced_roms:
        saves = self.romm_api.get_saves(rom_id=rom['roms_id'])
        
        for save in saves:
            local_path = self._get_save_path(rom, save)
            
            # Check if local save is newer
            if os.path.exists(local_path):
                local_mtime = datetime.fromtimestamp(os.path.getmtime(local_path))
                remote_mtime = datetime.fromisoformat(save['updated_at'])
                
                if local_mtime > remote_mtime:
                    self._upload_save(rom['roms_id'], local_path, save['emulator'])
                    continue
            
            # Download save from RomM
            self.romm_api.download_save(save['id'], local_path)
```

---

### Priority 2: Enhanced Features (User Experience) 🟡

#### 2.1 Alternative Media Assets Download
**Effort:** 1-2 days | **Impact:** MEDIUM

- Download 3D box art, screenshots, manuals
- Generate ES-DE gamelist.xml with media paths

#### 2.2 ES-DE Gamelist.xml Export
**Effort:** 2-3 days | **Impact:** MEDIUM

- Generate per-platform gamelist.xml
- Place in RetroDeck directory structure

#### 2.3 Hash Verification
**Effort:** 1 day | **Impact:** LOW-MEDIUM

- Verify downloaded ROM integrity
- Detect corrupt files

---

### Priority 3: Integration & Polish (Nice-to-Have) 🟢

#### 3.1 RomM Statistics Integration
**Effort:** 0.5 day | **Impact:** LOW

- Add server stats to dashboard
- Show "X of Y ROMs synced"

#### 3.2 Task API Integration
**Effort:** 2-3 days | **Impact:** LOW

- Replace custom sync tracking with RomM tasks

---

## Implementation Roadmap

### Phase 1: Authentication & Security (Week 1-2)
- [ ] Implement OAuth2 token authentication
- [ ] Add token storage and encryption
- [ ] Backward compatibility with Basic Auth
- [ ] Update configuration UI
- [ ] Test token refresh logic

### Phase 2: Save File Synchronization (Week 3-5)
- [ ] Database schema for saves/states
- [ ] API methods for save operations
- [ ] Download saves from RomM
- [ ] Upload Steam Deck saves to RomM
- [ ] Conflict resolution logic
- [ ] UI for save management

### Phase 3: Media Assets & ES-DE (Week 6-7)
- [ ] Download alternative media types
- [ ] Generate ES-DE gamelist.xml
- [ ] Media path configuration
- [ ] Storage optimization

### Phase 4: Verification & Polish (Week 8)
- [ ] Hash verification for downloads
- [ ] RomM statistics integration
- [ ] Performance testing
- [ ] Documentation updates

---

## Configuration Changes

### config.json Updates
```json
{
  "romm": {
    "use_oauth": true,
    "oauth_scopes": [
      "platforms.read",
      "roms.read",
      "collections.read",
      "assets.read",
      "assets.write"
    ]
  },
  "sync": {
    "enable_save_sync": true,
    "enable_state_sync": true,
    "download_media": true,
    "media_types": ["box3d", "screenshot", "manual"],
    "skip_videos": true,
    "generate_gamelist_xml": true,
    "verify_hashes": true
  }
}
```

---

## Success Metrics

**Key Performance Indicators:**
- Authentication Reliability: 99.9% successful OAuth token refreshes
- Save Sync Accuracy: 100% save files synced without corruption
- User Adoption: 80%+ users enable save sync within 1 month
- Performance: <5% increase in sync time with new features
- Error Rate: <1% failed save file syncs

---

**RomM v4.4.0 Analysis Updated:** November 15, 2025  
**Implementation Status:** Planning Phase  
**Estimated Completion:** 8 weeks (full implementation)

---

**Document Generated:** November 15, 2025  
**Codebase Version:** 1.0.0  
**Analysis Depth:** Complete codebase review with recommendations
