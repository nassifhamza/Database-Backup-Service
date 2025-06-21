import os
import subprocess
import datetime
import time
import traceback
import psycopg2
import pymysql
from configparser import ConfigParser

class DatabaseBackupService:
    def __init__(self):
        self.connection = None
        self.current_db_type = None
        self.pg_dump_path = None
        self.pg_restore_path = None
        self.mysqldump_path = None
        self.mysql_path = None
        self.config = ConfigParser()
        self.config_file = 'config.ini'
        self.max_backups = 3  # Maximum number of backups to keep
        self.load_config()
        self.find_database_tools()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'Database' in self.config:
                db_config = self.config['Database']
                self.host = db_config.get('host', 'localhost')
                self.port = db_config.get('port')
                self.db_name = db_config.get('database')
                self.user = db_config.get('username')
                self.password = db_config.get('password')
                self.current_db_type = db_config.get('db_type')
            if 'Tools' in self.config:
                tool_config = self.config['Tools']
                self.pg_dump_path = tool_config.get('pg_dump_path')
                self.pg_restore_path = tool_config.get('pg_restore_path')
                self.mysqldump_path = tool_config.get('mysqldump_path')
                self.mysql_path = tool_config.get('mysql_path')

    def save_config(self):
        if 'Database' not in self.config:
            self.config['Database'] = {}
        db_config = self.config['Database']
        db_config['host'] = self.host
        db_config['port'] = self.port
        db_config['database'] = self.db_name
        db_config['username'] = self.user
        db_config['password'] = self.password
        db_config['db_type'] = self.current_db_type

        if 'Tools' not in self.config:
            self.config['Tools'] = {}
        tool_config = self.config['Tools']
        tool_config['pg_dump_path'] = self.pg_dump_path if self.pg_dump_path else ''
        tool_config['pg_restore_path'] = self.pg_restore_path if self.pg_restore_path else ''
        tool_config['mysqldump_path'] = self.mysqldump_path if self.mysqldump_path else ''
        tool_config['mysql_path'] = self.mysql_path if self.mysql_path else ''

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def find_database_tools(self):
        # Simplified for backend service, assuming tools are in PATH or specified manually
        if not self.pg_dump_path:
            self.pg_dump_path = self._find_tool('pg_dump')
        if not self.pg_restore_path:
            self.pg_restore_path = self._find_tool('pg_restore')
        if not self.mysqldump_path:
            self.mysqldump_path = self._find_tool('mysqldump')
        if not self.mysql_path:
            self.mysql_path = self._find_tool('mysql')

    def _find_tool(self, tool_name):
        try:
            return subprocess.check_output(['which', tool_name]).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return None

    def connect_to_db(self, db_type, host, port, db_name, user, password):
        self.current_db_type = db_type
        self.host = host
        self.port = port
        self.db_name = db_name
        self.user = user
        self.password = password

        try:
            if self.connection:
                self.connection.close()
            
            if db_type == "PostgreSQL":
                self.connection = psycopg2.connect(
                    host=host, port=port, database=db_name, user=user, password=password
                )
            elif db_type == "MySQL":
                self.connection = pymysql.connect(
                    host=host, port=int(port), database=db_name, user=user, password=password
                )
            self.connection.autocommit = True
            return True, "Connection successful."
        except Exception as e:
            self.connection = None
            return False, f"Connection failed: {e}"

    def logout_from_db(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            return True, "Logged out successfully."
        return False, "Not connected."

    def get_backup_files(self, backup_location):
        """Get list of backup files sorted by creation time (newest first)"""
        if not os.path.exists(backup_location):
            return []
        
        backup_files = []
        for file in os.listdir(backup_location):
            if file.endswith('.sql'):
                file_path = os.path.join(backup_location, file)
                file_stat = os.stat(file_path)
                backup_files.append({
                    'filename': file,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'created': file_stat.st_ctime
                })
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x['created'], reverse=True)
        return backup_files

    def cleanup_old_backups(self, backup_location):
        """Remove old backups if more than max_backups exist"""
        backup_files = self.get_backup_files(backup_location)
        
        if len(backup_files) > self.max_backups:
            # Remove the oldest backups
            files_to_remove = backup_files[self.max_backups:]
            removed_files = []
            
            for backup in files_to_remove:
                try:
                    os.remove(backup['path'])
                    removed_files.append(backup['filename'])
                except Exception as e:
                    print(f"Error removing backup {backup['filename']}: {e}")
            
            return removed_files
        
        return []

    def create_backup(self, backup_name=None, backup_location='./backups'):
        if not self.connection:
            return False, "Not connected to a database."
        if not self.current_db_type:
            return False, "Database type not selected."

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_name:
            filename = f"{backup_name}_{timestamp}"
        else:
            filename = f"{self.db_name}_{timestamp}"

        os.makedirs(backup_location, exist_ok=True)
        backup_path = os.path.join(backup_location, filename)

        try:
            if self.current_db_type == "PostgreSQL":
                if not self.pg_dump_path:
                    return False, "pg_dump tool not found. Please configure its path."
                backup_path += ".sql"
                cmd = [
                    self.pg_dump_path,
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    "-F", "p", # Plain text SQL dump
                    "-d", self.db_name,
                    "-f", backup_path
                ]
                env = os.environ.copy()
                env['PGPASSWORD'] = self.password
                process = subprocess.run(cmd, env=env, capture_output=True, text=True)

            elif self.current_db_type == "MySQL":
                if not self.mysqldump_path:
                    return False, "mysqldump tool not found. Please configure its path."
                backup_path += ".sql"
                cmd = [
                    self.mysqldump_path,
                    f"--host={self.host}",
                    f"--port={self.port}",
                    f"--user={self.user}",
                    f"--password={self.password}",
                    self.db_name
                ]
                with open(backup_path, 'w') as f:
                    process = subprocess.run(cmd, stdout=f, capture_output=True, text=True)
            else:
                return False, "Unsupported database type."

            if process.returncode == 0:
                # Cleanup old backups after successful backup
                removed_files = self.cleanup_old_backups(backup_location)
                message = f"Backup created successfully at {backup_path}"
                if removed_files:
                    message += f". Removed old backups: {', '.join(removed_files)}"
                return True, message
            else:
                return False, f"Backup failed: {process.stderr}"
        except Exception as e:
            return False, f"An error occurred during backup: {e}"

    def restore_backup(self, backup_file_path):
        if not self.connection:
            return False, "Not connected to a database."
        if not self.current_db_type:
            return False, "Database type not selected."

        try:
            if self.current_db_type == "PostgreSQL":
                if not self.pg_restore_path:
                    return False, "pg_restore tool not found. Please configure its path."
                cmd = [
                    self.pg_restore_path,
                    "-h", self.host,
                    "-p", str(self.port),
                    "-U", self.user,
                    "-d", self.db_name,
                    backup_file_path
                ]
                env = os.environ.copy()
                env['PGPASSWORD'] = self.password
                process = subprocess.run(cmd, env=env, capture_output=True, text=True)

            elif self.current_db_type == "MySQL":
                if not self.mysql_path:
                    return False, "mysql tool not found. Please configure its path."
                cmd = [
                    self.mysql_path,
                    f"--host={self.host}",
                    f"--port={self.port}",
                    f"--user={self.user}",
                    f"--password={self.password}",
                    self.db_name
                ]
                with open(backup_file_path, 'r') as f:
                    process = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            else:
                return False, "Unsupported database type."

            if process.returncode == 0:
                return True, f"Restore successful from {backup_file_path}"
            else:
                return False, f"Restore failed: {process.stderr}"
        except Exception as e:
            return False, f"An error occurred during restore: {e}"

    def list_users(self):
        if not self.connection:
            return False, "Not connected to a database.", []
        
        users = []
        try:
            with self.connection.cursor() as cursor:
                if self.current_db_type == "PostgreSQL":
                    cursor.execute("SELECT usename, usesuper, usecreatedb, userepl, usebypassrls FROM pg_user;")
                    for row in cursor.fetchall():
                        users.append({
                            'username': row[0],
                            'superuser': row[1],
                            'create_db': row[2],
                            'replication': row[3],
                            'bypass_rls': row[4]
                        })
                elif self.current_db_type == "MySQL":
                    cursor.execute("SELECT user, host FROM mysql.user;")
                    for row in cursor.fetchall():
                        users.append({'username': f"{row[0]}@{row[1]}"})
            return True, "Users listed successfully.", users
        except Exception as e:
            return False, f"Failed to list users: {e}", []

    def execute_user_operation(self, operation, username, password=None, privileges=None):
        if not self.connection:
            return False, "Not connected to a database."
        
        try:
            with self.connection.cursor() as cursor:
                if self.current_db_type == "PostgreSQL":
                    if operation == "Create User":
                        create_sql = f"CREATE USER {username} WITH PASSWORD %s;"
                        cursor.execute(create_sql, (password,))
                        if privileges:
                            for priv in privileges:
                                if priv == 'LOGIN': # LOGIN is default, no need to explicitly grant
                                    continue
                                alter_sql = f"ALTER USER {username} {priv};"
                                cursor.execute(alter_sql)
                    elif operation == "Delete Users":
                        delete_sql = f"DROP USER {username};"
                        cursor.execute(delete_sql)
                    else:
                        return False, "Unsupported PostgreSQL user operation."
                elif self.current_db_type == "MySQL":
                    if operation == "Create User":
                        create_sql = f"CREATE USER %s@'localhost' IDENTIFIED BY %s;"
                        cursor.execute(create_sql, (username, password))
                        if privileges:
                            for priv in privileges:
                                grant_sql = f"GRANT {priv} ON *.* TO %s@'localhost';"
                                cursor.execute(grant_sql, (username,))
                    elif operation == "Delete Users":
                        delete_sql = f"DROP USER %s@'localhost';"
                        cursor.execute(delete_sql, (username,))
                    else:
                        return False, "Unsupported MySQL user operation."
                else:
                    return False, "Unsupported database type for user operations."
            
            self.connection.commit()
            return True, f"User operation '{operation}' for '{username}' successful."
        except Exception as e:
            self.connection.rollback()
            return False, f"User operation failed: {e}"

if __name__ == '__main__':
    # Example usage (for testing purposes)
    service = DatabaseBackupService()
    # Configure and connect to a database for testing
    # success, message = service.connect_to_db("PostgreSQL", "localhost", "5432", "testdb", "testuser", "testpassword")
    # print(message)
    # if success:
    #     success, message = service.create_backup(backup_name="my_first_backup", backup_location="./backups")
    #     print(message)
    #     success, message, users = service.list_users()
    #     print(message, users)
    pass

