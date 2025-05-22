from textual import on
from textual.worker import get_current_worker
from textual.app import ComposeResult
from textual.widgets import TabPane, Log
from textual.widget import Widget
from textual.message import Message
from datetime import datetime
import paho.mqtt.client as mqtt
import time

class MqttClient:
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

    class MqttMessage(Message):
        def __init__(self, topic: str, payload: str) -> None:
            super().__init__()
            self.topic = topic
            self.payload = payload

    class MqttConnected(Message): pass
    class MqttDisonnected(Message): pass

    def connect(self):
        self.client.connect(self.host, self.port, keepalive=60)
        while (not get_current_worker().is_cancelled):
            self.client.loop()

    def on_connect(self, client, userdata, flags, rc):
        # if rc != 0: return

        for topic in self.subscribers:
            client.subscribe(topic)
        if self.subscribe_all:
            client.subscribe('#')
        for callback in self.on_connect_subscribers:
            callback(rc)

    def on_disconnect(self, client, userdata, rc):
        for callback in self.on_disconnect_subscribers:
            callback()

    def on_message(self, client, userdata, msg):
        if msg.topic in self.subscribers:
            self.subscribers[msg.topic].post_message(self.MqttMessage(msg.topic, msg.payload.decode()))
        for widget in self.subscribers_all:
            widget.post_message(self.MqttMessage(msg.topic, msg.payload.decode()))

    # def subscribe(self, topic, callback):
    #     if topic not in self.subscribers:
    #         self.client.subscribe(topic)
    #     self.subscribers[topic] = callback

    def subscribe(self, topic, widget: Widget):
        if topic not in self.subscribers:
            self.client.subscribe(topic)
        self.subscribers[topic] = widget

    def unsubscribe(self, topic):
        if topic in self.subscribers:
            self.client.unsubscribe(topic)
            del self.subscribers[topic]


    def subscribe_all(self, widget: Widget):
        if not self.subscribers_all:
            self.client.subscribe('#')
        self.subscribers_all.append(widget)

    def subscribe_on_connect(self, callback):
        if callback not in self.on_connect_subscribers:
            self.on_connect_subscribers.append(callback)
            if self.client.is_connected():
                callback(77)

    def unsubscribe_on_connect(self, callback):
        if callback in self.on_connect_subscribers:
            self.on_connect_subscribers.remove(callback)

    def subscribe_on_disconnect(self, callback):
        if callback not in self.on_disconnect_subscribers:
            self.on_disconnect_subscribers.append(callback)

    def publish(self, topic, payload):
        self.client.publish(topic, payload)


class MqttViewer(Log):
    def __init__(self, mqtt_client: MqttClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    def on_mount(self):
        self.mqtt_client.subscribe_all(self)

    @on(MqttClient.MqttMessage)
    def on_mqtt_message(self, message: MqttClient.MqttMessage):
        self.write_line(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + message.topic + " " + message.payload)

class MqttClientPane(TabPane):
    def __init__(self, mqtt_client: MqttClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    def compose(self) -> ComposeResult:
        yield MqttViewer(self.mqtt_client)