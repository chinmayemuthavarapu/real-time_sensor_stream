 # sensors/sensor_simulator.py
import threading
import time
import random
import json
from datetime import datetime

class DeviceSimulator(threading.Thread):
    def __init__(self, device_id: str, data_queue, device_name="Device"):
        super().__init__()
        self.device_id = device_id
        self.device_name = device_name
        self.data_queue = data_queue
        self.running = True
        self.message_id = 0
        self.daemon = True  # Thread will exit when main program exits
        
        # Device characteristics - different for each device
        self.base_temp = random.uniform(25.0, 40.0)
        self.base_vibration = random.uniform(0.5, 3.0)
        self.base_voltage = random.uniform(210.0, 240.0)
        
        # Statistics
        self.packets_sent = 0
        
    def generate_sensor_data(self):
        """Generate realistic sensor readings with occasional anomalies"""
        self.message_id += 1
        
        # Normal variations
        temp_variation = random.uniform(-3.0, 3.0)
        vibration_variation = random.uniform(-0.5, 0.5)
        voltage_variation = random.uniform(-5.0, 5.0)
        
        # Occasionally add anomalies (5% chance for each sensor)
        if random.random() < 0.05:  # 5% chance of abnormal temperature
            temp_variation = random.uniform(20.0, 50.0)  # High temperature
            
        if random.random() < 0.03:  # 3% chance of high vibration
            vibration_variation = random.uniform(5.0, 15.0)
            
        if random.random() < 0.02:  # 2% chance of low voltage
            voltage_variation = random.uniform(-50.0, -30.0)
        
        # Create sensor data
        sensor_data = {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "message_id": self.message_id,
            "timestamp": datetime.now().isoformat(),
            "temperature": round(self.base_temp + temp_variation, 2),
            "vibration": round(max(0.1, self.base_vibration + vibration_variation), 2),
            "voltage": round(self.base_voltage + voltage_variation, 2)
        }
        
        return sensor_data
    
    def run(self):
        """Main thread loop - generates data every 1-2 seconds"""
        print(f"📡 Device {self.device_id} ({self.device_name}) started")
        
        while self.running:
            try:
                # Generate sensor data
                sensor_data = self.generate_sensor_data()
                
                # Put data in queue for processing
                self.data_queue.put(sensor_data)
                self.packets_sent += 1
                
                # Print status every 5 packets
                if self.packets_sent % 5 == 0:
                    print(f"📤 {self.device_id}: Sent {self.packets_sent} packets")
                
                # Wait 1-2 seconds
                wait_time = random.uniform(1.0, 2.0)
                time.sleep(wait_time)
                
            except Exception as e:
                print(f" Error in {self.device_id}: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the device thread"""
        self.running = False
        print(f"⏹️  Device {self.device_id} stopped. Total packets: {self.packets_sent}")