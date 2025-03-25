import base64
import json
import cv2
import torch
import pygame
import asyncio
import time
import pytz
import sqlite3
from collections import deque
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
from datetime import datetime


CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence to consider a detection

# Initialize the model
model = YOLO('app1/best.pt')

# Set up video capture (webcam)
video_capture = cv2.VideoCapture(0)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
video_capture.set(cv2.CAP_PROP_FPS, 30)

# Pygame setup for sound alert
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("app1/alert.mp3")

# Database setup
def setup_database():
    conn = sqlite3.connect('detections.db')  # Connect to SQLite database
    cursor = conn.cursor()

    # Create table to store detection data
    cursor.execute('''CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id INTEGER,
                        class_name TEXT,
                        confidence REAL,
                        track_id INTEGER,
                        bbox TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    
    conn.commit()
    return conn, cursor

# Create database connection
conn, cursor = setup_database()

class VideoStreamConsumer(AsyncWebsocketConsumer):
    active_connections = set()
    current_class_ids = []
    tracked_objects = {}
    object_entry_time = {}
    object_counter = 0  
    ALERT_TIME_THRESHOLD = 3  # Time threshold to trigger alert (in seconds)

    async def connect(self):
        print("WebSocket connection established")
        self.active_connections.add(self)
        await self.accept()
        self.streaming = True

        if len(self.active_connections) == 1:
            asyncio.create_task(self.stream_video())

    async def disconnect(self, close_code):
        print("WebSocket connection closed")
        self.active_connections.discard(self)
        self.streaming = False

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'set_class_ids':
            self.current_class_ids = data.get('class_ids', [])
            print(f"Class IDs set to {self.current_class_ids}")

        elif data.get('action') == 'set_confidence_threshold':
            new_threshold = data.get('confidence_threshold')
            if isinstance(new_threshold, (int, float)) and 0 <= new_threshold <= 1:
                global CONFIDENCE_THRESHOLD
                CONFIDENCE_THRESHOLD = new_threshold
                print(f"Confidence threshold set to {CONFIDENCE_THRESHOLD}")

    def calculate_iou(self, box1, box2):
        # Calculate Intersection over Union (IoU) to compare bounding boxes
        x1, y1, x2, y2 = box1
        x1_b, y1_b, x2_b, y2_b = box2
        
        inter_x1 = max(x1, x1_b)
        inter_y1 = max(y1, y1_b)
        inter_x2 = min(x2, x2_b)
        inter_y2 = min(y2, y2_b)
        
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x2_b - x1_b) * (y2_b - y1_b)
        
        union_area = area1 + area2 - inter_area
        return inter_area / union_area if union_area != 0 else 0

    def assign_tracking_ids(self, results, frame_id):
        detections = []
        current_time = time.time()

        for result in results[0].boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            confidence = result.conf[0].item()
            class_id = int(result.cls[0].item())

            if confidence > CONFIDENCE_THRESHOLD and (not self.current_class_ids or class_id in self.current_class_ids):
                detection = {
                    'bbox': (x1, y1, x2, y2),
                    'confidence': confidence,
                    'class_id': class_id,
                    'class_name': model.names[class_id]
                }

                assigned = False
                for track_id, tracked_data in list(self.tracked_objects.items()):
                    tracked_bbox = tracked_data[-1][1]  
                    iou = self.calculate_iou(detection['bbox'], tracked_bbox)
                    
                    if iou > 0.3:
                        self.tracked_objects[track_id].append((frame_id, detection['bbox']))
                        detection['track_id'] = track_id
                        assigned = True
                        break
                
                if not assigned:
                    self.object_counter += 1
                    track_id = self.object_counter
                    self.tracked_objects[track_id] = deque([(frame_id, detection['bbox'])])
                    detection['track_id'] = track_id

                # Save detection to the database
                self.save_detection_to_db(detection)

                if class_id in [1, 2]:
                    if track_id not in self.object_entry_time:
                        self.object_entry_time[track_id] = current_time
                    else:
                        duration = current_time - self.object_entry_time[track_id]
                        if duration > self.ALERT_TIME_THRESHOLD:
                            print(f"Alert! Object ID {track_id} with Class ID {class_id} detected for {duration:.2f} seconds!")
                            pygame.mixer.Sound.play(alert_sound)
                            del self.object_entry_time[track_id]

                detections.append(detection)

        return detections
    
    def save_detection_to_db(self, detection):
        class_id = detection["class_id"]
        class_name = detection["class_name"]
        confidence = detection["confidence"]
        track_id = detection["track_id"]
        bbox = str(detection["bbox"])  # Convert tuple to string for storage

        # Get current time in Asia/Riyadh time zone
        riyadh_tz = pytz.timezone("Asia/Riyadh") #For india Timezone Replace Riyadh To Kolkata
        timestamp = datetime.now(riyadh_tz).strftime("%Y-%m-%d %H:%M:%S")  # Convert to formatted string

    # Insert the detection into the database with the converted timestamp
        cursor.execute('''INSERT INTO detections (class_id, class_name, confidence, track_id, bbox, timestamp)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (class_id, class_name, confidence, track_id, bbox, timestamp))
        conn.commit()

        print(f"Detection saved: {class_name} (ID: {track_id}, Conf: {confidence:.2f}, Time: {timestamp})")

    async def stream_video(self):
        frame_id = 0
        while self.active_connections:
            ret, frame = video_capture.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            results = model(frame, verbose=False)
            detections = self.assign_tracking_ids(results, frame_id)

            # Draw bounding boxes on the frame
            for detection in detections:
                x1, y1, x2, y2 = detection['bbox']
                class_name = detection['class_name']
                confidence = detection['confidence']
                track_id = detection['track_id']

                # Set color based on class_id
                if detection['class_id'] in [1, 2]:  # For class 1 and 2, use red
                    color = (0, 0, 255)  # Red
                else:
                    color = (0, 255, 0)  # Green

                # Draw rectangle on the frame (using OpenCV)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)

                # Add label with confidence score
                label = f"{class_name} ({confidence:.2f})"
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Convert the frame to base64 for WebSocket transmission
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')

            message = json.dumps({'frame': frame_data, 'detected_objects': detections})

            tasks = [connection.send(text_data=message) for connection in self.active_connections]
            await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(0.02)  # To control frame rate
            frame_id += 1

        print("Video stream ended")

    def close_database(self):
        cursor.close()
        conn.close()
        print("Database connection closed")
