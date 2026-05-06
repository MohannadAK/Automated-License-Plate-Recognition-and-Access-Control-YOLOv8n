# License Plate Authorization System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [File Structure](#file-structure)
3. [Components](#components)
4. [Database Schema](#database-schema)
5. [API Reference](#api-reference)
6. [Integration Guide](#integration-guide)
7. [Usage Examples](#usage-examples)
8. [Advanced Features](#advanced-features)

---

## System Overview

The License Plate Authorization System is a modular solution for:
- **Detecting** license plates using YOLOv8n
- **Checking** if plates are authorized against a SQLite database
- **Visualizing** results with colored boxes (green=authorized, red=unauthorized)
- **Logging** all access attempts for audit trails

### Key Features
- ✅ Standalone service (can be used independently)
- ✅ SQLite database for persistent storage
- ✅ Real-time authorization checking
- ✅ Visual feedback on video frames
- ✅ Access logging and audit trails
- ✅ Easy integration with existing YOLOv8 detection code

---

## File Structure

```
project/
├── license_plate_service.py          # Core service implementation
├── main_with_authorization.py         # Integration example with YOLOv8
├── LICENSE_PLATE_SERVICE_README.md   # Service documentation (component-focused)
├── DOCUMENTATION.md                   # This file (system-level documentation)
├── quickstart.py                      # Quick-start script and testing
├── license_plates.db                  # SQLite database (auto-created)
└── [existing files]
    ├── main.py                       # Original main script
    ├── util.py                       # Utility functions
    ├── sort.py                       # SORT tracker
    └── yolov8n.pt                   # YOLOv8 model
```

---

## Components

### 1. license_plate_service.py

**Purpose**: Core service implementation containing all authorization logic

**Classes**:

#### a) LicensePlateDatabase
Manages all database operations using SQLite.

```python
from license_plate_service import LicensePlateDatabase

# Initialize
db = LicensePlateDatabase('license_plates.db')

# Operations
db.add_authorized_plate('ABC1234', 'John Doe', 'Car')
db.remove_authorized_plate('ABC1234')
plates = db.get_all_authorized_plates()
db.log_access('ABC1234', 'AUTHORIZED', frame_number=50)
```

**Key Methods**:
- `init_database()` - Creates tables on first use
- `add_authorized_plate(plate, owner, vehicle_type)` - Add new plate
- `remove_authorized_plate(plate)` - Deactivate plate
- `get_all_authorized_plates()` - Retrieve all active plates
- `log_access(plate, status, frame_number)` - Log access attempt

#### b) AuthorizationService
Handles authorization checking logic.

```python
from license_plate_service import AuthorizationService

auth = AuthorizationService('license_plates.db')

# Check if authorized
is_auth = auth.is_authorized('ABC1234')  # Returns: True/False

# Check and log in one call
result = auth.check_and_log('ABC1234', frame_number=50)
# Returns: {'authorized': True/False, 'status': 'AUTHORIZED'/'UNAUTHORIZED', 'plate_number': 'ABC1234'}
```

**Key Methods**:
- `is_authorized(plate_number)` → bool
- `check_and_log(plate_number, frame_number)` → dict

#### c) VisualizationService
Draws colored boxes on video frames.

```python
from license_plate_service import VisualizationService
import cv2

viz = VisualizationService()
frame = cv2.imread('frame.jpg')

# Draw around license plate
frame = viz.draw_plate_box(frame, (100, 100, 200, 150), is_authorized=True, plate_text='ABC1234')

# Draw around vehicle
frame = viz.draw_vehicle_box(frame, (50, 50, 300, 300), is_authorized=False)
```

**Key Methods**:
- `draw_plate_box(frame, bbox, is_authorized, plate_text)` → modified frame
- `draw_vehicle_box(frame, bbox, is_authorized)` → modified frame

**Colors**:
- GREEN (0, 255, 0) - Authorized
- RED (0, 0, 255) - Unauthorized
- WHITE (255, 255, 255) - Text
- BLACK (0, 0, 0) - Background

#### d) AccessControlService (Main Service)
Combines all components into one unified service.

```python
from license_plate_service import AccessControlService

service = AccessControlService('license_plates.db')

# Add plates
service.add_plate('ABC1234', 'Owner', 'Car')

# Process detected plate with visualization
result = service.process_plate(
    plate_text='ABC1234',
    frame=frame,
    plate_bbox=(100, 100, 200, 150),
    vehicle_bbox=(50, 50, 300, 300),
    frame_number=100
)

# Result contains:
# - frame: with visualization
# - authorized: True/False
# - status: 'AUTHORIZED'/'UNAUTHORIZED'
# - plate_number: 'ABC1234'
```

**Key Methods**:
- `process_plate(plate_text, frame, plate_bbox, vehicle_bbox, frame_number)` → dict
- `add_plate(plate_number, owner_name, vehicle_type)` → bool
- `remove_plate(plate_number)` → bool
- `get_authorized_plates()` → list

---

### 2. main_with_authorization.py

**Purpose**: Complete example showing how to integrate authorization service with YOLOv8 detection

**Function**: `main_with_authorization(video_path, output_path)`

**What it does**:
1. Loads YOLOv8 models (COCO for vehicles, custom for license plates)
2. Reads video frame by frame
3. Detects vehicles and license plates
4. Extracts and reads license plate text
5. **Checks authorization** using the service
6. **Draws colored boxes** on frames (green/red)
7. Writes output video with visualization
8. Logs all access attempts

**Usage**:
```python
python main_with_authorization.py
```

**Output**:
- `out_authorized.mp4` - Video with green/red boxes
- `test_authorized.csv` - Results CSV with authorization status

**Key Integration Points**:
```python
# Initialize service
auth_service = AccessControlService('license_plates.db')

# Add authorized plates
auth_service.add_plate('ABC1234', 'Owner 1', 'Car')

# Process detected plate
result = auth_service.process_plate(
    plate_text=license_plate_text,
    frame=frame,
    plate_bbox=[x1, y1, x2, y2],
    vehicle_bbox=[xcar1, ycar1, xcar2, ycar2],
    frame_number=frame_nmr
)

# Update frame with visualization
frame = result['frame']
```

---

### 3. LICENSE_PLATE_SERVICE_README.md

**Purpose**: Component-focused documentation

**Contains**:
- Detailed class documentation
- Method signatures and parameters
- Database schema definitions
- Individual component examples
- Integration snippets

**When to use**: Reference for specific component usage

---

### 4. quickstart.py

**Purpose**: Demonstration and testing script

**What it does**:
1. Initializes the authorization service
2. Adds 4 test license plates
3. Retrieves all plates
4. Tests authorization checks
5. Demonstrates plate removal
6. Shows database information
7. Provides usage examples

**Usage**:
```python
python quickstart.py
```

**Output**: Formatted console output showing all features working

---

## Database Schema

### Table 1: authorized_plates

Stores all authorized license plates.

```sql
CREATE TABLE authorized_plates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT UNIQUE NOT NULL,
    owner_name TEXT,
    vehicle_type TEXT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)
```

**Fields**:
- `id` - Unique identifier
- `plate_number` - License plate (e.g., 'ABC1234')
- `owner_name` - Vehicle owner's name
- `vehicle_type` - Type of vehicle (e.g., 'Car', 'Truck')
- `added_date` - When the plate was added
- `is_active` - 1=active, 0=deactivated (soft delete)

**Example Data**:
```
id | plate_number | owner_name   | vehicle_type | added_date              | is_active
1  | ABC1234      | John Doe     | Toyota       | 2026-05-04 10:30:15    | 1
2  | XYZ5678      | Jane Smith   | Honda        | 2026-05-04 10:30:20    | 1
3  | LPR9012      | Bob Johnson  | Ford Truck   | 2026-05-04 10:30:25    | 1
```

### Table 2: access_log

Records all access attempts for audit trails.

```sql
CREATE TABLE access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    frame_number INTEGER
)
```

**Fields**:
- `id` - Unique log entry ID
- `plate_number` - License plate that was checked
- `access_time` - When the check occurred
- `status` - 'AUTHORIZED' or 'UNAUTHORIZED'
- `frame_number` - Frame number from video (if applicable)

**Example Data**:
```
id | plate_number | access_time             | status       | frame_number
1  | ABC1234      | 2026-05-04 10:35:10    | AUTHORIZED   | 0
2  | XYZ5678      | 2026-05-04 10:35:11    | AUTHORIZED   | 5
3  | UNKNOWN      | 2026-05-04 10:35:12    | UNAUTHORIZED | 10
```

---

## API Reference

### AccessControlService (Primary API)

The main class you'll interact with.

#### Initialization
```python
service = AccessControlService(db_path='license_plates.db')
```

#### Methods

##### 1. add_plate()
```python
success = service.add_plate(plate_number, owner_name='', vehicle_type='')
```
- **Parameters**:
  - `plate_number` (str): License plate (will be uppercased)
  - `owner_name` (str, optional): Vehicle owner's name
  - `vehicle_type` (str, optional): Vehicle type
- **Returns**: bool - True if added, False if already exists
- **Example**:
  ```python
  service.add_plate('ABC1234', 'John Doe', 'Toyota Camry')
  ```

##### 2. remove_plate()
```python
success = service.remove_plate(plate_number)
```
- **Parameters**:
  - `plate_number` (str): License plate to remove
- **Returns**: bool - True if removed
- **Example**:
  ```python
  service.remove_plate('ABC1234')
  ```

##### 3. get_authorized_plates()
```python
plates = service.get_authorized_plates()
```
- **Returns**: list - All active authorized plate numbers
- **Example**:
  ```python
  plates = service.get_authorized_plates()
  # Output: ['ABC1234', 'XYZ5678', 'LPR9012']
  ```

##### 4. process_plate()
```python
result = service.process_plate(
    plate_text,
    frame,
    plate_bbox,
    vehicle_bbox=None,
    frame_number=None
)
```
- **Parameters**:
  - `plate_text` (str): Detected license plate text
  - `frame` (np.ndarray): Video frame
  - `plate_bbox` (tuple): License plate box [x1, y1, x2, y2]
  - `vehicle_bbox` (tuple, optional): Vehicle box [x1, y1, x2, y2]
  - `frame_number` (int, optional): Frame number for logging
- **Returns**: dict with:
  ```python
  {
      'frame': np.ndarray,         # Modified frame with visualization
      'authorized': bool,          # True if authorized
      'status': str,               # 'AUTHORIZED' or 'UNAUTHORIZED'
      'plate_number': str          # Uppercase plate number
  }
  ```
- **Example**:
  ```python
  result = service.process_plate(
      plate_text='ABC1234',
      frame=frame,
      plate_bbox=(100, 100, 200, 150),
      vehicle_bbox=(50, 50, 300, 300),
      frame_number=100
  )
  
  if result['authorized']:
      print("✓ Access GRANTED")
  else:
      print("✗ Access DENIED")
  
  output_frame = result['frame']
  ```

---

## Integration Guide

### Step 1: Initialize Service
```python
from license_plate_service import AccessControlService

service = AccessControlService('license_plates.db')
```

### Step 2: Populate Authorized Plates

**Option A: Programmatically**
```python
service.add_plate('ABC1234', 'Owner 1', 'Car')
service.add_plate('XYZ5678', 'Owner 2', 'Truck')
```

**Option B: From CSV**
```python
import csv

with open('authorized_plates.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        service.add_plate(row['plate'], row['owner'], row['vehicle'])
```

**Option C: Bulk insert**
```python
plates_data = [
    ('ABC1234', 'John Doe', 'Car'),
    ('XYZ5678', 'Jane Smith', 'Truck'),
    ('LPR9012', 'Bob Johnson', 'Bus'),
]

for plate, owner, vehicle in plates_data:
    service.add_plate(plate, owner, vehicle)
```

### Step 3: Use in Detection Loop

Modify your existing detection code:

```python
# In your main processing loop
for license_plate in license_plates.boxes.data.tolist():
    x1, y1, x2, y2, score, class_id = license_plate
    
    # ... your existing plate detection code ...
    
    if license_plate_text is not None:
        # NEW: Use authorization service
        result = service.process_plate(
            plate_text=license_plate_text,
            frame=frame,
            plate_bbox=[x1, y1, x2, y2],
            vehicle_bbox=[xcar1, ycar1, xcar2, ycar2],
            frame_number=frame_nmr
        )
        
        # Update frame with visualization
        frame = result['frame']
        
        # Handle based on authorization
        if result['authorized']:
            print(f"✓ {result['plate_number']} - AUTHORIZED")
            # Take action: open gate, log access, etc.
        else:
            print(f"✗ {result['plate_number']} - UNAUTHORIZED")
            # Take action: alert, block entry, etc.
```

### Step 4: Process Video

```python
# Full example in main_with_authorization.py
python main_with_authorization.py
```

---

## Usage Examples

### Example 1: Simple Authorization Check

```python
from license_plate_service import AccessControlService

# Initialize
service = AccessControlService()

# Add plates
service.add_plate('ABC1234', 'John', 'Car')
service.add_plate('XYZ5678', 'Jane', 'Truck')

# Check authorization
plates = service.get_authorized_plates()
print(f"Authorized plates: {plates}")

# Check if specific plate is authorized
is_auth = service.auth_service.is_authorized('ABC1234')
print(f"ABC1234 authorized: {is_auth}")  # True

is_auth = service.auth_service.is_authorized('UNKNOWN')
print(f"UNKNOWN authorized: {is_auth}")  # False
```

### Example 2: Video Processing with Visualization

```python
import cv2
from license_plate_service import AccessControlService

service = AccessControlService()
service.add_plate('ABC1234', 'Owner', 'Car')

# Read frame
frame = cv2.imread('frame.jpg')

# Process plate
result = service.process_plate(
    plate_text='ABC1234',
    frame=frame,
    plate_bbox=(100, 100, 200, 150),
    vehicle_bbox=(50, 50, 300, 300)
)

# Save result
cv2.imwrite('output.jpg', result['frame'])
```

### Example 3: Access Logging and Reporting

```python
import sqlite3
from license_plate_service import AccessControlService

service = AccessControlService('license_plates.db')

# Check some plates
for plate in ['ABC1234', 'UNKNOWN', 'ABC1234']:
    service.auth_service.check_and_log(plate)

# Query access logs
conn = sqlite3.connect('license_plates.db')
cursor = conn.cursor()

# Get all unauthorized attempts
cursor.execute('''
    SELECT plate_number, access_time, status 
    FROM access_log 
    WHERE status = 'UNAUTHORIZED' 
    ORDER BY access_time DESC
''')

print("Unauthorized access attempts:")
for plate, time, status in cursor.fetchall():
    print(f"  {plate} - {time} - {status}")

conn.close()
```

### Example 4: Bulk Database Operations

```python
from license_plate_service import LicensePlateDatabase

db = LicensePlateDatabase('license_plates.db')

# Add multiple plates
plates = [
    ('ABC1234', 'Owner 1', 'Car'),
    ('XYZ5678', 'Owner 2', 'Truck'),
    ('LPR9012', 'Owner 3', 'Bus'),
    ('QWE3456', 'Owner 4', 'Car'),
]

for plate, owner, vehicle in plates:
    db.add_authorized_plate(plate, owner, vehicle)

# Get all
all_plates = db.get_all_authorized_plates()
print(f"Total: {len(all_plates)}")

# Deactivate some
db.remove_authorized_plate('LPR9012')

# Get remaining
active_plates = db.get_all_authorized_plates()
print(f"Active: {len(active_plates)}")
```

---

## Advanced Features

### Feature 1: Access Log Analysis

```python
import sqlite3
from collections import Counter

conn = sqlite3.connect('license_plates.db')
cursor = conn.cursor()

# Most frequent plates
cursor.execute('''
    SELECT plate_number, COUNT(*) as count
    FROM access_log
    GROUP BY plate_number
    ORDER BY count DESC
    LIMIT 10
''')

print("Top 10 Most Frequent Plates:")
for plate, count in cursor.fetchall():
    print(f"  {plate}: {count} accesses")

conn.close()
```

### Feature 2: Time-based Analysis

```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('license_plates.db')
cursor = conn.cursor()

# Accesses in last 24 hours
yesterday = datetime.now() - timedelta(days=1)

cursor.execute('''
    SELECT COUNT(*) as total, 
           SUM(CASE WHEN status = 'AUTHORIZED' THEN 1 ELSE 0 END) as authorized,
           SUM(CASE WHEN status = 'UNAUTHORIZED' THEN 1 ELSE 0 END) as unauthorized
    FROM access_log
    WHERE access_time > ?
''', (yesterday.isoformat(),))

total, auth, unauth = cursor.fetchone()
print(f"Last 24 hours: {total} total, {auth} authorized, {unauth} unauthorized")

conn.close()
```

### Feature 3: Custom Authorization Rules

You can extend the authorization logic:

```python
class CustomAuthorizationService(AuthorizationService):
    def is_authorized(self, plate_number):
        """Custom logic with time-based rules"""
        from datetime import datetime
        
        base_auth = super().is_authorized(plate_number)
        
        # Example: deny access outside business hours
        hour = datetime.now().hour
        if hour < 9 or hour > 17:  # Outside 9 AM - 5 PM
            return False
        
        return base_auth
```

### Feature 4: Real-time Alerts

```python
from license_plate_service import AccessControlService
import smtplib
from email.mime.text import MIMEText

service = AccessControlService()

# When processing plates
result = service.process_plate(plate_text, frame, bbox)

# Alert on unauthorized access
if not result['authorized']:
    # Send email alert
    msg = MIMEText(f"Unauthorized access attempt: {result['plate_number']}")
    msg['Subject'] = "Security Alert"
    msg['From'] = "system@company.com"
    msg['To'] = "admin@company.com"
    
    # Send email (configure SMTP)
    # smtp = smtplib.SMTP('smtp.gmail.com', 587)
    # smtp.send_message(msg)
```

---

## Troubleshooting

### Issue: Database file not found
**Solution**: Database is created automatically on first use. Ensure you have write permissions in the directory.

### Issue: Plate always shows as unauthorized
**Solution**: Make sure the plate is added to the database:
```python
service.add_plate('YOUR_PLATE_NUMBER')
plates = service.get_authorized_plates()
print(plates)  # Verify it's there
```

### Issue: Visualization boxes not showing
**Solution**: Ensure bounding box coordinates are integers:
```python
bbox = (int(x1), int(y1), int(x2), int(y2))
```

### Issue: Video output file not created
**Solution**: Ensure OpenCV video writer is initialized correctly:
```python
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
# Check that fps and dimensions are correct
```

---

## Quick Reference

| Task | Code |
|------|------|
| Initialize service | `service = AccessControlService()` |
| Add authorized plate | `service.add_plate('ABC1234', 'Owner', 'Car')` |
| Check authorization | `result = service.auth_service.check_and_log('ABC1234')` |
| Process with visualization | `result = service.process_plate(...) frame = result['frame']` |
| Get all plates | `plates = service.get_authorized_plates()` |
| Remove plate | `service.remove_plate('ABC1234')` |

---

## Summary

This system provides a complete, production-ready solution for license plate authorization with:
- **Modular design** - Use components independently
- **Easy integration** - Drop into existing YOLOv8 code
- **Visual feedback** - Real-time colored visualization
- **Audit trails** - Complete access logging
- **Database persistence** - SQLite for reliable storage

For detailed component documentation, see `LICENSE_PLATE_SERVICE_README.md`.
For integration examples, see `main_with_authorization.py`.
For testing, run `python quickstart.py`.
