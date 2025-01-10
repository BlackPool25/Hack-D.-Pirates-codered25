// Initialize Leaflet Map
function initLeafletMap() {
    const map = L.map('map').setView([12.9716, 77.5946], 13); // Default location (Bangalore)

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Add a locate control to find user's location
    map.locate({ setView: true, maxZoom: 16 });
    
    map.on('locationfound', (e) => {
        const radius = e.accuracy / 2;
        L.marker(e.latlng)
            .addTo(map)
            .bindPopup('You are within ' + radius + ' meters from this point')
            .openPopup();
        L.circle(e.latlng, radius).addTo(map);
        
        // Store location for MQTT messages
        window.userLocation = e.latlng;
    });

    map.on('locationerror', () => {
        showNotification('Location access denied. Please enable location services.', 'error');
    });

    return map;
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 25px',
        borderRadius: '5px',
        backgroundColor: type === 'error' ? '#ff4444' : '#44aa44',
        color: 'white',
        zIndex: '1000',
        boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
        transition: 'opacity 0.5s ease-in-out'
    });

    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Setup MQTT Client and Button Actions
function setupButtonActions() {
    // Initialize MQTT Client
    const clientId = 'clientId-' + Math.random().toString(16).substr(2, 8);
    const mqttClient = new Paho.MQTT.Client('broker.emqx.io', 8083, clientId);

    // Set callback handlers
    mqttClient.onConnectionLost = (responseObject) => {
        if (responseObject.errorCode !== 0) {
            showNotification('Connection lost. Reconnecting...', 'error');
            setTimeout(() => connectMQTT(mqttClient), 3000);
        }
    };

    mqttClient.onMessageArrived = (message) => {
        console.log('Message received:', message.payloadString);
        showNotification('Response received: ' + message.payloadString, 'success');
    };

    // Connect to MQTT broker
    function connectMQTT(client) {
        const connectOptions = {
            useSSL: true,
            timeout: 3,
            onSuccess: () => {
                console.log('Connected to MQTT broker');
                showNotification('Connected to emergency services', 'success');
            },
            onFailure: (err) => {
                console.error('Failed to connect:', err);
                showNotification('Connection failed. Retrying...', 'error');
                setTimeout(() => connectMQTT(client), 3000);
            }
        };

        try {
            client.connect(connectOptions);
        } catch (error) {
            showNotification('Connection error. Retrying...', 'error');
            setTimeout(() => connectMQTT(client), 3000);
        }
    }

    connectMQTT(mqttClient);

    // Button configurations
    const buttonConfig = {
        'accident-btn': {
            topic: 'car/accident',
            message: 'Accident reported',
            alert: 'Accident reported. Emergency services have been notified.'
        },
        'help-btn': {
            topic: 'car/help',
            message: 'Help requested',
            alert: 'Help is on the way. Please stay at your location.'
        },
        'towing-btn': {
            topic: 'car/towing',
            message: 'Towing service requested',
            alert: 'Towing service has been notified. Please wait for assistance.'
        },
        'overspeeding-btn': {
            topic: 'car/overspeeding',
            message: 'Overspeeding reported',
            alert: 'Overspeeding report submitted successfully.'
        }
    };

    // Setup button event listeners
    Object.entries(buttonConfig).forEach(([btnId, config]) => {
        const button = document.getElementById(btnId);
        if (button) {
            button.addEventListener('click', () => {
                if (!mqttClient.isConnected()) {
                    showNotification('Reconnecting to server...', 'error');
                    connectMQTT(mqttClient);
                    return;
                }

                // Prepare MQTT message with location data
                const payload = {
                    timestamp: new Date().toISOString(),
                    location: window.userLocation ? {
                        lat: window.userLocation.lat,
                        lng: window.userLocation.lng
                    } : null,
                    message: config.message
                };

                // Send MQTT message
                try {
                    const message = new Paho.MQTT.Message(JSON.stringify(payload));
                    message.destinationName = config.topic;
                    message.qos = 1;
                    mqttClient.send(message);
                    
                    // Show success notifications
                    showNotification(config.message, 'success');
                    alert(config.alert);
                } catch (error) {
                    console.error('Error sending message:', error);
                    showNotification('Failed to send request. Please try again.', 'error');
                }
            });
        }
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initLeafletMap();
    setupButtonActions();
});