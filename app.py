from flask import Flask, redirect, render_template, request, jsonify, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler
from classes.RommAPIHelper import RommAPIHelper
from classes.DeckRommSyncDatabase import DeckRommSyncDatabase
from classes.BackgroundWorker import BackgroundWorker
from classes.InputValidator import InputValidator, ValidationError
from classes.SyncStatistics import SyncStatistics
import json
import os
import logging

# Logging for the Background Worker
background_logger = logging.getLogger("background_worker")
background_logger.setLevel(logging.INFO)
background_handler = logging.FileHandler("background_worker.log", encoding="utf-8")
background_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
background_handler.setFormatter(background_formatter)
background_logger.addHandler(background_handler)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Set up System Logger
system_logger = logging.getLogger("system_logger")
system_logger.setLevel(logging.INFO)
system_handler = logging.FileHandler("system.log", encoding="utf-8")
system_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
system_handler.setFormatter(system_formatter)
system_logger.addHandler(system_handler)

def load_json_config(file_path="config.json"):
    """Loads the configuration from the JSON file."""
    system_logger.info("Load Config from File")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def initialize_database(db_name: str = "deckrommsync.db"):
    """
    Initialize database with all required tables and default configuration.
    Runs automatically on first app startup.
    """
    try:
        # Create database connection (this triggers _init_database() which creates tables)
        db = DeckRommSyncDatabase(db_name)
        
        # Check if config table has default values
        config_count = len(db.select('config'))
        if config_count == 0:
            print("First run detected - initializing default configuration...")
            
            default_configs = [
                ('romm_api_base_url', ''),
                ('romm_username', ''),
                ('romm_password', ''),
                ('steamdeck_retrodeck_path', '/home/deck/retrodeck/roms'),
                ('use_oauth', '0'),
                ('oauth_scopes', 'platforms.read,roms.read,collections.read,assets.read,assets.write'),
                ('enable_save_sync', '1'),
                ('enable_state_sync', '0'),
            ]
            
            for key, value in default_configs:
                db.insert('config', ['config_key', 'config_value'], (key, value))
            
            print(f"✓ Database initialized with {len(default_configs)} default configuration entries")
            print()
            print("⚠️  Next steps:")
            print("   1. Open http://localhost:5000/config in your browser")
            print("   2. Configure your RomM API URL, username, and password")
            print("   3. Enable collections to sync")
            print("   4. Click 'Sync Now' to start syncing")
            print()
        
        return True
    except Exception as e:
        system_logger.error(f"Database initialization failed: {e}")
        print(f"❌ Error initializing database: {e}")
        return False

# Initialize app_config at module level
app_config = load_json_config()

# Initialize database on startup (creates tables and default config if needed)
initialize_database(app_config.get("database", {}).get("name", "deckrommsync.db"))

# Global sync status tracking
sync_status = {
    "is_running": False,
    "current_step": "Idle",
    "progress": {
        "platforms_synced": 0,
        "collections_synced": 0,
        "roms_processed": 0,
        "roms_success": 0,
        "roms_error": 0,
        "total_roms": 0
    },
    "last_update": None,
    "start_time": None
}

def run_background_task():
    """Calls the `run()` method of the background class."""
    global sync_status
    
    # Prevent concurrent runs
    if sync_status["is_running"]:
        background_logger.warning("Sync already in progress, skipping this run")
        return
    
    from datetime import datetime
    
    try:
        # Mark sync as running
        sync_status["is_running"] = True
        sync_status["start_time"] = datetime.now().isoformat()
        sync_status["current_step"] = "Initializing"
        sync_status["last_update"] = datetime.now().isoformat()
        
        # Get debug mode settings from config
        debug_enabled = app_config.get("debug", {}).get("enabled", False)
        debug_output = app_config.get("debug", {}).get("output_folder", "./debug_output")
        max_workers = app_config.get("sync", {}).get("max_workers", 4)
        
        # Create Background Worker with debug mode settings
        bgWorker = BackgroundWorker(
            "deckrommsync.db", 
            background_logger,
            debug_mode=debug_enabled,
            debug_output_folder=debug_output,
            max_workers=max_workers
        )    
        background_logger.info("Background Task started...")
        if debug_enabled:
            background_logger.info(f"Running in DEBUG MODE - ROM metadata will be saved to {debug_output}")
        
        # Sync collections and platforms
        sync_status["current_step"] = "Syncing platforms and collections"
        sync_status["last_update"] = datetime.now().isoformat()
        bgWorker.sync_rommCollections()
        
        # Sync ROMs
        sync_status["current_step"] = "Syncing ROMs"
        sync_status["last_update"] = datetime.now().isoformat()
        bgWorker.sync_copyRoms()
        
        # Sync save files if enabled
        if app_config.get("sync", {}).get("enable_save_sync", False):
            sync_status["current_step"] = "Syncing save files"
            sync_status["last_update"] = datetime.now().isoformat()
            bgWorker.sync_save_files()
        
        background_logger.info("Background Task finished...")
        sync_status["current_step"] = "Completed"
        sync_status["last_update"] = datetime.now().isoformat()
        
    except Exception as e:
        background_logger.error(f"Background task error: {e}", exc_info=True)
        sync_status["current_step"] = f"Error: {str(e)}"
        sync_status["last_update"] = datetime.now().isoformat()
    finally:
        # Mark sync as finished
        sync_status["is_running"] = False

@app.route('/')
def status():  
    system_logger.info("Status Page")  
    db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))
    collection_db_result = db.select_as_dict("collections", ['*'], 'collection_sync = 1')    
    collections = []
    
    for collection in collection_db_result:
        roms_in_collection = db.select_as_dict("roms", ['*'], 'collections_id = ?', (collection["collections_id"],))
        
        # Get save file info for each ROM
        for rom in roms_in_collection:
            # Get saves for this ROM
            saves = db.select_as_dict("rom_saves", ['*'], 'rom_id = ?', (rom['roms_id'],))
            rom['saves'] = saves or []
            rom['save_count'] = len(saves) if saves else 0
            
            # Get states for this ROM
            states = db.select_as_dict("rom_states", ['*'], 'rom_id = ?', (rom['roms_id'],))
            rom['states'] = states or []
            rom['state_count'] = len(states) if states else 0
        
        collection["roms"] = roms_in_collection    
        collections.append(collection)

    return render_template('status.html', status="Server running", version="1.0.0", collections=collections)

@app.route('/stats')
def stats():
    """Statistics dashboard showing sync metrics and history."""
    system_logger.info("Statistics Page")
    
    try:
        stats_helper = SyncStatistics(app_config["database"].get("name", "deckrommsync.db"))
        
        # Get all statistics
        rom_stats = stats_helper.get_total_roms_stats()
        sync_history = stats_helper.get_sync_history(limit=20)
        success_rate = stats_helper.get_success_rate()
        total_synced = stats_helper.get_total_synced_count()
        platform_breakdown = stats_helper.get_platform_breakdown()
        disk_space = stats_helper.get_estimated_disk_space()
        sync_trends = stats_helper.get_sync_trends(days=7)
        collection_stats = stats_helper.get_collection_stats()
        
        return render_template('stats.html',
                             rom_stats=rom_stats,
                             sync_history=sync_history,
                             success_rate=success_rate,
                             total_synced=total_synced,
                             platform_breakdown=platform_breakdown,
                             disk_space=disk_space,
                             sync_trends=sync_trends,
                             collection_stats=collection_stats)
    except Exception as e:
        system_logger.error(f"Error loading statistics: {e}")
        flash(f"Error loading statistics: {str(e)}", "error")
        return redirect(url_for('status'))

@app.route('/config', methods=['GET', 'POST'])
def config():
    db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))
    # Get Config    
    config_result = db.select("config")    
    config_dict = {row[1]: row[2] for row in config_result}  # Convert the list to a dictionary    
    
    # Get Platform Matching
    platform_matching = db.select_as_dict("platforms_matching")

    # Get Collections
    collections = db.select_as_dict("collections")
    
    # Get OAuth token status if OAuth is enabled
    oauth_token = None
    if config_dict.get('use_oauth') == '1' or config_dict.get('use_oauth') == 'true':
        tokens = db.select_as_dict("oauth_tokens", order_by="id DESC", limit=1)
        if tokens:
            oauth_token = tokens[0]

    if request.method == 'POST':
        new_config = request.form.to_dict()
        # Save Config
    return render_template('config.html', config=config_dict, collections=collections, 
                         platform_matching=platform_matching, oauth_token=oauth_token)

# Update Romm API Settings
@app.route('/config/config_romm_api_settings', methods=['POST'])
def config_romm_api_settings():        
    try:
        # Validate inputs
        api_url = InputValidator.validate_url(
            request.form.get("romm_api_base_url"),
            "RomM API Base URL"
        )
        username = InputValidator.validate_username(
            request.form.get("romm_username"),
            "RomM Username"
        )
        password = InputValidator.validate_password(
            request.form.get("romm_password"),
            "RomM Password"
        )
        
        # Get OAuth settings
        use_oauth = request.form.get("use_oauth", "0")
        
        # Collect selected OAuth scopes
        oauth_scopes = []
        if use_oauth == "1":
            scope_fields = [
                'oauth_scope_platforms_read',
                'oauth_scope_roms_read',
                'oauth_scope_collections_read',
                'oauth_scope_assets_read',
                'oauth_scope_assets_write'
            ]
            for field in scope_fields:
                if field in request.form:
                    oauth_scopes.append(request.form[field])
        
        oauth_scopes_str = ','.join(oauth_scopes) if oauth_scopes else 'platforms.read,roms.read,collections.read'
        
        # Create Database Object
        db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))

        # Update Config in Database
        db.update("config", {"config_value": api_url}, "config_key = ?", ("romm_api_base_url",))
        db.update("config", {"config_value": username}, "config_key = ?", ("romm_username",))
        db.update("config", {"config_value": password}, "config_key = ?", ("romm_password",))
        db.update("config", {"config_value": use_oauth}, "config_key = ?", ("use_oauth",))
        db.update("config", {"config_value": oauth_scopes_str}, "config_key = ?", ("oauth_scopes",))
        
        # If OAuth is enabled, try to authenticate and get token
        if use_oauth == "1":
            try:
                api = RommAPIHelper(
                    api_base_url=api_url,
                    logger=system_logger,
                    db=db
                )
                api.login(
                    username=username,
                    password=password,
                    use_oauth=True,
                    scopes=oauth_scopes or ['platforms.read', 'roms.read', 'collections.read']
                )
                flash("RomM API settings updated and OAuth token obtained successfully", "success")
            except Exception as e:
                flash(f"Settings saved but OAuth authentication failed: {str(e)}", "warning")
                system_logger.warning(f"OAuth authentication failed: {e}")
        else:
            flash("RomM API settings updated successfully", "success")
        
        system_logger.info(f"RomM API settings updated: {api_url}, OAuth: {use_oauth}")
        
    except ValidationError as e:
        flash(f"Validation error: {str(e)}", "error")
        system_logger.warning(f"Validation error in RomM API settings: {e}")
    except Exception as e:
        flash(f"Error updating settings: {str(e)}", "error")
        system_logger.error(f"Error updating RomM API settings: {e}")
    
    return redirect(url_for('config'))

# Test RomM Connection
@app.route('/config/test_romm_connection', methods=['POST'])
def test_romm_connection():
    try:
        # Get form data
        api_url = request.form.get("romm_api_base_url")
        username = request.form.get("romm_username")
        password = request.form.get("romm_password")
        use_oauth = request.form.get("use_oauth", "0")
        
        # Collect OAuth scopes if enabled
        oauth_scopes = []
        if use_oauth == "1":
            scope_fields = [
                'oauth_scope_platforms_read',
                'oauth_scope_roms_read',
                'oauth_scope_collections_read',
                'oauth_scope_assets_read',
                'oauth_scope_assets_write'
            ]
            for field in scope_fields:
                if field in request.form:
                    oauth_scopes.append(request.form[field])
        
        # Create API helper
        api = RommAPIHelper(
            api_base_url=api_url,
            logger=system_logger
        )
        
        # Login
        if use_oauth == "1":
            api.login(
                username=username,
                password=password,
                use_oauth=True,
                scopes=oauth_scopes or ['platforms.read', 'roms.read', 'collections.read']
            )
        else:
            api.login(
                username=username,
                password=password,
                use_oauth=False
            )
        
        # Test connection with heartbeat
        heartbeat = api.getRommHeartbeat()
        
        if heartbeat:
            return jsonify({
                'success': True,
                'message': 'Connection successful',
                'auth_method': 'OAuth2' if use_oauth == "1" else 'Basic Auth'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Heartbeat failed - server may be unreachable'
            }), 400
            
    except Exception as e:
        system_logger.error(f"Connection test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Update Collection Sync Settings
@app.route('/config/config_collection_sync_settings', methods=['POST']) 
def config_collection_sync_settings():
    try:
        # Create Database Object
        db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))

        # Get Collections IDs from Form
        collections_ids = request.form.getlist("collections_id")    
        
        updated_count = 0
        for collections_id in collections_ids:
            # Validate collection ID
            try:
                validated_id = InputValidator.validate_collection_id(collections_id)
            except ValidationError as e:
                system_logger.warning(f"Invalid collection ID: {collections_id} - {e}")
                continue
            
            # Get Checkbox Value
            checkbox_value = "1" if f"collection_sync_{collections_id}" in request.form else "0"             
            db.update("collections", {"collection_sync": checkbox_value}, "collections_id = ?", (validated_id,))
            updated_count += 1
        
        flash(f"Updated {updated_count} collection(s)", "success")
        system_logger.info(f"Updated sync settings for {updated_count} collections")
        
    except Exception as e:
        flash(f"Error updating collection settings: {str(e)}", "error")
        system_logger.error(f"Error updating collection sync settings: {e}")

    return redirect(url_for('config'))

# Update Platform Matching
@app.route('/config/config_platform_matching', methods=['POST'])
def config_platform_matching():    
    try:
        # Validate inputs
        platform_id = InputValidator.validate_platform_id(
            request.form.get("romm_platform_id")
        )
        platform_name = InputValidator.validate_platform_name(
            request.form.get("steamdeck_platform_name"),
            "Steam Deck platform name"
        )
        
        # Create Database Object
        db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))

        # Update Config in Database
        db.update("platforms_matching", {"steamdeck_platform_name": platform_name}, "romm_platform_id = ?", (platform_id,))
        
        flash(f"Platform matching updated for platform ID {platform_id}", "success")
        system_logger.info(f"Platform matching updated: {platform_id} -> {platform_name}")
        
    except ValidationError as e:
        flash(f"Validation error: {str(e)}", "error")
        system_logger.warning(f"Validation error in platform matching: {e}")
    except Exception as e:
        flash(f"Error updating platform matching: {str(e)}", "error")
        system_logger.error(f"Error updating platform matching: {e}")
    
    return redirect(url_for('config'))

# Update Steamdeck Platform Path
@app.route('/config/config_steamdeck_platform_path', methods=['POST'])
def config_steamdeck_platform_path():    
    try:
        # Validate path input
        steamdeck_path = InputValidator.validate_path(
            request.form.get("steamdeck_path"),
            "Steam Deck path"
        )
        
        # Create Database Object
        db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))

        # Update Config in Database
        db.update("config", {"config_value": steamdeck_path}, "config_key = ?", ("steamdeck_retrodeck_path",))
        
        flash(f"Steam Deck path updated successfully", "success")
        system_logger.info(f"Steam Deck path updated: {steamdeck_path}")
        
    except ValidationError as e:
        flash(f"Validation error: {str(e)}", "error")
        system_logger.warning(f"Validation error in Steam Deck path: {e}")
    except Exception as e:
        flash(f"Error updating Steam Deck path: {str(e)}", "error")
        system_logger.error(f"Error updating Steam Deck path: {e}")
    
    return redirect(url_for('config'))

# Status Dropdown: Reset Status
@app.route('/api/trigger_sync', methods=['POST'])
def trigger_sync():
    """Manually trigger a sync operation."""
    global sync_status
    
    if sync_status["is_running"]:
        return jsonify({
            "success": False,
            "message": "Sync already in progress"
        }), 409
    
    try:
        # Run sync in background thread to avoid blocking
        import threading
        sync_thread = threading.Thread(target=run_background_task, daemon=True)
        sync_thread.start()
        
        system_logger.info("Manual sync triggered")
        return jsonify({
            "success": True,
            "message": "Sync started successfully"
        })
    except Exception as e:
        system_logger.error(f"Error triggering sync: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/sync_status', methods=['GET'])
def get_sync_status():
    """API endpoint to get current sync status."""
    global sync_status
    
    # Get current ROM stats from database
    db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))
    
    # Get ROM counts
    try:
        all_roms = db.select_as_dict("roms", ['sync_status'])
        total_roms = len(all_roms)
        synced = sum(1 for rom in all_roms if rom['sync_status'] == 1)
        pending = sum(1 for rom in all_roms if rom['sync_status'] == 0)
        errors = sum(1 for rom in all_roms if rom['sync_status'] == 2)
        
        sync_status["progress"]["total_roms"] = total_roms
        sync_status["progress"]["roms_success"] = synced
        sync_status["progress"]["roms_error"] = errors
        sync_status["progress"]["roms_processed"] = synced + errors
    except Exception as e:
        system_logger.error(f"Error fetching ROM stats: {e}")
    
    return jsonify(sync_status)

@app.route('/dropdown/reset_status', methods=['POST'])
def dropdown_reset_status():
    try:
        data = request.get_json()
        
        if not data or 'roms_id' not in data:
            return jsonify({"error": "Missing roms_id"}), 400
        
        # Validate ROM ID
        rom_id = InputValidator.validate_rom_id(str(data['roms_id']))
        
        # Create Database Object
        db = DeckRommSyncDatabase(app_config["database"].get("name", "deckrommsync.db"))

        # Update Rom Status
        db.update("roms", {"sync_status": "0"}, "roms_id = ?", (rom_id,))
        
        system_logger.info(f"Reset sync status for ROM ID: {rom_id}")
        return jsonify({"message": "Status reset successfully", "rom_id": rom_id})
        
    except ValidationError as e:
        system_logger.warning(f"Validation error in reset status: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        system_logger.error(f"Error resetting status: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/log')
def log():
    """Reads the log file line by line and returns a list."""
    """Reads the log file and divides it into sections when 'Background Task finished...' occurs."""
    try:
        with open("background_worker.log", "r", encoding="utf-8") as file:
            logs = []
            current_section = []

            for line in file:
                if "Background Task started..." in line:
                    if current_section:
                        logs.append(current_section)  # Save the current group
                        current_section = []  # Start a new group
                current_section.append(line.strip())  # Add line to current group

            if current_section:  # Add last group (if present)
                logs.append(current_section)

            log_content = logs[::-1]  # Newest group first
    except FileNotFoundError:
        return [["Log file not found!"]]
    
    return render_template('log.html', log_groups=log_content)

if __name__ == '__main__':    
    system_logger.info("Flask-App started...")

    # Start Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_background_task, "interval", minutes=1)  # Every 2 minutes
    scheduler.start()  

    app.run(debug=True, use_reloader=False, host=app_config["server"].get("host", "localhost"), port=app_config["server"].get("port", 5000))
