#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from typing import Iterable
from datetime import datetime, timedelta
from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, TabbedContent
from widgets.pump_service import PumpServicePane
from widgets.pump_config import PumpConfigPane
from widgets.mqtt_console import MqttClientPane
from widgets.mqtt_console import MQTTClient

class RightHandForecourtConsole(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mqtt = MQTTClient()
        self.mqtt.connect()

    CSS_PATH = "style.tcss"

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
        # self.mqtt.connect()
        self.title = "RightHand Forecourt Console"
        self.mqtt.subscribe_on_connect(self.on_mqtt_connect)
        self.mqtt.subscribe_on_disconnect(self.on_mqtt_disconnect)

    def on_mqtt_connect(self):
        self.query_one("#mqtt_status", Label).update("🟢 MQTT Connected")

    def on_mqtt_disconnect(self):
        self.query_one("#mqtt_status", Label).update("🔴 MQTT Disconnected")

    # def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
    #     yield from super().get_system_commands(screen)

if __name__ == "__main__":
    RightHandForecourtConsole().run()
