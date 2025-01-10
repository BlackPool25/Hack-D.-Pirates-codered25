import paho.mqtt.client as mqtt
import json
import time
import math
from geopy.distance import geodesic
from tempserver import send_data_to_main_server

# MQTT broker details
BROKER = "broker.emqx.io"  # Replace with your broker's address
PORT = 1883
TOPIC_VEHICLE_STATUS_CAR1 = "myvehiclestatus/car1"
TOPIC_VEHICLE_STATUS_CAR2 = "myvehiclestatus/car2"
TOPIC_VEHICLE_STATUS_CAR3 = "myvehiclestatus/car3"
TOPIC_SERVER_MAIN_CONTENT_SEND = "servermaincontentsend"
TOPIC_SEND_SERVER_DATA = "sendserverdata"  # Existing topic
TOPIC_SEND_SERVER_DATA1 = "sendserverdata1"  # New topic
TOPIC_ACCIDENT = "accident"
TOPIC_OVERSPEEDING = "overspeeding"
TOPIC_AUTHORITIES = "authorities"
TOPIC_ROAD_CONDITION = "roadcondition"
TOPIC_TRAFFIC = "traffic"
TOPIC_AMBLOC = "ambloc"
TOPIC_CAR_LOCATION = "car/location"
TOPIC_INPUT = "input"

# Data storage
vehicle_status_data = []
last_speed_store_time = 0
last_location = {}
car_locations = {}

# Thresholds
SPEED_CAP = 80  # Speed cap in km/h
LOCATION_DISTANCE_THRESHOLD = 5  # Location threshold in meters
STORE_INTERVAL = 30 * 60  # 30 minutes in seconds

# Function to calculate distance between two coordinates (latitude, longitude)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 * 1000  # Radius of Earth in meters
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_geodesic_distance(coord1, coord2):
    return geodesic(coord1, coord2).meters

# Callback for MQTT connection
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe([
            (TOPIC_VEHICLE_STATUS_CAR1, 0), 
            (TOPIC_VEHICLE_STATUS_CAR2, 0), 
            (TOPIC_VEHICLE_STATUS_CAR3, 0), 
            (TOPIC_ACCIDENT, 0), 
            (TOPIC_OVERSPEEDING, 0), 
            (TOPIC_AUTHORITIES, 0), 
            (TOPIC_ROAD_CONDITION, 0), 
            (TOPIC_TRAFFIC, 0), 
            (TOPIC_AMBLOC, 0), 
            (TOPIC_CAR_LOCATION, 0), 
            (TOPIC_INPUT, 0),
            (TOPIC_SEND_SERVER_DATA, 0),  # Subscribe to existing topic
            (TOPIC_SEND_SERVER_DATA1, 0)  # Subscribe to new topic
        ])
        print(f"Subscribed to all relevant topics")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback for receiving messages
def on_message(client, userdata, msg):
    global last_speed_store_time, last_location, car_locations
    topic = msg.topic
    payload = msg.payload.decode()
    timestamp = time.time()

    try:
        data = json.loads(payload)

        if topic in [TOPIC_VEHICLE_STATUS_CAR1, TOPIC_VEHICLE_STATUS_CAR2, TOPIC_VEHICLE_STATUS_CAR3]:
            car_id = data["vehicle_id"]
            latitude = data["latitude"]
            longitude = data["longitude"]
            speed = data.get("speed", None)

            # Store speed if it exceeds the cap or 30 minutes have passed
            if speed and (speed > SPEED_CAP or timestamp - last_speed_store_time >= STORE_INTERVAL):
                vehicle_status_data.append({"id": car_id, "speed": speed, "timestamp": timestamp})
                last_speed_store_time = timestamp
                print(f"Stored speed: {speed} km/h for {car_id}")

            # Check if the car has moved more than 5 meters
            if car_id in last_location:
                prev_lat, prev_lon = last_location[car_id]
                distance = calculate_distance(prev_lat, prev_lon, latitude, longitude)
                if distance >= LOCATION_DISTANCE_THRESHOLD:
                    vehicle_status_data.append({"id": car_id, "latitude": latitude, "longitude": longitude, "timestamp": timestamp})
                    last_location[car_id] = (latitude, longitude)
                    print(f"Stored location: {data} (Distance: {distance:.2f} meters)")
            else:
                # Store the first location
                last_location[car_id] = (latitude, longitude)
                vehicle_status_data.append({"id": car_id, "latitude": latitude, "longitude": longitude, "timestamp": timestamp})
                print(f"Stored initial location: {data}")

        elif topic == TOPIC_SEND_SERVER_DATA:
            print(f"Processing data received on {TOPIC_SEND_SERVER_DATA}: {data}")
            # Process the data and take necessary actions
            # Example: Send the data to the main server
            send_data_to_main_server(client, data)

        elif topic == TOPIC_SEND_SERVER_DATA1:
            print(f"Processing data received on {TOPIC_SEND_SERVER_DATA1}: {data}")
            # Process the data and take necessary actions
            # Example: Store the received data
            vehicle_status_data.append(data)

        # Process data for other topics and send to servermaincontentsend
        elif topic in [TOPIC_ACCIDENT, TOPIC_OVERSPEEDING, TOPIC_AUTHORITIES, TOPIC_ROAD_CONDITION, TOPIC_TRAFFIC]:
            print(f"Data received on topic {topic}: {data}")
            client.publish(TOPIC_SERVER_MAIN_CONTENT_SEND, json.dumps(data))
            print(f"Published to {TOPIC_SERVER_MAIN_CONTENT_SEND}: {data}")

        elif topic == TOPIC_AMBLOC:
            print(f"Received ambulance location: {data}")
            ambulance_coords = (data['location']['latitude'], data['location']['longitude'])
            cars_within_radius = []
            for car_id, car_coords in car_locations.items():
                distance = calculate_geodesic_distance(ambulance_coords, car_coords)
                if distance <= 50:
                    cars_within_radius.append(car_id)
            print(f"Cars within 50 meters of the ambulance: {cars_within_radius}")

        elif topic == TOPIC_CAR_LOCATION:
            car_location = data
            car_id = car_location['id']
            car_coords = (car_location['location']['latitude'], car_location['location']['longitude'])
            car_locations[car_id] = car_coords
            print(f"Updated car location: {car_id} -> {car_coords}")

        elif topic == TOPIC_INPUT:
            input_state = payload.strip().lower()
            if input_state == "true":
                print("Received 'true' on input topic. Ready to process emergency messages.")
            elif input_state == "false":
                print("Received 'false' on input topic. No action taken.")
            else:
                print("Invalid input received. Expected 'true' or 'false'.")

    except KeyError as e:
        print(f"KeyError: {e}. Check the keys in the received JSON data.")
    except Exception as e:
        print(f"Error processing message: {e}")

# Main function
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    try:
        print(f"Connecting to broker {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print(f"Error: Unable to connect to broker. {e}")
        return

    # Start the MQTT client loop
    try:
        client.loop_start()

        # Simulate sending data to main server periodically
        while True:
            send_data_to_main_server(client)
            time.sleep(STORE_INTERVAL)

    except KeyboardInterrupt:
        print("Stopping the server.")
        client.disconnect()

# Run the script
if __name__ == "__main__":
    main()
