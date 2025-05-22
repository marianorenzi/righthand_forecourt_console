from textual import on
from textual.app import ComposeResult
from datetime import datetime, timedelta
from textual.widget import Widget
from textual.widgets import Checkbox, Label, ListView, ListItem
from textual_plotext import PlotextPlot
from textual_slider import Slider
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from threading import Thread
import paho.mqtt.client as mqtt

class Probe(Widget):
    mqtt_client = mqtt.Client()
    mqtt_enabled = reactive(False)
    level = reactive(500)
    water = reactive(0)
    temperature = reactive(25)
    data = []

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                yield Label(f"Product Level: {self.level}", id="product_label")
                yield Slider(min=0, max=1000, value=self.level, id="product_slider")
                yield Label(f"Water Level: {self.water}", id="water_label")
                yield Slider(min=0, max=1000, value=self.water, id="water_slider")
                yield Label(f"Temperature: {self.temperature}", id="temperature_label")
                yield Slider(min=0, max=100, value=self.temperature, id="temperature_slider")
                yield Checkbox("Enable MQTT Publish", value=self.mqtt_enabled, id="mqtt_checkbox")
            yield ListView(
                ListItem(Label("One")),
                ListItem(Label("Two")),
                ListItem(Label("Three")),
            )
        yield PlotextPlot()

    def on_mount(self):
        # initialize plot
        plt = self.query_one(PlotextPlot).plt
        plt.date_form("Y/m/d H:M:S.f")
        plt.title("Probe data (Last Hour)")
        plt.xlabel("Time")
        plt.ylabel("Value")

        # self.query_one("#mqtt_checkbox").watch("value", self.toggle_mqtt)
        
        self.handle_mqtt_connection()
        self.running = True
        self.mqtt_thread = Thread(target=self.probe_thread, daemon=True)
        self.mqtt_thread.start()
    
    def on_unmount(self):
        self.running = False
        self.mqtt_client.disconnect()
        
    @on(Slider.Changed, "#product_slider")
    def on_product_slider_changed_value(self) -> None:
        self.level = self.query_one("#product_slider", Slider).value
        self.query_one("#product_label", Label).update(f"Product Level: {self.level}")

    @on(Slider.Changed, "#water_slider")
    def on_water_slider_changed_value(self) -> None:
        self.water = self.query_one("#water_slider", Slider).value
        self.query_one("#water_label", Label).update(f"Water Level: {self.water}")

    @on(Slider.Changed, "#temperature_slider")
    def on_temperature_slider_changed_value(self) -> None:
        self.temperature = self.query_one("#temperature_slider", Slider).value
        self.query_one("#temperature_label", Label).update(f"Temperature: {self.temperature}")
    
    @on(Checkbox.Changed)
    def toggle_mqtt(self) -> None:
        self.mqtt_enabled = self.query_one("#mqtt_checkbox", Checkbox).value
        self.handle_mqtt_connection()

    def handle_mqtt_connection(self):
        if self.mqtt_enabled:
            self.mqtt_client.connect("localhost", 1883, 60)
            self.notify("Connected to MQTT broker")
        else:
            self.mqtt_client.disconnect()
            self.notify("Disconnected from MQTT broker")
    
    def probe_thread(self):
        while self.running:
            now = datetime.now()
            timestamp = now.strftime("%Y/%m/%d %H:%M:%S.%f")
            self.data.append((timestamp, self.level, self.water, self.temperature))

            # Keep only the last hour of data
            self.data = [(t, l, w, temp) for t, l, w, temp in self.data if now - datetime.strptime(t, "%Y/%m/%d %H:%M:%S.%f") <= timedelta(hours=1)]
            
            if self.mqtt_enabled:
               payload = json.dumps({"id": 1, "time": timestamp, "l": self.level, "w": self.water, "t": self.temperature})
               self.mqtt_client.publish("data/probe/1/level", payload)

            self.replot()
            
            time.sleep(1)
    
    def replot(self) -> None:
        """Redraw the plot."""
        if self.data:
            widget = self.query_one(PlotextPlot)
            plt = widget.plt
            plt.clear_data()
            times, levels, waters, temperatures = zip(*self.data)
            plt.plot(times, levels, marker="hd", label="Product Level")
            plt.plot(times, waters, marker="hd", label="Water Level")
            plt.plot(times, temperatures, marker="hd", label="Temperature")
            widget.refresh()