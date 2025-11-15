# Recommended Improvements

**Project:** DeckRommSync-Rivera  
**Version:** 2.0.0  
**Date:** November 15, 2025

---

## Overview

Prioritized list of improvements for DeckRommSync. Each item includes priority level, effort estimate, and implementation guidance optimized for LLM understanding.

---

## Priority 1: Critical (Security & Stability) 🔴

### 1.1 Token Encryption
**Effort:** 2 days | **Impact:** Security

**Problem:** OAuth tokens stored in plain text in database

**Solution:**
```python
from cryptography.fernet import Fernet

class TokenEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

**Files to modify:**
- `classes/DeckRommSyncDatabase.py` - Add encryption layer
- `classes/RommAPIHelper.py` - Encrypt before save, decrypt after load
- `config.json` - Store encryption key (or use env variable)

---

### 1.2 HTTPS Enforcement
**Effort:** 1 day | **Impact:** Security

**Problem:** HTTP allows password interception

**Solution:**
- Generate self-signed certificate for Steam Deck
- Add Flask SSL context
- Warn users if OAuth over HTTP

**Implementation:**
```python
# app.py
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('cert.pem', 'key.pem')  # Or use adhoc
    )
```

---

### 1.3 Database Connection Pooling
**Effort:** 1 day | **Impact:** Stability

**Problem:** Single SQLite connection shared across threads causes locks

**Solution:**
```python
from queue import Queue
import threading

class ConnectionPool:
    def __init__(self, db_path: str, size: int = 5):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            self.pool.put(conn)
    
    def get_connection(self):
        return self.pool.get()
    
    def return_connection(self, conn):
        self.pool.put(conn)
```

**Files to modify:**
- `classes/DeckRommSyncDatabase.py` - Implement connection pool

---

### 1.4 Error Recovery System
**Effort:** 2 days | **Impact:** Reliability

**Problem:** Failed syncs have no retry logic, status remains stuck

**Solution:**
- Set `sync_status = 2` on errors
- Add retry counter field
- Implement exponential backoff
- UI button to retry failed ROMs

**Database change:**
```sql
ALTER TABLE roms ADD COLUMN retry_count INTEGER DEFAULT 0;
ALTER TABLE roms ADD COLUMN last_error TEXT;
```

**Implementation:**
```python
def sync_with_retry(func, rom_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func(rom_id)
        except Exception as e:
            if attempt == max_retries - 1:
                db.update('roms', 
                    {'sync_status': 2, 'last_error': str(e)},
                    where='roms_id = ?', params=(rom_id,))
                raise
            time.sleep(2 ** attempt)
```

---

## Priority 2: Performance & UX 🟡

### 2.1 Async Downloads with Progress
**Effort:** 3 days | **Impact:** UX

**Problem:** No per-ROM download progress visible

**Solution:**
- Add `download_progress` field (0-100)
- Update during chunked download
- WebSocket or polling to display in UI

**Database change:**
```sql
ALTER TABLE roms ADD COLUMN download_progress INTEGER DEFAULT 0;
ALTER TABLE roms ADD COLUMN download_speed_mbps REAL;
ALTER TABLE roms ADD COLUMN eta_seconds INTEGER;
```

**Implementation:**
```python
def download_rom_with_progress(rom_id, url, dest):
    total_size = int(requests.head(url).headers.get('content-length', 0))
    downloaded = 0
    
    with requests.get(url, stream=True) as r:
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                progress = int((downloaded / total_size) * 100)
                db.update('roms', {'download_progress': progress}, 
                         where='roms_id = ?', params=(rom_id,))
```

---

### 2.2 Selective ROM Sync
**Effort:** 2 days | **Impact:** UX

**Problem:** Can only enable/disable entire collections

**Solution:**
- Add checkbox per ROM in UI
- Add `user_enabled` field to roms table
- Sync only ROMs with `user_enabled = 1`

**Database change:**
```sql
ALTER TABLE roms ADD COLUMN user_enabled INTEGER DEFAULT 1;
```

---

### 2.3 Save File Preview
**Effort:** 2 days | **Impact:** UX

**Problem:** Users can't see save file details before syncing

**Solution:**
- Parse save file metadata (game time, level, etc.)
- Display in modal with save count
- Show last played timestamp

---

### 2.4 Bandwidth Limiting
**Effort:** 1 day | **Impact:** Performance

**Problem:** Downloads can saturate network

**Solution:**
```python
import time

class RateLimiter:
    def __init__(self, max_bytes_per_sec: int):
        self.max_bytes = max_bytes_per_sec
        self.allowance = max_bytes_per_sec
        self.last_check = time.time()
    
    def throttle(self, bytes_sent: int):
        current = time.time()
        time_passed = current - self.last_check
        self.allowance += time_passed * self.max_bytes
        self.allowance = min(self.allowance, self.max_bytes)
        
        if bytes_sent > self.allowance:
            sleep_time = (bytes_sent - self.allowance) / self.max_bytes
            time.sleep(sleep_time)
            self.allowance = 0
        else:
            self.allowance -= bytes_sent
        
        self.last_check = current
```

**Config:**
```json
{
  "sync": {
    "max_download_speed_mbps": 50
  }
}
```

---

## Priority 3: Features & Polish 🟢

### 3.1 Webhook Notifications
**Effort:** 1 day | **Impact:** UX

**Problem:** No notifications when sync completes

**Solution:**
- Discord webhook integration
- Email via SMTP
- Custom webhook URLs

**Config:**
```json
{
  "notifications": {
    "discord_webhook": "https://discord.com/api/webhooks/...",
    "email": "user@example.com",
    "notify_on_error": true,
    "notify_on_complete": true
  }
}
```

---

### 3.2 Scheduled Syncs
**Effort:** 1 day | **Impact:** UX

**Problem:** Sync interval is hardcoded

**Solution:**
- Add cron-like scheduler
- UI to configure sync times
- Pause during specified hours

**Config:**
```json
{
  "sync": {
    "schedule": "0 */6 * * *",  // Every 6 hours
    "pause_hours": [0, 1, 2, 3, 4, 5]  // Midnight to 6am
  }
}
```

---

### 3.3 Multi-Destination Support
**Effort:** 3 days | **Impact:** Features

**Problem:** Can only sync to one Steam Deck path

**Solution:**
- Support multiple destination paths
- Sync same collection to different devices
- Per-destination sync status

**Database change:**
```sql
CREATE TABLE sync_destinations (
    id INTEGER PRIMARY KEY,
    name TEXT,
    path TEXT,
    enabled INTEGER DEFAULT 1
);

ALTER TABLE roms ADD COLUMN destination_id INTEGER;
```

---

### 3.4 Docker Support
**Effort:** 1 day | **Impact:** Deployment

**Problem:** Manual setup required

**Solution:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ROMMSYNC_PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  deckrommsync:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./deckrommsync.db:/app/deckrommsync.db
      - /path/to/retrodeck:/retrodeck
    environment:
      - ROMMSYNC_PORT=5000
```

---

### 3.5 Configuration Wizard
**Effort:** 2 days | **Impact:** UX

**Problem:** Complex first-time setup

**Solution:**
- Step-by-step wizard on first run
- Auto-detect RetroDECK path
- Test RomM connection
- Recommend optimal settings

---

### 3.6 Health Dashboard
**Effort:** 1 day | **Impact:** Monitoring

**Problem:** No system health visibility

**Solution:**
- `/health` endpoint
- Check RomM connectivity
- Disk space warnings
- Database health
- Background worker status

**Response:**
```json
{
  "status": "healthy",
  "romm_connection": "ok",
  "disk_space_gb": 245.8,
  "database_size_mb": 12.4,
  "background_worker": "running",
  "last_sync": "2025-11-15T10:30:00Z"
}
```

---

## Priority 4: Code Quality 🔵

### 4.1 Type Hints
**Effort:** 2 days | **Impact:** Maintainability

**Problem:** No type annotations

**Solution:**
```python
from typing import Optional, List, Dict, Any

def getSavesByRomID(self, romID: int) -> Optional[List[Dict[str, Any]]]:
    """Get all saves for a ROM"""
    ...
```

---

### 4.2 Logging Rotation
**Effort:** 0.5 days | **Impact:** Maintenance

**Problem:** Log files grow indefinitely

**Solution:**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'background_worker.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

### 4.3 Configuration Validation
**Effort:** 1 day | **Impact:** UX

**Problem:** Invalid config causes runtime errors

**Solution:**
```python
from pydantic import BaseModel, HttpUrl, validator

class SyncConfig(BaseModel):
    max_workers: int
    max_download_speed_mbps: Optional[int]
    
    @validator('max_workers')
    def validate_workers(cls, v):
        if v < 1 or v > 32:
            raise ValueError('max_workers must be 1-32')
        return v
```

---

### 4.4 API Rate Limiting
**Effort:** 1 day | **Impact:** Reliability

**Problem:** May overwhelm RomM server

**Solution:**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/trigger_sync', methods=['POST'])
@limiter.limit("5 per minute")
def trigger_sync():
    ...
```

---

## Implementation Priority Order

### Week 1-2: Security & Stability
1. Token encryption (1.1)
2. Error recovery system (1.4)
3. Database connection pooling (1.3)

### Week 3-4: Performance
1. Download progress (2.1)
2. Bandwidth limiting (2.4)
3. Logging rotation (4.2)

### Week 5-6: Features
1. Webhook notifications (3.1)
2. Scheduled syncs (3.2)
3. Docker support (3.4)

### Week 7-8: Polish
1. Configuration wizard (3.5)
2. Health dashboard (3.6)
3. Type hints (4.1)

---

## Effort Estimates

**Total:** ~35 days of development

**By Priority:**
- P1 (Critical): 6 days
- P2 (Performance): 8 days
- P3 (Features): 10 days
- P4 (Code Quality): 4.5 days

**Team Size:** 1 developer working alone: ~7-8 weeks

---

## Success Metrics

**After Implementation:**
- Zero plain-text tokens
- <1% sync failure rate
- 50% reduction in user setup time
- 100% uptime for 30 days
- <5% performance overhead
- 90% test coverage

---

**Document Version:** 1.0  
**Last Updated:** November 15, 2025  
**Optimized for:** LLM consumption and implementation
