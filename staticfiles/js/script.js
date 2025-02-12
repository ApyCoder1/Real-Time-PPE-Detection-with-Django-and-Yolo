
        const videoFrame = document.getElementById('video-frame');
        const statusDiv = document.getElementById('status');
        const startButton = document.getElementById('start-button');
        const stopButton = document.getElementById('stop-button');
        const detectedClassesDiv = document.getElementById('detected-classes');
        const classIdSelect = document.getElementById('class-id-select');
        const setClassButton = document.getElementById('set-class-button');
        const confidenceSlider = document.getElementById('confidence-slider');
        const confidenceValue = document.getElementById('confidence-value');
        const websocketUrl = 'ws://localhost:8000/ws/video_stream/';
        let socket = null;
        let currentClassIds = [];
        let confidenceThreshold = 0.1; // Default confidence threshold

        // Update confidence value display
        confidenceSlider.addEventListener('input', () => {
            confidenceValue.textContent = confidenceSlider.value;
            confidenceThreshold = parseFloat(confidenceSlider.value);
            if (socket) {
                const message = {
                    action: 'set_confidence_threshold',
                    confidence_threshold: confidenceThreshold
                };
                socket.send(JSON.stringify(message));
                console.log(`Confidence threshold set to ${confidenceThreshold}`);
            }
        });

        function updateStatus(connected) {
            if (connected) {
                statusDiv.innerHTML = '<i class="fas fa-check"></i>';
                statusDiv.className = 'status-connected';
                startButton.disabled = true;
                stopButton.disabled = false;
            } else {
                statusDiv.innerHTML = '<i class="fas fa-times"></i>';
                statusDiv.className = 'status-disconnected';
                startButton.disabled = false;
                stopButton.disabled = true;
            }
        }

        function connectWebSocket() {
            socket = new WebSocket(websocketUrl);

            socket.onopen = function () {
                console.log('WebSocket connected');
                updateStatus(true);
            };

            socket.onmessage = function (event) {
                const data = JSON.parse(event.data);
                if (data) {
                    requestAnimationFrame(() => {
                        videoFrame.src = 'data:image/jpeg;base64,' + data.frame;
                        detectedClassesDiv.textContent = 'Detected Classes: ' + data.detected_classes.join(', ');
                    });
                }
            };

            socket.onclose = function () {
                console.warn('WebSocket closed');
                updateStatus(false);
            };

            socket.onerror = function (error) {
                console.error('WebSocket error:', error);
                socket.close();
            };
        }

        function disconnectWebSocket() {
            if (socket) {
                socket.close();
                socket = null;
                updateStatus(false);
                videoFrame.src = "";
                detectedClassesDiv.textContent = '';
            }
        }

        function setClassesToDetect() {
            const selectedClassIds = Array.from(classIdSelect.selectedOptions).map(option => parseInt(option.value));
            if (selectedClassIds.length > 0) {
                currentClassIds = selectedClassIds;
                if (socket) {
                    const message = {
                        action: 'set_class_ids',
                        class_ids: currentClassIds
                    };
                    socket.send(JSON.stringify(message));
                    console.log(`Class IDs ${selectedClassIds.join(', ')} set for detection.`);
                }
            } else {
                alert('Please select at least one class.');
            }
        }

        startButton.addEventListener('click', connectWebSocket);
        stopButton.addEventListener('click', disconnectWebSocket);
        setClassButton.addEventListener('click', setClassesToDetect);
