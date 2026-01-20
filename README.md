# Real-Time Sensor Data Stream Processor &  Health Monitoring System
-------------------------------------------------------------------------------------------------

PROJECT OVERVIEW
---------------------------------------------------------------------------------------------
This system mimics real-world monitoring solutions used in factories, warehouses, robotics, automation units, and logistics. It provides a complete pipeline from sensor simulation to data visualization with intelligent alerting and reporting.

PROJECT STRUCTURE
----------------------------------------------------------------------------------------------
sensor_monitor/
├── main.py
├── dashboard.py
├── report_generator.py
├── requirements.txt
├── sensors/
│   ├── __init__.py
│   └── sensor_simulator.py          
├── processor/
│   ├── __init__.py
│   └── data_processor.py           
├── storage/
│   ├── __init__.py
│   └── database.py                  
├── logs/
│   ├── alerts.log
│   └── critical_alerts.log
└── reports/
    └── report_2026-01-20.txt

FEATURES
------------------------------------------------------------------------------------------------
* Sensor Simulation
* Real-Time Processing
* Device Health Monitoring
* Alerting System
* Data Storage
* Reporting & Dashboard
* Technology Stack
  
 INSTALATION DEPENDENCIES
-----------------------------------------------------------------------------------------------
reportlab

USAGE GUIDE
------------------------------------------------------------------------------------------------
Main Menu Options
1.Start Real-Time Monitoring
2.View Live Dashboard
3.Generate Daily Report
4.View Alert Logs
5.View Database Stats
6.Exit

SAMPLE OUTPUT
-----------------------------------------------------------------------------------------------
1.Console Monitoring
 Device DEV001 started
 DEV001: Sent 5 packets
 WARNING: [2024-01-15 10:30:15] DEV002 - High Temperature Warning: Temp=75.5°C, Vib=3.2, Volt=215.0V
 Total packets processed: 10
 CRITICAL: [2024-01-15 10:30:25] DEV003 - High Vibration: Temp=45.2°C, Vib=12.8, Volt=210.5V

2.Dashboard Display

📊 REAL-TIME SENSOR DASHBOARD
======================================
Time: 2024-01-15 10:30:30
Total Readings: 150 |   Warnings: 5 |  Critical: 2

🔧 DEVICE STATUS
--------------------------------------
DEV001:  GOOD | Temp: 45.2°C | Last: 10:30:28
DEV002:  WARNING | Temp: 75.5°C | Last: 10:30:25
DEV003:  CRITICAL | Temp: 45.2°C | Last: 10:30:20

3.Report File

DAILY SENSOR REPORT - 2024-01-15

Total Readings: 1250
Critical Alerts: 8
Warning Alerts: 25
Average Temperature: 42.5°C
Active Devices: 5
Generated: 2024-01-15 23:59:59
