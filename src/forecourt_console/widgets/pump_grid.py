from textual import on
from textual.app import ComposeResult
from textual.containers import Grid, ItemGrid, Container
from textual.widgets import ListView, ListItem
from textual.message import Message
from textual.reactive import reactive
from widgets.pump import Pump
from widgets.textual_mqtt import MqttMessageSubscription, MqttConnectionSubscription, MqttEvent
import json

class PumpGrid(Container):

    existing_pumps = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield ListView()
        yield MqttMessageSubscription("res/pumps/0/ids", id="ids")
        yield MqttMessageSubscription("evt/pumps/0/connection_established", id="connection_established")
        yield MqttConnectionSubscription()

    @on(MqttConnectionSubscription.MqttConnected)
    @on(MqttMessageSubscription.MqttMessageEvent, "#connection_established")
    def on_mqtt_connect(self, evt: MqttEvent):
        evt.control.publish(f"cmd/pumps/0/ids")

    @on(MqttMessageSubscription.MqttMessageEvent, "#ids")
    # @on(MqttMessageSubscription.MqttMessageEvent)
    def on_mqtt_ids(self, evt: MqttMessageSubscription.MqttMessageEvent):
        try:
            self.existing_pumps = json.loads(evt.payload)
            self.mount_pumps()
        except Exception as e:
            self.log.error(f"Error ON MQTT IDs: Payload={evt.payload}. {e}")

    def mount_pumps(self):
        # remove current pump widgets
        self.index = None
        self.post_message(ListView.Selected(self.query_one(ListView), ListItem()))
        for pump in self.query_one(ListView).query(Pump):
            pump.remove()

        # mount new ones
        for pump_id in self.existing_pumps:
            new_pump = Pump(pump_id)
            self.query_one(ListView).mount(new_pump)

        # force selection on first
        if len(self.children) > 0 and isinstance(self.children[0], Pump):
            self.index = 0
            self.post_message(ListView.Selected(self.query_one(ListView), self.children[0]))

    def set_auto_sale_config(self, auto_sale_config: dict):
        if auto_sale_config["pumps"] == 0:
            # all pumps
            for pump in self.query(Pump):
                pump.set_auto_sale_config(auto_sale_config)
        elif self.index != None:
            pump = self.children[self.index]
            if isinstance(pump, Pump): pump.set_auto_sale_config(auto_sale_config)
