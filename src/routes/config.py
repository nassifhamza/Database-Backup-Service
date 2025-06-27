from flask import Blueprint, request, jsonify
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backup_service import DatabaseBackupService

config_bp = Blueprint('config', __name__)

# Global service instance
backup_service = DatabaseBackupService()

@config_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config_data = {
        'host': getattr(backup_service, 'host', ''),
        'port': getattr(backup_service, 'port', ''),
        'database': getattr(backup_service, 'db_name', ''),
        'username': getattr(backup_service, 'user', ''),
        'db_type': getattr(backup_service, 'current_db_type', ''),
        'pg_dump_path': backup_service.pg_dump_path or '',
        'pg_restore_path': backup_service.pg_restore_path or '',
        'mysqldump_path': backup_service.mysqldump_path or '',
        'mysql_path': backup_service.mysql_path or ''
    }
    
    return jsonify({'success': True, 'config': config_data})

@config_bp.route('/config', methods=['POST'])
def save_config():
    """Save configuration"""
    data = request.get_json()
    
    # Update service configuration
    if 'host' in data:
        backup_service.host = data['host']
    if 'port' in data:
        backup_service.port = data['port']
    if 'database' in data:
        backup_service.db_name = data['database']
    if 'username' in data:
        backup_service.user = data['username']
    if 'password' in data:
        backup_service.password = data['password']
    if 'db_type' in data:
        backup_service.current_db_type = data['db_type']
    if 'pg_dump_path' in data:
        backup_service.pg_dump_path = data['pg_dump_path']
    if 'pg_restore_path' in data:
        backup_service.pg_restore_path = data['pg_restore_path']
    if 'mysqldump_path' in data:
        backup_service.mysqldump_path = data['mysqldump_path']
    if 'mysql_path' in data:
        backup_service.mysql_path = data['mysql_path']
    
    # Save to file
    backup_service.save_config()
    
    return jsonify({'success': True, 'message': 'Configuration saved successfully'})

@config_bp.route('/tools/detect', methods=['POST'])
def detect_tools():
    """Auto-detect database tools"""
    backup_service.find_database_tools()
    
    tools = {
        'pg_dump_path': backup_service.pg_dump_path or 'Not found',
        'pg_restore_path': backup_service.pg_restore_path or 'Not found',
        'mysqldump_path': backup_service.mysqldump_path or 'Not found',
        'mysql_path': backup_service.mysql_path or 'Not found'
    }
    
    return jsonify({'success': True, 'tools': tools})



