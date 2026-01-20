
# main.py - COMPLETE WORKING VERSION
import os
import sys
import threading
import time
import queue
from datetime import datetime
import signal
import random
import sqlite3

print("=" * 60)
print(" SENSOR MONITORING SYSTEM")
print("=" * 60)

# ========== DEVICE SIMULATOR CLASS ==========
class DeviceSimulator(threading.Thread):
    def __init__(self, device_id: str, data_queue, device_name="Device"):
        super().__init__()
        self.device_id = device_id
        self.device_name = device_name
        self.data_queue = data_queue
        self.running = True
        self.message_id = 0
        self.daemon = True
        
        self.base_temp = random.uniform(25.0, 40.0)
        self.base_vibration = random.uniform(0.5, 3.0)
        self.base_voltage = random.uniform(210.0, 240.0)
        self.packets_sent = 0
        
    def generate_sensor_data(self):
        self.message_id += 1
        temp_variation = random.uniform(-3.0, 3.0)
        vibration_variation = random.uniform(-0.5, 0.5)
        voltage_variation = random.uniform(-5.0, 5.0)
        
        # Occasionally add anomalies
        if random.random() < 0.05:
            temp_variation = random.uniform(20.0, 50.0)
        if random.random() < 0.03:
            vibration_variation = random.uniform(5.0, 15.0)
        if random.random() < 0.02:
            voltage_variation = random.uniform(-50.0, -30.0)
        
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "message_id": self.message_id,
            "timestamp": datetime.now().isoformat(),
            "temperature": round(self.base_temp + temp_variation, 2),
            "vibration": round(max(0.1, self.base_vibration + vibration_variation), 2),
            "voltage": round(self.base_voltage + voltage_variation, 2)
        }
    
    def run(self):
        print(f"📡 Device {self.device_id} started")
        while self.running:
            try:
                sensor_data = self.generate_sensor_data()
                self.data_queue.put(sensor_data)
                self.packets_sent += 1
                if self.packets_sent % 5 == 0:
                    print(f" {self.device_id}: Sent {self.packets_sent} packets")
                time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                print(f" Error in {self.device_id}: {e}")
                time.sleep(1)
    
    def stop(self):
        self.running = False
        print(f"⏹️  Device {self.device_id} stopped. Total packets: {self.packets_sent}")

# ========== DATA STORAGE CLASS ==========
class DataStorage:
    def __init__(self, db_path="sensor_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()
        
    def store_sensor_data(self, data):
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
            print(f" Database error: {e}")
            return False

# ========== DATA PROCESSOR CLASS ==========
class DataProcessor(threading.Thread):
    def __init__(self, data_queue, storage):
        super().__init__()
        self.data_queue = data_queue
        self.storage = storage
        self.running = True
        self.processed_count = 0
        self.daemon = True
        
        # Thresholds for alerts
        self.thresholds = {
            'temperature': {'warning': 70.0, 'critical': 85.0},
            'vibration': {'warning': 7.0, 'critical': 10.0},
            'voltage': {'warning_low': 190.0, 'critical_low': 180.0}
        }
        
        # Create logs folder if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
    def analyze_data(self, data):
        status = "Good"
        alert_type = "None"
        
        temperature = data['temperature']
        vibration = data['vibration']
        voltage = data['voltage']
        
        # Check temperature
        if temperature > self.thresholds['temperature']['critical']:
            status = "Critical"
            alert_type = "High Temperature"
        elif temperature > self.thresholds['temperature']['warning']:
            status = "Warning"
            alert_type = "High Temperature Warning"
            
        # Check vibration
        if vibration > self.thresholds['vibration']['critical']:
            status = "Critical"
            alert_type = "High Vibration"
        elif vibration > self.thresholds['vibration']['warning']:
            if status == "Good":
                status = "Warning"
            alert_type = "High Vibration Warning" if alert_type == "None" else alert_type + ", High Vibration"
                
        # Check voltage
        if voltage < self.thresholds['voltage']['critical_low']:
            status = "Critical"
            alert_type = "Low Voltage"
        elif voltage < self.thresholds['voltage']['warning_low']:
            if status == "Good":
                status = "Warning"
            alert_type = "Low Voltage Warning" if alert_type == "None" else alert_type + ", Low Voltage"
                
        return status, alert_type
    
    def log_alert(self, data, status, alert_type):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {data['device_id']} - {alert_type}: "
        log_entry += f"Temp={data['temperature']}°C, Vib={data['vibration']}, Volt={data['voltage']}V"
        
        if status == "Critical":
            print(f"\033[91m CRITICAL: {log_entry}\033[0m")
            with open('logs/critical_alerts.log', 'a') as f:
                f.write(log_entry + "\n")
        elif status == "Warning":
            print(f"\033[93m  WARNING: {log_entry}\033[0m")
            with open('logs/alerts.log', 'a') as f:
                f.write(log_entry + "\n")
    
    def run(self):
        print(" Data processor started")
        while self.running:
            try:
                data = self.data_queue.get(timeout=1)
                status, alert_type = self.analyze_data(data)
                data['status'] = status
                data['alert_type'] = alert_type
                
                if status in ["Warning", "Critical"]:
                    self.log_alert(data, status, alert_type)
                
                self.storage.store_sensor_data(data)
                self.processed_count += 1
                
                if self.processed_count % 10 == 0:
                    print(f" Total packets processed: {self.processed_count}")
                    
                self.data_queue.task_done()
            except:
                time.sleep(0.1)
    
    def stop(self):
        self.running = False
        print(f" Data processor stopped. Total: {self.processed_count}")

# ========== SENSOR MONITORING SYSTEM CLASS ==========
class SensorMonitoringSystem:
    def __init__(self):
        self.running = True
        self.devices = []
        self.data_queue = queue.Queue(maxsize=1000)
        self.storage = DataStorage()
        self.processor = DataProcessor(self.data_queue, self.storage)
        
    def start(self):
        print("=" * 60)
        print(" Starting Real-Time Monitoring")
        print("=" * 60)
        
        # Create 3 devices
        device_ids = ['DEV001', 'DEV002', 'DEV003']
        device_names = ['Conveyor Belt', 'Cooling Unit', 'Robotic Arm']
        
        for i, dev_id in enumerate(device_ids):
            device = DeviceSimulator(dev_id, self.data_queue, device_names[i])
            self.devices.append(device)
        
        # Start processor
        self.processor.start()
        time.sleep(0.5)
        
        # Start devices
        for device in self.devices:
            device.start()
            time.sleep(0.2)
        
        print(f"\n Monitoring started with {len(self.devices)} devices")
        print(" Generating sensor data every 1-2 seconds...")
        print("  Alerts will appear in colored text")
        print("-" * 60)
        print("\nPress Ctrl+C to stop monitoring\n")
        
    def run_monitoring(self):
        """Run monitoring until Ctrl+C"""
        self.start()
        
        # Handle Ctrl+C
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        print("\n Stopping monitoring...")
        for device in self.devices:
            device.stop()
        self.processor.stop()
        time.sleep(1)
        print(" Monitoring stopped")

# ========== MENU FUNCTIONS ==========
def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    """Display main menu"""
    clear_screen()
    print("=" * 60)
    print(" SENSOR MONITORING SYSTEM - MAIN MENU")
    print("=" * 60)
    print("1. Start Real-Time Monitoring")
    print("2. View Live Dashboard")
    print("3. Generate Daily Report")
    print("4. View Alert Logs")
    print("5. View Database Stats")
    print("6. Exit")
    print("-" * 60)
    
    try:
        choice = input("Select option (1-6): ")
        return choice
    except KeyboardInterrupt:
        return '6'

def view_alert_logs():
    """Display alert logs"""
    clear_screen()
    print("=" * 60)
    print(" ALERT LOGS")
    print("=" * 60)
    
    try:
        # Check if logs directory exists
        if not os.path.exists("logs"):
            print("No logs directory found. Start monitoring first.")
            input("\nPress Enter to continue...")
            return
        
        # View warning alerts
        warning_file = "logs/alerts.log"
        if os.path.exists(warning_file):
            print("\n WARNING ALERTS:")
            print("-" * 40)
            with open(warning_file, "r") as f:
                warnings = f.readlines()
                if warnings:
                    print("Last 10 warnings:")
                    for warning in warnings[-10:]:
                        print(f"  {warning.strip()}")
                else:
                    print("No warning alerts yet")
        else:
            print("Warning log file not found")
        
        # View critical alerts
        critical_file = "logs/critical_alerts.log"
        if os.path.exists(critical_file):
            print("\n CRITICAL ALERTS:")
            print("-" * 40)
            with open(critical_file, "r") as f:
                criticals = f.readlines()
                if criticals:
                    print("Last 10 critical alerts:")
                    for critical in criticals[-10:]:
                        print(f"  {critical.strip()}")
                else:
                    print("No critical alerts yet")
        else:
            print("Critical log file not found")
            
    except Exception as e:
        print(f"Error reading logs: {e}")
    
    input("\nPress Enter to continue...")

def view_database_stats():
    """Show database statistics"""
    clear_screen()
    print("=" * 60)
    print(" DATABASE STATISTICS")
    print("=" * 60)
    
    try:
        if not os.path.exists("sensor_data.db"):
            print("No database found. Start monitoring first.")
            input("\nPress Enter to continue...")
            return
            
        conn = sqlite3.connect("sensor_data.db")
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        total = cursor.fetchone()[0]
        print(f"Total Sensor Readings: {total}")
        
        if total == 0:
            print("\nNo data available yet. Start monitoring to collect data.")
            conn.close()
            input("\nPress Enter to continue...")
            return
        
        # Device count
        cursor.execute("SELECT COUNT(DISTINCT device_id) FROM sensor_readings")
        devices = cursor.fetchone()[0]
        print(f"Devices Monitored: {devices}")
        
        # Alert statistics
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM sensor_readings 
            GROUP BY status
        ''')
        print("\n Status Distribution:")
        for status, count in cursor.fetchall():
            print(f"  {status}: {count}")
        
        # Latest readings
        print("\n Latest Readings:")
        cursor.execute('''
            SELECT device_id, temperature, status, timestamp 
            FROM sensor_readings 
            ORDER BY id DESC 
            LIMIT 5
        ''')
        for device_id, temp, status, timestamp in cursor.fetchall():
            time_str = timestamp[11:19] if len(timestamp) > 11 else timestamp
            print(f"  {device_id}: {temp}°C ({status}) at {time_str}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def generate_daily_report():
    """Generate a simple daily report"""
    clear_screen()
    
    print("=" * 60)
    print(" GENERATING DAILY REPORT")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        if not os.path.exists("sensor_data.db"):
            print("No database found. Start monitoring first.")
            input("\nPress Enter to continue...")
            return
            
        conn = sqlite3.connect("sensor_data.db")
        cursor = conn.cursor()
        
        # Get today's data
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='Critical' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN status='Warning' THEN 1 ELSE 0 END) as warning,
                AVG(temperature) as avg_temp
            FROM sensor_readings 
            WHERE DATE(timestamp) = ?
        ''', (today,))
        
        result = cursor.fetchone()
        
        if result[0] == 0:
            print("No data available for today yet.")
            print("Start monitoring to collect data.")
        else:
            total, critical, warning, avg_temp = result
            
            print(f"\n Report for: {today}")
            print("-" * 40)
            print(f"Total Readings: {total}")
            print(f"Critical Alerts: {critical}")
            print(f"Warning Alerts: {warning}")
            print(f"Average Temperature: {avg_temp:.1f}°C")
            
            # Save to file
            report_text = f"""DAILY SENSOR REPORT - {today}
===============================
Total Readings: {total}
Critical Alerts: {critical}
Warning Alerts: {warning}
Average Temperature: {avg_temp:.1f}°C
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================="""
            
            # Create reports folder if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            # Save as text file
            filename = f"reports/report_{today}.txt"
            with open(filename, "w") as f:
                f.write(report_text)
            
            print(f"\n Report saved to: {filename}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error generating report: {e}")
    
    input("\nPress Enter to continue...")

def run_dashboard():
    """Run the dashboard"""
    clear_screen()
    print("Loading dashboard...")
    time.sleep(1)
    
    try:
        # Simple dashboard implementation
        if not os.path.exists("sensor_data.db"):
            print("=" * 60)
            print(" DASHBOARD")
            print("=" * 60)
            print("\n No data available!")
            print("Start monitoring first (Option 1 in main menu)")
            input("\nPress Enter to continue...")
            return
        
        import sqlite3
        conn = sqlite3.connect("sensor_data.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        total = cursor.fetchone()[0]
        
        if total == 0:
            print("=" * 60)
            print(" DASHBOARD")
            print("=" * 60)
            print("\n No data available!")
            print("Start monitoring to collect data")
            conn.close()
            input("\nPress Enter to continue...")
            return
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE status='Critical'")
        critical = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE status='Warning'")
        warning = cursor.fetchone()[0]
        
        # Get latest device data
        cursor.execute('''
            SELECT device_id, temperature, vibration, voltage, status, timestamp
            FROM sensor_readings 
            WHERE id IN (
                SELECT MAX(id) FROM sensor_readings GROUP BY device_id
            )
            ORDER BY device_id
        ''')
        devices = cursor.fetchall()
        
        conn.close()
        
        # Display dashboard
        clear_screen()
        print("=" * 70)
        print(" REAL-TIME SENSOR DASHBOARD")
        print("=" * 70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f" Total Readings: {total} |   Warnings: {warning} |  Critical: {critical}")
        print("-" * 70)
        
        print("\n DEVICE STATUS")
        print("-" * 70)
        print(f"{'Device':<10} {'Status':<12} {'Temp (°C)':<12} {'Last Update':<15}")
        print("-" * 70)
        
        for device in devices:
            device_id, temp, vib, volt, status, timestamp = device
            
            # Format time
            time_str = timestamp[11:19] if len(timestamp) > 11 else timestamp
            
            # Status icon
            if status == "Critical":
                status_display = " CRITICAL"
            elif status == "Warning":
                status_display = " WARNING"
            else:
                status_display = " GOOD"
            
            # Temperature warning
            temp_display = f"{temp}°C"
            if temp > 80:
                temp_display = f" {temp}°C"
            
            print(f"{device_id:<10} {status_display:<12} {temp_display:<12} {time_str:<15}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
    
    input("\nPress Enter to continue...")

# ========== MAIN PROGRAM ==========
def main():
    """Main program with menu"""
    clear_screen()
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Start monitoring
            system = SensorMonitoringSystem()
            try:
                system.run_monitoring()
            except KeyboardInterrupt:
                print("\nReturning to menu...")
                time.sleep(1)
                
        elif choice == '2':
            # Run dashboard
            run_dashboard()
            
        elif choice == '3':
            # Generate report
            generate_daily_report()
            
        elif choice == '4':
            # View alert logs
            view_alert_logs()
            
        elif choice == '5':
            # View database stats
            view_database_stats()
            
        elif choice == '6':
            # Exit
            clear_screen()
            print("=" * 60)
            print(" Thank you for using Sensor Monitoring System!")
            print("Goodbye!")
            print("=" * 60)
            break
            
        else:
            print("\n Invalid choice. Please select 1-6")
            time.sleep(1)

# ========== RUN THE PROGRAM ==========
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Program terminated by user")
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        input("Press Enter to exit...")