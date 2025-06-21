import threading
import time
import schedule
from datetime import datetime, timedelta
from backup_service import DatabaseBackupService

class BackupScheduler:
    def __init__(self, backup_service):
        self.backup_service = backup_service
        self.scheduler_thread = None
        self.running = False
        self.setup_schedule()

    def setup_schedule(self):
        """Setup the backup schedule for every Saturday at midnight"""
        schedule.clear()
        schedule.every().saturday.at("00:00").do(self.run_scheduled_backup)

    def run_scheduled_backup(self):
        """Execute the scheduled backup"""
        print(f"[{datetime.now()}] Running scheduled backup...")
        
        if not self.backup_service.connection:
            print("No database connection available for scheduled backup")
            return
        
        try:
            # Use default backup location
            backup_location = "./backups"
            success, message = self.backup_service.create_backup(
                backup_name="scheduled_backup", 
                backup_location=backup_location
            )
            
            if success:
                print(f"[{datetime.now()}] Scheduled backup completed successfully: {message}")
            else:
                print(f"[{datetime.now()}] Scheduled backup failed: {message}")
                
        except Exception as e:
            print(f"[{datetime.now()}] Error during scheduled backup: {e}")

    def start_scheduler(self):
        """Start the background scheduler thread"""
        if self.running:
            return False, "Scheduler is already running"
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        return True, "Backup scheduler started successfully"

    def stop_scheduler(self):
        """Stop the background scheduler"""
        if not self.running:
            return False, "Scheduler is not running"
        
        self.running = False
        schedule.clear()
        
        return True, "Backup scheduler stopped successfully"

    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def get_next_backup_time(self):
        """Get the next scheduled backup time"""
        jobs = schedule.get_jobs()
        if jobs:
            next_run = jobs[0].next_run
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return "No scheduled backups"

    def is_running(self):
        """Check if scheduler is running"""
        return self.running

    def force_backup_now(self):
        """Force a backup to run immediately (for testing)"""
        return self.run_scheduled_backup()

# Global scheduler instance
scheduler = None

def get_scheduler(backup_service):
    """Get or create the global scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = BackupScheduler(backup_service)
    return scheduler

