 # processor/data_processor.py
import threading
import time
from datetime import datetime
import os

class DataProcessor(threading.Thread):
    def __init__(self, data_queue, storage):
        super().__init__()
        self.data_queue = data_queue
        self.storage = storage
        self.running = True
        self.processed_count = 0
        self.daemon = True
        
        # Thresholds for alerts (from project requirements)
        self.thresholds = {
            'temperature': {'warning': 70.0, 'critical': 85.0},
            'vibration': {'warning': 7.0, 'critical': 10.0},
            'voltage': {'warning_low': 190.0, 'critical_low': 180.0}
        }
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
    def analyze_data(self, data):
        """Analyze sensor data and determine status"""
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
        """Log alerts to appropriate files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {data['device_id']} - {alert_type}: "
        log_entry += f"Temp={data['temperature']}°C, Vib={data['vibration']}, Volt={data['voltage']}V"
        
        # Print to console with colors
        if status == "Critical":
            print(f"\033[91m CRITICAL: {log_entry}\033[0m")  # Red
        elif status == "Warning":
            print(f"\033[93m WARNING: {log_entry}\033[0m")  # Yellow
            
        # Log to file
        try:
            if status == "Critical":
                with open('logs/critical_alerts.log', 'a', encoding='utf-8') as f:
                    f.write(log_entry + "\n")
            elif status == "Warning":
                with open('logs/alerts.log', 'a', encoding='utf-8') as f:
                    f.write(log_entry + "\n")
        except Exception as e:
            print(f" Failed to write log: {e}")
            
        # Simulate email alert for critical events
        if status == "Critical":
            self.simulate_email_alert(data, alert_type)
    
    def simulate_email_alert(self, data, alert_type):
        """Simulate sending email alert"""
        email_content = f"""
        {'='*60}
         CRITICAL ALERT - Immediate Attention Required 
        
        Device: {data['device_id']} ({data.get('device_name', 'Unknown')})
        Alert Type: {alert_type}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Sensor Readings:
        - Temperature: {data['temperature']}°C
        - Vibration: {data['vibration']}
        - Voltage: {data['voltage']}V
        - Message ID: {data['message_id']}
        
        Action Required: Please inspect the device immediately!
        
        ---
        Sensor Monitoring System
        {'='*60}
        """
        print(f"\033[91m📧 EMAIL ALERT SIMULATED:\033[0m")
        print(email_content)
        
    def run(self):
        """Main processing loop"""
        print("⚙️ Data processor started and waiting for data...")
        
        while self.running:
            try:
                # Get data from queue with timeout
                data = self.data_queue.get(timeout=1)
                
                # Process the data
                status, alert_type = self.analyze_data(data)
                
                # Add processing results to data
                data['status'] = status
                data['alert_type'] = alert_type
                
                # Log alerts if needed
                if status in ["Warning", "Critical"]:
                    self.log_alert(data, status, alert_type)
                
                # Store in database
                self.storage.store_sensor_data(data)
                
                # Update device health
                error_increment = 1 if status == "Critical" else 0
                self.storage.update_device_health(
                    data['device_id'], 
                    status, 
                    packets_increment=1,
                    error_increment=error_increment
                )
                
                self.processed_count += 1
                
                # Print progress every 10 processed items
                if self.processed_count % 10 == 0:
                    print(f"Total packets processed: {self.processed_count}")
                    
                self.data_queue.task_done()
                
            except Exception as e:
                # Handle empty queue (timeout) - this is normal
                if "empty" not in str(e).lower():
                    print(f" Processing error: {e}")
                time.sleep(0.1)
                
    def stop(self):
        """Stop the processor thread"""
        self.running = False
        print(f"⏹️  Data processor stopped. Total processed: {self.processed_count}")