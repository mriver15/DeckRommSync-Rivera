"""
Statistics calculation helper for DeckRommSync.
Provides methods to calculate and aggregate sync statistics.
"""

from classes.DeckRommSyncDatabase import DeckRommSyncDatabase
from typing import Dict, List, Any
from datetime import datetime, timedelta


class SyncStatistics:
    """Helper class for calculating sync statistics."""
    
    def __init__(self, db_name: str):
        """Initialize with database name."""
        self.db = DeckRommSyncDatabase(db_name)
    
    def get_total_roms_stats(self) -> Dict[str, int]:
        """
        Get total ROM counts by sync status.
        
        Returns:
            Dict with keys: total, synced, pending, errors
        """
        roms = self.db.select_as_dict("roms", ['sync_status'])
        
        total = len(roms)
        synced = len([r for r in roms if r['sync_status'] == 1])
        pending = len([r for r in roms if r['sync_status'] == 0])
        errors = len([r for r in roms if r['sync_status'] == 2])
        
        return {
            'total': total,
            'synced': synced,
            'pending': pending,
            'errors': errors
        }
    
    def get_sync_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sync history.
        
        Args:
            limit: Number of recent sync runs to return
            
        Returns:
            List of sync history records
        """
        history = self.db.select_as_dict(
            "sync_history",
            ['*'],
            order_by="id DESC",
            limit=limit
        )
        
        # Add formatted timestamps and success rate
        for record in history:
            if record.get('start_time'):
                try:
                    start_dt = datetime.fromisoformat(record['start_time'])
                    record['start_time_formatted'] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    record['start_time_formatted'] = record['start_time']
            
            total = record.get('total_roms', 0)
            success = record.get('success_count', 0)
            record['success_rate'] = round((success / total * 100) if total > 0 else 0, 1)
        
        return history
    
    def get_success_rate(self) -> float:
        """
        Calculate overall success rate from all sync history.
        
        Returns:
            Success rate as percentage (0-100)
        """
        history = self.db.select_as_dict("sync_history")
        
        if not history:
            return 0.0
        
        total_roms = sum(h.get('total_roms', 0) for h in history)
        total_success = sum(h.get('success_count', 0) for h in history)
        
        return round((total_success / total_roms * 100) if total_roms > 0 else 0, 1)
    
    def get_total_synced_count(self) -> int:
        """
        Get total number of ROMs successfully synced across all history.
        
        Returns:
            Total successful sync count
        """
        history = self.db.select_as_dict("sync_history", ['success_count'])
        return sum(h.get('success_count', 0) for h in history)
    
    def get_platform_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get ROM count breakdown by platform.
        
        Returns:
            List of platforms with ROM counts
        """
        roms = self.db.select_as_dict("roms", ['platform_fs_slug', 'sync_status'])
        
        # Group by platform
        platforms = {}
        for rom in roms:
            platform = rom.get('platform_fs_slug', 'Unknown')
            if platform not in platforms:
                platforms[platform] = {
                    'name': platform,
                    'total': 0,
                    'synced': 0,
                    'pending': 0,
                    'errors': 0
                }
            
            platforms[platform]['total'] += 1
            status = rom.get('sync_status', 0)
            if status == 1:
                platforms[platform]['synced'] += 1
            elif status == 0:
                platforms[platform]['pending'] += 1
            elif status == 2:
                platforms[platform]['errors'] += 1
        
        return sorted(platforms.values(), key=lambda x: x['total'], reverse=True)
    
    def get_estimated_disk_space(self) -> Dict[str, Any]:
        """
        Estimate disk space used by synced ROMs.
        Uses average ROM sizes by platform.
        
        Returns:
            Dict with total_mb and formatted size string
        """
        # Average ROM sizes in MB (rough estimates)
        avg_sizes = {
            'psx': 650,      # CD-ROM
            'ps2': 4500,     # DVD
            'n64': 32,       # Cartridge
            'snes': 4,       # Cartridge
            'nes': 0.5,      # Cartridge
            'gba': 16,       # Cartridge
            'gbc': 2,        # Cartridge
            'gb': 0.5,       # Cartridge
            'nds': 128,      # Card
            'gamecube': 1400,  # Mini DVD
            'wii': 4700,     # DVD
            'default': 100   # Default average
        }
        
        roms = self.db.select_as_dict("roms", ['platform_fs_slug', 'sync_status'])
        synced_roms = [r for r in roms if r['sync_status'] == 1]
        
        total_mb = 0
        for rom in synced_roms:
            platform = rom.get('platform_fs_slug', 'default')
            size = avg_sizes.get(platform, avg_sizes['default'])
            total_mb += size
        
        # Format size
        if total_mb < 1024:
            formatted = f"{total_mb:.1f} MB"
        else:
            total_gb = total_mb / 1024
            formatted = f"{total_gb:.2f} GB"
        
        return {
            'total_mb': round(total_mb, 2),
            'formatted': formatted,
            'rom_count': len(synced_roms)
        }
    
    def get_sync_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get sync trends for the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of daily statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        history = self.db.select_as_dict("sync_history")
        
        # Filter by date and aggregate by day
        daily_stats = {}
        for record in history:
            try:
                start_time = datetime.fromisoformat(record.get('start_time', ''))
                if start_time < cutoff_date:
                    continue
                
                date_key = start_time.strftime("%Y-%m-%d")
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'total_roms': 0,
                        'success_count': 0,
                        'error_count': 0,
                        'runs': 0
                    }
                
                daily_stats[date_key]['total_roms'] += record.get('total_roms', 0)
                daily_stats[date_key]['success_count'] += record.get('success_count', 0)
                daily_stats[date_key]['error_count'] += record.get('error_count', 0)
                daily_stats[date_key]['runs'] += 1
            except:
                continue
        
        return sorted(daily_stats.values(), key=lambda x: x['date'])
    
    def get_collection_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for each collection.
        
        Returns:
            List of collections with ROM counts
        """
        collections = self.db.select_as_dict("collections")
        
        stats = []
        for collection in collections:
            coll_id = collection.get('collections_id')
            roms = self.db.select_as_dict("roms", ['sync_status'], 
                                          'collections_id = ?', (coll_id,))
            
            synced = len([r for r in roms if r['sync_status'] == 1])
            pending = len([r for r in roms if r['sync_status'] == 0])
            errors = len([r for r in roms if r['sync_status'] == 2])
            
            stats.append({
                'name': collection.get('name', 'Unknown'),
                'total': len(roms),
                'synced': synced,
                'pending': pending,
                'errors': errors,
                'enabled': collection.get('collection_sync', 0) == 1
            })
        
        return stats
