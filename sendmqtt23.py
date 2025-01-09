import paho.mqtt.client as mqtt
import random
import time
import json
import uuid

# MQTT broker details
BROKER = "broker.emqx.io"  # Replace with your broker's address
PORT = 1883

# Topics
TOPIC_LOCATION = "car/location"     # Topic to publish car locations
TOPIC_SPEED = "car/speed"           # Topic to publish car speeds
TOPIC_GENERATE = "generatelocandid" # Topic to publish generated location and IDs

# Generate random latitude and longitude
def generate_random_location():
    latitude = round(random.uniform(-90, 90), 6)    # Latitude range: -90 to 90
    longitude = round(random.uniform(-180, 180), 6) # Longitude range: -180 to 180
    return latitude, longitude

# Generate random speed with a 10% chance of being above the speed cap
def generate_random_speed():
    if random.random() < 0.1:
        return round(random.uniform(81.0, 120.0), 2)  # Speed range: 81 to 120 km/h
    else:
        return round(random.uniform(40.0, 80.0), 2)  # Speed range: 40 to 80 km/h

# Callback when the client successfully connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

# Function to simulate and publish location and speed data for 10 cars
def publish_car_data(client):
    car_ids = [str(uuid.uuid4()) for _ in range(10)]  # Generate unique IDs for 10 cars
    while True:
        for car_id in car_ids:
            latitude, longitude = generate_random_location()
            speed = generate_random_speed()
            
            # Create data for car location and speed
            location_data = {
                "id": car_id,
                "latitude": latitude,
                "longitude": longitude
            }
            speed_data = {
                "id": car_id,
                "speed": speed
            }
            
            # Publish data to respective topics
            client.publish(TOPIC_LOCATION, json.dumps(location_data))
            print(f"Published to {TOPIC_LOCATION}: {location_data}")
            
            client.publish(TOPIC_SPEED, json.dumps(speed_data))
            print(f"Published to {TOPIC_SPEED}: {speed_data}")
        
        print("Published location and speed for all 10 cars. Delaying for 10 seconds...")
        time.sleep(10)  # Delay for 10 seconds

# Function to generate and publish additional vehicle data in real-time
def publish_generated_data(client):
    while True:
        for _ in range(20):  # Generate data for 20 vehicles
            # Generate a unique ID for the vehicle
            vehicle_id = str(uuid.uuid4())

            # Generate random location
            latitude, longitude = generate_random_location()
            location_data = {
                "id": vehicle_id,
                "latitude": latitude,
                "longitude": longitude
            }

            # Publish location data
            client.publish(TOPIC_GENERATE, json.dumps(location_data))
            print(f"Published to {TOPIC_GENERATE}: {location_data}")

        print("Published data for 20 additional vehicles. Delaying for 10 seconds...")
        time.sleep(10)  # Delay for 10 seconds

# Main function to set up the MQTT client and start publishing
def main():
    client = mqtt.Client()
    client.on_connect = on_connect

    # Connect to the MQTT broker
    try:
        print(f"Connecting to broker {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print(f"Error: Unable to connect to broker. {e}")
        return

    client.loop_start()

    try:
        # Start two parallel tasks: car data and additional vehicle data
        publish_car_data(client)  # Publishes car/location and car/speed
        publish_generated_data(client)  # Publishes generatelocandid
    except KeyboardInterrupt:
        print("Stopped publishing data.")
        client.loop_stop()
        client.disconnect()

# Run the script
if __name__ == "__main__":
    main()
