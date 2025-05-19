from textual.app import ComposeResult
from textual.containers import Grid, ItemGrid
from textual.widgets import ListView, ListItem
from textual.reactive import reactive
from widgets.pump import Pump
from widgets.mqtt_console import MQTTClient
import json

class PumpGrid(ListView):

    def __init__(self, mqtt_client: MQTTClient, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_client = mqtt_client

    # def compose(self) -> ComposeResult:
    #     yield None

    def on_mount(self):
        self.mqtt_client.subscribe("res/pumps/0/ids", self.on_mqtt_ids)
        self.mqtt_client.subscribe("evt/pumps/0/connection_established", self.on_mqtt_connection_established)
        self.mqtt_client.subscribe_on_connect(self.on_mqtt_connect)

    def on_mqtt_connect(self):
        def req_ids():
            self.mqtt_client.publish(f"cmd/pumps/0/ids", "")

        try:
            self.app.call_from_thread(req_ids)
        except Exception as e:
            req_ids()

    def on_mqtt_connection_established(self, topic: str, payload: str):
        self.on_mqtt_connect()

    def on_mqtt_ids(self, topic: str, payload: str):
        def mount_pumps():
            # remove current pump widgets
            self.index = None
            self.post_message(ListView.Selected(self, ListItem()))
            for pump in self.query(Pump):
                pump.remove()

            # mount new ones
            for pump_id in existing_pumps:
                new_pump = Pump(pump_id, self.mqtt_client)
                self.mount(new_pump)

            # force selection on first
            if len(self.children) > 0 and isinstance(self.children[0], Pump):
                self.index = 0
                self.post_message(ListView.Selected(self, self.children[0]))

        existing_pumps = json.loads(payload)
        self.app.call_from_thread(mount_pumps)

