from flask import Flask, request, jsonify
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

# In-memory storage for demonstration purposes
data_store = {
    "accident": [],
    "cartow": [],
    "overspeeding": [],
    "roadcondition": [],
    "traffic": [],
    "myvehiclestatus": [],
    "serverdata/carid": [],
    "Serversend1": []
}

# MQTT broker details
broker = "broker.emqx.io"
port = 1883

# Callback when the client successfully connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to all relevant topics
        client.subscribe("accident")
        client.subscribe("cartow")
        client.subscribe("overspeeding")
        client.subscribe("roadcondition")
        client.subscribe("traffic")
        client.subscribe("myvehiclestatus")
        client.subscribe("serverdata/carid")
        client.subscribe("Serversend1")
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = json.loads(msg.payload.decode())
    if topic in data_store:
        data_store[topic].append(payload)
        print(f"Received and stored message on {topic}: {payload}")

# Initialize MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Button Server!"})

@app.route('/get_data/<topic>', methods=['GET'])
def get_data(topic):
    if topic in data_store:
        return jsonify(data_store[topic]), 200
    else:
        return jsonify({"error": "Invalid topic"}), 400

# Main function to connect to MQTT broker and start Flask app
def main():
    try:
        mqtt_client.connect(broker, port, 60)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return

    mqtt_client.loop_start()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
    


