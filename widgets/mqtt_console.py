from textual.app import ComposeResult
from textual.widgets import Label, TabPane, Log
from datetime import datetime
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host: str="localhost", port: int=1883):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.host = host
        self.port = port
        self.subscribers = {}
        self.on_connect_subscribers = []

    def connect(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with code {rc}")
        for topic in self.subscribers:
            client.subscribe(topic)
        for callback in self.on_connect_subscribers:
            callback()

    def on_message(self, client, userdata, msg):
        if msg.topic in self.subscribers:
            for callback in self.subscribers[msg.topic]:
                callback(msg.topic, msg.payload.decode())
        if "#" in self.subscribers:
            for callback in self.subscribers["#"]:
                callback(msg.topic, msg.payload.decode())

    def subscribe(self, topic, callback):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
            self.client.subscribe(topic)
        self.subscribers[topic].append(callback)

    def subscribe_on_connect(self, callback):
        self.on_connect_subscribers.append(callback)
        if self.client.is_connected():
            callback()

    def publish(self, topic, payload):
        self.client.publish(topic, payload)


class MqttViewer(Log):
    def __init__(self, mqtt_client: MQTTClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    def on_mount(self):
        self.mqtt_client.subscribe("#", self.on_mqtt_message)

    def on_mqtt_message(self, topic: str, payload: str):
        self.write_line(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + topic + " " + payload)

class MqttClientPane(TabPane):
        
    def compose(self) -> ComposeResult:
        yield Label("WIP")