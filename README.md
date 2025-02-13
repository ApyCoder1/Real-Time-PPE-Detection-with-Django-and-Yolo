# PPE Detection System

This project is a real-time PPE (Personal Protective Equipment) detection system using Django Channels, YOLO, WebSockets, and OpenCV. The system captures live video, detects PPE violations (e.g., missing helmets or vests), and alerts users via sound notifications.

## Features
- Real-time object detection using YOLO.
- WebSocket-based live video streaming.
- Adjustable confidence threshold for detections.
- Class-based filtering to detect specific PPE violations.
- Audio alerts for specific violations.
- User interface with class selection and threshold adjustment.

## Technologies Used
- Python
- Django & Django Channels
- Daphne (ASGI server)
- OpenCV
- Ultralytics YOLO
- Pygame (for audio alerts)
- WebSockets
- HTML, CSS, JavaScript

## Installation

### Prerequisites
Ensure you have Python installed along with the required dependencies.

```bash
pip install -r requirements.txt
```

### Running the Project
1. Start the Django server using Daphne:
   ```bash
   daphne -b 0.0.0.0 -p 8000 ppe.asgi:application
   ```
2. Open the application in your browser. http://127.0.0.1:8000/
3. Click "Start Streaming" to begin real-time video detection.

## WebSocket Consumer (`VideoStreamConsumer`)
- Establishes WebSocket connections.
- Handles video streaming and detection processing.
- Supports setting class IDs and confidence thresholds dynamically.
- Implements object tracking using IoU (Intersection over Union).

## Frontend Components
- **HTML/CSS**: Provides the UI for selecting detection parameters.
- **JavaScript (WebSockets)**: Handles real-time video updates and communication with the backend.

## Configuration
- **Model Path:** `app1/best.pt`
- **Alert Sound File:** `app1/alert.mp3`
- **Adjustable Confidence Threshold** (Default: `0.3`)
- **Classes Detected:**
  - `1`: No Vest
  - `2`: No Helmet
  - `3`: Safety Vest
  - `4`: Helmet

## Future Improvements
- Expand support for more object classes.
- Optimize performance for real-time detection.
- Implement cloud-based storage for detection logs.

## Author
ApyCoder

## License
This project is licensed under the MIT License.

