import json
import math
import time
import random
import paho.mqtt.client as mqtt

# MQTT broker details
broker = "broker.emqx.io"
port = 1883
topics = ["myvehiclestatus/car1", "myvehiclestatus/car2", "myvehiclestatus/car3"]

car_locations = {}
car_speeds = {}
alert_distance_threshold = 50

def classify_density(vehicle_count):
    return random.choice(["low", "medium", "high"])

def calculate_average_speed(data):
    if len(data) == 0:
        return 0
    total_speed = sum(item.get('speed', 0) for item in data)
    return total_speed / len(data)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 * 1000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def process_data(client):
    while True:
        with open("data.json", "r") as f:
            data = json.load(f)

        avg_speed = calculate_average_speed(data)
        density = classify_density(len(data))

        if density == "high":
            threshold = avg_speed * 1.25
        elif density == "low":
            threshold = avg_speed * 1.75
        else:
            threshold = avg_speed * 1.5

        client.publish("client_process", json.dumps({"threshold": threshold}))

        with open("data.json", "w") as f:
            json.dump([], f)

        time.sleep(10)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        for topic in topics:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global car_locations, car_speeds

    topic = msg.topic
    payload = msg.payload.decode()

    try:
        data = json.loads(payload)
        vehicle_id = data["vehicle_id"]
        latitude = data["latitude"]
        longitude = data["longitude"]
        speed = data["speed"]
        
        car_speeds[vehicle_id] = speed
        car_locations[vehicle_id] = (latitude, longitude)
        
        print(f"Location updated for car {vehicle_id}: ({latitude}, {longitude})")
        print(f"Speed received: {speed} km/h for car {vehicle_id}")

        with open("data.json", "r") as f:
            existing_data = json.load(f)
        
        existing_data.append(data)
        
        with open("data.json", "w") as f:
            json.dump(existing_data, f)

        # Calculate dynamic speed cap based on density
        avg_speed = calculate_average_speed(existing_data)
        density = classify_density(len(existing_data))

        if density == "high":
            speed_cap = avg_speed * 1.25
        elif density == "low":
            speed_cap = avg_speed * 1.75
        else:
            speed_cap = avg_speed * 1.5

        # Set the alert threshold as the minimum of 60 km/h and calculated speed cap
        alert_threshold = min(60, speed_cap)

        if speed > alert_threshold:
            print(f"Speed alert for car {vehicle_id}. Sending alerts...")
            alert_message = f"Speed alert! Current speed: {speed} km/h. Please slow down!"
            for _ in range(3):
                client.publish(f"alert/{vehicle_id}", alert_message)
                print(f"Alert sent to {vehicle_id}: {alert_message}")
                time.sleep(1)

            lat1, lon1 = car_locations[vehicle_id]
            for other_vehicle_id, (lat2, lon2) in car_locations.items():
                if other_vehicle_id != vehicle_id:
                    distance = calculate_distance(lat1, lon1, lat2, lon2)
                    if distance <= alert_distance_threshold:
                        client.publish(f"alert/{other_vehicle_id}", "Please be aware of a speeding car nearby!")
                        print(f"Alert sent to {other_vehicle_id}: Speeding car nearby!")
    except Exception as e:
        print(f"Error processing message: {e}")


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
    process_data(client)
    client.loop_stop()

if __name__ == "__main__":
    main()
