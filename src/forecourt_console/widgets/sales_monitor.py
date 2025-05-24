from textual import on
from textual.app import ComposeResult
from textual.widgets import Label, TabPane, DataTable
from textual.containers import Container
from widgets.mqtt_console import MqttClient
import json

class SalesMonitorPane(TabPane):

    COLUMNS = ("Pump ID", "Grade", "Volume", "Money", "Price", "Start Time", "End Time")

    def __init__(self, title: str, **kwargs):
        super().__init__(title, **kwargs)

    def compose(self) -> ComposeResult:
        yield DataTable()

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns(*self.COLUMNS)
        self.app.mqtt.subscribe(f"evt/pumps/+/sale_end", self)

    @on(MqttClient.MqttMessage)
    def on_mqtt_message(self, message: MqttClient.MqttMessage):
        # parse sale
        topic = message.topic.split("/")
        sale = json.loads(message.payload)
        self.query_one(DataTable).add_row(*(topic[2], sale["grade"], sale["volume"], sale["money"], sale["price"], sale["start_time"], sale["end_time"]))