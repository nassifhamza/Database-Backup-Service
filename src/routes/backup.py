from flask import Blueprint, request, jsonify
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backup_service import DatabaseBackupService
from scheduler import get_scheduler

backup_bp = Blueprint('backup', __name__)

# Global service instance
backup_service = DatabaseBackupService()

@backup_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to a database"""
    data = request.get_json()
    
    required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    success, message = backup_service.connect_to_db(
        data['db_type'], data['host'], data['port'], 
        data['database'], data['username'], data['password']
    )
    
    if success:
        backup_service.save_config()
        # Start scheduler when connection is successful
        scheduler = get_scheduler(backup_service)
        scheduler.start_scheduler()
    
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from database"""
    success, message = backup_service.logout_from_db()
    
    # Stop scheduler when disconnecting
    if success:
        scheduler = get_scheduler(backup_service)
        scheduler.stop_scheduler()
    
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/status', methods=['GET'])
def status():
    """Get connection status"""
    connected = backup_service.connection is not None
    db_type = backup_service.current_db_type if connected else None
    db_name = backup_service.db_name if connected else None
    
    # Get scheduler status
    scheduler = get_scheduler(backup_service)
    scheduler_running = scheduler.is_running()
    next_backup = scheduler.get_next_backup_time() if scheduler_running else "Scheduler not running"
    
    return jsonify({
        'connected': connected,
        'db_type': db_type,
        'database': db_name,
        'scheduler_running': scheduler_running,
        'next_backup': next_backup
    })

@backup_bp.route('/backup', methods=['POST'])
def create_backup():
    """Create a database backup"""
    data = request.get_json() or {}
    
    backup_name = data.get('backup_name')
    backup_location = data.get('backup_location', './backups')
    
    success, message = backup_service.create_backup(backup_name, backup_location)
    
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/backup/force', methods=['POST'])
def force_backup():
    """Force a scheduled backup to run immediately"""
    scheduler = get_scheduler(backup_service)
    
    try:
        scheduler.run_scheduled_backup()
        return jsonify({'success': True, 'message': 'Forced backup completed'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Forced backup failed: {e}'})

@backup_bp.route('/restore', methods=['POST'])
def restore_backup():
    """Restore a database backup"""
    data = request.get_json()
    
    if 'backup_file_path' not in data:
        return jsonify({'success': False, 'message': 'backup_file_path is required'}), 400
    
    success, message = backup_service.restore_backup(data['backup_file_path'])
    
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/backups', methods=['GET'])
def list_backups():
    """List available backup files"""
    backup_location = request.args.get('backup_location', './backups')
    
    if not os.path.exists(backup_location):
        return jsonify({'success': False, 'message': 'Backup directory does not exist', 'backups': []})
    
    try:
        backup_files = backup_service.get_backup_files(backup_location)
        return jsonify({'success': True, 'backups': backup_files})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error listing backups: {e}', 'backups': []})

@backup_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the backup scheduler"""
    scheduler = get_scheduler(backup_service)
    success, message = scheduler.start_scheduler()
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the backup scheduler"""
    scheduler = get_scheduler(backup_service)
    success, message = scheduler.stop_scheduler()
    return jsonify({'success': success, 'message': message})

@backup_bp.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get scheduler status"""
    scheduler = get_scheduler(backup_service)
    
    return jsonify({
        'running': scheduler.is_running(),
        'next_backup': scheduler.get_next_backup_time()
    })

@backup_bp.route('/users', methods=['GET'])
def list_users():
    """List database users"""
    success, message, users = backup_service.list_users()
    
    return jsonify({'success': success, 'message': message, 'users': users})

@backup_bp.route('/users', methods=['POST'])
def manage_user():
    """Create, modify, or delete database users"""
    data = request.get_json()
    
    required_fields = ['operation', 'username']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    operation = data['operation']
    username = data['username']
    password = data.get('password')
    privileges = data.get('privileges', [])
    
    success, message = backup_service.execute_user_operation(operation, username, password, privileges)
    
    return jsonify({'success': success, 'message': message})



