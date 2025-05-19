from textual.app import ComposeResult
from textual.widgets import Label, TabPane, Log
from datetime import datetime
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host: str="localhost", port: int=1883):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.host = host
        self.port = port
        self.subscribers = {}
        self.subscribers_all = []
        self.on_connect_subscribers = []
        self.on_disconnect_subscribers = []

    def connect(self):
        self.client.connect_async(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        # if rc != 0: return

        for topic in self.subscribers:
            client.subscribe(topic)
        if self.subscribe_all:
            client.subscribe('#')
        for callback in self.on_connect_subscribers:
            callback()

    def on_disconnect(self, client, userdata, rc):
        for callback in self.on_disconnect_subscribers:
            callback()

    def on_message(self, client, userdata, msg):
        if msg.topic in self.subscribers:
            self.subscribers[msg.topic](msg.topic, msg.payload.decode())
        for callback in self.subscribers_all:
            callback(msg.topic, msg.payload.decode())

    def subscribe(self, topic, callback):
        if topic not in self.subscribers:
            self.client.subscribe(topic)
        self.subscribers[topic] = callback

    def unsubscribe(self, topic):
        if topic in self.subscribers:
            self.client.unsubscribe(topic)
            del self.subscribers[topic]


    def subscribe_all(self, callback):
        if not self.subscribers_all:
            self.client.subscribe('#')
        self.subscribers_all.append(callback)

    def subscribe_on_connect(self, callback):
        self.on_connect_subscribers.append(callback)
        if self.client.is_connected():
            callback()

    def unsubscribe_on_connect(self, callback):
        if callback in self.on_connect_subscribers:
            self.on_connect_subscribers.remove(callback)

    def subscribe_on_disconnect(self, callback):
        self.on_disconnect_subscribers.append(callback)

    def publish(self, topic, payload):
        self.client.publish(topic, payload)


class MqttViewer(Log):
    def __init__(self, mqtt_client: MQTTClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    def on_mount(self):
        self.mqtt_client.subscribe_all(self.on_mqtt_message)

    def on_mqtt_message(self, topic: str, payload: str):
        self.write_line(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + topic + " " + payload)

class MqttClientPane(TabPane):
    def __init__(self, mqtt_client: MQTTClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    def compose(self) -> ComposeResult:
        yield MqttViewer(self.mqtt_client)