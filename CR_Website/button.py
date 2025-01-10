import paho.mqtt.client as mqtt
import json
import time
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT broker details
broker = "broker.emqx.io"
port = 1883
client_id = f"python-backend-{int(time.time())}"

# MQTT Topics
TOPICS = {
    "accident": "car/accident",
    "help": "car/help",
    "towing": "car/towing",
    "overspeeding": "car/overspeeding"
}

class EmergencyHandler:
    def __init__(self):
        self.client = mqtt.Client(client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.setup_client()

    def setup_client(self):
        try:
            self.client.connect(broker, port, 60)
            logger.info("Connected to MQTT broker successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            # Subscribe to all topics
            for topic in TOPICS.values():
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect, return code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            # Parse the incoming message
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on topic {msg.topic}: {payload}")

            # Process the message based on topic
            response = self.process_message(msg.topic, payload)

            # Send response back
            response_topic = f"{msg.topic}/response"
            response_payload = json.dumps(response)
            self.client.publish(response_topic, response_payload)
            logger.info(f"Sent response to {response_topic}: {response}")

        except json.JSONDecodeError:
            logger.error("Failed to decode message payload")
            self.send_error_response(msg.topic)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.send_error_response(msg.topic)

    def process_message(self, topic, payload):
        """Process incoming messages and return appropriate response"""
        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": True,
            "original_message": payload.get("message", ""),
        }

        if topic == TOPICS["accident"]:
            return self.handle_accident(payload, response)
        elif topic == TOPICS["help"]:
            return self.handle_help(payload, response)
        elif topic == TOPICS["towing"]:
            return self.handle_towing(payload, response)
        elif topic == TOPICS["overspeeding"]:
            return self.handle_overspeeding(payload, response)
        else:
            response["status"] = False
            response["message"] = "Unknown topic"
            return response

    def handle_accident(self, payload, response):
        if not self.verify_location(payload):
            return self.create_error_response("Location data required for accident reporting")

        logger.info("Processing accident report")
        response["message"] = "Accident report received and processed. Emergency services notified."
        return response

    def handle_help(self, payload, response):
        logger.info("Processing help request")
        response["message"] = "Help request received. Support team dispatched."
        return response

    def handle_towing(self, payload, response):
        if not self.verify_location(payload):
            return self.create_error_response("Location data required for towing service")

        logger.info("Processing towing request")
        response["message"] = "Towing request received. Service provider dispatched."
        return response

    def handle_overspeeding(self, payload, response):
        if not self.verify_location(payload):
            return self.create_error_response("Location data required for overspeeding report")

        logger.info("Processing overspeeding report")
        response["message"] = "Overspeeding report logged successfully."
        return response

    def verify_location(self, payload):
        """Verify that the payload contains valid location data"""
        location = payload.get("location", {})
        return (
            isinstance(location, dict) and
            "lat" in location and
            "lng" in location and
            isinstance(location["lat"], (int, float)) and
            isinstance(location["lng"], (int, float))
        )

    def create_error_response(self, message):
        """Create a standardized error response"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": False,
            "message": message
        }

    def send_error_response(self, original_topic):
        """Send an error response to a topic"""
        response = self.create_error_response("Error processing request")
        response_topic = f"{original_topic}/response"
        self.client.publish(response_topic, json.dumps(response))

    def run(self):
        """Start the MQTT client loop"""
        try:
            logger.info("Starting MQTT client loop")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down emergency handler")
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

class EmergencyApp:
    def __init__(self, handler):
        self.handler = handler
        self.root = tk.Tk()
        self.root.title("Emergency Handler GUI")
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Emergency Handler", font=("Arial", 16)).pack(pady=10)

        tk.Button(self.root, text="Report Accident", width=20, command=self.send_accident).pack(pady=5)
        tk.Button(self.root, text="Request Help", width=20, command=self.send_help).pack(pady=5)
        tk.Button(self.root, text="Request Towing", width=20, command=self.send_towing).pack(pady=5)
        tk.Button(self.root, text="Report Overspeeding", width=20, command=self.send_overspeeding).pack(pady=5)

    def send_message(self, topic, payload):
        """Send a message to the MQTT broker"""
        try:
            self.handler.client.publish(topic, json.dumps(payload))
            messagebox.showinfo("Success", f"Message sent to topic {topic}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")

    def send_accident(self):
        payload = {"message": "Accident reported", "location": {"lat": 12.9716, "lng": 77.5946}}
        self.send_message(TOPICS["accident"], payload)

    def send_help(self):
        payload = {"message": "Help requested"}
        self.send_message(TOPICS["help"], payload)

    def send_towing(self):
        payload = {"message": "Towing requested", "location": {"lat": 12.9716, "lng": 77.5946}}
        self.send_message(TOPICS["towing"], payload)

    def send_overspeeding(self):
        payload = {"message": "Overspeeding reported", "location": {"lat": 12.9716, "lng": 77.5946}}
        self.send_message(TOPICS["overspeeding"], payload)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    handler = EmergencyHandler()

    # Start MQTT client in a separate thread
    import threading
    threading.Thread(target=handler.run, daemon=True).start()

    # Start the GUI
    app = EmergencyApp(handler)
    app.run()
