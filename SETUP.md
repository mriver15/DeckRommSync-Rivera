# Quick Setup Guide

**For New Installations on Different Devices**

## First Time Setup

### 1. Clone Repository

```bash
git clone https://github.com/mriver15/DeckRommSync-Rivera.git
cd DeckRommSync-Rivera
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Application

```bash
python app.py
```

**That's it!** The application will automatically:
- ✅ Create the database on first run
- ✅ Initialize all required tables
- ✅ Add default configuration values
- ✅ Be ready for configuration

### 5. Configure Settings

Open `http://localhost:5000/config` and set:
- RomM API URL: `http://your-romm-server:8080/api`
- Username & Password
- Choose OAuth2 (recommended for RomM v4.4.0+)
- Platform mappings
- Enable collections

### 6. Sync

Click "Sync Now" on the status page!

---

## Troubleshooting

### Database Issues

The database is automatically initialized on first run. If you encounter issues:

```bash
# Delete the database and restart the app
rm deckrommsync.db
python app.py
```

The app will recreate all tables with default configuration.

### Reset Configuration

To reset to defaults while keeping your ROMs data:

```bash
# Use the init_database.py script to recreate just config entries
python init_database.py
```

---

## Files You Need

**Required:**
- `app.py` - Main application
- `classes/` - Core logic
- `templates/` - Web UI
- `config.json` - Server config
- `requirements.txt` - Dependencies

**Auto-Generated:**
- `deckrommsync.db` - Created on first run
- `*.log` - Generated at runtime

**Not Needed:**
- `debug_output/` - Debug mode only
- `venv/` - Create fresh per device
- `init_database.py` - Optional (auto-init built into app.py)

---

## Quick Reference

### Start App

```bash
source venv/bin/activate  # If not already activated
python app.py
```

### Update from GitHub

```bash
git pull origin main
pip install -r requirements.txt  # In case dependencies changed
```

The app will automatically create any new database tables on startup.

---

**See [README.md](README.md) for full documentation**
