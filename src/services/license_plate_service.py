"""
License Plate Authorization Service
Handles database operations and authorization checks for license plates.
Uses SQLite database to store and validate authorized plates.
"""

import sqlite3
import cv2
from datetime import datetime
from pathlib import Path


class LicensePlateDatabase:
    """Manages SQLite database operations for authorized license plates."""
    
    def __init__(self, db_path='license_plates.db'):
        """
        Initialize the database connection.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create the database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            
            # Create authorized plates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authorized_plates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT UNIQUE NOT NULL,
                    owner_name TEXT,
                    vehicle_type TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create access log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT NOT NULL,
                    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    frame_number INTEGER
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def add_authorized_plate(self, plate_number, owner_name='', vehicle_type=''):
        """
        Add a license plate to the authorized list.
        
        Args:
            plate_number (str): License plate number
            owner_name (str): Owner's name
            vehicle_type (str): Type of vehicle
            
        Returns:
            bool: True if added successfully, False if already exists
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO authorized_plates (plate_number, owner_name, vehicle_type)
                VALUES (?, ?, ?)
            ''', (plate_number.upper(), owner_name, vehicle_type))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Plate {plate_number} already exists in the database.")
            return False
        finally:
            conn.close()
    
    def remove_authorized_plate(self, plate_number):
        """
        Remove a license plate from the authorized list (soft delete).
        
        Args:
            plate_number (str): License plate number
            
        Returns:
            bool: True if removed successfully
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE authorized_plates SET is_active = 0
                WHERE plate_number = ?
            ''', (plate_number.upper(),))
            conn.commit()
            success = cursor.rowcount > 0
            return success
        finally:
            conn.close()
    
    def get_all_authorized_plates(self):
        """
        Get all active authorized plates.
        
        Returns:
            list: List of authorized plate numbers
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute('''
                SELECT plate_number FROM authorized_plates WHERE is_active = 1
            ''')
            plates = [row[0] for row in cursor.fetchall()]
            return plates
        finally:
            conn.close()
    
    def log_access(self, plate_number, status, frame_number=None):
        """
        Log access attempt to the database.
        
        Args:
            plate_number (str): License plate number
            status (str): 'AUTHORIZED' or 'UNAUTHORIZED'
            frame_number (int): Frame number from video
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO access_log (plate_number, status, frame_number)
                VALUES (?, ?, ?)
            ''', (plate_number.upper(), status, frame_number))
            conn.commit()
        finally:
            conn.close()


class AuthorizationService:
    """Handles authorization checking for license plates."""
    
    def __init__(self, db_path='license_plates.db'):
        """
        Initialize the authorization service.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db = LicensePlateDatabase(db_path)
    
    def is_authorized(self, plate_number):
        """
        Check if a license plate is authorized.
        
        Args:
            plate_number (str): License plate number to check
            
        Returns:
            bool: True if authorized, False otherwise
        """
        authorized_plates = self.db.get_all_authorized_plates()
        return plate_number.upper() in authorized_plates
    
    def check_and_log(self, plate_number, frame_number=None):
        """
        Check authorization status and log the access attempt.
        
        Args:
            plate_number (str): License plate number
            frame_number (int): Frame number from video
            
        Returns:
            dict: {'authorized': bool, 'status': 'AUTHORIZED'/'UNAUTHORIZED'}
        """
        is_authorized = self.is_authorized(plate_number)
        status = 'AUTHORIZED' if is_authorized else 'UNAUTHORIZED'
        self.db.log_access(plate_number, status, frame_number)
        
        return {
            'authorized': is_authorized,
            'status': status,
            'plate_number': plate_number.upper()
        }


class VisualizationService:
    """Handles visualization of authorization status on video frames."""
    
    # Colors (BGR)
    GREEN = (0, 255, 0)
    RED = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    @staticmethod
    def draw_plate_box(frame, bbox, is_authorized, plate_text=''):
        h, w, _ = frame.shape

       # Dynamic scaling based on resolution
        scale = max(1, w / 1000)
        thickness = int(3 * scale)
        text_scale = 1.0 * scale

        x1, y1, x2, y2 = map(int, bbox)

        # Choose color
        color = VisualizationService.GREEN if is_authorized else VisualizationService.RED

        #  Draw plate bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        if plate_text:
            status_text = "AUTHORIZED" if is_authorized else "UNAUTHORIZED"
            display_text = f"{plate_text} - {status_text}"

            # Get text size
            text_size = cv2.getTextSize(
                display_text,
                cv2.FONT_HERSHEY_SIMPLEX,
                text_scale,
                thickness
            )[0]

            #  Background box (bigger padding)
            cv2.rectangle(
                frame,
                (x1, y1 - text_size[1] - 20),
                (x1 + text_size[0] + 20, y1),
                color,
                -1
            )

            #  Shadow (black text behind)
            cv2.putText(
                frame,
                display_text,
                (x1 + 10, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                text_scale,
                VisualizationService.BLACK,
                thickness + 2
            )

            #  Main text (white)
            cv2.putText(
                frame,
                display_text,
                (x1 + 10, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                text_scale,
                VisualizationService.WHITE,
                thickness
            )

        return frame

    @staticmethod
    def draw_vehicle_box(frame, bbox, is_authorized):
        h, w, _ = frame.shape

        #  Dynamic scaling
        scale = max(1, w / 1000)
        thickness = int(4 * scale)

        x1, y1, x2, y2 = map(int, bbox)

        color = VisualizationService.GREEN if is_authorized else VisualizationService.RED

        # ✅ Draw vehicle bounding box (thicker)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        return frame
class AccessControlService:
    """Main service that combines all components."""
    
    def __init__(self, db_path='license_plates.db'):
        """
        Initialize the complete access control service.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.auth_service = AuthorizationService(db_path)
        self.viz_service = VisualizationService()
    
    def process_plate(self, plate_text, frame, plate_bbox, vehicle_bbox=None, frame_number=None):
        """
        Process a detected license plate and draw result on frame.
        
        Args:
            plate_text (str): Detected license plate text
            frame (np.ndarray): The video frame
            plate_bbox (tuple): License plate bounding box (x1, y1, x2, y2)
            vehicle_bbox (tuple): Vehicle bounding box (optional)
            frame_number (int): Frame number from video (optional)
            
        Returns:
            dict: Contains 'frame', 'authorized', 'status', 'plate_number'
        """
        # Check authorization and log
        check_result = self.auth_service.check_and_log(plate_text, frame_number)
        is_authorized = check_result['authorized']
        
        # Draw vehicle box if provided
        if vehicle_bbox is not None:
            frame = self.viz_service.draw_vehicle_box(frame, vehicle_bbox, is_authorized)
        
        # Draw license plate box
        frame = self.viz_service.draw_plate_box(frame, plate_bbox, is_authorized, plate_text)
        
        return {
            'frame': frame,
            'authorized': is_authorized,
            'status': check_result['status'],
            'plate_number': check_result['plate_number']
        }
    
    def add_plate(self, plate_number, owner_name='', vehicle_type=''):
        """Add a plate to the authorized list."""
        return self.auth_service.db.add_authorized_plate(plate_number, owner_name, vehicle_type)
    
    def remove_plate(self, plate_number):
        """Remove a plate from the authorized list."""
        return self.auth_service.db.remove_authorized_plate(plate_number)
    
    def get_authorized_plates(self):
        """Get all authorized plates."""
        return self.auth_service.db.get_all_authorized_plates()


# Example usage
if __name__ == '__main__':
    # Initialize the service
    service = AccessControlService('license_plates.db')
    
    # Add some authorized plates
    service.add_plate('ABC1234', 'John Doe', 'Car')
    service.add_plate('XYZ5678', 'Jane Smith', 'Truck')
    
    # Print authorized plates
    print("Authorized plates:", service.get_authorized_plates())
    
    # Test authorization check
    print("\nAuthorization check results:")
    print("ABC1234:", service.auth_service.is_authorized('ABC1234'))
    print("UNKNOWN:", service.auth_service.is_authorized('UNKNOWN'))
