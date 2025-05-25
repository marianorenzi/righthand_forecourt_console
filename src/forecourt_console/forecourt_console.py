#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from typing import Iterable
from datetime import datetime, timedelta
from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, TabbedContent
from widgets.pump_service import PumpServicePane
from widgets.sales_monitor import SalesMonitorPane
from widgets.textual_mqtt import MqttClient, MqttConnectionSubscription
import threading

class RightHandForecourtConsole(App):
    
    CSS_PATH = "style.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield MqttClient()
        yield Header(show_clock=True)
        with TabbedContent(initial="pump_service"):
            yield PumpServicePane("Pump Service", id="pump_service")
            yield SalesMonitorPane(title="Sales Monitor", id="sales_monitor")
        with Horizontal(id="new_footer"):
            with Horizontal(id="new_inner"):
                yield Footer()
            yield Label("🔴 MQTT Disconnected", id="mqtt_status")
        yield MqttConnectionSubscription()

    def on_mount(self) -> None:
        self.title = "RightHand Forecourt Console"

    @on(MqttConnectionSubscription.MqttConnected)
    def on_mqtt_connect(self, rc):
        self.query_one("#mqtt_status", Label).update("🟢 MQTT Connected")

    @on(MqttConnectionSubscription.MqttDisconnected)
    def on_mqtt_disconnect(self):
        self.query_one("#mqtt_status", Label).update("🔴 MQTT Disconnected")

if __name__ == "__main__":
    RightHandForecourtConsole().run()
