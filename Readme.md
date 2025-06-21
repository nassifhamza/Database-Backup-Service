# Database Backup Service

An automated backend service for database backup and restore operations with API endpoints, retention policies, and scheduled backups.

## Overview

This service transforms the original PyQt5 desktop application into a robust backend API service that provides:

- **Automated Database Backups**: Support for PostgreSQL and MySQL databases
- **RESTful API**: Complete API endpoints for all backup operations
- **Backup Retention Policy**: Automatically maintains only the 3 most recent backups
- **Scheduled Backups**: Automatic backups every Saturday at midnight
- **Web Interface**: Simple web UI for managing backups and connections
- **User Management**: Database user creation, modification, and deletion

## Features

### Core Functionality
- Database connection management (PostgreSQL and MySQL)
- Manual and automated backup creation
- Backup restoration from files
- Database user management
- Configuration persistence

### Automation Features
- **Scheduled Backups**: Runs every Saturday at 00:00 (midnight)
- **Retention Policy**: Keeps only the 3 most recent backups, automatically removes older ones
- **Background Scheduler**: Runs as a background service when connected to a database

### API Endpoints
- Connection management (`/api/connect`, `/api/disconnect`, `/api/status`)
- Backup operations (`/api/backup`, `/api/restore`, `/api/backups`)
- Scheduler control (`/api/scheduler/start`, `/api/scheduler/stop`, `/api/scheduler/status`)
- User management (`/api/users`)
- Configuration management (`/api/config`)

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL client tools (pg_dump, pg_restore) for PostgreSQL support
- MySQL client tools (mysqldump, mysql) for MySQL support

### Setup Instructions

1. **Clone or extract the project files**
   ```bash
   cd database_backup_api
   ```

2. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies** (already included in the project)
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the service**
   ```bash
   python src/main.py
   ```

The service will start on `http://localhost:5002` by default.

## Configuration

### Database Tools Detection
The service automatically detects database tools in your system PATH:
- `pg_dump` and `pg_restore` for PostgreSQL
- `mysqldump` and `mysql` for MySQL

If tools are not in PATH, you can configure custom paths via the API or web interface.

### Configuration File
Settings are automatically saved to `config.ini` including:
- Database connection details
- Tool paths
- Last used settings

## Usage

### Web Interface
Access the web interface at `http://localhost:5002` to:
- Configure database connections
- Create and restore backups manually
- Monitor scheduler status
- View available backups

### API Usage

#### Connect to Database
```bash
curl -X POST http://localhost:5002/api/connect \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "PostgreSQL",
    "host": "localhost",
    "port": "5432",
    "database": "mydb",
    "username": "user",
    "password": "password"
  }'
```

#### Create Backup
```bash
curl -X POST http://localhost:5002/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "backup_name": "manual_backup",
    "backup_location": "./backups"
  }'
```

#### List Backups
```bash
curl -X GET "http://localhost:5002/api/backups?backup_location=./backups"
```

#### Restore Backup
```bash
curl -X POST http://localhost:5002/api/restore \
  -H "Content-Type: application/json" \
  -d '{
    "backup_file_path": "./backups/mydb_20231220_120000.sql"
  }'
```

#### Check Status
```bash
curl -X GET http://localhost:5002/api/status
```



## API Reference

### Connection Endpoints

#### POST /api/connect
Connect to a database.

**Request Body:**
```json
{
  "db_type": "PostgreSQL|MySQL",
  "host": "localhost",
  "port": "5432",
  "database": "database_name",
  "username": "username",
  "password": "password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful."
}
```

#### POST /api/disconnect
Disconnect from the current database.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully."
}
```

#### GET /api/status
Get current connection and scheduler status.

**Response:**
```json
{
  "connected": true,
  "db_type": "PostgreSQL",
  "database": "mydb",
  "scheduler_running": true,
  "next_backup": "2023-12-23 00:00:00"
}
```

### Backup Endpoints

#### POST /api/backup
Create a manual backup.

**Request Body:**
```json
{
  "backup_name": "optional_name",
  "backup_location": "./backups"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Backup created successfully at ./backups/mydb_20231220_120000.sql"
}
```

#### POST /api/backup/force
Force a scheduled backup to run immediately.

**Response:**
```json
{
  "success": true,
  "message": "Forced backup completed"
}
```

#### GET /api/backups
List available backup files.

**Query Parameters:**
- `backup_location` (optional): Directory to search for backups (default: "./backups")

**Response:**
```json
{
  "success": true,
  "backups": [
    {
      "filename": "mydb_20231220_120000.sql",
      "path": "./backups/mydb_20231220_120000.sql",
      "size": 1024000,
      "created": 1703073600
    }
  ]
}
```

#### POST /api/restore
Restore a backup file.

**Request Body:**
```json
{
  "backup_file_path": "./backups/mydb_20231220_120000.sql"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Restore successful from ./backups/mydb_20231220_120000.sql"
}
```

### Scheduler Endpoints

#### POST /api/scheduler/start
Start the backup scheduler.

**Response:**
```json
{
  "success": true,
  "message": "Backup scheduler started successfully"
}
```

#### POST /api/scheduler/stop
Stop the backup scheduler.

**Response:**
```json
{
  "success": true,
  "message": "Backup scheduler stopped successfully"
}
```

#### GET /api/scheduler/status
Get scheduler status and next backup time.

**Response:**
```json
{
  "running": true,
  "next_backup": "2023-12-23 00:00:00"
}
```

### User Management Endpoints

#### GET /api/users
List database users.

**Response:**
```json
{
  "success": true,
  "message": "Users listed successfully.",
  "users": [
    {
      "username": "user1",
      "superuser": false,
      "create_db": true,
      "replication": false,
      "bypass_rls": false
    }
  ]
}
```

#### POST /api/users
Create, modify, or delete database users.

**Request Body:**
```json
{
  "operation": "Create User|Modify Users|Delete Users",
  "username": "new_user",
  "password": "password",
  "privileges": ["LOGIN", "CREATEDB"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "User operation 'Create User' for 'new_user' successful."
}
```

### Configuration Endpoints

#### GET /api/config
Get current configuration.

**Response:**
```json
{
  "success": true,
  "config": {
    "host": "localhost",
    "port": "5432",
    "database": "mydb",
    "username": "user",
    "db_type": "PostgreSQL",
    "pg_dump_path": "/usr/bin/pg_dump",
    "pg_restore_path": "/usr/bin/pg_restore",
    "mysqldump_path": "",
    "mysql_path": ""
  }
}
```

#### POST /api/config
Save configuration.

**Request Body:**
```json
{
  "host": "localhost",
  "port": "5432",
  "database": "mydb",
  "username": "user",
  "password": "password",
  "db_type": "PostgreSQL"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration saved successfully"
}
```

#### POST /api/tools/detect
Auto-detect database tools.

**Response:**
```json
{
  "success": true,
  "tools": {
    "pg_dump_path": "/usr/bin/pg_dump",
    "pg_restore_path": "/usr/bin/pg_restore",
    "mysqldump_path": "/usr/bin/mysqldump",
    "mysql_path": "/usr/bin/mysql"
  }
}
```


## Backup Retention Policy

The service implements an automatic backup retention policy:

- **Maximum Backups**: Only the 3 most recent backups are kept
- **Automatic Cleanup**: When a new backup is created and more than 3 backups exist, the oldest backup is automatically deleted
- **Sorting**: Backups are sorted by creation time (newest first)
- **File Naming**: Backups are named with timestamp format: `{database_name}_{YYYYMMDD_HHMMSS}.sql`

### Example Retention Behavior
1. Create backup 1: `mydb_20231220_100000.sql`
2. Create backup 2: `mydb_20231220_110000.sql`
3. Create backup 3: `mydb_20231220_120000.sql`
4. Create backup 4: `mydb_20231220_130000.sql` → `mydb_20231220_100000.sql` is automatically deleted

## Scheduled Backup System

### Schedule Configuration
- **Frequency**: Every Saturday
- **Time**: 00:00 (midnight)
- **Automatic Start**: Scheduler starts automatically when a database connection is established
- **Background Operation**: Runs in a separate thread without blocking the main application

### Scheduler Features
- **Persistent**: Continues running until explicitly stopped or service is shut down
- **Error Handling**: Logs errors and continues operation
- **Manual Control**: Can be started/stopped via API endpoints
- **Status Monitoring**: Provides next backup time and running status

### Force Backup
You can trigger a scheduled backup immediately using:
```bash
curl -X POST http://localhost:5002/api/backup/force
```

## Architecture

### Core Components

1. **DatabaseBackupService** (`backup_service.py`)
   - Core backup and restore logic
   - Database connection management
   - User management operations
   - Backup retention policy implementation

2. **BackupScheduler** (`scheduler.py`)
   - Scheduled backup management
   - Background thread execution
   - Schedule configuration and monitoring

3. **Flask API** (`src/main.py`, `src/routes/`)
   - RESTful API endpoints
   - CORS support for web interface
   - Request/response handling

4. **Web Interface** (`src/static/index.html`)
   - User-friendly web UI
   - Real-time status updates
   - Backup management interface

### File Structure
```
database_backup_api/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── routes/
│   │   ├── backup.py          # Backup and scheduler API routes
│   │   └── config.py          # Configuration API routes
│   └── static/
│       └── index.html         # Web interface
├── backup_service.py          # Core backup service logic
├── scheduler.py               # Backup scheduler implementation
├── config.ini                 # Configuration file (auto-generated)
├── requirements.txt           # Python dependencies
├── venv/                      # Virtual environment
└── README.md                  # This documentation
```

## Error Handling

The service includes comprehensive error handling:

- **Database Connection Errors**: Clear error messages for connection failures
- **Tool Detection**: Graceful handling when database tools are not found
- **File System Errors**: Proper error reporting for backup/restore file operations
- **Scheduler Errors**: Logging and continuation of service despite backup failures
- **API Validation**: Input validation with appropriate HTTP status codes

## Security Considerations

- **Password Storage**: Database passwords are stored in configuration files (consider encryption for production)
- **File Permissions**: Ensure backup directories have appropriate permissions
- **Network Security**: Service runs on localhost by default; configure firewall rules for remote access
- **Database Privileges**: Use dedicated backup users with minimal required privileges

## Troubleshooting

### Common Issues

1. **Database Tools Not Found**
   - Install PostgreSQL client tools: `sudo apt-get install postgresql-client`
   - Install MySQL client tools: `sudo apt-get install mysql-client`
   - Configure custom tool paths via API

2. **Connection Failures**
   - Verify database server is running
   - Check connection parameters (host, port, credentials)
   - Ensure database user has necessary privileges

3. **Backup Failures**
   - Check disk space in backup directory
   - Verify database user has backup privileges
   - Ensure backup directory is writable

4. **Scheduler Not Working**
   - Check if scheduler is running: `GET /api/scheduler/status`
   - Verify database connection is active
   - Check service logs for error messages

### Logs and Debugging
- Scheduler events are logged to console output
- Flask debug mode provides detailed error information
- Check backup directory for successful backup files

## Production Deployment

For production use, consider:

1. **WSGI Server**: Use Gunicorn or uWSGI instead of Flask development server
2. **Process Management**: Use systemd or supervisor for service management
3. **Security**: Implement authentication and HTTPS
4. **Monitoring**: Add logging and monitoring solutions
5. **Backup Storage**: Consider remote backup storage solutions
6. **Database Security**: Use dedicated backup users with minimal privileges

### Example Systemd Service
```ini
[Unit]
Description=Database Backup Service
After=network.target

[Service]
Type=simple
User=backup
WorkingDirectory=/path/to/database_backup_api
Environment=PATH=/path/to/database_backup_api/venv/bin
ExecStart=/path/to/database_backup_api/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

This project is provided as-is for educational and operational purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Examine service logs for error details
4. Verify database tool installation and configuration


## Screenshots

### Web Interface Overview

The service includes a user-friendly web interface accessible at `http://localhost:5002`:

![Web Interface](screenshots/web_interface.png)

The interface is divided into two main sections:

#### Database Connection Panel (Left)
- **Database Type Selection**: Choose between PostgreSQL and MySQL
- **Connection Parameters**: Host, port, database name, username, and password fields
- **Connection Controls**: Connect and Disconnect buttons
- **Status Display**: Shows current connection status

#### Backup Operations Panel (Right)
- **Backup Configuration**: Optional backup name and location settings
- **Backup Controls**: Create backup and refresh backup list buttons
- **Available Backups**: List of existing backup files with details
- **Restore Function**: Select and restore backup files

### Key Features Demonstrated

1. **Responsive Design**: The interface adapts to different screen sizes
2. **Real-time Status**: Connection and operation status updates
3. **File Management**: Easy backup file selection and management
4. **User-friendly Controls**: Clear buttons and form fields

## Transformation Summary

This project successfully transforms the original PyQt5 desktop application into a modern backend service with the following improvements:

### Original Application
- Desktop GUI application using PyQt5
- Manual operation only
- Single-user interface
- Windows-specific features
- No automation capabilities

### Transformed Service
- **Web-based API service** with RESTful endpoints
- **Automated scheduling** with Saturday midnight backups
- **Multi-client support** through HTTP API
- **Cross-platform compatibility** (Linux, Windows, macOS)
- **Backup retention policy** (3-backup limit)
- **Background operation** as a service
- **Web interface** for easy management
- **Configuration persistence** across restarts

### Technical Improvements
- **Flask framework** for robust web service architecture
- **Threading** for background scheduler operation
- **CORS support** for web interface integration
- **JSON API** for programmatic access
- **Error handling** and logging
- **Modular design** with separated concerns

### Operational Benefits
- **Unattended operation** with scheduled backups
- **Remote management** via web interface or API
- **Automated retention** prevents disk space issues
- **Service integration** through API endpoints
- **Monitoring capabilities** with status endpoints

The transformation maintains all original functionality while adding significant automation and accessibility improvements, making it suitable for production environments and integration with other systems.

