# License Plate Authorization Service Documentation

## Overview

The `license_plate_service.py` provides a complete authorization system for license plates with SQLite database integration. It can check if a detected license plate is authorized and visualize the result on video frames with colored boxes (green for authorized, red for unauthorized).

## Components

### 1. **LicensePlateDatabase**
Manages all database operations using SQLite.

#### Methods:
- `init_database()` - Creates database tables if they don't exist
- `add_authorized_plate(plate_number, owner_name='', vehicle_type='')` - Add a new authorized plate
- `remove_authorized_plate(plate_number)` - Deactivate an authorized plate
- `get_all_authorized_plates()` - Retrieve all active authorized plates
- `log_access(plate_number, status, frame_number=None)` - Log access attempts

#### Example:
```python
from license_plate_service import LicensePlateDatabase

db = LicensePlateDatabase('license_plates.db')

# Add authorized plates
db.add_authorized_plate('ABC1234', 'John Doe', 'Car')
db.add_authorized_plate('XYZ5678', 'Jane Smith', 'Truck')

# Get all authorized plates
plates = db.get_all_authorized_plates()
print(plates)  # ['ABC1234', 'XYZ5678']

# Remove a plate
db.remove_authorized_plate('ABC1234')

# Log access
db.log_access('ABC1234', 'AUTHORIZED', frame_number=100)
```

### 2. **AuthorizationService**
Handles authorization checking for license plates.

#### Methods:
- `is_authorized(plate_number)` - Check if a plate is authorized (returns bool)
- `check_and_log(plate_number, frame_number=None)` - Check and log authorization

#### Example:
```python
from license_plate_service import AuthorizationService

auth = AuthorizationService('license_plates.db')

# Check if authorized
is_auth = auth.is_authorized('ABC1234')
print(is_auth)  # True/False

# Check and log
result = auth.check_and_log('ABC1234', frame_number=50)
print(result)  
# {'authorized': True, 'status': 'AUTHORIZED', 'plate_number': 'ABC1234'}
```

### 3. **VisualizationService**
Handles drawing colored boxes on video frames.

#### Methods:
- `draw_plate_box(frame, bbox, is_authorized, plate_text='')` - Draw box around license plate
- `draw_vehicle_box(frame, bbox, is_authorized)` - Draw box around vehicle

#### Colors:
- **GREEN** (0, 255, 0) - Authorized vehicle
- **RED** (0, 0, 255) - Unauthorized vehicle
- **WHITE** (255, 255, 255) - Text color
- **BLACK** (0, 0, 0) - Background

#### Example:
```python
from license_plate_service import VisualizationService
import cv2

viz = VisualizationService()

# Read frame
frame = cv2.imread('frame.jpg')

# Draw authorized plate
frame = viz.draw_plate_box(
    frame, 
    bbox=(100, 100, 200, 150), 
    is_authorized=True, 
    plate_text='ABC1234'
)

# Draw vehicle box
frame = viz.draw_vehicle_box(
    frame, 
    bbox=(50, 50, 300, 300), 
    is_authorized=True
)

cv2.imwrite('output.jpg', frame)
```

### 4. **AccessControlService** (Main Service)
Combines all components for complete access control.

#### Methods:
- `process_plate(plate_text, frame, plate_bbox, vehicle_bbox=None, frame_number=None)` - Complete processing
- `add_plate(plate_number, owner_name='', vehicle_type='')` - Add authorized plate
- `remove_plate(plate_number)` - Remove authorized plate
- `get_authorized_plates()` - Get all authorized plates

#### Example:
```python
from license_plate_service import AccessControlService

# Initialize service
service = AccessControlService('license_plates.db')

# Add plates
service.add_plate('ABC1234', 'Owner 1', 'Car')
service.add_plate('XYZ5678', 'Owner 2', 'Truck')

# Process a detected plate
result = service.process_plate(
    plate_text='ABC1234',
    frame=frame,
    plate_bbox=(100, 100, 200, 150),
    vehicle_bbox=(50, 50, 300, 300),
    frame_number=100
)

print(result['authorized'])  # True/False
print(result['status'])      # 'AUTHORIZED' or 'UNAUTHORIZED'
# result['frame'] - frame with visualization
```

## Database Schema

### authorized_plates table
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

### access_log table
```sql
CREATE TABLE access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number TEXT NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    frame_number INTEGER
)
```

## Integration with Existing Code

See `main_with_authorization.py` for complete integration example.

### Quick Integration:

```python
from license_plate_service import AccessControlService

# In your main loop:
service = AccessControlService('license_plates.db')

# Add authorized plates
service.add_plate('ABC1234', 'Owner 1', 'Car')

# When processing each license plate:
result = service.process_plate(
    plate_text=license_plate_text,
    frame=frame,
    plate_bbox=[x1, y1, x2, y2],
    vehicle_bbox=[xcar1, ycar1, xcar2, ycar2],
    frame_number=frame_nmr
)

# Use the processed frame with visualization
frame = result['frame']
```

## Usage Workflow

### 1. Initialize Service
```python
service = AccessControlService('license_plates.db')
```

### 2. Populate Authorized Plates
```python
# From CSV file
with open('authorized_plates.csv') as f:
    for line in f:
        plate, owner, vehicle = line.strip().split(',')
        service.add_plate(plate, owner, vehicle)
```

### 3. Process Video
```python
# In your detection loop
if license_plate_text:
    result = service.process_plate(
        plate_text=license_plate_text,
        frame=frame,
        plate_bbox=plate_bbox,
        vehicle_bbox=vehicle_bbox,
        frame_number=frame_nmr
    )
    
    # Frame now has visualization
    frame = result['frame']
    
    # Access authorization status
    if result['authorized']:
        print(f"Access GRANTED: {result['plate_number']}")
    else:
        print(f"Access DENIED: {result['plate_number']}")
```

## Features

✅ SQLite database for persistent storage  
✅ Authorization checking  
✅ Access logging with timestamps  
✅ Visual feedback (green/red boxes)  
✅ Modular design for easy integration  
✅ Support for plate text display on visualization  
✅ Multiple database operations (add, remove, query)  
✅ Soft delete for authorized plates (maintains history)  

## Output Format

When processing a plate, the service returns:
```python
{
    'frame': numpy_array,          # Frame with visualization
    'authorized': bool,            # True if authorized
    'status': str,                 # 'AUTHORIZED' or 'UNAUTHORIZED'
    'plate_number': str            # Uppercase plate number
}
```

## Notes

- All plate numbers are converted to uppercase for consistency
- Database is created automatically on first use
- Access attempts are logged for audit trails
- Green box = Authorized, Red box = Unauthorized
- Visualization includes plate text and authorization status
- Can be used with or without vehicle bounding box visualization
