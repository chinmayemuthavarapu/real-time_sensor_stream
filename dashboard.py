 # dashboard.py
import time
import os
import sqlite3
from datetime import datetime

class RealTimeDashboard:
    def __init__(self, db_path="sensor_data.db"):
        self.db_path = db_path
        self.running = True
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_live_data(self):
        """Get the latest data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            
            # Get total statistics
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE status='Critical'")
            critical = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sensor_readings WHERE status='Warning'")
            warning = cursor.fetchone()[0]
            
            # Get latest readings from each device
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
            
            return {
                'total': total,
                'critical': critical,
                'warning': warning,
                'devices': devices
            }
            
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    def display_dashboard(self):
        """Display the real-time dashboard"""
        print(" Starting Real-Time Dashboard...")
        print("Press Ctrl+C to exit\n")
        time.sleep(2)
        
        try:
            while self.running:
                self.clear_screen()
                
                # Get latest data
                data = self.get_live_data()
                
                if data is None:
                    print(" No data available yet")
                    print("Start the monitoring system first to collect data")
                    time.sleep(3)
                    break
                
                # Display header
                print("=" * 70)
                print(" REAL-TIME SENSOR MONITORING DASHBOARD")
                print("=" * 70)
                print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f" Total Readings: {data['total']} | "
                      f" Warnings: {data['warning']} | "
                      f" Critical: {data['critical']}")
                print("-" * 70)
                
                # Display device status
                print("\n🔧 DEVICE STATUS")
                print("-" * 70)
                print(f"{'Device':<10} {'Status':<12} {'Temp (°C)':<10} {'Vibration':<10} {'Voltage':<10} {'Last Update':<15}")
                print("-" * 70)
                
                for device in data['devices']:
                    device_id, temp, vib, volt, status, timestamp = device
                    
                    # Format timestamp
                    if 'T' in timestamp:
                        time_str = timestamp.split('T')[1][:8]
                    else:
                        time_str = timestamp[11:19] if len(timestamp) > 11 else timestamp
                    
                    # Status icons
                    if status == "Critical":
                        status_icon = "🔴"
                    elif status == "Warning":
                        status_icon = "🟡"
                    else:
                        status_icon = "🟢"
                    
                    # Highlight high temperature
                    temp_display = f"{temp}°C"
                    if temp > 80:
                        temp_display = f" {temp}°C"
                    
                    print(f"{device_id:<10} {status_icon} {status:<9} {temp_display:<12} {vib:<10} {volt:<10} {time_str:<15}")
                
                print("\n" + "=" * 70)
                print("Auto-refreshing every 5 seconds... Press Ctrl+C to exit")
                
                # Wait before refresh
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n Dashboard closed")
            self.running = False
        except Exception as e:
            print(f"Dashboard error: {e}")
            
    def run(self):
        """Start the dashboard"""
        self.display_dashboard()

# Quick test function
if __name__ == "__main__":
    print("Testing Dashboard...")
    
    # First, check if database exists
    if not os.path.exists("sensor_data.db"):
        print(" No database found!")
        print("Run main.py first to generate sensor data")
    else:
        dashboard = RealTimeDashboard()
        dashboard.run()