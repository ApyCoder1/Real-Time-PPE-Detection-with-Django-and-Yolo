import base64
import json
import cv2
import torch
import pygame
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
import asyncio
from collections import deque
import numpy as np
import time  # Import time module for tracking duration

# Confidence threshold for detections
CONFIDENCE_THRESHOLD = 0.3  

# Global model & video capture (shared for all connections)
model = YOLO('app1/best.pt')  # Load YOLO model once
video_capture = cv2.VideoCapture(0)  # Shared video capture
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
video_capture.set(cv2.CAP_PROP_FPS, 30)  # Adjust FPS to balance performance

# Initialize pygame for sound alerts
pygame.mixer.init()
alert_sound = pygame.mixer.Sound("app1/alert.mp3")  # Load alert sound file

class VideoStreamConsumer(AsyncWebsocketConsumer):
    active_connections = set()  # Track active WebSocket connections
    current_class_ids = []  # List of class IDs to detect
    tracked_objects = {}  # Dictionary to track object IDs and their timestamps
    object_entry_time = {}  # Track entry time of objects with class ID 1 or 2
    object_counter = 0  # Track unique object IDs
    ALERT_TIME_THRESHOLD = 1  # Alert if an object is detected for more than 3 seconds

    async def connect(self):
        print("WebSocket connection established")
        self.active_connections.add(self)  # Add client to active connections
        await self.accept()
        self.streaming = True

        # Start streaming only if this is the first connection
        if len(self.active_connections) == 1:
            asyncio.create_task(self.stream_video())

    async def disconnect(self, close_code):
        print("WebSocket connection closed")
        self.active_connections.discard(self)  # Remove client
        self.streaming = False

    async def receive(self, text_data):
        # Handle received message (e.g., setting class IDs or confidence threshold)
        data = json.loads(text_data)

        # Check for the action to set class IDs
        if data.get('action') == 'set_class_ids':
            self.current_class_ids = data.get('class_ids', [])
            print(f"Class IDs set to {self.current_class_ids}")

        # Check for the action to set the confidence threshold
        elif data.get('action') == 'set_confidence_threshold':
            new_threshold = data.get('confidence_threshold')
            if isinstance(new_threshold, (int, float)) and 0 <= new_threshold <= 1:
                global CONFIDENCE_THRESHOLD
                CONFIDENCE_THRESHOLD = new_threshold  # Update the global confidence threshold
                print(f"Confidence threshold set to {CONFIDENCE_THRESHOLD}")
            else:
                print("Invalid confidence threshold value received.")

    def calculate_iou(self, box1, box2):
        # Calculate Intersection over Union (IoU) between two bounding boxes
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
        
        iou = inter_area / union_area if union_area != 0 else 0
        return iou

    def assign_tracking_ids(self, results, frame_id):
        detections = []
        current_time = time.time()  # Get current time

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

                # **Track entry time for alert triggering**
                if class_id in [1, 2]:
                    if track_id not in self.object_entry_time:
                        self.object_entry_time[track_id] = current_time  # First time detection
                    else:
                        duration = current_time - self.object_entry_time[track_id]
                        if duration > self.ALERT_TIME_THRESHOLD:
                            print(f"Alert! Object ID {track_id} with Class ID {class_id} detected for {duration:.2f} seconds!")
                            pygame.mixer.Sound.play(alert_sound)  # Play sound alert
                            del self.object_entry_time[track_id]  # Reset after alert

                detections.append(detection)

        return detections

    async def stream_video(self):
        frame_id = 0
        while self.active_connections:
            ret, frame = video_capture.read()
            if not ret:
                print("Error: Failed to capture frame")
                break

            results = model(frame, verbose=False)

            detections = self.assign_tracking_ids(results, frame_id)

            for detection in detections:
                x1, y1, x2, y2 = detection['bbox']
                label = f"{detection['class_name']}:{detection['confidence']:.2f} ID:{detection['track_id']}"

                # Check for class ID 1 and 2 to apply red color
                if detection['class_id'] in [1, 2]:
                    color = (0, 0, 255)  # Red color (BGR format)
                else:
                    color = (0, 255, 0)  # Green color (BGR format)

                # Draw the rectangle with increased thickness (e.g., thickness=4)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)

                # Draw the label
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')

            message = json.dumps({
                'frame': frame_data,
                'detected_objects': detections
            })

            tasks = [connection.send(text_data=message) for connection in self.active_connections]
            await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(0.02)
            frame_id += 1

        print("Video stream ended")




###############################################
