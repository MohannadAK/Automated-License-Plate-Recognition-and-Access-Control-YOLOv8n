from src.services.license_plate_service import AccessControlService

# Connect to the database
svc = AccessControlService('data/database/license_plates.db')

# Add the plate (Plate Number, Owner Name, Vehicle Type)
svc.add_plate('SYI4OAH', 'Target Vehicle', 'Car')

# Verify it was added
print(svc.get_authorized_plates())