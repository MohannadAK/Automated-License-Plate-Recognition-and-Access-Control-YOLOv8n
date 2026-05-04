"""
Quick Start Guide: License Plate Authorization Service
Run this script to test the authorization service functionality
"""

from license_plate_service import AccessControlService
import json


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def main():
    """Run quick start examples."""
    
    print_section("License Plate Authorization Service - Quick Start")
    
    # Initialize the service
    print("\n1. Initializing Authorization Service...")
    service = AccessControlService('license_plates.db')
    print("   ✓ Service initialized with database: license_plates.db")
    
    # Add authorized plates
    print_section("2. Adding Authorized License Plates")
    
    test_plates = [
        ('ABC1234', 'John Doe', 'Toyota Camry'),
        ('XYZ5678', 'Jane Smith', 'Honda Civic'),
        ('LPR9012', 'Bob Johnson', 'Ford Truck'),
        ('QWE3456', 'Alice Williams', 'BMW'),
    ]
    
    for plate, owner, vehicle in test_plates:
        success = service.add_plate(plate, owner, vehicle)
        status = "✓" if success else "✗"
        print(f"   {status} Added: {plate} - {owner} ({vehicle})")
    
    # Get all authorized plates
    print_section("3. Retrieving All Authorized Plates")
    plates = service.get_authorized_plates()
    for plate in plates:
        print(f"   • {plate}")
    print(f"\n   Total authorized plates: {len(plates)}")
    
    # Test authorization checks
    print_section("4. Testing Authorization Checks")
    
    test_cases = [
        ('ABC1234', True),      # Should be authorized
        ('XYZ5678', True),      # Should be authorized
        ('UNKNOWN', False),     # Should be unauthorized
        ('DENIED', False),      # Should be unauthorized
    ]
    
    for plate, expected in test_cases:
        result = service.auth_service.check_and_log(plate)
        is_authorized = result['authorized']
        status = "✓" if is_authorized == expected else "✗"
        auth_text = "AUTHORIZED" if is_authorized else "UNAUTHORIZED"
        print(f"   {status} {plate:12} -> {auth_text}")
    
    # Test plate removal
    print_section("5. Testing Plate Removal (Soft Delete)")
    
    plate_to_remove = 'QWE3456'
    print(f"\n   Removing plate: {plate_to_remove}")
    service.remove_plate(plate_to_remove)
    print(f"   ✓ Plate deactivated")
    
    # Verify removal
    plates_after = service.get_authorized_plates()
    print(f"\n   Authorized plates after removal: {len(plates_after)}")
    for plate in plates_after:
        print(f"   • {plate}")
    
    # Show database location
    print_section("6. Database Information")
    print("\n   Database file: license_plates.db")
    print("   Location: Current working directory")
    print("\n   Tables created:")
    print("   • authorized_plates - Stores authorized license plates")
    print("   • access_log - Logs all access attempts")
    
    # Usage example
    print_section("7. Usage Example in Your Code")
    
    example_code = '''
from license_plate_service import AccessControlService

# Initialize service
service = AccessControlService('license_plates.db')

# Add authorized plates
service.add_plate('ABC1234', 'Owner Name', 'Car Model')

# When processing video frames:
result = service.process_plate(
    plate_text='ABC1234',
    frame=frame,
    plate_bbox=(100, 100, 200, 150),
    vehicle_bbox=(50, 50, 300, 300),
    frame_number=frame_number
)

# Access results
if result['authorized']:
    print("✓ Access GRANTED")
else:
    print("✗ Access DENIED")

# Get the frame with visualization (green or red box)
output_frame = result['frame']
'''
    
    print(example_code)
    
    # Summary
    print_section("8. Summary")
    
    summary = {
        'Service Status': 'Active',
        'Database': 'license_plates.db (Created)',
        'Authorized Plates': len(plates_after),
        'Features': [
            'Check authorization status',
            'Log access attempts',
            'Visualize on video frames',
            'Green box (Authorized)',
            'Red box (Unauthorized)'
        ]
    }
    
    print("\n   Service Status: ✓ Ready to use")
    print(f"   Active Authorized Plates: {len(plates_after)}")
    print(f"\n   Features:")
    for feature in summary['Features']:
        print(f"   ✓ {feature}")
    
    print_section("Next Steps")
    
    print("""
   1. Copy your existing authorized plates to the database:
      service.add_plate('YOUR_PLATE', 'Owner Name', 'Vehicle Type')
   
   2. Integrate with your main.py:
      - See main_with_authorization.py for complete example
      - Use service.process_plate() in your detection loop
   
   3. Process your video with authorization visualization:
      python main_with_authorization.py
   
   4. Check output video with colored boxes:
      - Green: Authorized vehicles
      - Red: Unauthorized vehicles
   
   5. Review access logs in database:
      - Database: license_plates.db
      - Table: access_log
""")
    
    print("="*60)
    print("  Quick Start Complete! ✓")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
