#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from typing import Iterable
from datetime import datetime, timedelta
from textual import work
from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, TabbedContent
from widgets.pump_service import PumpServicePane
from widgets.mqtt_console import MqttClientPane
from widgets.mqtt_console import MqttClient
import threading

class RightHandForecourtConsole(App):
    
    CSS_PATH = "style.tcss"

    mqtt: MqttClient

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mqtt = MqttClient()

    @work(thread=True, group="mqtt")
    def start_mqtt(self):
        self.mqtt.connect()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="pump_service"):
            yield PumpServicePane("Pump Service", self.mqtt, id="pump_service")
            yield MqttClientPane(self.mqtt, title="MQTT Console", id="mqtt_console")
        with Horizontal(id="new_footer"):
            with Horizontal(id="new_inner"):
                yield Footer()
            yield Label("🔴 MQTT Disconnected", id="mqtt_status")

    def on_mount(self) -> None:
        self.start_mqtt()
        self.title = "RightHand Forecourt Console"
        self.mqtt.subscribe_on_connect(self.on_mqtt_connect)
        self.mqtt.subscribe_on_disconnect(self.on_mqtt_disconnect)

    def on_mqtt_connect(self, rc):
        self.query_one("#mqtt_status", Label).update("🟢 MQTT Connected")

    def on_mqtt_disconnect(self):
        self.query_one("#mqtt_status", Label).update("🔴 MQTT Disconnected")

if __name__ == "__main__":
    RightHandForecourtConsole().run()
