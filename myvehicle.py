import time
import json
import random
import paho.mqtt.client as mqtt

# MQTT broker details
broker = "broker.emqx.io"
port = 1883
topics = ["accident", "cartow", "overspeeding", "roadcondition", "traffic", "myvehiclestatus/car1", "Serversend1"]

# Function to simulate continuous random location updates
def simulate_location(client, start_lat, start_lon, duration_sec):
    for _ in range(duration_sec):
        # Use a fixed vehicle ID for one specific car
        vehicle_id = "1234"
        
        # Generate random speed between 0 and 100 km/h
        speed_kmph = random.uniform(0, 150)
        
        # Generate random latitude and longitude within a range
        current_lat = start_lat + random.uniform(-0.01, 0.01)
        current_lon = start_lon + random.uniform(-0.01, 0.01)
        
        location = {
            "vehicle_id": vehicle_id,
            "latitude": current_lat,
            "longitude": current_lon,
            "speed": speed_kmph
        }

        # Publish location to all topics
        for topic in topics:
            client.publish(topic, json.dumps(location))
            print(f"Published to {topic}: {location}")
        
        time.sleep(1)  # Ensure the updates are sent once every second

# Callback when the client successfully connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the required topics
        for topic in topics:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received
def on_message(client, userdata, msg):
    print(f"Received message from topic {msg.topic}: {msg.payload.decode()}")

# Main function to connect to MQTT broker and send location updates
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(broker, port, 60)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return

    client.loop_start()

    # Simulate random location updates
    start_latitude = 12.9716  # Starting latitude (Bangalore)
    start_longitude = 77.5946  # Starting longitude (Bangalore)
    duration_seconds = 10  # Duration for which location updates are generated

    simulate_location(client, start_latitude, start_longitude, duration_seconds)

    client.loop_stop()

if __name__ == "__main__":
    main()
