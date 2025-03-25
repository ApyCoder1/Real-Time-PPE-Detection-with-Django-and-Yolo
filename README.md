
---

# PPE Detection System

This project is a real-time PPE (Personal Protective Equipment) detection system using Django Channels, YOLO, WebSockets, and OpenCV. The system captures live video, detects PPE violations (e.g., missing helmets or vests), and alerts users via sound notifications. Additionally, it includes a **detection log dashboard** that provides insights into total detections, class distributions, and historical logs.

![image](https://github.com/user-attachments/assets/40c94630-8880-4893-b2fb-83c10fe32759)

![2025-03-25-10-04-46](https://github.com/user-attachments/assets/1a5511d3-639a-47f4-9d41-79263a22c9da)

## Features
- **Real-time object detection** using YOLO.
- **WebSocket-based live video streaming** for low-latency updates.
- **Detection log dashboard** with:
  - **Total detections** count.
  - **Class distribution analysis** (Pie chart visualization).
  - **Detections by time of day**.
  - **Recent detection logs** with details like class ID, confidence, and timestamp.
- **Adjustable confidence threshold** for detections.
- **Class-based filtering** to detect specific PPE violations.
- **Audio alerts** for detected violations.
- **User interface** with class selection and threshold adjustment.

## Technologies Used
- Python
- Django & Django Channels
- Daphne (ASGI server)
- OpenCV
- Ultralytics YOLO
- Pygame (for audio alerts)
- WebSockets
- HTML, CSS, JavaScript
- Chart.js (for pie charts and detection analysis)

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
2. Open the application in your browser:  
   **http://127.0.0.1:8000/**
3. Click **"Start Streaming"** to begin real-time video detection.

## WebSocket Consumer (`VideoStreamConsumer`)
- Establishes WebSocket connections.
- Handles video streaming and detection processing.
- Supports dynamic class ID selection and confidence threshold adjustments.
- Implements **object tracking using IoU (Intersection over Union)**.

## Detection Log Dashboard
### **Real-Time PPE Logs**
- Data updates **automatically every 2 seconds**.

#### **Statistics:**
- **Total Detections:** `670`
- **Total Class IDs:** `4`
- **Total Class Names:** `4`

#### **Detection Analysis:**
- **Pie Chart:** Displays the percentage distribution of detected PPE classes.
- **Detections by Time of Day:** A graph showing detection patterns over the day.
- **Recent Log History:**
  | ID  | Class ID | Class Name  | Confidence | Track ID | Bounding Box        | Timestamp |
  |-----|---------|------------|------------|---------|---------------------|----------------|
  | 670 | 3       | Safety Vest | 45.44%     | 3       | (253, 276, 501, 480) | 3/25/2025, 9:58:03 AM |
  | 665 | 3       | Safety Vest | 45.76%     | 3       | (254, 276, 500, 480) | 3/25/2025, 9:58:02 AM |
  | 666 | 3       | Safety Vest | 46.59%     | 3       | (253, 275, 500, 480) | 3/25/2025, 9:58:02 AM |
  | 661 | 2       | No Helmet   | 54.05%     | 1       | (316, 122, 429, 282) | 3/25/2025, 9:58:01 AM |

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
- Expand support for more PPE object classes.
- Optimize real-time detection for improved speed.
- Implement cloud-based storage for detection logs.

## Author
**ApyCoder**

## License
This project is licensed under the **MIT License**.

