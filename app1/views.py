from django.shortcuts import render
import sqlite3
from collections import Counter
from datetime import datetime
from django.http import JsonResponse


def ppe_detection(request): 
    return render(request, 'ppe_detection.html')


def detection_list(request):
    # Connect to the SQLite database
    conn = sqlite3.connect('detections.db')
    cursor = conn.cursor()

    # Retrieve all detection data from the database
    cursor.execute("SELECT * FROM detections ORDER BY timestamp DESC")
    detections = cursor.fetchall()

    # Calculate total number of detections, total class IDs, and total class names
    total_detections = len(detections)
    class_ids = set([detection[1] for detection in detections])  # Assuming class_id is in index 1
    class_names = set([detection[2] for detection in detections])  # Assuming class_name is in index 2
    
    total_class_ids = len(class_ids)
    total_class_names = len(class_names)

    # Calculate most frequent class names (with counts)
    class_names_list = [detection[2] for detection in detections]  # Assuming class_name is in index 2
    class_name_counts = Counter(class_names_list)
    most_frequent_classes = class_name_counts.most_common(5)  # Get class names with counts

    # Calculate detection counts by time of day
    time_based_counts = {
        '6 AM - 12 PM': 0,
        '12 PM - 6 PM': 0,
        '6 PM - 12 AM': 0,
        '12 AM - 6 AM': 0
    }

    # Iterate through the detections to calculate time-based counts
    for detection in detections:
        timestamp = datetime.strptime(detection[6], "%Y-%m-%d %H:%M:%S")  # Assuming timestamp is in index 6
        hour = timestamp.hour
        
        if 6 <= hour < 12:
            time_based_counts['6 AM - 12 PM'] += 1
        elif 12 <= hour < 18:
            time_based_counts['12 PM - 6 PM'] += 1
        elif 18 <= hour < 24:
            time_based_counts['6 PM - 12 AM'] += 1
        else:
            time_based_counts['12 AM - 6 AM'] += 1

    # Close the database connection
    conn.close()

    # Pass the detections and totals to the template
    return render(request, 'detection_logs.html', {
        'detections': detections,
        'total_detections': total_detections,
        'total_class_ids': total_class_ids,
        'total_class_names': total_class_names,
        'most_frequent_classes': most_frequent_classes,
        'time_based_counts': time_based_counts  # Pass the time-based counts to the template
    })


def fetch_detections(request):
    # Connect to the SQLite database
    conn = sqlite3.connect('detections.db')
    cursor = conn.cursor()

    # Retrieve the latest detection data from the database
    cursor.execute("SELECT * FROM detections ORDER BY timestamp DESC")
    detections = cursor.fetchall()

    # Close the database connection
    conn.close()

    # Convert detections into a JSON-friendly format
    detections_data = []
    for detection in detections:
        detections_data.append({
            'id': detection[0],
            'class_id': detection[1],
            'class_name': detection[2],
            'confidence': detection[3],
            'track_id': detection[4],
            'bbox': detection[5],
            'timestamp': detection[6]
        })

    # Calculate total number of detections, total class IDs, and total class names
    total_detections = len(detections)
    class_ids = set([detection[1] for detection in detections])
    class_names = set([detection[2] for detection in detections])

    total_class_ids = len(class_ids)
    total_class_names = len(class_names)

    # Calculate most frequent class names (with counts)
    class_names_list = [detection[2] for detection in detections]
    class_name_counts = Counter(class_names_list)
    most_frequent_classes = class_name_counts.most_common(5)  # Get class names with counts

    # Calculate detection counts by time of day
    time_based_counts = {
        '6 AM - 12 PM': 0,
        '12 PM - 6 PM': 0,
        '6 PM - 12 AM': 0,
        '12 AM - 6 AM': 0
    }

    # Iterate through the detections to calculate time-based counts
    for detection in detections:
        timestamp = datetime.strptime(detection[6], "%Y-%m-%d %H:%M:%S")  # Assuming timestamp is in index 6
        hour = timestamp.hour
        
        if 6 <= hour < 12:
            time_based_counts['6 AM - 12 PM'] += 1
        elif 12 <= hour < 18:
            time_based_counts['12 PM - 6 PM'] += 1
        elif 18 <= hour < 24:
            time_based_counts['6 PM - 12 AM'] += 1
        else:
            time_based_counts['12 AM - 6 AM'] += 1

    # Return a JSON response with the detections, totals, most frequent class names, and time-based counts
    return JsonResponse({
        'detections': detections_data,
        'total_detections': total_detections,
        'total_class_ids': total_class_ids,
        'total_class_names': total_class_names,
        'most_frequent_classes': most_frequent_classes,  # Include only class names with counts
        'time_based_counts': time_based_counts  # Include the time-based counts
    })
