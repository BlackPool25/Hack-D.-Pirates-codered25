import math
import random
import json
import paho.mqtt.client as mqtt
from geopy.distance import geodesic

# MQTT broker details
broker = "broker.emqx.io"
port = 1883

# Topic for the vehicle's status
my_vehicle_status_topic = "myvehiclestatus/car3"

# Central location (latitude and longitude) from myvehiclestatus/car3
central_lat = 12.9715987  # Example latitude for Bengaluru
central_lon = 77.594566  # Example longitude for Bengaluru

# Variable to represent the ambulance's siren state
ambulance = {"siren_on": False}

# Function to generate random latitude and longitude within a certain distance
def generate_random_location(lat, lon, radius):
    R = 6371 * 1000  # Earth's radius in meters
    radius_in_degrees = radius / R

    u = random.random()
    v = random.random()

    w = radius_in_degrees * math.sqrt(u)
    t = 2 * math.pi * v
    x = w * math.cos(t)
    y = w * math.sin(t)

    new_lat = lat + (x / math.cos(lon))
    new_lon = lon + y

    return new_lat, new_lon

# Generate 20 cars with random locations and speeds
cars = []
for i in range(1, 21):
    car_id = f"car{i}"
    lat, lon = generate_random_location(central_lat, central_lon, 1000)  # 1 km radius
    speed = random.uniform(0, 100)  # Random speed between 0 and 100 km/h
    cars.append({"vehicle_id": car_id, "latitude": lat, "longitude": lon, "speed": speed})

# Function to calculate distance between two coordinates (latitude, longitude)
def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).meters

# Check for cars within 50 meters of the central location
alert_distance_threshold = 50  # 50 meters
cars_in_proximity = []

for car in cars:
    distance = calculate_distance((central_lat, central_lon), (car["latitude"], car["longitude"]))
    if distance <= alert_distance_threshold:
        cars_in_proximity.append(car)

# Display the IDs, locations, and speeds of cars within 50 meters
if cars_in_proximity:
    print("Cars within 50 meters of the central location (myvehiclestatus/car3):")
    for car in cars_in_proximity:
        print(f"Vehicle ID: {car['vehicle_id']}, Location: ({car['latitude']}, {car['longitude']}), Speed: {car['speed']} km/h")
else:
    print("No cars within 50 meters of the central location.")

# Optional: Save generated car data to a file
with open("generated_cars.json", "w") as f:
    json.dump(cars, f, indent=4)

# Callback when the client successfully connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(my_vehicle_status_topic)
        print(f"Subscribed to topic: {my_vehicle_status_topic}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global ambulance

    if msg.topic == my_vehicle_status_topic:
        try:
            status_data = json.loads(msg.payload.decode())
            ambulance["siren_on"] = status_data.get("siren_on", False)

            if ambulance["siren_on"]:
                print("Ambulance siren is ON. Processing emergency procedures.")
                # Add your processing logic here
            else:
                print("Ambulance siren is OFF. No emergency detected.")

        except KeyError as e:
            print(f"KeyError: {e}. Check the keys in the received JSON data.")
        except Exception as e:
            print(f"Error: {e}")

# Main function to set up the MQTT client
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    try:
        print(f"Connecting to broker {broker}:{port}...")
        client.connect(broker, port, 60)
    except Exception as e:
        print(f"Error: Unable to connect to broker. {e}")
        return

    client.loop_forever()

# Run the script
if __name__ == "__main__":
    main()

