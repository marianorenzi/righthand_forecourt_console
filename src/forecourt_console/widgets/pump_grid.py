from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, ItemGrid
from textual.widgets import ListView, ListItem
from textual.message import Message
from textual.reactive import reactive
from widgets.pump import Pump
from widgets.mqtt_console import MqttClient
from widgets.pump_details import PumpDetails
import json
import threading

class PumpGrid(ListView):

    existing_pumps = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_mount(self):
        self.app.mqtt.subscribe("res/pumps/0/ids", self)
        self.app.mqtt.subscribe("evt/pumps/0/connection_established", self)
        self.app.mqtt.subscribe_on_connect(self.on_mqtt_connect)

    @on(MqttClient.MqttMessage)
    def on_mqtt_message(self, message: MqttClient.MqttMessage):
        if message.topic == "res/pumps/0/ids":
            self.on_mqtt_ids(message.payload)
        elif message.topic == "evt/pumps/0/connection_established":
            self.on_mqtt_connect(99)

    def on_mqtt_connect(self, rc):
        self.app.mqtt.publish(f"cmd/pumps/0/ids", "")

    def on_mqtt_ids(self, payload: str):
        self.existing_pumps = json.loads(payload)
        self.mount_pumps()

    def mount_pumps(self):
        # remove current pump widgets
        self.index = None
        self.post_message(ListView.Selected(self, ListItem()))
        for pump in self.query(Pump):
            pump.remove()

        # mount new ones
        for pump_id in self.existing_pumps:
            new_pump = Pump(pump_id)
            self.mount(new_pump)

        # force selection on first
        if len(self.children) > 0 and isinstance(self.children[0], Pump):
            self.index = 0
            self.post_message(ListView.Selected(self, self.children[0]))
