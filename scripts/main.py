"""
Unified Automatic License Plate Recognition Pipeline
Executes detection, data interpolation, and final annotated video rendering in a single script.
"""

from ultralytics import YOLO
import cv2
import numpy as np
import pandas as pd
import ast
import csv

from src.core import util
from src.core.sort import SortTracker
from src.services.license_plate_service import AccessControlService
from src.core.util import get_car, read_license_plate, write_csv

from add_missing_data import interpolate_bounding_boxes
from visualize import draw_border


def main(video_path='data/videos/sample.mp4', output_path='data/videos/out.mp4'):
    """
    Process video with license plate authorization and visualization.

    Args:
        video_path (str): Path to input video
        output_path (str): Path to output video with authorization visualization
    """

    print("=== PASS 1: Inference & Tracking ===")
    
    # Initialize the access control service
    auth_service = AccessControlService('data/database/license_plates.db')

    # Add some authorized plates for testing
    auth_service.add_plate('ABC1234', 'Owner 1', 'Car')
    auth_service.add_plate('DEF5678', 'Owner 2', 'Truck')

    results = {}
    mot_tracker = SortTracker()

    # Load models
    coco_model = YOLO('yolov8m.pt')
    license_plate_detector = YOLO('models/license_plate_detector.pt')

    # Load video
    cap = cv2.VideoCapture(video_path)

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
            license_plates = license_plate_detector(frame, conf=0.1)[0]
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
                        # Use authorization service to check and log (do not draw here)
                        result = auth_service.auth_service.check_and_log(
                            plate_number=license_plate_text,
                            frame_number=frame_nmr
                        )

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

            # Display progress
            if frame_nmr % 30 == 0:
                print(f"Processing inference for frame {frame_nmr}...")

    cap.release()
    print("Inference complete! Writing raw CSV data...")
    write_csv(results, 'data/csv/test.csv')

    print("\n=== PASS 2: Interpolating Missing Data ===")
    
    with open('data/csv/test.csv', 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)

    interpolated_data = interpolate_bounding_boxes(data)

    header = ['frame_nmr', 'car_id', 'car_bbox', 'license_plate_bbox', 'license_plate_bbox_score', 'license_number', 'license_number_score']
    with open('data/csv/test_interpolated.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerows(interpolated_data)
        
    print("Interpolation complete!")

    print("\n=== PASS 3: Rendering Final Annotated Video ===")

    # Extract auth status per car to use during interpolation/rendering
    car_auth_status = {}
    for fn in results:
        for c_id in results[fn]:
            if 'authorization' in results[fn][c_id]:
                car_auth_status[int(c_id)] = results[fn][c_id]['authorization']['authorized']

    results_df = pd.read_csv('data/csv/test_interpolated.csv')
    
    # Reload video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print("Extracting highest-confidence license plate crops...")
    license_plate = {}
    for car_id in np.unique(results_df['car_id']):
        max_score = np.amax(results_df[results_df['car_id'] == car_id]['license_number_score'])
        row_data = results_df[(results_df['car_id'] == car_id) & (results_df['license_number_score'] == max_score)].iloc[0]
        license_plate[car_id] = {
            'license_crop': None,
            'license_plate_number': row_data['license_number']
        }
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, row_data['frame_nmr'])
        ret, frame = cap.read()
        if ret:
            x1, y1, x2, y2 = ast.literal_eval(row_data['license_plate_bbox'].replace('[ ', '[').replace('   ', ' ').replace('  ', ' ').replace(' ', ','))
            license_crop = frame[int(y1):int(y2), int(x1):int(x2), :]
            if license_crop.size > 0:
                license_crop = cv2.resize(license_crop, (int((x2 - x1) * 400 / (y2 - y1)), 400))
                license_plate[car_id]['license_crop'] = license_crop

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_nmr = -1
    ret = True
    
    print("Rendering frames...")
    while ret:
        ret, frame = cap.read()
        frame_nmr += 1
        
        if ret:
            df_ = results_df[results_df['frame_nmr'] == frame_nmr]
            for row_indx in range(len(df_)):
                car_id = int(df_.iloc[row_indx]['car_id'])
                
                # Fetch color dynamically based on auth status
                is_authorized = car_auth_status.get(car_id, False)
                box_color = (0, 255, 0) if is_authorized else (0, 0, 255) # Green vs Red
                
                # Draw car boundary brackets
                car_x1, car_y1, car_x2, car_y2 = ast.literal_eval(df_.iloc[row_indx]['car_bbox'].replace('[ ', '[').replace('   ', ' ').replace('  ', ' ').replace(' ', ','))
                draw_border(frame, (int(car_x1), int(car_y1)), (int(car_x2), int(car_y2)), box_color, 25, line_length_x=200, line_length_y=200)

                # Draw plate bounding box
                x1, y1, x2, y2 = ast.literal_eval(df_.iloc[row_indx]['license_plate_bbox'].replace('[ ', '[').replace('   ', ' ').replace('  ', ' ').replace(' ', ','))
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), box_color, 12)

                # Overlay cropped plate and large text above car
                try:
                    license_crop = license_plate[car_id]['license_crop']
                    if license_crop is not None:
                        H, W, _ = license_crop.shape

                        # Paste cropped plate
                        frame[int(car_y1) - H - 100:int(car_y1) - 100,
                              int((car_x2 + car_x1 - W) / 2):int((car_x2 + car_x1 + W) / 2), :] = license_crop

                        # Prepare text banner
                        plate_text = license_plate[car_id]['license_plate_number']
                        auth_text = "AUTHORIZED" if is_authorized else "UNAUTHORIZED"
                        display_text = f"{plate_text} - {auth_text}"

                        (text_width, text_height), _ = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 12)

                        # Paste white banner behind text
                        frame[int(car_y1) - H - 350:int(car_y1) - H - 100,
                              int((car_x2 + car_x1 - W) / 2):int((car_x2 + car_x1 + W) / 2), :] = (255, 255, 255)

                        # Banner fill color based on auth
                        text_x = int((car_x2 + car_x1 - text_width) / 2)
                        text_y = int(car_y1 - H - 150)
                        
                        # Add a colored backdrop box for the text to improve contrast
                        cv2.rectangle(frame, 
                                      (text_x - 20, text_y - text_height - 20),
                                      (text_x + text_width + 20, text_y + 20),
                                      box_color, 
                                      -1)

                        # Draw Text (black text on green/red backdrop)
                        cv2.putText(frame,
                                    display_text,
                                    (text_x, text_y),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    2.5,
                                    (0, 0, 0) if is_authorized else (255, 255, 255),
                                    12)
                except Exception as e:
                    # Failsafe if bounding box calculations fall outside frame limits
                    pass

            out.write(frame)
            if frame_nmr % 30 == 0:
                print(f"Rendering frame {frame_nmr}...")

    cap.release()
    out.release()
    
    print("\n" + "="*50)
    print(f"PIPELINE COMPLETE! Final video saved to {output_path}")
    print("="*50 + "\n")

    return results

if __name__ == '__main__':
    results = main('data/videos/sample2.mp4', 'data/videos/out.mp4')
