from textual.app import ComposeResult
from textual.widgets import Label, TabPane, ListView
from textual.containers import VerticalScroll
from widgets.pump_details import PumpDetails
from widgets.pump_grid import PumpGrid
from widgets.pump import Pump
from widgets.mqtt_console import MqttViewer
from widgets.mqtt_console import MQTTClient

class PumpServicePane(TabPane):
    def __init__(self, title: str, mqtt_client: MQTTClient, **kwargs):
        super().__init__(title, **kwargs)
        self.mqtt_client = mqtt_client

    BINDINGS = [
    ("[", "prev_probe", "Previous probe"),
    ("]", "next_probe", "Next probe"),
    ]
        
    def compose(self) -> ComposeResult:
        yield PumpDetails()
        yield PumpGrid(self.mqtt_client)
        yield MqttViewer(self.mqtt_client, auto_scroll=True)

    def on_mount(self):
        self.query_one(PumpGrid).focus()

    def on_list_view_selected(self, event: ListView.Selected):
        if isinstance(event.item, Pump):
            self.query_one(PumpDetails).set_pump(event.item)
        else:
            self.notify("Selected item is not a Pump!")