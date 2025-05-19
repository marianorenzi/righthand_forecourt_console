from textual.app import ComposeResult
from textual.containers import Grid, ItemGrid
from textual.widgets import ListView
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
        self.mqtt_client.subscribe_on_connect(self.on_mqtt_connect)

    def on_mqtt_connect(self):
        self.mqtt_client.publish(f"cmd/pumps/0/ids", "")

    def on_mqtt_ids(self, topic: str, payload: str):
        existing_pumps = json.loads(payload)

        def mount_pumps():
            for pump_id in existing_pumps:
                new_pump = Pump(pump_id, self.mqtt_client)
                self.mount(new_pump)

        def select_first():
            if len(self.children) > 0 and isinstance(self.children[0], Pump):
                self.index = 0
                self.post_message(ListView.Selected(self, self.children[0]))

        self.app.call_from_thread(mount_pumps)
        select_first()

