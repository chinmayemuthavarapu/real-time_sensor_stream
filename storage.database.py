 # storage/database.py
import sqlite3
import json
from datetime import datetime
import os

class DataStorage:
    def __init__(self, db_path="sensor_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Raw sensor data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                device_name TEXT,
                message_id INTEGER,
                timestamp DATETIME,
                temperature REAL,
                vibration REAL,
                voltage REAL,
                status TEXT,
                alert_type TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Device health table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_health (
                device_id TEXT PRIMARY KEY,
                device_name TEXT,
                status TEXT DEFAULT 'Good',
                uptime_seconds INTEGER DEFAULT 0,
                packets_received INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                last_active DATETIME,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f" Database initialized: {self.db_path}")
        
    def store_sensor_data(self, data):
        """Store processed sensor data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sensor_readings 
                (device_id, device_name, message_id, timestamp, temperature, 
                 vibration, voltage, status, alert_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['device_id'],
                data.get('device_name', 'Unknown'),
                data['message_id'],
                data['timestamp'],
                data['temperature'],
                data['vibration'],
                data['voltage'],
                data.get('status', 'Good'),
                data.get('alert_type', 'None')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f" Database error (store_sensor_data): {e}")
            return False
        
    def update_device_health(self, device_id, status, packets_increment=1, error_increment=0):
        """Update device health metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get device name if available
            cursor.execute('SELECT device_name FROM sensor_readings WHERE device_id = ? LIMIT 1', (device_id,))
            result = cursor.fetchone()
            device_name = result[0] if result else device_id
            
            # Check if device exists in health table
            cursor.execute('SELECT * FROM device_health WHERE device_id = ?', (device_id,))
            exists = cursor.fetchone()
            
            current_time = datetime.now().isoformat()
            
            if exists:
                # Update existing record
                cursor.execute('''
                    UPDATE device_health 
                    SET status = ?,
                        packets_received = packets_received + ?,
                        error_count = error_count + ?,
                        last_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE device_id = ?
                ''', (status, packets_increment, error_increment, current_time, device_id))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO device_health 
                    (device_id, device_name, status, packets_received, error_count, last_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (device_id, device_name, status, packets_increment, error_increment, current_time))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f" Database error (update_device_health): {e}")
            return False
        
    def close(self):
        """Close database connection"""
        # SQLite handles connections automatically
        pass
        
    def get_stats(self):
        """Get basic statistics from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM sensor_readings')
            total_readings = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT device_id) FROM sensor_readings')
            active_devices = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM sensor_readings WHERE status != "Good"')
            alerts_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_readings': total_readings,
                'active_devices': active_devices,
                'alerts_count': alerts_count
            }
        except Exception as e:
            print(f" Error getting stats: {e}")
            return {}