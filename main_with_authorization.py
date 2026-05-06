"""
Example: Integration of License Plate Authorization Service with YOLOv8 Detection
This shows how to use the license_plate_service.py with your existing main.py
"""

from ultralytics import YOLO
import cv2
import numpy as np

import util
from sort import SortTracker
from license_plate_service import AccessControlService
from util import get_car, read_license_plate, write_csv


def main_with_authorization(video_path='./sample.mp4', output_path='./out_authorized.mp4'):
    """
    Process video with license plate authorization and visualization.
    
    Args:
        video_path (str): Path to input video
        output_path (str): Path to output video with authorization visualization
    """
    
    # Initialize the access control service
    auth_service = AccessControlService('license_plates.db')
    
    # Add some authorized plates for testing
    auth_service.add_plate('ABC1234', 'Owner 1', 'Car')
    auth_service.add_plate('DEF5678', 'Owner 2', 'Truck')
    # You can load plates from database or add them programmatically
    
    results = {}
    mot_tracker = SortTracker()
    
    # Load models
    coco_model = YOLO('yolov8n.pt')
    license_plate_detector = YOLO('./license_plate_detector.pt')
    
    # Load video
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties for output
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    vehicles = [2, 3, 5, 7]  # car, motorbike, bus, truck
    
    # Read frames from video
    frame_nmr = -1
    ret = True
    while ret:
        frame_nmr += 1
        ret, frame = cap.read()
        
        if ret:
            results[frame_nmr] = {}
            
            # Detect vehicles
            detections = coco_model(frame)[0]
            detections_ = []
            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                if int(class_id) in vehicles:
                    detections_.append([x1, y1, x2, y2, score, class_id])
            
            # Convert to numpy array
            if len(detections_) == 0:
                detections_ = np.empty((0, 6))
            else:
                detections_ = np.asarray(detections_)
            
            # Track vehicles
            track_ids = mot_tracker.update(detections_[:, :5])
            
            # Detect license plates
            license_plates = license_plate_detector(frame)[0]
            for license_plate in license_plates.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = license_plate
                
                # Assign license plate to car
                xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)
                
                if car_id != -1:
                    # Crop and process license plate
                    license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
                    license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
                    _, license_plate_crop_thresh = cv2.threshold(
                        license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV
                    )
                    
                    # Read license plate
                    license_plate_text, license_plate_text_score = read_license_plate(
                        license_plate_crop_thresh
                    )
                    
                    if license_plate_text is not None:
                        # Use authorization service to check and visualize
                        result = auth_service.process_plate(
                            plate_text=license_plate_text,
                            frame=frame,
                            plate_bbox=[x1, y1, x2, y2],
                            vehicle_bbox=[xcar1, ycar1, xcar2, ycar2],
                            frame_number=frame_nmr
                        )
                        
                        # Update frame with visualization
                        frame = result['frame']
                        
                        # Store result
                        results[frame_nmr][car_id] = {
                            'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                            'license_plate': {
                                'bbox': [x1, y1, x2, y2],
                                'text': license_plate_text,
                                'bbox_score': score,
                                'text_score': license_plate_text_score
                            },
                            'authorization': {
                                'authorized': result['authorized'],
                                'status': result['status']
                            }
                        }
            
            # Write frame to output video
            out.write(frame)
            
            # Display progress
            if frame_nmr % 30 == 0:
                print(f"Processing frame {frame_nmr}...")
    
    # Release resources
    cap.release()
    out.release()
    
    print(f"Video processing complete! Output saved to {output_path}")
    
    # Write results to CSV
    write_csv(results, './test_authorized.csv')
    
    return results


if __name__ == '__main__':
    # Run the authorization-enabled video processing
    results = main_with_authorization('./sample.mp4', './out_authorized.mp4')
