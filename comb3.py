import paho.mqtt.client as mqtt
import time
import json
import math

# MQTT broker details
BROKER = "broker.emqx.io"  # Replace with your broker's address
PORT = 1883
TOPIC_SPEED = "car/speed"
TOPIC_LOCATION = "car/location"
TOPIC_ALERT = "car/alert"
SPEED_CAP = 80  # Speed cap in km/h
ALERT_DISTANCE_THRESHOLD = 50  # Distance threshold in meters

# Data storage
car_locations = {}
car_speeds = {}

# Haversine formula to calculate the distance between two latitude/longitude points
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 * 1000  # Radius of Earth in meters
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Callback when the client successfully connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe([(TOPIC_SPEED, 0), (TOPIC_LOCATION, 0)])
        print(f"Subscribed to topics: {TOPIC_SPEED}, {TOPIC_LOCATION}")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    global car_locations, car_speeds

    topic = msg.topic
    payload = msg.payload.decode()
    timestamp = time.time()

    if topic == TOPIC_SPEED:
        try:
            data = json.loads(payload)
            car_id = data["id"]
            speed = data["speed"]
            car_speeds[car_id] = speed
            print(f"Speed received: {speed} km/h for car {car_id}")

            # Check if the speed exceeds the cap
            if speed > SPEED_CAP:
                print(f"Speed cap exceeded for car {car_id}. Sending alerts...")
                # Send alert to the speeding vehicle three times
                alert_message = f"Speed cap exceeded! Current speed: {speed} km/h. Please stop!"
                for _ in range(3):
                    client.publish(f"{TOPIC_ALERT}/{car_id}", alert_message)
                    print(f"Alert sent to {car_id}: {alert_message}")
                      # 1-second delay between alerts
                
                # Send alerts to all cars within 50 meters
                if car_id in car_locations:
                    lat1, lon1 = car_locations[car_id]
                    for other_car_id, (lat2, lon2) in car_locations.items():
                        if other_car_id != car_id:
                            distance = calculate_distance(lat1, lon1, lat2, lon2)
                            if distance <= ALERT_DISTANCE_THRESHOLD:
                                client.publish(f"{TOPIC_ALERT}/{other_car_id}", "Please be aware of a speeding car nearby!")
                                print(f"Alert sent to {other_car_id}: Speeding car nearby!")
        except ValueError:
            print(f"Invalid speed data received: {payload}")

    elif topic == TOPIC_LOCATION:
        try:
            data = json.loads(payload)
            car_id = data["id"]
            latitude = data["latitude"]
            longitude = data["longitude"]
            car_locations[car_id] = (latitude, longitude)
            print(f"Location updated for car {car_id}: ({latitude}, {longitude})")
        except Exception as e:
            print(f"Error processing location data: {e}")

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
        client.loop_forever()
    except KeyboardInterrupt:
        print("Stopping the server.")
        client.disconnect()

# Run the script
if __name__ == "__main__":
    main()