from textual import on
from textual.app import ComposeResult
from textual.widgets import Label, TabPane, DataTable
from textual.containers import Container
from textual_mqtt import MqttMessageSubscription
import json

class SalesMonitorPane(TabPane):

    COLUMNS = ("Pump ID", "Grade", "Volume", "Money", "Price", "Start Time", "End Time")

    def __init__(self, title: str, **kwargs):
        super().__init__(title, **kwargs)

    def compose(self) -> ComposeResult:
        yield DataTable()
        yield MqttMessageSubscription("evt/pumps/+/sale_end")

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns(*self.COLUMNS)

    @on(MqttMessageSubscription.MqttMessageEvent)
    def on_mqtt_message(self, evt: MqttMessageSubscription.MqttMessageEvent):
        evt.stop()
        # parse sale
        topic = evt.topic.split("/")
        sale = json.loads(evt.payload)
        self.query_one(DataTable).add_row(*(topic[2], sale["grade"], sale["volume"], sale["money"], sale["price"], sale["start_time"], sale["end_time"]))